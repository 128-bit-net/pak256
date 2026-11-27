"""路面電車の絵と表を書き出す（docs/vehicles.md の「路面電車」・#153）。MIT License。
絵は仮（箱を組んだ物）で、見た目は後から描き直す。

- 線路の車両の決まり（docs/standards.md の 4 章）で描く。車線のずれは付けず、線路（道路に敷いた軌道では道路の中央）の
  中心に描く（`footprint(centered=True)`。本体は路面電車を線路の車両として描く）。
- 画面の長さと幅は pak128.Japan の路面電車（`Toden 400`）の 2 倍に合わせる。長さは実物の換算（12m → length 7）、幅と高さは
  実物の値に `tools/vehicles.py` の `RAIL_WIDTH_SCALE`・`RAIL_HEIGHT_SCALE` を掛ける。手本の絵の高さは集電装置（屋根の上の
  ポール）を含むので高さの目標にせず、屋根の高さだけにする。集電装置は、AMI の架線の線の高さに届くように描く。
- 7 単位の車体は 256 のセルに収まる（`cell_size` は書かない）。
- 8 方向のセルを横に並べたシート（2048x256）を `tramcar/tramcar.png` に、表を `tramcar.yaml` に書く。
- 面の向きや明るさの決まりは、道路の車両の道具（objects/vehicle/road/draw_vehicles.py）の関数を読んで使う。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/vehicle/tram/draw_tram.py
試験の印（車体の地面の枠と基準点）を重ねた絵を別の場所に書くとき（git に入れない）:
    python -X utf8 objects/vehicle/tram/draw_tram.py --marker --out build/tram_marker
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

SS = dv.SS
CHASSIS = (44, 44, 50)
GLASS = dv.GLASS
DOOR = (96, 104, 112)
ROOF = (150, 152, 156)
SIDE_WINDOWS = 6  # 車体の横を分ける数。両端の 1 つずつは扉

WIDTH_M = 2.2
HEIGHT_M = 3.5
FLOOR_M = 0.7  # 床の下面（台車の上）
WINDOW_M = (1.7, 2.8)  # 窓の下端と上端
BAND_M = 1.5  # 下の帯の上端
BOGIE_WIDTH_M = 1.8
TARGET_PX = (82, 22, 25)  # 長さ・幅は Toden 400（41,11）の 2 倍。高さは屋根まで（3.5m × 1.2 = 約 25px）
WIRE_PX = 48  # AMI の路面軌道の架線（ami_tram_catenary）のトロリ線の高さ（画面の px。地面から）。集電装置の舟はここに届く
COLLECTOR_HALF = 0.055  # 舟の長さの半分（タイルの単位）

# 値は pak128 の路面電車（MHz_TRAM_1930）の機能上の数値に合わせた（docs/vehicles.md の表）
SPEC = {
    "name": "pak256_tram", "dir": "tramcar", "stem": "tramcar", "title": "路面電車",
    "real_length_m": 12.0,
    "payload": 72, "power": 113, "speed": 50, "gear": 110, "weight": 18,
    "cost": 1308000, "runningcost": 55, "intro_year": 1930,
    "body": (226, 212, 170), "band": (176, 62, 48),
}


def length_of(spec=SPEC):
    return V.length_units(spec["real_length_m"])


class Canvas:
    """3 倍に拡大して描き、最後に 256px に縮めて半透明を切る（makeobj の特別な色を避ける）。"""

    def __init__(self):
        self.img = Image.new("RGBA", (V.CELL * SS, V.CELL * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def scr(self, p, z_m):
        sx, sy = V.to_screen(p[0], p[1], z_m * V.RAIL_HEIGHT_SCALE)
        return sx * SS, (sy + V.RAIL_WHEEL_DROP_PX) * SS

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
                if (r << 16 | g << 8 | b) in dv.SPECIAL:
                    r = r + 1 if r < 255 else r - 1
                px[x, y] = (r, g, b, 255)
        return img


def boxes(direction):
    """車体と台車の地面の四隅（前の右・前の左・後の左・後の右）。"""
    length = length_of()
    whole = V.footprint(direction, length, WIDTH_M * V.RAIL_WIDTH_SCALE, V.FRONT_UNITS, centered=True)
    bogie = V.footprint(direction, length - 2, BOGIE_WIDTH_M * V.RAIL_WIDTH_SCALE, V.FRONT_UNITS - 1, centered=True)
    return whole, bogie


def draw_collector(c, direction, cx, cy):
    """屋根の上の集電装置（くの字の腕と、線路を横切る舟）。舟は車体の中心の真上の、架線の高さ。"""
    hx, hy = V.HEADING[direction]

    def at(along, side, z_px):
        # along・side はタイルの単位（前・右が正）。z_px は地面からの画面の高さ
        p = (cx + hx * along - hy * side, cy + hy * along + hx * side)
        return c.scr(p, z_px / (V.PX_PER_M_Z * V.RAIL_HEIGHT_SCALE))

    roof = HEIGHT_M * V.RAIL_HEIGHT_SCALE * V.PX_PER_M_Z
    knee = (roof + WIRE_PX) / 2
    head = [at(0.0, -COLLECTOR_HALF, WIRE_PX), at(0.0, COLLECTOR_HALF, WIRE_PX)]
    base = [at(-0.02, -0.025, roof), at(-0.02, 0.025, roof)]
    c.d.line(base, fill=CHASSIS, width=3 * SS)
    c.d.line([at(-0.02, 0.0, roof), at(0.055, 0.0, knee), at(0.0, 0.0, WIRE_PX)], fill=CHASSIS, width=2 * SS)
    c.d.line(head, fill=CHASSIS, width=2 * SS)


def draw_cell(direction, marker=False, collector=True):
    """1 方向のセル（256x256、RGBA）を描く。前後が同じ形なので、逆向きに走っても崩れない。
    collector=False は車体だけ（位置と大きさの検査が使う）。"""
    spec = SPEC
    whole, bogie = boxes(direction)
    cx = (whole[0][0] + whole[2][0]) / 2
    cy = (whole[0][1] + whole[2][1]) / 2
    c = Canvas()
    for a, b, k, _ in dv.visible_faces(bogie, cx, cy):
        c.quad(a, b, 0.0, FLOOR_M, dv.shade(CHASSIS, k))
    for a, b, k, is_front in dv.visible_faces(whole, cx, cy):
        rear = a is whole[2]
        c.quad(a, b, FLOOR_M, BAND_M, dv.shade(spec["band"], k))
        c.quad(a, b, BAND_M, HEIGHT_M, dv.shade(spec["body"], k))
        if is_front or rear:  # 両端の運転台: 大きな前面の窓と、上の行き先の表示
            c.quad(dv.lerp(a, b, 0.08), dv.lerp(a, b, 0.92), WINDOW_M[0], WINDOW_M[1], dv.shade(GLASS, k))
            c.quad(dv.lerp(a, b, 0.3), dv.lerp(a, b, 0.7), WINDOW_M[1] + 0.15, HEIGHT_M - 0.15, dv.shade(CHASSIS, k))
        else:  # 横: 両端に扉、その間に窓
            for i in range(SIDE_WINDOWS):
                t0 = 0.04 + i * 0.92 / SIDE_WINDOWS
                if i in (0, SIDE_WINDOWS - 1):
                    c.quad(dv.lerp(a, b, t0), dv.lerp(a, b, t0 + 0.92 / SIDE_WINDOWS * 0.8), FLOOR_M, WINDOW_M[1], dv.shade(DOOR, k))
                else:
                    c.quad(dv.lerp(a, b, t0), dv.lerp(a, b, t0 + 0.92 / SIDE_WINDOWS * 0.75), WINDOW_M[0], WINDOW_M[1],
                           dv.shade(GLASS, k))
    c.top(whole, HEIGHT_M, dv.shade(ROOF, 1.1))
    if collector:
        draw_collector(c, direction, cx, cy)
    if marker:
        fr, fl, bl, br = whole
        pts = [c.scr(p, 0.0) for p in whole]
        c.d.line(pts + [pts[0]], fill=dv.MARK, width=SS)
        c.d.line([c.scr(fr, 0.0), c.scr(fl, 0.0)], fill=dv.MARK2, width=2 * SS)
        ox, oy = c.scr((0.0, 0.0), 0.0)
        c.d.line([ox - 4 * SS, oy, ox + 4 * SS, oy], fill=dv.MARK, width=SS)
        c.d.line([ox, oy - 2 * SS, ox, oy + 2 * SS], fill=dv.MARK, width=SS)
    return c.finish()


def yaml_lines(spec=SPEC):
    length = length_of(spec)
    stem = spec["stem"]
    lines = [
        f"# {spec['title']}（絵は仮）。この表と PNG は draw_tram.py が書き出す。直すときはスクリプトを直して流し直す。",
        f"# 実物 {spec['real_length_m']:g}m ÷ 1.65 = {spec['real_length_m'] / V.M_PER_UNIT:.2f} → length {length}（docs/vehicles.md）。",
        "# 架線（AMI の ami_tram_catenary）を張った路面軌道だけを走る（engine_type: electric）。",
        "obj: vehicle",
        f"name: {spec['name']}",
        "copyright: pak256.LongScale チーム",
        "waytype: tram_track",
        "freight: Passagiere",
        f"payload: {spec['payload']}",
        "engine_type: electric",
        "sound: pak256_tram.wav  # 停留所から発車するときの音（docs/sound.md）",
        f"power: {spec['power']}",
        f"speed: {spec['speed']}",
        f"gear: {spec['gear']}",
        f"intro_year: {spec['intro_year']}",
        f"cost: {spec['cost']}",
        f"runningcost: {spec['runningcost']}",
        f"weight: {spec['weight']}",
        f"length: {length}",
        # 単独か、路面電車どうしの連結だけ（車庫の違う線路の車両とはつながない）
        "constraint:",
        "  prev:",
        "    0: none",
        f"    1: {spec['name']}",
        "  next:",
        "    0: none",
        f"    1: {spec['name']}",
        "emptyimage:       # 向きごとの絵（画像名,x の位置合わせ,y の位置合わせ）",
    ]
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: \"{stem}.0.{i}\"")
    return "\n".join(lines) + "\n"


def draw_sheet(marker=False, collector=True):
    sheet = Image.new("RGBA", (V.CELL * len(V.DIRECTIONS), V.CELL), (0, 0, 0, 0))
    for i, direction in enumerate(V.DIRECTIONS):
        sheet.paste(draw_cell(direction, marker, collector), (i * V.CELL, 0))
    return sheet


def write_vehicle(out, marker=False):
    os.makedirs(out, exist_ok=True)
    draw_sheet(marker).save(os.path.join(out, SPEC["stem"] + ".png"))
    with open(os.path.join(out, SPEC["stem"] + ".yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(yaml_lines())
    print("wrote", os.path.join(out, SPEC["stem"] + ".png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marker", action="store_true", help="試験の印を重ねる（git に入れない）")
    ap.add_argument("--out", default=os.path.join(HERE, SPEC["dir"]), help="書き出す場所")
    args = ap.parse_args()
    write_vehicle(args.out, args.marker)


if __name__ == "__main__":
    main()
