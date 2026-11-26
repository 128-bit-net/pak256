"""AMI の 256 版の道（obj=way）の絵の縁が、横 4px・縦 2px の階段になっていないかを調べる（#111）。

256 のタイルの菱形の縁は、横 2px・縦 1px の段（pak256 の地面 objects/ground と同じ）。pak128 の大きさで切ったマスクを
2 倍にすると、横 4px・縦 2px の段になる。セルの絵の上と下の輪郭を列ごとに読み、「横 4px の平らな所が、縦に 2px ずつ
同じ向きにずれて MIN_STEPS 個以上続く」所を階段とみなす。坂のタイルの縁（横 4px・縦 1px など）や、形そのものの長い
水平な縁は数えない。

見るセルは、src256/ の dat のうち obj=way で高架（system_type=1）でないものの、image[<形>] と diagonal[<形>]（何も
つながらない image[-] は除く）。絵のシートは pak に組む前の PNG なので、AMI の 256 版を組むとき（build_ami256.py の
check の段）に流す。

使い方:
    python -X utf8 tools/check_way_edges.py <AMI の src256 のフォルダ> [--partial]
--partial はシートの無い dat を飛ばす（試しの build）。階段があるか、調べたセルが 1 つも無ければ終了コード 1。
"""
import argparse
import glob
import os
import re
import sys

from PIL import Image, ImageChops

CELL = 512  # AMI の 256 版のセルの一辺（pak256 のアドオンは makeobj の pak512）
TRANSPARENT = (231, 255, 255)
STEP_W, STEP_H = 4, 2  # 見つける段の形（横・縦）
MIN_STEPS = 3
IMAGE_RE = re.compile(r"^(?:image|diagonal)\[([a-z0-9]+)\](?:\[\d+\])*=\s*(?:>\s*)?([\w\-]+)\.(\d+)\.(\d+)", re.I)


def way_cells(dat_text):
    """dat の文から、調べるセル (キー, シートの名前, 行, 列) を返す。way でない・高架の物は空。"""
    out = []
    for block in re.split(r"(?m)^-{2,}.*$", dat_text):
        lines = [line.strip() for line in block.splitlines()]
        values = {k.strip().lower(): v.strip() for k, _, v in (line.partition("=") for line in lines) if v}
        if values.get("obj", "").lower() != "way" or values.get("system_type") == "1":
            continue
        for line in lines:
            m = IMAGE_RE.match(line)
            if m:  # image[-]（何もつながらない絵）は [a-z0-9]+ に当たらない
                out.append((line.partition("=")[0], m.group(2), int(m.group(3)), int(m.group(4))))
    return out


def outlines(cell):
    """セルの絵の上と下の輪郭 {x: y}（透明でない画素の最初と最後の行）。"""
    rgba = cell.convert("RGBA")
    width, height = rgba.size
    r, g, b = ImageChops.difference(rgba.convert("RGB"), Image.new("RGB", rgba.size, TRANSPARENT)).split()
    colored = ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v else 0)
    mask = ImageChops.darker(colored, rgba.getchannel("A").point(lambda v: 255 if v else 0))
    top, bottom = {}, {}
    for x in range(width):
        box = mask.crop((x, 0, x + 1, height)).getbbox()
        if box:
            top[x], bottom[x] = box[1], box[3] - 1
    return top, bottom


def flats(outline):
    """輪郭を、隣り合う列で同じ高さの所にまとめる: [(始まりの x, 幅, y)]。"""
    out = []
    for x in sorted(outline):
        y = outline[x]
        if out and out[-1][0] + out[-1][1] == x and out[-1][2] == y:
            out[-1][1] += 1
        else:
            out.append([x, 1, y])
    return [tuple(f) for f in out]


def staircase(outline):
    """横 STEP_W・縦 STEP_H の段が続く数の最大と、その始まりの (x, y)。段が無ければ (0, None)。"""
    best, best_at = 0, None
    count, sign, start, prev = 0, 0, None, None
    for x, w, y in flats(outline):
        if w != STEP_W:
            count, prev = 0, None
            continue
        if prev and prev[0] + STEP_W == x and abs(y - prev[1]) == STEP_H:
            s = 1 if y > prev[1] else -1
            if s == sign or count == 1:
                count += 1
            else:  # 向きが変わった（山・谷）: 前の段から数え直す
                count, start = 2, prev
            sign = s
        else:
            count, sign, start = 1, 0, (x, y)
        prev = (x, y)
        if count > best:
            best, best_at = count, start
    return best, best_at


def check(src_dir, partial=False):
    """src_dir の dat とシートを調べる。(調べたセルの数, 問題の行の一覧) を返す。"""
    sheets, seen, problems = {}, {}, []
    for dat in sorted(glob.glob(os.path.join(src_dir, "*.dat"))):
        with open(dat, encoding="utf-8", errors="replace") as f:
            cells = way_cells(f.read())
        for key, sheet, row, col in cells:
            if (sheet, row, col) in seen:
                continue
            seen[(sheet, row, col)] = True
            if sheet not in sheets:
                path = os.path.join(src_dir, sheet + ".png")
                sheets[sheet] = Image.open(path).convert("RGBA") if os.path.isfile(path) else None
                if sheets[sheet] is None and not partial:
                    problems.append(f"{sheet}.png が無い（{os.path.basename(dat)}）")
            im = sheets[sheet]
            if im is None:
                del seen[(sheet, row, col)]
                continue
            box = (col * CELL, row * CELL, (col + 1) * CELL, (row + 1) * CELL)
            if box[2] > im.width or box[3] > im.height:
                problems.append(f"{sheet}.{row}.{col} がシートの外（{os.path.basename(dat)} の {key}）")
                continue
            for side, outline in zip(("上", "下"), outlines(im.crop(box))):
                n, at = staircase(outline)
                if n >= MIN_STEPS:
                    problems.append(f"{sheet}.{row}.{col}（{key}）の{side}の縁: 横 {STEP_W}px・縦 {STEP_H}px の段が {n} 個"
                                    f"続く（セル内の x={at[0]} y={at[1]} から）")
    return len(seen), problems


def report(count, problems, limit=20):
    """結果を出して、通れば True。"""
    for p in problems[:limit]:
        print("   ", p)
    if len(problems) > limit:
        print(f"    ほか {len(problems) - limit} 件")
    if not count:
        print("道の縁の検査: 調べるセルが 1 つも無い")
        return False
    print(f"道の縁の検査: {count} セルを調べ、問題は {len(problems)} 件")
    return not problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", help="AMI の src256 のフォルダ")
    ap.add_argument("--partial", action="store_true", help="シートの無い dat を飛ばす")
    a = ap.parse_args(argv)
    if not os.path.isdir(a.src):
        sys.exit(f"フォルダが無い: {a.src}")
    sys.exit(0 if report(*check(a.src, a.partial)) else 1)


if __name__ == "__main__":
    main()
