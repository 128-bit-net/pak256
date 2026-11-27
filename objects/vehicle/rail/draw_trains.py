"""線路の車両（気動車・付随車）の絵と表を書き出す（docs/vehicles.md の「線路の車両」・#46）。MIT License。
絵は仮（箱を組んだ物）で、見た目は後から描き直す。

- 画面の大きさは pak128.Japan の手本（`yoshi_kiha35_m`）の 2 倍（docs/standards.md の 4 章「大きさ」）。長さは実物の換算のままで、
  幅と高さは実物の値に `tools/vehicles.py` の `RAIL_WIDTH_SCALE`・`RAIL_HEIGHT_SCALE` を掛けて描く。
- 長さと描画位置は tools/vehicles.py の決まりで決める。線路の車両は車線のずれを付けず、線路の中心（基準点）に描く
  （`footprint(centered=True)`）。20m の車体は length=12 で、横の斜めでは 1 タイルのセル（256）に収まらないので、512 のセルに描く
  （表に cell_size: 512 と位置合わせ -128,-128 を書く。docs/layout.md の「セルの大きさ」）。
- 8 方向を 512px のセルに横に並べたシート（4096x512）を車両ごとに `<名前>/<名前>.png` に、表を `<名前>.yaml` に書く。
- 道路の車両の描く道具（objects/vehicle/road/draw_vehicles.py）の箱を組む関数と色の決まりを読んで使う（道具を写して増やさない）。
- 車輪の下端の高さは `V.RAIL_WHEEL_DROP_PX`（地面より何 px 下に描くか。今は 0 = 地面の高さ。docs/vehicles.md）。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/vehicle/rail/draw_trains.py
試験の印（車体の地面の枠と基準点）を重ねた絵を別の場所に書くとき（git に入れない）:
    python -X utf8 objects/vehicle/rail/draw_trains.py --marker --out build/train_marker
"""
import argparse
import importlib.util
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import vehicles as V  # noqa: E402

_DV = os.path.join(HERE, "..", "road", "draw_vehicles.py")
_spec = importlib.util.spec_from_file_location("draw_vehicles", _DV)
dv = importlib.util.module_from_spec(_spec)
sys.modules["draw_vehicles"] = dv
_spec.loader.exec_module(dv)

CELL = 512  # 20m の車体が収まるセル
PAD = (CELL - V.CELL) // 2  # 256 のセルの絵を 512 のセルの真ん中に置く（256 のセルの座標 + PAD）。位置合わせは -PAD
SS = dv.SS
CHASSIS = (44, 44, 50)  # 台車のあたりの暗い帯
GLASS = dv.GLASS
SIDE_WINDOWS = 6  # 車体の横の窓の数

WIDTH_M = 2.8
HEIGHT_M = 3.6
FLOOR_M = 0.9  # 床の下面（台車の上）
BOGIE_WIDTH_M = 2.2
TARGET_PX = (132, 28, 24)  # yoshi_kiha35_m（66,14,12）の 2 倍

# 車両の表。値は pak128 の気動車（Haru_VT98 とその付随車）の機能上の数値に合わせた（docs/vehicles.md の表）。
VEHICLES = [
    {
        "name": "pak256_railcar", "dir": "railcar", "stem": "railcar", "title": "気動車",
        "real_length_m": 20.0, "powered": True,
        "payload": 80, "power": 220, "speed": 90, "gear": 100, "weight": 21,
        "cost": 8959000, "runningcost": 221, "intro_year": 1930,
        "body": (214, 196, 150), "band": (52, 112, 84), "cab": True,
    },
    {
        "name": "pak256_railcar_trailer", "dir": "railcar_trailer", "stem": "railcar_trailer", "title": "気動車の付随車",
        "real_length_m": 20.0, "powered": False,
        "payload": 80, "power": 0, "speed": 90, "gear": 100, "weight": 17,
        "cost": 1894000, "runningcost": 28, "intro_year": 1930,
        "body": (214, 196, 150), "band": (52, 112, 84), "cab": False,
    },
]


def length_of(spec):
    return V.length_units(spec["real_length_m"])


class Canvas:
    """3 倍に拡大して描き、最後に 512px に縮めて半透明を切る（makeobj の特別な色を避ける）。"""

    def __init__(self):
        self.img = Image.new("RGBA", (CELL * SS, CELL * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def scr(self, p, z_m):
        sx, sy = V.to_screen(p[0], p[1], z_m * V.RAIL_HEIGHT_SCALE)
        return (sx + PAD) * SS, (sy + PAD + V.RAIL_WHEEL_DROP_PX) * SS

    def quad(self, p0, p1, z0, z1, color):
        self.d.polygon([self.scr(p0, z0), self.scr(p1, z0), self.scr(p1, z1), self.scr(p0, z1)], fill=color)

    def top(self, box, z, color):
        self.d.polygon([self.scr(p, z) for p in box], fill=color)

    def finish(self):
        img = self.img.resize((CELL, CELL), Image.LANCZOS)
        px = img.load()
        for y in range(CELL):
            for x in range(CELL):
                r, g, b, a = px[x, y]
                if a < 128:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                if (r << 16 | g << 8 | b) in dv.SPECIAL:
                    r = r + 1 if r < 255 else r - 1
                px[x, y] = (r, g, b, 255)
        return img


def draw_cell(spec, direction, marker):
    """1 方向のセル（512x512、RGBA）を描く。前後が同じ形なので、逆向きに走っても崩れない。"""
    length = length_of(spec)
    whole = V.footprint(direction, length, WIDTH_M * V.RAIL_WIDTH_SCALE, V.FRONT_UNITS, centered=True)
    bogie = V.footprint(direction, length - 3, BOGIE_WIDTH_M * V.RAIL_WIDTH_SCALE, V.FRONT_UNITS - 1.5, centered=True)
    cx = (whole[0][0] + whole[2][0]) / 2
    cy = (whole[0][1] + whole[2][1]) / 2
    c = Canvas()
    # 台車のあたり（暗い帯）。車体より狭く、車体の下に隠れる
    for a, b, k, _ in dv.visible_faces(bogie, cx, cy):
        c.quad(a, b, 0.0, FLOOR_M, dv.shade(CHASSIS, k))
    for a, b, k, is_front in dv.visible_faces(whole, cx, cy):
        rear = a is whole[2]
        c.quad(a, b, FLOOR_M, 1.5, dv.shade(spec["band"], k))  # 下の帯
        c.quad(a, b, 1.5, HEIGHT_M, dv.shade(spec["body"], k))
        if is_front or rear:  # 車体の端
            if spec["cab"]:
                c.quad(dv.lerp(a, b, 0.1), dv.lerp(a, b, 0.9), 1.9, 3.1, dv.shade(GLASS, k))  # 運転席の前面ガラス
            else:
                c.quad(dv.lerp(a, b, 0.35), dv.lerp(a, b, 0.65), 1.7, 3.0, dv.shade(GLASS, k))  # 貫通扉の窓
        else:  # 横の窓
            for i in range(SIDE_WINDOWS):
                t0 = 0.08 + i * 0.84 / SIDE_WINDOWS
                c.quad(dv.lerp(a, b, t0), dv.lerp(a, b, t0 + 0.84 / SIDE_WINDOWS * 0.7), 1.9, 3.0, dv.shade(GLASS, k))
    c.top(whole, HEIGHT_M, dv.shade(spec["body"], 1.1))  # 屋根
    if marker:
        fr, fl, bl, br = whole
        pts = [c.scr(p, 0.0) for p in whole]
        c.d.line(pts + [pts[0]], fill=dv.MARK, width=SS)
        c.d.line([c.scr(fr, 0.0), c.scr(fl, 0.0)], fill=dv.MARK2, width=2 * SS)
        ox, oy = c.scr((0.0, 0.0), 0.0)
        c.d.line([ox - 4 * SS, oy, ox + 4 * SS, oy], fill=dv.MARK, width=SS)
        c.d.line([ox, oy - 2 * SS, ox, oy + 2 * SS], fill=dv.MARK, width=SS)
    return c.finish()


def yaml_lines(spec):
    length = length_of(spec)
    stem = spec["stem"]
    lines = [
        f"# {spec['title']}（絵は仮）。この表と PNG は draw_trains.py が書き出す。直すときはスクリプトを直して流し直す。",
        f"# 実物 {spec['real_length_m']:g}m ÷ 1.65 = {spec['real_length_m'] / V.M_PER_UNIT:.2f} → length {length}（docs/vehicles.md）。",
        "# 20m の車体は 256 のセルに収まらないので 512 のセルに描く（cell_size と、各絵の位置合わせ）。",
        "obj: vehicle",
        f"name: {spec['name']}",
        "copyright: pak256.LongScale チーム",
        "waytype: track",
        "cell_size: 512",
        "freight: Passagiere",
        f"payload: {spec['payload']}",
    ]
    if spec["powered"]:
        lines.append("engine_type: diesel")
        lines.append("sound: pak256_railcar.wav  # 停留所から発車するときの音（docs/sound.md）")
        lines.append("smoke: pak256_smoke_diesel  # 加速中に出る（objects/smoke/。docs/smoke.md）")
    lines += [
        f"power: {spec['power']}",
        f"speed: {spec['speed']}",
        f"gear: {spec['gear']}",
        f"intro_year: {spec['intro_year']}",
        f"cost: {spec['cost']}",
        f"runningcost: {spec['runningcost']}",
        f"weight: {spec['weight']}",
        f"length: {length}",
    ]
    if not spec["powered"]:  # 付随車は先頭にならない（気動車か付随車の後ろ）
        lines += ["constraint:", "  prev:", "    0: pak256_railcar", "    1: pak256_railcar_trailer"]
    lines += [
        "emptyimage:       # 向きごとの絵（画像名,x の位置合わせ,y の位置合わせ）",
    ]
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: \"{stem}.0.{i},{-PAD},{-PAD}\"")
    return "\n".join(lines) + "\n"


def draw_sheet(spec, marker=False):
    sheet = Image.new("RGBA", (CELL * len(V.DIRECTIONS), CELL), (0, 0, 0, 0))
    for i, direction in enumerate(V.DIRECTIONS):
        sheet.paste(draw_cell(spec, direction, marker), (i * CELL, 0))
    return sheet


def write_vehicle(spec, out, marker=False):
    os.makedirs(out, exist_ok=True)
    draw_sheet(spec, marker).save(os.path.join(out, spec["stem"] + ".png"))
    with open(os.path.join(out, spec["stem"] + ".yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(yaml_lines(spec))
    print("wrote", os.path.join(out, spec["stem"] + ".png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", action="store_true", help="試験の印を重ねる（git に入れない）")
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
        write_vehicle(spec, args.out or os.path.join(HERE, spec["dir"]), args.marker)


if __name__ == "__main__":
    main()
