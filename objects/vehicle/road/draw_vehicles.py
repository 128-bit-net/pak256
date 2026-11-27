"""道路の車両（バス・郵便のトラック・石炭のトラック）の絵と表を書き出す（docs/vehicles.md・#41・#42・#59）。MIT License。
絵は仮（箱を組んだ物）で、見た目は後から描き直す。

長さと描画位置は tools/vehicles.py の決まりで決める。画面の大きさは pak128 の同じ種類の手本の 2 倍（`target_px`。長さ・幅・高さ。
docs/standards.md の 4 章「大きさ」）。`length` はその長さから決め、幅と高さは実物の値に `scale` の倍率を掛けて描く。
8 方向を 256px のセルに横に並べたシート（2048x256。積み荷の絵がある車両は
2 行目に積んだ絵を足した 2048x512）を車両ごとに `<種類>/<名前>.png` に、表を `<名前>.yaml` に書く。値（登場年・速さ・定員・費用）は
docs/vehicles.md の表。車両を足すときは `VEHICLES` に 1 件足す（絵の組み方は 2 通り）:
- `style: panel`: 車体の長さを前から割った部分（`parts`）を、全幅の箱として組む（バス・郵便のトラック）。
- `style: boxes`: 前後の端と幅・高さを持つ箱（`boxes`）を重ねる（石炭のトラック。積んだ絵の箱は `loaded: True`）。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/vehicle/road/draw_vehicles.py
試験の印（車体の地面の枠と基準点）を重ねた絵を別の場所に書くとき（描画位置を確かめる試験用。git に入れない）:
    python -X utf8 objects/vehicle/road/draw_vehicles.py --marker --out build/vehicle_marker
一部の車両だけ書くとき: `--only pak256_coal_truck`（名前は何回でも）。
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
INSIDE = (84, 88, 96)  # 空の荷台の内側（上から見える底）
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

# --- 石炭のトラックの箱 ---
# (前の端, 後ろの端, 幅, 下の高さ, 上の高さ, 色, 種類)。端は基準点から車体の前を正にした m（前の端 = 0、後ろの端 = -length × 1.65）。
# 長さは dat の length（単位）× 1.65m に合わせる。運転席は 2.1m の 1.3 倍・荷台はその後ろ全部。幅は実物の 1.22 倍
COAL_REAL_LENGTH_M = 7.0  # 実物の長さ（仮。2 軸の貨物車の大きさ）
COAL_WIDTH_M = 2.5
COAL_LENGTH = 8  # dat の length。手本（pak128 の Bulk_Truck_2）の 2 倍の長さ 86px から
COAL_SCALE = (1.22, 1.87)  # (幅, 高さ) の倍率
COAL_DRAW_WIDTH_M = COAL_WIDTH_M * COAL_SCALE[0]
_L = COAL_LENGTH * V.M_PER_UNIT
CAB_M = 2.1 * 1.3
CHASSIS = (0.0, -_L, 2.1 * COAL_SCALE[0], 0.0, 0.6, (40, 40, 44), "chassis")  # 車輪のあたりの暗い帯（全長）
CAB = (0.0, -CAB_M, COAL_DRAW_WIDTH_M, 0.6, 2.7, (176, 52, 44), "cab")  # 運転席（赤）
BED = (-CAB_M, -_L, COAL_DRAW_WIDTH_M, 0.6, 2.2, (118, 124, 132), "bed")  # 荷台（灰色の鉄）
# 積んだ石炭の山（荷台の内側）。荷台の壁より少し高い
COAL = (-CAB_M - 0.25, -_L + 0.2, COAL_DRAW_WIDTH_M - 0.4, 2.2, 2.55, (30, 30, 34), "coal")
PARTS_EMPTY = (CHASSIS, CAB, BED)
PARTS_LOADED = (CHASSIS, CAB, BED, COAL)

# 車両の表。値は pak128 の同じ種類を目安にした（docs/vehicles.md の表に理由）。
# panel の parts: 車体の部分。(前からの位置の始め, 終わり, 高さ m, 車体の色, 帯の色 or None, 窓の種類)。位置は車体の長さの 0〜1。
VEHICLES = [
    {
        "name": "pak256_bus", "dir": "bus", "stem": "bus", "title": "bus", "style": "panel",
        "real_length_m": 12.0, "width_m": 2.5,
        # 手本は pak128 の S_Kroytor_Ikarus-260（49,11,12）と Man_Lions_City（51,11,12）の平均の 2 倍
        "target_px": (100, 22, 24), "length": 9, "scale": (1.22, 1.30),
        "freight": "Passagiere", "payload": 70, "power": 205, "speed": 60, "gear": 80,
        "weight": 11, "sound": "pak256_bus.wav", "cost": 661000, "runningcost": 39, "intro_year": 1930,
        "parts": [(0.0, 1.0, 3.2, (214, 196, 150), (52, 112, 84), "bus")],
    },
    {
        "name": "pak256_mail_truck", "dir": "mail_truck", "stem": "mail_truck", "title": "mail_truck", "style": "panel",
        "real_length_m": 7.0, "width_m": 2.2,
        # 手本は pak128 の Mail_Truck_2（34,12,11）の 2 倍
        "target_px": (68, 24, 22), "length": 6, "scale": (1.62, 1.18),
        "freight": "Post", "payload": 44, "power": 77, "speed": 60, "gear": 80,
        "weight": 5, "sound": "pak256_truck.wav", "cost": 863000, "runningcost": 38, "intro_year": 1930,
        "parts": [
            (0.0, 0.3, 2.3, (190, 52, 44), None, "cab"),  # 運転席
            (0.3, 1.0, 3.0, (200, 62, 52), (236, 220, 120), "van"),  # 荷台の箱
        ],
    },
    {
        "name": "pak256_coal_truck", "dir": "coal_truck", "stem": "coal_truck", "title": "石炭のトラック", "style": "boxes",
        "real_length_m": COAL_REAL_LENGTH_M, "width_m": COAL_WIDTH_M,
        # 手本は pak128 の Bulk_Truck_2（43,11,14）の 2 倍
        "target_px": (86, 22, 28), "length": COAL_LENGTH, "scale": COAL_SCALE,
        "freight": "Kohle", "payload": 12, "power": 95, "speed": 55, "gear": 90,
        "weight": 8, "sound": "pak256_truck.wav", "cost": 384000, "runningcost": 24, "intro_year": 1930,
        "note": "値は pak128 の石炭のトラック（Bulk_Truck_2）に合わせた（docs/vehicles.md の表）。登場年だけ見本のバスと同じ 1930。",
        "freight_image": True,  # 2 行目に積んだ絵（freightimage）。0 行 = 空、1 行 = 積んだ
        "boxes_empty": PARTS_EMPTY, "boxes_loaded": PARTS_LOADED,
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
    return spec["length"]


def corners(direction, part):
    """boxes の箱の地面の四隅（前の右・前の左・後の左・後の右。タイルの単位）。"""
    front, back, width = part[0], part[1], part[2]
    # footprint は「基準点から前の端までの単位」と「長さ（単位）」を取る。端を m から単位に直して渡す
    return V.footprint(direction, (front - back) / V.M_PER_UNIT, width, front / V.M_PER_UNIT)


def depth(direction, part):
    """箱の奥行き（画面の手前ほど大きい。x + y）。描く順を決める。"""
    return sum(p[0] + p[1] for p in corners(direction, part)) / 4


def visible_faces(box, cx, cy):
    """箱の地面の四隅から、見る側（VIEW）を向く側面を (a, b, 明るさ, 前の面か) で返す。cx, cy は箱が広がる向きを決める中心。"""
    fr, fl, bl, br = box
    for a, b, k, is_front in ((fr, fl, 1.0, True), (fl, bl, 0.85, False), (bl, br, 0.7, False), (br, fr, 0.85, False)):
        nx, ny = b[1] - a[1], -(b[0] - a[0])
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        if nx * (mx - cx) + ny * (my - cy) < 0:
            nx, ny = -nx, -ny
        if nx * VIEW[0] + ny * VIEW[1] <= 1e-9:
            continue
        yield a, b, k, is_front


class Canvas:
    """3 倍に拡大して描き、最後に 256px に縮めて半透明を切る（makeobj の特別な色を避ける）。shift は試験の絵のずれ（px）。"""

    def __init__(self, shift=(0.0, 0.0), height_scale=1.0):
        self.height_scale = height_scale
        self.img = Image.new("RGBA", (V.CELL * SS, V.CELL * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.shift = shift

    def scr(self, p, z):
        sx, sy = V.to_screen(p[0], p[1], z * self.height_scale)
        return (sx + self.shift[0]) * SS, (sy + self.shift[1]) * SS

    def quad(self, p0, p1, z0, z1, color):
        self.d.polygon([self.scr(p0, z0), self.scr(p1, z0), self.scr(p1, z1), self.scr(p0, z1)], fill=color)

    def top(self, box, z, color):
        self.d.polygon([self.scr(p, z) for p in box], fill=color)

    def finish(self):
        img = self.img.resize((V.CELL, V.CELL), Image.LANCZOS)
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


def draw_panel(c, spec, direction, whole):
    """panel: 車体を前から割った部分を全幅の箱として描く。"""
    # 奥の部分から描く（画面の x + y の小さい方が奥）
    parts = sorted(spec["parts"], key=lambda p: sum(
        (q[0] + q[1]) for q in part_corners(whole, p[0], p[1])))
    for t0, t1, height, body, band, kind in parts:
        box = part_corners(whole, t0, t1)
        # 面の向きは部分の箱の中心から決める（車体全体の中心からだと、前の部分の後ろの面を手前向きと誤り、前の面に塗り重ねる。#116）
        cx = (box[0][0] + box[2][0]) / 2
        cy = (box[0][1] + box[2][1]) / 2
        for a, b, k, is_front in visible_faces(box, cx, cy):
            c.quad(a, b, 0.0, 0.5, shade(SKIRT, k))
            c.quad(a, b, 0.5, height, shade(body, k))
            if band:
                c.quad(a, b, 0.5, 1.0, shade(band, k))
            if kind == "bus":
                if is_front:
                    c.quad(lerp(a, b, 0.1), lerp(a, b, 0.9), 1.5, 2.8, shade(GLASS, k))
                else:
                    c.quad(lerp(a, b, 0.06), lerp(a, b, 0.94), 1.7, 2.6, shade(GLASS, k))
            elif kind == "cab":
                if is_front:
                    c.quad(lerp(a, b, 0.1), lerp(a, b, 0.9), 1.3, 2.1, shade(GLASS, k))
                else:
                    c.quad(lerp(a, b, 0.15), lerp(a, b, 0.85), 1.3, 2.1, shade(GLASS, k))
            elif kind == "van" and not is_front and band:
                c.quad(lerp(a, b, 0.1), lerp(a, b, 0.9), 1.6, 1.9, shade(band, k))  # 郵便の帯
        c.top(box, height, shade(body, 1.15))


def draw_boxes(c, spec, direction, loaded):
    """boxes: 前後の端・幅・高さを持つ箱を奥から重ねる。石炭の山は荷台の上に載るので、荷台と同じ奥行きとして荷台の後に描く。"""
    parts = spec["boxes_loaded"] if loaded else spec["boxes_empty"]
    bed = next(p for p in parts if p[6] == "bed")
    for part in sorted(parts, key=lambda p: (depth(direction, bed if p[6] == "coal" else p), p[6] == "coal")):
        box = corners(direction, part)
        fr, fl, bl, br = box
        _, _, _, z0, z1, color, kind = part
        cx = (fr[0] + bl[0]) / 2
        cy = (fr[1] + bl[1]) / 2
        for a, b, k, is_front in visible_faces(box, cx, cy):
            c.quad(a, b, z0, z1, shade(color, k))
            if kind == "cab" and a is fr:  # 運転席の前の面に窓
                c.quad(lerp(a, b, 0.1), lerp(a, b, 0.9), 1.5, 2.45, shade(GLASS, k))
        if kind == "bed" and not loaded:
            c.top(box, z1, INSIDE)
        elif kind == "coal":
            c.top(box, z1, shade(color, 1.35))
        elif kind == "cab":
            c.top(box, z1, shade(color, 1.25))
        elif kind == "bed":
            c.top(box, z1, shade(color, 1.15))  # 荷台の上の縁（壁の上の面）。内側は石炭の山が覆う


def draw_cell(spec, direction, marker, emulate_right=False, loaded=False):
    """1 方向のセル（256x256、RGBA）を描く。

    emulate_right: 左側通行の地図で右側通行の見え方を確かめる試験の絵。本体が左側通行で足すずれ
    （tools/vehicles.py の DRIVELEFT_64）をあらかじめ引いて描く。
    """
    whole = V.footprint(direction, body_box(spec), spec["width_m"] * spec["scale"][0], V.FRONT_UNITS)
    shift = (0.0, 0.0)
    if emulate_right:
        lx, ly = V.DRIVELEFT_64[direction]
        shift = (-lx * V.CELL / 64, -ly * V.CELL / 64)
    c = Canvas(shift, spec["scale"][1])
    if spec["style"] == "panel":
        draw_panel(c, spec, direction, whole)
    else:
        draw_boxes(c, spec, direction, loaded)

    if marker:
        fr, fl, bl, br = whole
        pts = [c.scr(p, 0.0) for p in whole]
        c.d.line(pts + [pts[0]], fill=MARK, width=SS)
        c.d.line([c.scr(fr, 0.0), c.scr(fl, 0.0)], fill=MARK2, width=2 * SS)
        lx, ly = c.scr(V.lane_point(direction), 0.0)  # noqa: E741
        c.d.ellipse([lx - 2 * SS, ly - 2 * SS, lx + 2 * SS, ly + 2 * SS], fill=MARK2)
        ox, oy = c.scr((0.0, 0.0), 0.0)
        c.d.line([ox - 4 * SS, oy, ox + 4 * SS, oy], fill=MARK, width=SS)
        c.d.line([ox, oy - 2 * SS, ox, oy + 2 * SS], fill=MARK, width=SS)
    return c.finish()


def sheet_rows(spec):
    """シートの行数（積んだ絵があれば 2）。"""
    return 2 if spec.get("freight_image") else 1


def yaml_lines(spec, name=None):
    """表（yaml）の全文。name は試験の絵（_right_test）のときだけ変える。"""
    length = body_box(spec)
    stem = spec["stem"]
    lines = [
        f"# {spec['title']}（絵は仮）。この表と PNG は draw_vehicles.py が書き出す。直すときはスクリプトを直して流し直す。",
        f"# 実物 {spec['real_length_m']:g}m。画面の大きさは pak128 の手本の 2 倍で、length {length}（docs/standards.md の 4 章）。",
    ]
    if spec.get("note"):
        lines.append(f"# {spec['note']}")
    lines += [
        "obj: vehicle",
        f"name: {name or spec['name']}",
        "copyright: pak256.LongScale チーム",
        "waytype: road",
        f"freight: {spec['freight']}",
        f"payload: {spec['payload']}",
        "engine_type: diesel",
        f"sound: {spec['sound']}  # 停留所から発車するときの音（docs/sound.md）",
        f"power: {spec['power']}",
        f"speed: {spec['speed']}",
        f"gear: {spec['gear']}",
        f"intro_year: {spec['intro_year']}",
        f"cost: {spec['cost']}",
        f"runningcost: {spec['runningcost']}",
        f"weight: {spec['weight']}",
        f"length: {length}",
        "emptyimage:       # 向きごとの絵" + ("（0 行 = 空）" if spec.get("freight_image") else ""),
    ]
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: {stem}.0.{i}")
    if spec.get("freight_image"):
        lines.append("freightimage:     # 積み荷を積んだ絵（1 行）")
        for i, direction in enumerate(V.DIRECTIONS):
            lines.append(f"  {direction}: {stem}.1.{i}")
    return "\n".join(lines) + "\n"


def draw_sheet(spec, marker=False, emulate_right=False):
    """車両のシート（8 方向 × 1〜2 行）を描く。"""
    sheet = Image.new("RGBA", (V.CELL * len(V.DIRECTIONS), V.CELL * sheet_rows(spec)), (0, 0, 0, 0))
    for row in range(sheet_rows(spec)):
        for i, direction in enumerate(V.DIRECTIONS):
            sheet.paste(draw_cell(spec, direction, marker, emulate_right, loaded=bool(row)), (i * V.CELL, row * V.CELL))
    return sheet


def write_vehicle(spec, out, marker=False, emulate_right=False):
    os.makedirs(out, exist_ok=True)
    draw_sheet(spec, marker, emulate_right).save(os.path.join(out, spec["stem"] + ".png"))
    with open(os.path.join(out, spec["stem"] + ".yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(yaml_lines(spec, spec["name"] + ("_right_test" if emulate_right else "")))
    print("wrote", os.path.join(out, spec["stem"] + ".png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", action="store_true", help="試験の印を重ねる（git に入れない）")
    ap.add_argument("--emulate-right", action="store_true",
                    help="左側通行の地図で右側通行の見え方を確かめる試験の絵（名前に _right_test を付ける。git に入れない）")
    ap.add_argument("--out", default=None, help="書き出す場所（既定は、車両ごとのこのフォルダの下）")
    ap.add_argument("--only", action="append", default=[], help="書く車両の name（既定は全部）")
    args = ap.parse_args()
    names = {s["name"] for s in VEHICLES}
    for n in args.only:
        if n not in names:
            sys.exit(f"車両が無い: {n}（{sorted(names)}）")
    for spec in VEHICLES:
        if args.only and spec["name"] not in args.only:
            continue
        write_vehicle(spec, args.out or os.path.join(HERE, spec["dir"]), args.marker, args.emulate_right)


if __name__ == "__main__":
    main()
