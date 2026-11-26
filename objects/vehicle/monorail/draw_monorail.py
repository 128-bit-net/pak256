"""モノレールの車両（跨座式）の絵と表を書き出す（docs/vehicles.md の「モノレールの車両」・#156）。MIT License。
絵は仮（箱を組んだ物）で、見た目は後から描き直す。

- 軌道は AMI の 256 版の跨座式の桁（`ami_monorail_straddle`。幅 0.085 タイル = 2.24m、上面は地面から 1.85m）。
  車体は桁をまたぐ形で、裾（スカート）を地面の高さまで下ろして桁の側面を隠す。車体の端の面は、桁の通る所を空ける。
- 長さと描画位置は tools/vehicles.py の線路の車両と同じ決まり（線路の中心に描く。`footprint(centered=True)`）。
  幅と高さは、実物の値に線路の車両の倍率（`RAIL_WIDTH_SCALE`・`RAIL_HEIGHT_SCALE`）を掛けて描く。
- 15m の車体は length=9 で、どの向きも 256px のセルに収まる。
- 8 方向を 256px のセルに横に並べたシート（2048x256）を `<名前>/<名前>.png` に、表を `<名前>.yaml` に書く。
- 面の向き・色の決まり・描く枠は、道路の車両の道具（objects/vehicle/road/draw_vehicles.py）を読んで使う。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/vehicle/monorail/draw_monorail.py
試験の印（車体の地面の枠と基準点）を重ねた絵を別の場所に書くとき（git に入れない）:
    python -X utf8 objects/vehicle/monorail/draw_monorail.py --marker --out build/monorail_marker
"""
import argparse
import importlib.util
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import vehicles as V  # noqa: E402

_DV = os.path.join(HERE, "..", "road", "draw_vehicles.py")
_spec = importlib.util.spec_from_file_location("draw_vehicles", _DV)
dv = importlib.util.module_from_spec(_spec)
sys.modules["draw_vehicles"] = dv
_spec.loader.exec_module(dv)

WIDTH_M = 3.0
HEIGHT_M = 5.0  # 裾の下端（地面）から屋根まで
FLOOR_M = 2.0  # 客室の床の下面（裾の上端）
# AMI の跨座式の桁（addons/ami の sheetlib/monorail_parts.py: 幅 0.85・上面 0.7。1 タイル = 10）。描いた寸法の m
BEAM_WIDTH_M = 0.85 / 10 * V.M_PER_TILE
BEAM_TOP_M = 0.7 / 10 * V.M_PER_TILE
SKIRT_COLOR = (96, 104, 116)
SIDE_WINDOWS = 5

VEHICLES = [
    {
        "name": "pak256_monorail", "dir": "monorail", "stem": "monorail", "title": "モノレール",
        "real_length_m": 15.0,
        "payload": 82, "power": 330, "speed": 100, "gear": 80, "weight": 18,
        "cost": 482000, "runningcost": 29, "intro_year": 1930,
        "body": (232, 232, 228), "band": (44, 96, 168),
    },
]


def length_of(spec):
    return V.length_units(spec["real_length_m"])


def footprint(spec, direction):
    return V.footprint(direction, length_of(spec), WIDTH_M * V.RAIL_WIDTH_SCALE, V.FRONT_UNITS, centered=True)


def notch():
    """端の面で桁の通る所。面の幅に対する割合 (始め, 終わり) と、高さ（車両の高さの倍率を掛ける前の m）。"""
    half = BEAM_WIDTH_M / (WIDTH_M * V.RAIL_WIDTH_SCALE) / 2
    return 0.5 - half, 0.5 + half, BEAM_TOP_M / V.RAIL_HEIGHT_SCALE


def draw_cell(spec, direction, marker):
    """1 方向のセル（256x256、RGBA）を描く。前後が同じ形なので、逆向きに走っても崩れない。"""
    whole = footprint(spec, direction)
    cx = (whole[0][0] + whole[2][0]) / 2
    cy = (whole[0][1] + whole[2][1]) / 2
    c = dv.Canvas(height_scale=V.RAIL_HEIGHT_SCALE)
    t0, t1, top = notch()
    for a, b, k, is_front in dv.visible_faces(whole, cx, cy):
        end = is_front or a is whole[2]
        if end:  # 端の面の裾は、桁の通る所を空ける
            skirt = dv.shade(SKIRT_COLOR, k)
            c.quad(a, dv.lerp(a, b, t0), 0.0, FLOOR_M, skirt)
            c.quad(dv.lerp(a, b, t1), b, 0.0, FLOOR_M, skirt)
            c.quad(dv.lerp(a, b, t0), dv.lerp(a, b, t1), top, FLOOR_M, skirt)
        else:
            c.quad(a, b, 0.0, FLOOR_M, dv.shade(SKIRT_COLOR, k))
        c.quad(a, b, FLOOR_M, HEIGHT_M, dv.shade(spec["body"], k))
        c.quad(a, b, FLOOR_M, FLOOR_M + 0.6, dv.shade(spec["band"], k))
        if end:  # 運転席の前面ガラス
            c.quad(dv.lerp(a, b, 0.1), dv.lerp(a, b, 0.9), 3.1, 4.5, dv.shade(dv.GLASS, k))
        else:
            for i in range(SIDE_WINDOWS):
                s0 = 0.08 + i * 0.84 / SIDE_WINDOWS
                c.quad(dv.lerp(a, b, s0), dv.lerp(a, b, s0 + 0.84 / SIDE_WINDOWS * 0.72), 3.2, 4.4, dv.shade(dv.GLASS, k))
    c.top(whole, HEIGHT_M, dv.shade(spec["body"], 1.05))
    if marker:
        fr, fl, bl, br = whole
        pts = [c.scr(p, 0.0) for p in whole]
        c.d.line(pts + [pts[0]], fill=dv.MARK, width=dv.SS)
        c.d.line([c.scr(fr, 0.0), c.scr(fl, 0.0)], fill=dv.MARK2, width=2 * dv.SS)
        ox, oy = c.scr((0.0, 0.0), 0.0)
        c.d.line([ox - 4 * dv.SS, oy, ox + 4 * dv.SS, oy], fill=dv.MARK, width=dv.SS)
        c.d.line([ox, oy - 2 * dv.SS, ox, oy + 2 * dv.SS], fill=dv.MARK, width=dv.SS)
    return c.finish()


def yaml_lines(spec):
    length = length_of(spec)
    stem = spec["stem"]
    lines = [
        f"# {spec['title']}（跨座式。絵は仮）。この表と PNG は draw_monorail.py が書き出す。直すときはスクリプトを直して流し直す。",
        f"# 実物 {spec['real_length_m']:g}m ÷ 1.65 = {spec['real_length_m'] / V.M_PER_UNIT:.2f} → length {length}（docs/vehicles.md）。",
        "# 値は pak128 のモノレールの車両の機能上の数値に合わせた（docs/vehicles.md の表）。",
        "obj: vehicle",
        f"name: {spec['name']}",
        "copyright: pak256.LongScale チーム",
        "waytype: monorail_track",
        "freight: Passagiere",
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
        lines.append(f"  {direction}: {stem}.0.{i}")
    return "\n".join(lines) + "\n"


def draw_sheet(spec, marker=False):
    sheet = Image.new("RGBA", (V.CELL * len(V.DIRECTIONS), V.CELL), (0, 0, 0, 0))
    for i, direction in enumerate(V.DIRECTIONS):
        sheet.paste(draw_cell(spec, direction, marker), (i * V.CELL, 0))
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
    args = ap.parse_args()
    for spec in VEHICLES:
        write_vehicle(spec, args.out or os.path.join(HERE, spec["dir"]), args.marker)


if __name__ == "__main__":
    main()
