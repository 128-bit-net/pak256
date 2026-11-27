"""煙の物（obj=smoke）の絵と dat を書き出す（docs/smoke.md・#174）。MIT License。絵は仮（丸い粒を重ねた物）。

本体の煙は、絵のコマ（image[0]〜）を寿命の間に順に出し、少しずつ昇らせて左へ流す（obj/wolke.cc）。絵に向きは無い。
256 のセルの中の粒の中心が、出る位置との差になる:
- 工場の煙は、工場の dat の smoketile・smokeoffset がセルの左上のずれを決める。粒はセルの (128, 128) に描く。
- 車両の煙は、車両の基準点（タイルの中心 = セルの (128, 192)）の 32px 上に出る（vehicle_t::make_smoke）。
  粒をセルの (128, 192 - 上げる px) に描くと、出る高さが 32px + 上げる px になる。

yaml でなく dat を書き出すのは、煙の名前が画面に出ず、訳（text/）を置かないため（tools/test_text.py は yaml の名前を数える）。

使い方（Pillow が要る。書き出した PNG と dat は git に入れる）:
    python -X utf8 objects/smoke/draw_smoke.py
出る位置を確かめる印（桃色の濃い粒。git に入れない）:
    python -X utf8 objects/smoke/draw_smoke.py --marker --out build/smoke_marker
"""
import argparse
import os
import random

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = 256
SS = 3

# makeobj が特別な色として読む色（昼夜で色の変わる色・プレーヤー色・透明色）。避ける
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}

# 煙の種類。center: 粒の群れの中心（セルの px。出る位置を上下に合わせる）。frames: (粒の群れの半径 px, 不透明度 0〜255) をコマの順に
SMOKES = [
    {
        "name": "pak256_smoke_chimney", "stem": "chimney", "title": "煙突の煙（工場）",
        "center": (128, 128), "grey": 170, "puffs": 16,
        "frames": [(13, 235), (18, 215), (23, 190), (28, 155), (33, 115), (37, 70)],
    },
    {
        "name": "pak256_smoke_diesel", "stem": "diesel", "title": "ディーゼルの車両の排気",
        "center": (128, 192), "grey": 100, "puffs": 11,
        "frames": [(8, 210), (12, 180), (15, 145), (18, 110), (22, 70)],
    },
    {
        "name": "pak256_smoke_ship", "stem": "ship", "title": "船の排気",
        "center": (128, 180), "grey": 100, "puffs": 14,
        "frames": [(10, 215), (15, 190), (20, 160), (24, 115), (28, 70)],
    },
]

MARKER = (255, 40, 200)


def safe(rgb):
    r, g, b = (max(0, min(255, int(round(v)))) for v in rgb)
    if (r << 16 | g << 8 | b) in SPECIAL:
        b = b + 1 if b < 255 else b - 1
    return (r, g, b)


def neutral(v):
    """灰色の明るさを、半透明の画素でも色が付かない値にそろえる。

    makeobj は半透明の画素の色を赤 3・緑 4・青 3 ビットに落とすので、緑だけが細かく残って灰色が緑や紫に寄る。
    32 の倍数 + 6 なら 3 色が同じ段に落ちる。
    """
    return min(6, max(1, int(v // 32))) * 32 + 6


def draw_frame(spec, index, marker):
    """1 コマ（256x256、RGBA）。小さい丸を群れにして重ね、縁を少し透かす。"""
    radius, alpha = spec["frames"][index]
    cx, cy = spec["center"]
    rnd = random.Random(f"{spec['name']}:{index}")  # 毎回同じ絵にする
    img = Image.new("RGBA", (CELL * SS, CELL * SS), (0, 0, 0, 0))
    puffs = []
    for _ in range(spec["puffs"]):
        while True:
            dx, dy = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
            if dx * dx + dy * dy <= 1:
                break
        r = radius * rnd.uniform(0.40, 0.58)
        puffs.append((cx + dx * (radius - r), cy + dy * (radius - r) * 0.85, r))
    # 下の粒から塗る。上の粒ほど明るくして、丸みを出す
    for px, py, r in sorted(puffs, key=lambda p: -p[1]):
        for k, shift, grow in ((-18, 0.0, 1.0), (8, 0.18, 0.72), (28, 0.32, 0.40)):
            grey = spec["grey"] + k + (cy - py) / max(1, radius) * 14
            color = MARKER if marker else safe((grey, grey, grey + 3))
            a = 255 if marker else int(alpha * (0.85 if k < 0 else 1.0))
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ox, oy, rr = px - r * shift, py - r * shift, r * grow
            ImageDraw.Draw(layer).ellipse(
                [(ox - rr) * SS, (oy - rr) * SS, (ox + rr) * SS, (oy + rr) * SS], fill=color + (a,))
            img = Image.alpha_composite(img, layer)
    small = img.resize((CELL, CELL), Image.LANCZOS)
    px_ = small.load()
    for y in range(CELL):
        for x in range(CELL):
            r, g, b, a = px_[x, y]
            # ほぼ透明な画素は消す（makeobj は不透明度を 30 段にする）
            if a < 16:
                px_[x, y] = (0, 0, 0, 0)
                continue
            if not marker:
                v = neutral((r + g + b) / 3)
                r, g, b = v, v, v
            px_[x, y] = safe((r, g, b)) + (a,)
    return small


def sheet(spec, marker=False):
    out = Image.new("RGBA", (CELL * len(spec["frames"]), CELL), (0, 0, 0, 0))
    for i in range(len(spec["frames"])):
        out.paste(draw_frame(spec, i, marker), (i * CELL, 0))
    return out


def dat_text():
    lines = ["# 煙の物（絵は仮）。この dat と PNG は draw_smoke.py が書き出す。直すときはスクリプトを直して流し直す。"]
    for spec in SMOKES:
        lines += [
            "obj=smoke",
            f"name={spec['name']}",
            "copyright=pak256.LongScale チーム",
            f"# {spec['title']}",
        ]
        lines += [f"image[{i}]={spec['stem']}.0.{i}" for i in range(len(spec["frames"]))]
        lines.append("-")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", action="store_true", help="出る位置を確かめる印にする（git に入れない）")
    ap.add_argument("--out", help="書き出す場所（省くとこのフォルダ。--marker では必ず渡す）")
    args = ap.parse_args()
    if args.marker and not args.out:
        ap.error("--marker は --out で別の場所に書く（コミットした絵を上書きしないため）")
    args.out = args.out or HERE
    os.makedirs(args.out, exist_ok=True)
    for spec in SMOKES:
        sheet(spec, args.marker).save(os.path.join(args.out, spec["stem"] + ".png"))
    with open(os.path.join(args.out, "smoke.dat"), "w", encoding="utf-8", newline="\n") as f:
        f.write(dat_text())


if __name__ == "__main__":
    main()
