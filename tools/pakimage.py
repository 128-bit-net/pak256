"""組んだ pak の中の画像を、ゲームを起動せずに取り出して見る道具（docs/game-check.md の「pak の中の画像を見る」。#148）。MIT License。

使い方（リポジトリの直下から。pak を省くと build/pak/ の全部）:
    python -X utf8 tools/pakimage.py list [--name 名前の一部] [--type 種類] [--pak 場所]...
        物の名前と種類、画像の数を並べる
    python -X utf8 tools/pakimage.py tree <名前> [--type 種類] [--pak 場所]...
        物の中の画像の場所（子の番号の道筋）と、大きさ・ずらしを出す
    python -X utf8 tools/pakimage.py export <指定>... -o <出力のフォルダ>
        指定した画像を 1 枚ずつ PNG に書き出す
    python -X utf8 tools/pakimage.py sheet <指定>... -o <出力の PNG> [--scale 4] [--cols 4] [--crop x0,y0,x1,y1]
        指定した画像を並べた 1 枚を書き出す（--scale は最近傍の拡大）

指定は「名前」か「名前:道筋」。道筋は子の番号を / か . でつなぎ、* はその段の全部。
道筋より下の画像は全部選ぶ（`ami_road_local:6` は 6 の下の全部、`ami_road_local:6/8` は 1 枚、`x:*/0` も書ける）。
"""
import argparse
import glob
import math
import os
import re
import struct
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PAK = os.path.join(ROOT, "build", "pak")

# makeobj が書く pak の版（本体の descriptor/objversion.h の COMPILER_VERSION_CODE）
PAK_VERSION = 1003

# 本体の descriptor/image.cc の rgbtab。pak の 0x8000〜0x801E の画素が指す 31 色（プレーヤー色・灯りなど）
SPECIAL_COLORS = (
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
)


class PakError(Exception):
    pass


class Node:
    def __init__(self, kind, body, children):
        self.kind = kind          # "IMG"・"IMG1"・"TEXT"・"WAY" など
        self.body = body          # 節の中身（bytes）
        self.children = children


def parse_pak(data):
    """pak のバイト列を節の木にして、根の節を返す。"""
    head = data.find(b"\x1a")
    if head < 0 or head + 5 > len(data):
        raise PakError("pak の形でない（説明の文の終わりが無い）")
    version = struct.unpack_from("<I", data, head + 1)[0]
    if version > PAK_VERSION:
        raise PakError(f"pak の版 {version} は読めない（{PAK_VERSION} まで）")

    def node(pos):
        kind = data[pos:pos + 4].rstrip(b"\0").decode("latin1")
        count, size = struct.unpack_from("<HH", data, pos + 4)
        pos += 8
        if size == 0xFFFF:  # 大きい節は、続く 4 バイトが長さ
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4
        if pos + size > len(data):
            raise PakError("pak が途中で切れている")
        body = data[pos:pos + size]
        pos += size
        children = []
        for _ in range(count):
            child, pos = node(pos)
            children.append(child)
        return Node(kind, body, children), pos

    try:
        return node(head + 5)[0]
    except struct.error:
        raise PakError("pak が途中で切れている") from None


def object_name(obj):
    """物の名前。最初の子の TEXT。FACT のように最初の子が別の節（BUIL）なら、その中を見る。無ければ空。"""
    while obj.children:
        first = obj.children[0]
        if first.kind == "TEXT":
            return first.body.split(b"\0")[0].decode("utf-8", errors="replace")
        obj = first
    return ""


def images(obj, path=()):
    """物の中の IMG の節を (道筋, 節) で順に返す。空の画像も番号を詰めずに返す。"""
    if obj.kind == "IMG":
        yield path, obj
    for i, child in enumerate(obj.children):
        yield from images(child, path + (i,))


class Picture:
    """IMG の節を解いた画像。pixels は {(x, y): pak の 16bit の色}。x, y はセルの中の位置。"""

    def __init__(self, body):
        if len(body) < 10:
            raise PakError("画像の節が短い")
        version = body[6]
        if version == 3:
            self.x, self.y, self.w, _, self.h, _ = struct.unpack_from("<hhhBhB", body, 0)
        elif version in (1, 2):
            self.x, self.y, self.w, self.h = struct.unpack_from("<hhBB", body, 0)
        else:
            raise PakError(f"画像の版 {version} は読めない（1〜3）")
        words = struct.unpack_from(f"<{(len(body) - 10) // 2}H", body, 10)
        self.pixels = {}
        i = 0
        try:
            for row in range(self.h if words else 0):
                x = self.x
                skip = words[i]
                i += 1
                while True:
                    # 透明の数の語は 0x8000（0 画素。半透明との区切り）のことがある。行の終わりは 0 の語だけ
                    x += skip & 0x7FFF
                    count = words[i] & 0x7FFF  # 0x8000 は半透明の続きの印
                    i += 1
                    for _ in range(count):
                        self.pixels[(x, self.y + row)] = words[i]
                        i += 1
                        x += 1
                    skip = words[i]
                    i += 1
                    if skip == 0:
                        break
        except IndexError:
            raise PakError("画像のデータが途中で切れている") from None

    @property
    def empty(self):
        return not self.pixels


def rgba(color):
    """pak の 16bit の色を (r, g, b, a) にする。

    - 0x0000〜0x7FFF: RGB555
    - 0x8000〜0x801E: 特別な色（dat の元の色で出す。ゲームでの色はプレーヤー・昼夜で変わる）
    - 0x8020〜: 半透明。31 段の不透明度 × （特別な色 31 個 + RGB343）
    """
    if color < 0x8000:
        return tuple(((color >> s) & 31) << 3 | ((color >> s) & 31) >> 2 for s in (10, 5, 0)) + (255,)
    if color < 0x8020:
        if color - 0x8000 >= len(SPECIAL_COLORS):
            raise PakError(f"知らない色 {color:#06x}")
        c = SPECIAL_COLORS[color - 0x8000]
        return (c >> 16, (c >> 8) & 255, c & 255, 255)
    index, alpha = divmod(color - 0x8020, 31)
    a = round((alpha + 1) * 255 / 32)
    if index < len(SPECIAL_COLORS):
        c = SPECIAL_COLORS[index]
        return (c >> 16, (c >> 8) & 255, c & 255, a)
    c = index - len(SPECIAL_COLORS)
    return ((c & 0x380) >> 2, (c & 0x78) << 1, (c & 7) << 5, a)


def canvas_box(pictures, cell):
    """画像を置く範囲 (x0, y0, x1, y1)。セルを基本にし、はみ出す画像があれば cell の単位で広げる。"""
    xs, ys = [0, cell], [0, cell]
    for p in pictures:
        if not p.empty:
            xs += [min(x for x, _ in p.pixels), max(x for x, _ in p.pixels) + 1]
            ys += [min(y for _, y in p.pixels), max(y for _, y in p.pixels) + 1]
    return (math.floor(min(xs) / cell) * cell, math.floor(min(ys) / cell) * cell,
            math.ceil(max(xs) / cell) * cell, math.ceil(max(ys) / cell) * cell)


def render(picture, box):
    """box の範囲の RGBA の画像にする。透明な所は (0, 0, 0, 0)。"""
    x0, y0, x1, y1 = box
    im = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    put = im.load()
    for (x, y), color in picture.pixels.items():
        if x0 <= x < x1 and y0 <= y < y1:
            put[x - x0, y - y0] = rgba(color)
    return im


def pak_files(places):
    """pak のファイル・フォルダ・ワイルドカードを、ファイルの一覧にする。"""
    found = []
    for place in places or [DEFAULT_PAK]:
        if os.path.isdir(place):
            files = sorted(glob.glob(os.path.join(glob.escape(place), "*.pak")))
        elif os.path.isfile(place):
            files = [place]
        else:
            files = sorted(glob.glob(place))
        if not files:
            raise PakError(f"pak が無い: {place}（先に python -X utf8 tools/build.py で組む）")
        found += files
    return found


def objects(places):
    """(pak のファイル, 物の節) を順に返す。"""
    for path in pak_files(places):
        with open(path, "rb") as f:
            data = f.read()
        try:
            root = parse_pak(data)
        except PakError as e:
            raise PakError(f"{path}: {e}") from None
        for obj in root.children:
            yield path, obj


def find_object(found, name, kind):
    """名前（と種類）に合う物を 1 つ返す。無い・2 つ以上は誤り。"""
    hits = [(p, o) for p, o in found if object_name(o) == name and (kind is None or o.kind == kind.upper())]
    if not hits:
        raise PakError(f"物が無い: {name}（list で名前を確かめる）")
    if len(hits) > 1:
        where = ", ".join(f"{o.kind} {os.path.basename(p)}" for p, o in hits)
        raise PakError(f"同じ名前の物が {len(hits)} 個ある: {name}（{where}）。--type か --pak で絞る")
    return hits[0]


def parse_spec(spec):
    """「名前:道筋」を (名前, 道筋の段の列) にする。名前の中の : は、道筋の形でなければ名前に含める。"""
    m = re.fullmatch(r"(.+?):((?:\d+|\*)(?:[./](?:\d+|\*))*)", spec)
    if not m:
        return spec, ()
    return m.group(1), tuple(None if s == "*" else int(s) for s in re.split(r"[./]", m.group(2)))


def matches(path, pattern):
    """道筋 path が指定 pattern に合うか（pattern より下は全部合う）。"""
    return len(path) >= len(pattern) and all(w is None or w == s for s, w in zip(path, pattern))


def path_text(path):
    return "/".join(map(str, path))


def select(places, specs, kind):
    """指定の画像を (物の名前, 道筋, Picture) の列にする。"""
    found = list(objects(places))
    out = []
    for spec in specs:
        name, pattern = parse_spec(spec)
        _, obj = find_object(found, name, kind)
        chosen = [(name, p, Picture(n.body)) for p, n in images(obj) if matches(p, pattern)]
        if not chosen:
            raise PakError(f"画像が無い: {spec}（tree {name} で道筋を確かめる）")
        out += chosen
    return out


def safe(name):
    return re.sub(r'[<>:"/\\|?*\s]', "_", name)


def export(chosen, out_dir, box):
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name, path, picture in chosen:
        file = os.path.join(out_dir, f"{safe(name)}_{'-'.join(map(str, path))}.png")
        render(picture, box).save(file)
        written.append(file)
    return written


def sheet(chosen, box, crop=None, scale=1, cols=None, background=(96, 128, 96)):
    """画像を並べた 1 枚（RGB）。透明な所は background。下に「名前 道筋」を書く。"""
    x0, y0, x1, y1 = crop or box
    labels = [f"{name} {path_text(path)}" + (" (empty)" if p.empty else "") for name, path, p in chosen]
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    cw = max((x1 - x0) * scale, max(int(probe.textlength(t)) + 4 for t in labels))
    ch, label_h, gap = (y1 - y0) * scale, 14, 4
    cols = cols or min(len(chosen), max(1, math.ceil(math.sqrt(len(chosen)))))
    rows = math.ceil(len(chosen) / cols)
    size = (cols * (cw + gap) - gap, rows * (ch + label_h + gap) - gap)
    if size[0] * size[1] > 80_000_000:
        raise PakError(f"出力が大きすぎる（{size[0]}x{size[1]}）。指定を絞るか、--scale・--crop を使う")
    out = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(out)
    for i, ((_, _, picture), label) in enumerate(zip(chosen, labels)):
        left, top = (i % cols) * (cw + gap), (i // cols) * (ch + label_h + gap)
        tile = render(picture, (x0, y0, x1, y1))
        base = Image.new("RGBA", tile.size, background + (255,))
        base.alpha_composite(tile)
        out.paste(base.convert("RGB").resize(((x1 - x0) * scale, ch), Image.NEAREST), (left, top))
        draw.text((left + 2, top + ch + 1), label, fill=(0, 0, 0))
    return out


def cmd_list(a):
    for path, obj in objects(a.pak):
        name = object_name(obj)
        if a.name and a.name.lower() not in name.lower():
            continue
        if a.type and obj.kind != a.type.upper():
            continue
        print(f"{obj.kind:5} {name}  画像 {sum(1 for _ in images(obj))}  {os.path.basename(path)}")


def cmd_tree(a):
    path, obj = find_object(list(objects(a.pak)), a.object, a.type)
    print(f"{obj.kind} {object_name(obj)}  {os.path.basename(path)}")

    def walk(node, where):
        for i, child in enumerate(node.children):
            at = where + (i,)
            indent = "  " * len(at)
            if child.kind == "IMG":
                p = Picture(child.body)
                info = "空" if p.empty else f"{p.w}x{p.h} 左上 ({p.x}, {p.y})"
                print(f"{indent}{path_text(at)} IMG {info}")
            elif any(True for _ in images(child)):
                print(f"{indent}{path_text(at)} {child.kind}（画像 {sum(1 for _ in images(child))}）")
                walk(child, at)
            elif child.kind != "TEXT":
                print(f"{indent}{path_text(at)} {child.kind}（画像なし）")

    walk(obj, ())


def parse_crop(text):
    try:
        box = tuple(int(v) for v in text.split(","))
    except ValueError:
        box = ()
    if len(box) != 4 or box[0] >= box[2] or box[1] >= box[3]:
        raise argparse.ArgumentTypeError("x0,y0,x1,y1（x0 < x1、y0 < y1）で指定する")
    return box


def positive(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("1 以上にする")
    return value


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--pak", action="append", help="pak のファイルかフォルダ（何回でも）。省くと build/pak/")
    common.add_argument("--type", help="物の種類で絞る（WAY・VHCL・BUIL など。list の左の列）")
    pick = argparse.ArgumentParser(add_help=False)
    pick.add_argument("spec", nargs="+", help="名前 か 名前:道筋")
    pick.add_argument("-o", "--out", required=True)
    pick.add_argument("--cell", type=positive, default=256, help="画像を置くマスの大きさ（512 のセルに描いた物は 512）")

    s = sub.add_parser("list", parents=[common])
    s.add_argument("--name", help="名前の一部で絞る")
    s = sub.add_parser("tree", parents=[common])
    s.add_argument("object")
    sub.add_parser("export", parents=[common, pick])
    s = sub.add_parser("sheet", parents=[common, pick])
    s.add_argument("--scale", type=positive, default=1, help="最近傍の拡大の倍率")
    s.add_argument("--cols", type=positive, help="横に並べる数")
    s.add_argument("--crop", type=parse_crop, help="マスの中の x0,y0,x1,y1 だけを出す")
    a = ap.parse_args(argv)

    try:
        if a.command == "list":
            cmd_list(a)
        elif a.command == "tree":
            cmd_tree(a)
        else:
            chosen = select(a.pak, a.spec, a.type)
            box = canvas_box([p for _, _, p in chosen], a.cell)
            if box != (0, 0, a.cell, a.cell):
                print(f"[pakimage] 画像がマスからはみ出すので、範囲を {box} にした")
            if a.command == "export":
                for file in export(chosen, a.out, box):
                    print(file)
            else:
                os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
                sheet(chosen, box, a.crop, a.scale, a.cols).save(a.out)
                print(f"{a.out}（{len(chosen)} 枚）")
    except PakError as e:
        sys.exit(f"[pakimage] {e}")


if __name__ == "__main__":
    main()
