"""バスと郵便のトラックの絵と表を書き出す（docs/vehicles.md・#41）。MIT License。絵は仮（箱を組んだ物）で、見た目は後から描き直す。

長さと描画位置は tools/vehicles.py の決まりで決める。8 方向を 256px のセルに横に並べたシート（2048x256）を車両ごとに
`<種類>/<名前>.png` に、表を `<名前>.yaml` に書く。値（登場年・速さ・定員・費用）は docs/vehicles.md の表。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/vehicle/road/draw_vehicles.py
試験の印（車体の地面の枠と基準点）を重ねた絵を別の場所に書くとき（描画位置を確かめる試験用。git に入れない）:
    python -X utf8 objects/vehicle/road/draw_vehicles.py --marker --out build/vehicle_marker
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import vehicles as V  # noqa: E402

SS = 3  # 描くときの拡大（縁をなめらかにしてから、半透明を切る）
SKIRT = (40, 40, 44)  # 車輪のあたりの暗い帯
GLASS = (58, 72, 88)
MARK = (230, 0, 150)  # 試験の印
MARK2 = (0, 150, 230)

# makeobj の特別な色を避ける。当たれば 1 ずらす
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}
VIEW = (1.0, 1.0)  # 見る側（画面の手前 = x + y の大きい側）

# 車両の表。値は pak128 の同じ種類を目安にした（docs/vehicles.md の表に理由）。
# parts: 車体の部分。(前からの位置の始め, 終わり, 高さ m, 車体の色, 帯の色 or None, 窓の種類)。位置は車体の長さの 0〜1。
VEHICLES = [
    {
        "name": "pak256_bus", "dir": "bus", "stem": "bus",
        "real_length_m": 12.0, "width_m": 2.5,
        "freight": "Passagiere", "payload": 70, "power": 205, "speed": 60, "gear": 80,
        "weight": 11, "cost": 661000, "runningcost": 39, "intro_year": 1930,
        "parts": [(0.0, 1.0, 3.2, (214, 196, 150), (52, 112, 84), "bus")],
    },
    {
        "name": "pak256_mail_truck", "dir": "mail_truck", "stem": "mail_truck",
        "real_length_m": 7.0, "width_m": 2.2,
        "freight": "Post", "payload": 44, "power": 77, "speed": 60, "gear": 80,
        "weight": 5, "cost": 863000, "runningcost": 38, "intro_year": 1930,
        "parts": [
            (0.0, 0.3, 2.3, (190, 52, 44), None, "cab"),  # 運転席
            (0.3, 1.0, 3.0, (200, 62, 52), (236, 220, 120), "van"),  # 荷台の箱
        ],
    },
]


def shade(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in color)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def part_corners(corners, t0, t1):
    """車体の地面の四隅（前の右・前の左・後の左・後の右）から、前から t0〜t1 の部分の四隅を出す。"""
    fr, fl, bl, br = corners
    return (lerp(fr, br, t0), lerp(fl, bl, t0), lerp(fl, bl, t1), lerp(fr, br, t1))


def body_box(spec):
    """車体の長さ（dat の length）。"""
    return V.length_units(spec["real_length_m"])


def draw_cell(spec, direction, marker, emulate_right=False):
    """1 方向のセル（256x256、RGBA）を描く。

    emulate_right: 左側通行の地図で右側通行の見え方を確かめる試験の絵。本体が左側通行で足すずれ
    （tools/vehicles.py の DRIVELEFT_64）をあらかじめ引いて描く。
    """
    length = body_box(spec)
    whole = V.footprint(direction, length, spec["width_m"], V.FRONT_UNITS)
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

    cx = (whole[0][0] + whole[2][0]) / 2
    cy = (whole[0][1] + whole[2][1]) / 2
    # 奥の部分から描く（画面の x + y の小さい方が奥）
    parts = sorted(spec["parts"], key=lambda p: sum(
        (q[0] + q[1]) for q in part_corners(whole, p[0], p[1])))
    for t0, t1, height, body, band, kind in parts:
        fr, fl, bl, br = part_corners(whole, t0, t1)
        faces = [(fr, fl, 1.0, True), (fl, bl, 0.85, False), (bl, br, 0.7, False), (br, fr, 0.85, False)]
        for a, b, k, is_front in faces:
            nx, ny = b[1] - a[1], -(b[0] - a[0])
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            if nx * (mx - cx) + ny * (my - cy) < 0:
                nx, ny = -nx, -ny
            if nx * VIEW[0] + ny * VIEW[1] <= 1e-9:
                continue
            quad(a, b, 0.0, 0.5, shade(SKIRT, k))
            quad(a, b, 0.5, height, shade(body, k))
            if band:
                quad(a, b, 0.5, 1.0, shade(band, k))
            if kind == "bus":
                if is_front:
                    quad(lerp(a, b, 0.1), lerp(a, b, 0.9), 1.5, 2.8, shade(GLASS, k))
                else:
                    quad(lerp(a, b, 0.06), lerp(a, b, 0.94), 1.7, 2.6, shade(GLASS, k))
            elif kind == "cab":
                if is_front:
                    quad(lerp(a, b, 0.1), lerp(a, b, 0.9), 1.3, 2.1, shade(GLASS, k))
                else:
                    quad(lerp(a, b, 0.15), lerp(a, b, 0.85), 1.3, 2.1, shade(GLASS, k))
            elif kind == "van" and not is_front and band:
                quad(lerp(a, b, 0.1), lerp(a, b, 0.9), 1.6, 1.9, shade(band, k))  # 郵便の帯
        d.polygon([scr(p, height) for p in (fr, fl, bl, br)], fill=shade(body, 1.15))

    if marker:
        fr, fl, bl, br = whole
        pts = [scr(p, 0.0) for p in whole]
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
            if (r << 16 | g << 8 | b) in SPECIAL:
                r = r + 1 if r < 255 else r - 1
            px[x, y] = (r, g, b, 255)
    return img


def write_yaml(path, spec, name):
    length = body_box(spec)
    lines = [
        f"# {spec['stem']}（絵は仮）。この表と PNG は draw_vehicles.py が書き出す。直すときはスクリプトを直して流し直す。",
        f"# 実物 {spec['real_length_m']:g}m ÷ 1.65 = {spec['real_length_m'] / V.M_PER_UNIT:.2f} → length {length}（docs/vehicles.md）。",
        "obj: vehicle",
        f"name: {name}",
        "copyright: pak256.LongScale チーム",
        "waytype: road",
        f"freight: {spec['freight']}",
        f"payload: {spec['payload']}",
        "engine_type: diesel",
        f"power: {spec['power']}",
        f"speed: {spec['speed']}",
        f"gear: {spec['gear']}",
        f"intro_year: {spec['intro_year']}",
        f"cost: {spec['cost']}",
        f"runningcost: {spec['runningcost']}",
        f"weight: {spec['weight']}",
        f"length: {length}",
        "emptyimage:       # 向きごとの絵",
    ]
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: {spec['stem']}.0.{i}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", action="store_true", help="試験の印を重ねる（git に入れない）")
    ap.add_argument("--emulate-right", action="store_true",
                    help="左側通行の地図で右側通行の見え方を確かめる試験の絵（名前に _right_test を付ける。git に入れない）")
    ap.add_argument("--out", default=None, help="書き出す場所（既定は、車両ごとのこのフォルダの下）")
    args = ap.parse_args()
    for spec in VEHICLES:
        out = args.out or os.path.join(HERE, spec["dir"])
        os.makedirs(out, exist_ok=True)
        sheet = Image.new("RGBA", (V.CELL * len(V.DIRECTIONS), V.CELL), (0, 0, 0, 0))
        for i, direction in enumerate(V.DIRECTIONS):
            sheet.paste(draw_cell(spec, direction, args.marker, args.emulate_right), (i * V.CELL, 0))
        sheet.save(os.path.join(out, spec["stem"] + ".png"))
        write_yaml(os.path.join(out, spec["stem"] + ".yaml"), spec,
                   spec["name"] + ("_right_test" if args.emulate_right else ""))
        print("wrote", os.path.join(out, spec["stem"] + ".png"))


if __name__ == "__main__":
    main()
