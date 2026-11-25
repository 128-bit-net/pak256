"""見本のバスの絵と表を書き出す（docs/vehicles.md）。MIT License。絵は仮（箱を組んだ物）で、見た目は後から描き直す。

長さと描画位置は tools/vehicles.py の決まりで決める。8 方向を 256px のセルに横に並べたシート（2048x256）。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/vehicle/road/sample_bus/draw_bus.py
試験の印（車体の地面の枠と基準点）を重ねた絵を別の場所に書くとき（描画位置を確かめる試験用。git に入れない）:
    python -X utf8 objects/vehicle/road/sample_bus/draw_bus.py --marker --out build/vehicle_marker
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
import vehicles as V  # noqa: E402

NAME = "pak256_sample_bus"
REAL_LENGTH_M = 12.0  # 実物の長さ
WIDTH_M = 2.5
HEIGHT_M = 3.2
SS = 3  # 描くときの拡大（縁をなめらかにしてから、半透明を切る）

# 色（makeobj の特別な色を避ける。_SPECIAL に当たれば 1 ずらす）
BODY = (214, 196, 150)  # 車体（クリーム）
BAND = (52, 112, 84)  # 帯（緑）
ROOF = (232, 226, 210)
GLASS = (58, 72, 88)
SKIRT = (40, 40, 44)  # 車輪のあたりの暗い帯
MARK = (230, 0, 150)  # 試験の印
MARK2 = (0, 150, 230)

_SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}
VIEW = (1.0, 1.0)  # 見る側（画面の手前 = x + y の大きい側）


def shade(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in color)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def draw_cell(direction, marker, emulate_right=False):
    """1 方向のセル（256x256、RGBA）を描く。

    emulate_right: 左側通行の地図で右側通行の見え方を確かめる試験の絵。本体が左側通行で足すずれ
    （tools/vehicles.py の DRIVELEFT_64）をあらかじめ引いて描く。本体は左側通行のとき絵をずらすだけなので、
    この絵は右側通行の地図での普通の絵と同じ所に出る。
    """
    length = V.length_units(REAL_LENGTH_M)
    fr, fl, bl, br = V.footprint(direction, length, WIDTH_M, V.FRONT_UNITS)
    img = Image.new("RGBA", (V.CELL * SS, V.CELL * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    shift = (0.0, 0.0)
    if emulate_right:
        lx, ly = V.DRIVELEFT_64[direction]
        shift = (-lx * V.CELL / 64, -ly * V.CELL / 64)

    def scr(p, z):
        sx, sy = V.to_screen(p[0], p[1], z)
        return (sx + shift[0]) * SS, (sy + shift[1]) * SS

    def quad(p0, p1, z0, z1, color):
        d.polygon([scr(p0, z0), scr(p1, z0), scr(p1, z1), scr(p0, z1)], fill=color)

    # 側面（外向きの向きが見る側を向く面だけ）。面は (端 a, 端 b, 明るさ, 前の面か)
    faces = [(fr, fl, 1.0, True), (fl, bl, 0.85, False), (bl, br, 0.7, False), (br, fr, 0.85, False)]
    for a, b, k, is_front in faces:
        nx, ny = b[1] - a[1], -(b[0] - a[0])  # 四隅は時計回りなので、外向きは右手
        # 外向きの向きは、面の中点から箱の中心へ向かう向きの反対で決める
        cx = (fr[0] + bl[0]) / 2
        cy = (fr[1] + bl[1]) / 2
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if nx * (mx - cx) + ny * (my - cy) < 0:
            nx, ny = -nx, -ny
        if nx * VIEW[0] + ny * VIEW[1] <= 1e-9:
            continue
        quad(a, b, 0.0, 0.5, shade(SKIRT, k))
        quad(a, b, 0.5, HEIGHT_M, shade(BODY, k))
        quad(a, b, 0.5, 1.0, shade(BAND, k))
        if is_front:
            quad(lerp(a, b, 0.1), lerp(a, b, 0.9), 1.5, 2.8, shade(GLASS, k))
        else:
            quad(lerp(a, b, 0.06), lerp(a, b, 0.94), 1.7, 2.6, shade(GLASS, k))
    d.polygon([scr(p, HEIGHT_M) for p in (fr, fl, bl, br)], fill=ROOF)

    if marker:
        # 車体の地面の枠と、前の端の線と、基準点（右側の車線の点）
        pts = [scr(p, 0.0) for p in (fr, fl, bl, br)]
        d.line(pts + [pts[0]], fill=MARK, width=SS)
        d.line([scr(fr, 0.0), scr(fl, 0.0)], fill=MARK2, width=2 * SS)
        lx, ly = scr(V.lane_point(direction), 0.0)  # noqa: E741
        d.ellipse([lx - 2 * SS, ly - 2 * SS, lx + 2 * SS, ly + 2 * SS], fill=MARK2)
        ox, oy = scr((0.0, 0.0), 0.0)
        d.line([ox - 4 * SS, oy, ox + 4 * SS, oy], fill=MARK, width=SS)
        d.line([ox, oy - 2 * SS, ox, oy + 2 * SS], fill=MARK, width=SS)

    img = img.resize((V.CELL, V.CELL), Image.LANCZOS)
    px = img.load()
    for y in range(V.CELL):
        for x in range(V.CELL):
            r, g, b, a = px[x, y]
            if a < 128:
                px[x, y] = (0, 0, 0, 0)
                continue
            if (r << 16 | g << 8 | b) in _SPECIAL:
                r = r + 1 if r < 255 else r - 1
            px[x, y] = (r, g, b, 255)
    return img


def write_yaml(path, stem, name=NAME):
    length = V.length_units(REAL_LENGTH_M)
    lines = [
        "# 見本のバス（絵は仮）。この表と PNG は draw_bus.py が書き出す。直すときはスクリプトを直して流し直す。",
        f"# 実物 {REAL_LENGTH_M:g}m ÷ 1.65 = {REAL_LENGTH_M / V.M_PER_UNIT:.2f} → length {length}（docs/vehicles.md）。",
        "obj: vehicle",
        f"name: {name}",
        "copyright: pak256.LongScale チーム",
        "waytype: road",
        "freight: Passagiere",
        "payload: 40",
        "engine_type: diesel",
        "power: 90",
        "speed: 60",
        "gear: 100",
        "intro_year: 1930",
        "cost: 700000",
        "runningcost: 50",
        "weight: 9",
        f"length: {length}",
        "emptyimage:       # 向きごとの絵",
    ]
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: {stem}.0.{i}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", action="store_true", help="試験の印を重ねる（git に入れない）")
    ap.add_argument("--emulate-right", action="store_true",
                    help="左側通行の地図で右側通行の見え方を確かめる試験の絵（名前に _right_test を付ける。git に入れない）")
    ap.add_argument("--out", default=HERE, help="書き出す場所（既定はこのフォルダ）")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    stem = "sample_bus"
    sheet = Image.new("RGBA", (V.CELL * len(V.DIRECTIONS), V.CELL), (0, 0, 0, 0))
    for i, direction in enumerate(V.DIRECTIONS):
        sheet.paste(draw_cell(direction, args.marker, args.emulate_right), (i * V.CELL, 0))
    sheet.save(os.path.join(args.out, stem + ".png"))
    write_yaml(os.path.join(args.out, stem + ".yaml"), stem, NAME + ("_right_test" if args.emulate_right else ""))
    print("wrote", os.path.join(args.out, stem + ".png"))


if __name__ == "__main__":
    main()
