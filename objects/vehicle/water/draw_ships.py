"""船（旅客船・貨物船）の絵と表を書き出す（docs/vehicles.md の「船」・#154）。MIT License。絵は仮（多角形を押し出した物）。

長さと描画位置は tools/vehicles.py の決まりで決める。船は実物比例（docs/standards.md の 4 章「船・飛行機」）で、
`length` = 実物の長さ（m）÷ 1.65。船は水路の中心に描く（本体の左側通行のずれは道路の車両だけ）。船首の先を基準点に置き、
船体は基準点から後ろへ伸びる。喫水線は地面の高さ（水面）。30〜36m の船体は 256 のセルに収まらないので 512 のセルに描く
（256 のセルの絵を真ん中に置く形。位置合わせ -128,-128）。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/vehicle/water/draw_ships.py
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import vehicles as V  # noqa: E402

CELL = 512
PAD = 128  # 256 のセルの座標を 512 のセルの中ほどへ
SS = 3
VIEW = (1.0, 1.0)  # 見る側（画面の手前 = x + y の大きい側）

# makeobj の特別な色を避ける
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}

WHITE = (232, 232, 226)
DECK = (168, 142, 108)
GLASS = (58, 72, 88)
COAL = (34, 34, 38)
HOLD = (96, 74, 62)

# 船の表。値は pak128 の同じ種類を手本にした（docs/vehicles.md の「船」）。
# hull: 船体の色と高さ（m）。house: 甲板の上の箱。(船首からの始め, 終わり（長さに対する割合）, 幅の割合, 下, 上（m）, 壁の色, 屋根の色, 窓)
VEHICLES = [
    {
        "name": "pak256_ferry", "dir": "ferry", "stem": "ferry", "title": "旅客船",
        "real_length_m": 30.0, "width_m": 7.0,
        "freight": "Passagiere", "payload": 300, "power": 2400, "speed": 37, "gear": 100,
        "weight": 70, "cost": 800000, "runningcost": 915, "intro_year": 1930,
        "hull_z": 1.6, "hull": (44, 84, 140), "stripe": (206, 70, 52),
        "house": [
            (0.30, 0.86, 0.80, 1.6, 4.0, WHITE, (190, 192, 186), True),
            (0.38, 0.58, 0.56, 4.0, 5.8, WHITE, (170, 60, 52), True),  # 操舵室
        ],
        "funnel": (0.68, 0.76, 0.30, 4.0, 6.6, (206, 70, 52), (60, 60, 64)),
    },
    {
        "name": "pak256_cargo_ship", "dir": "cargo_ship", "stem": "cargo_ship", "title": "貨物船",
        "real_length_m": 36.0, "width_m": 8.0,
        "freight": "Kohle", "payload": 165, "power": 1050, "speed": 25, "gear": 100,
        "weight": 122, "cost": 2101315, "runningcost": 573, "intro_year": 1930,
        "hull_z": 1.8, "hull": (86, 48, 44), "stripe": (40, 40, 44),
        "hold": (0.16, 0.72, 0.74),  # (始め, 終わり, 幅の割合)。積んだ絵は石炭の山
        "house": [
            (0.75, 0.94, 0.78, 1.8, 4.2, WHITE, (118, 124, 132), True),
        ],
        "funnel": (0.88, 0.93, 0.22, 4.2, 6.0, (40, 40, 44), (60, 60, 64)),
        "freight_image": True,
    },
]


def length_of(spec):
    return V.length_units(spec["real_length_m"])


def safe(rgb):
    r, g, b = (max(0, min(255, int(round(v)))) for v in rgb)
    if (r << 16 | g << 8 | b) in SPECIAL:
        b = b + 1 if b < 255 else b - 1
    return (r, g, b)


class Frame:
    """船の座標（前からの長さ m, 右への距離 m, 高さ m）を、セルの画面の座標にする。"""

    def __init__(self, direction):
        self.h = V.HEADING[direction]
        self.r = (-self.h[1], self.h[0])

    def ground(self, back_m, side_m):
        hx, hy = self.h
        rx, ry = self.r
        return (-hx * back_m + rx * side_m) / V.M_PER_TILE, (-hy * back_m + ry * side_m) / V.M_PER_TILE

    def P(self, pt, z):
        x, y = self.ground(*pt)
        sx, sy = V.to_screen(x, y, z)
        return (sx + PAD) * SS, (sy + PAD) * SS

    def depth(self, pt):
        x, y = self.ground(*pt)
        return x + y


def outline(back0, back1, half, bow=0.0):
    """上から見た輪郭（前からの長さ, 右への距離）。bow（m）> 0 なら、前の端をとがらせる。右回り。"""
    if bow:
        return [(back0, 0.0), (back0 + bow * 0.5, half * 0.7), (back0 + bow, half), (back1, half * 0.92),
                (back1, -half * 0.92), (back0 + bow, -half), (back0 + bow * 0.5, -half * 0.7)]
    return [(back0, half), (back1, half), (back1, -half), (back0, -half)]


def extrude(dr, fr, pts, z0, z1, wall, top, stripe=None, windows=False):
    """多角形を z0〜z1 に押し出す。見える側面（外向きの法線が手前を向く面）を奥から塗り、最後に上の面。"""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    cg = fr.ground(cx, cy)
    faces = []
    for a, b in zip(pts, pts[1:] + pts[:1]):
        ga, gb = fr.ground(*a), fr.ground(*b)
        ex, ey = gb[0] - ga[0], gb[1] - ga[1]
        nx, ny = ey, -ex
        mx, my = (ga[0] + gb[0]) / 2, (ga[1] + gb[1]) / 2
        if nx * (mx - cg[0]) + ny * (my - cg[1]) < 0:
            nx, ny = -nx, -ny
        norm = (nx * nx + ny * ny) ** 0.5 or 1.0
        nx, ny = nx / norm, ny / norm
        if nx * VIEW[0] + ny * VIEW[1] <= 0:
            continue
        # 光は左上から。左下（+y）を向く面は明るく、右下（+x）を向く面は暗く
        k = 0.74 + 0.28 * max(0.0, ny) - 0.0 * max(0.0, nx)
        faces.append((mx + my, a, b, k))
    for _, a, b, k in sorted(faces):
        quad = [fr.P(a, z0), fr.P(b, z0), fr.P(b, z1), fr.P(a, z1)]
        dr.polygon(quad, fill=safe(c * k for c in wall) + (255,))
        if stripe:
            zm = z0 + (z1 - z0) * 0.28
            dr.polygon([fr.P(a, z0), fr.P(b, z0), fr.P(b, zm), fr.P(a, zm)], fill=safe(c * k for c in stripe) + (255,))
        if windows:
            n = max(1, int(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 / 2.0))
            zl, zh = z0 + (z1 - z0) * 0.42, z0 + (z1 - z0) * 0.74
            for i in range(n):
                p0 = tuple(a[j] + (b[j] - a[j]) * (i + 0.2) / n for j in (0, 1))
                p1 = tuple(a[j] + (b[j] - a[j]) * (i + 0.8) / n for j in (0, 1))
                dr.polygon([fr.P(p0, zl), fr.P(p1, zl), fr.P(p1, zh), fr.P(p0, zh)], fill=GLASS + (255,))
    dr.polygon([fr.P(p, z1) for p in pts], fill=safe(top) + (255,))


def boxes(spec, loaded):
    """甲板より上の物。(輪郭, 下, 上, 壁の色, 上の色, 窓)。"""
    length = length_of(spec) * V.M_PER_UNIT
    half = spec["width_m"] / 2
    z = spec["hull_z"]
    out = []
    if "hold" in spec:
        a, b, w = spec["hold"]
        out.append((outline(a * length, b * length, half * w), z, z + 0.6, spec["hull"], HOLD, False))
        if loaded:
            out.append((outline(a * length + 1.0, b * length - 1.0, half * w * 0.8), z + 0.6, z + 1.5, COAL, COAL, False))
    for a, b, w, z0, z1, wall, roof, win in spec["house"]:
        out.append((outline(a * length, b * length, half * w), z0, z1, wall, roof, win))
    a, b, w, z0, z1, wall, roof = spec["funnel"]
    out.append((outline(a * length, b * length, half * w), z0, z1, wall, roof, False))
    return out


def draw_cell(spec, direction, loaded=False):
    im = Image.new("RGBA", (CELL * SS, CELL * SS), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    fr = Frame(direction)
    length = length_of(spec) * V.M_PER_UNIT
    half = spec["width_m"] / 2
    hull = outline(0.0, length, half, bow=length * 0.2)
    extrude(dr, fr, hull, 0.0, spec["hull_z"], spec["hull"], DECK, stripe=spec["stripe"])

    def key(box):
        pts, z0 = box[0], box[1]
        c = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        return fr.depth(c)

    # 下の段（甲板に載る物）を奥から、次にその上の段を描く
    items = boxes(spec, loaded)
    floor = [b for b in items if b[1] <= spec["hull_z"]]
    upper = [b for b in items if b[1] > spec["hull_z"]]
    for group in (floor, upper):
        for pts, z0, z1, wall, roof, win in sorted(group, key=key):
            extrude(dr, fr, pts, z0, z1, wall, roof, windows=win)

    small = im.resize((CELL, CELL), Image.LANCZOS)
    px = small.load()
    for y in range(CELL):
        for x in range(CELL):
            r, g, b, a = px[x, y]
            px[x, y] = safe((r, g, b)) + (255,) if a >= 128 else (0, 0, 0, 0)
    return small


def sheet_rows(spec):
    return 2 if spec.get("freight_image") else 1


def draw_sheet(spec):
    sheet = Image.new("RGBA", (CELL * len(V.DIRECTIONS), CELL * sheet_rows(spec)), (0, 0, 0, 0))
    for row in range(sheet_rows(spec)):
        for i, direction in enumerate(V.DIRECTIONS):
            sheet.paste(draw_cell(spec, direction, loaded=bool(row)), (i * CELL, row * CELL))
    return sheet


def yaml_lines(spec):
    stem = spec["stem"]
    length = length_of(spec)
    lines = [
        f"# {spec['title']}（絵は仮）。この表と PNG は draw_ships.py が書き出す。直すときはスクリプトを直して流し直す。",
        f"# 実物 {spec['real_length_m']:g}m。船は実物比例で、length {length}（docs/standards.md の 4 章「船・飛行機」）。",
        "# 値は pak128 の同じ種類の船の機能上の数値に合わせた（docs/vehicles.md の「船」）。",
        "obj: vehicle",
        f"name: {spec['name']}",
        "copyright: pak256.LongScale チーム",
        "waytype: water",
        f"freight: {spec['freight']}",
        f"payload: {spec['payload']}",
        "engine_type: diesel",
        "sound: pak256_ship.wav  # 停留所から発車するときの音（docs/sound.md）",
        "smoke: pak256_smoke_ship  # 加速中に出る（objects/smoke/。docs/smoke.md）",
        f"power: {spec['power']}",
        f"speed: {spec['speed']}",
        f"gear: {spec['gear']}",
        f"intro_year: {spec['intro_year']}",
        f"cost: {spec['cost']}",
        f"runningcost: {spec['runningcost']}",
        f"weight: {spec['weight']}",
        f"length: {length}",
        "cell_size: 512",
        "emptyimage:       # 向きごとの絵" + ("（0 行 = 空）" if spec.get("freight_image") else ""),
    ]
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: {stem}.0.{i},-128,-128")
    if spec.get("freight_image"):
        lines.append("freightimage:     # 積み荷を積んだ絵（1 行）")
        for i, direction in enumerate(V.DIRECTIONS):
            lines.append(f"  {direction}: {stem}.1.{i},-128,-128")
    return "\n".join(lines) + "\n"


def main():
    for spec in VEHICLES:
        out = os.path.join(HERE, spec["dir"])
        os.makedirs(out, exist_ok=True)
        draw_sheet(spec).save(os.path.join(out, spec["stem"] + ".png"))
        with open(os.path.join(out, spec["stem"] + ".yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(yaml_lines(spec))
        print("wrote", spec["name"])


if __name__ == "__main__":
    main()
