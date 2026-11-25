"""石炭のトラックの絵と表を書き出す（docs/vehicles.md）。MIT License。絵は仮（箱を組んだ物）で、見た目は後から描き直す。

長さと描画位置は tools/vehicles.py の決まりで決める。シートは 8 方向（列）× 2 行（0 行 = 空、1 行 = 石炭を積んだ）、
セルは 256px（2048x512）。運転席と荷台の 2 つの箱を組む（荷台は上が開いた箱で、積んだときは石炭の山が載る）。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/vehicle/road/coal_truck/draw_coal_truck.py
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "..", "tools"))
import vehicles as V  # noqa: E402

NAME = "pak256_coal_truck"
REAL_LENGTH_M = 7.0  # 実物の長さ（pak128 の石炭のトラックの 1 つ、Tatra 801 の級の 2 軸の貨物車）
WIDTH_M = 2.5
SS = 3  # 描くときの拡大（縁をなめらかにしてから、半透明を切る）

# 車体の箱。(前の端, 後ろの端, 幅, 下の高さ, 上の高さ, 色)。端は基準点から車体の前を正にした m（前の端 = 0、後ろの端 = -length × 1.65）。
# 長さは dat の length（単位）× 1.65m に合わせる。運転席 2.1m・荷台はその後ろ全部
_L = V.length_units(REAL_LENGTH_M) * V.M_PER_UNIT
CAB_M = 2.1
CHASSIS = (0.0, -_L, 2.1, 0.0, 0.6, (40, 40, 44))  # 車輪のあたりの暗い帯（全長）
CAB = (0.0, -CAB_M, WIDTH_M, 0.6, 2.7, (176, 52, 44))  # 運転席（赤）
BED = (-CAB_M, -_L, WIDTH_M, 0.6, 2.2, (118, 124, 132))  # 荷台（灰色の鉄）
# 積んだ石炭の山（荷台の内側）。荷台の壁より少し高い
COAL = (-CAB_M - 0.25, -_L + 0.2, WIDTH_M - 0.4, 2.2, 2.55, (30, 30, 34))
GLASS = (58, 72, 88)
INSIDE = (84, 88, 96)  # 空の荷台の内側（上から見える底）

PARTS_EMPTY = (CHASSIS, CAB, BED)
PARTS_LOADED = (CHASSIS, CAB, BED, COAL)
HEIGHT_M = CAB[4]

_SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}
VIEW = (1.0, 1.0)  # 見る側（画面の手前 = x + y の大きい側）


def shade(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in color)


def corners(direction, part):
    """箱の地面の四隅（前の右・前の左・後の左・後の右。タイルの単位）。"""
    front, back, width, _, _, _ = part
    # footprint は「基準点から前の端までの単位」と「長さ（単位）」を取る。端を m から単位に直して渡す
    fu = front / V.M_PER_UNIT
    return V.footprint(direction, (front - back) / V.M_PER_UNIT, width, fu)


def depth(direction, part):
    """箱の奥行き（画面の手前ほど大きい。x + y）。描く順を決める。"""
    fr, fl, bl, br = corners(direction, part)
    return sum(p[0] + p[1] for p in (fr, fl, bl, br)) / 4


def draw_cell(direction, loaded):
    img = Image.new("RGBA", (V.CELL * SS, V.CELL * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def scr(p, z):
        sx, sy = V.to_screen(p[0], p[1], z)
        return sx * SS, sy * SS

    def quad(p0, p1, z0, z1, color):
        d.polygon([scr(p0, z0), scr(p1, z0), scr(p1, z1), scr(p0, z1)], fill=color)

    parts = PARTS_LOADED if loaded else PARTS_EMPTY
    # 奥の箱から手前の箱へ。石炭の山は荷台の上に載るので、荷台と同じ奥行きとして荷台の後に描く
    for part in sorted(parts, key=lambda p: (depth(direction, BED if p is COAL else p), p is COAL)):
        fr, fl, bl, br = corners(direction, part)
        _, _, _, z0, z1, color = part
        cx = (fr[0] + bl[0]) / 2
        cy = (fr[1] + bl[1]) / 2
        faces = [(fr, fl, 1.0), (fl, bl, 0.85), (bl, br, 0.7), (br, fr, 0.85)]
        for a, b, k in faces:
            nx, ny = b[1] - a[1], -(b[0] - a[0])
            mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            if nx * (mx - cx) + ny * (my - cy) < 0:
                nx, ny = -nx, -ny
            if nx * VIEW[0] + ny * VIEW[1] <= 1e-9:
                continue
            quad(a, b, z0, z1, shade(color, k))
            if part is CAB and a is fr:  # 運転席の前の面に窓
                lo = lambda s, t, u: (s[0] + (t[0] - s[0]) * u, s[1] + (t[1] - s[1]) * u)  # noqa: E731
                quad(lo(a, b, 0.1), lo(a, b, 0.9), 1.5, 2.45, shade(GLASS, k))
        if part is BED and not loaded:
            top = [scr(p, z1) for p in (fr, fl, bl, br)]
            d.polygon(top, fill=INSIDE)
        elif part is COAL:
            d.polygon([scr(p, z1) for p in (fr, fl, bl, br)], fill=shade(color, 1.35))
        elif part is CAB:
            d.polygon([scr(p, z1) for p in (fr, fl, bl, br)], fill=shade(color, 1.25))
        elif part is BED:
            # 荷台の上の縁（壁の上の面）。内側は石炭の山が覆う
            d.polygon([scr(p, z1) for p in (fr, fl, bl, br)], fill=shade(color, 1.15))

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


def write_yaml(path, stem):
    length = V.length_units(REAL_LENGTH_M)
    lines = [
        "# 石炭のトラック（絵は仮）。この表と PNG は draw_coal_truck.py が書き出す。直すときはスクリプトを直して流し直す。",
        f"# 実物 {REAL_LENGTH_M:g}m ÷ 1.65 = {REAL_LENGTH_M / V.M_PER_UNIT:.2f} → length {length}（docs/vehicles.md）。",
        "# 値は pak128 の石炭のトラック（Bulk_Truck_2）に合わせた（docs/vehicles.md の表）。登場年だけ見本のバスと同じ 1930。",
        "obj: vehicle",
        f"name: {NAME}",
        "copyright: pak256.LongScale チーム",
        "waytype: road",
        "freight: Kohle",
        "payload: 12",
        "engine_type: diesel",
        "power: 95",
        "speed: 55",
        "gear: 90",
        "intro_year: 1930",
        "cost: 384000",
        "runningcost: 24",
        "weight: 8",
        f"length: {length}",
        "emptyimage:       # 向きごとの絵（0 行 = 空）",
    ]
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: {stem}.0.{i}")
    lines.append("freightimage:     # 石炭を積んだ絵（1 行）")
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: {stem}.1.{i}")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=HERE, help="書き出す場所（既定はこのフォルダ）")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    stem = "coal_truck"
    sheet = Image.new("RGBA", (V.CELL * len(V.DIRECTIONS), V.CELL * 2), (0, 0, 0, 0))
    for row, loaded in enumerate((False, True)):
        for i, direction in enumerate(V.DIRECTIONS):
            sheet.paste(draw_cell(direction, loaded), (i * V.CELL, row * V.CELL))
    sheet.save(os.path.join(args.out, stem + ".png"))
    write_yaml(os.path.join(args.out, stem + ".yaml"), stem)
    print("wrote", os.path.join(args.out, stem + ".png"))


if __name__ == "__main__":
    main()
