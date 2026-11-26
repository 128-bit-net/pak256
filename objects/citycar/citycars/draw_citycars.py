"""街の車（本体の obj: citycar。街の中を勝手に走る自家用車）の絵と表を書き出す（docs/vehicles.md の「街の車」・#173）。
MIT License。絵は仮（箱を組んだ物）で、見た目は後から描き直す。

大きさは道路の車両と同じ決まり（pak128 の同じ種類の手本の 2 倍。docs/standards.md の 4 章）で、`target_px`（長さ・幅・高さ）に描く。
citycar の dat には `length` が無いので、描く長さは `target_px` の長さをそのまま単位に直す（端数のまま）。
描画位置は道路の車両と同じ（右側の車線・車体の前の端が基準点）。本体は左側通行のずれを道路の車両と同じに足す
（`private_car_t::get_screen_offset`）。8 方向を 256px のセルに横に並べたシート（2048x256）を車ごとに `<stem>.png` に、
表を `<stem>.yaml` に書く。車を足すときは `CARS` に 1 件足し、docs/vehicles.md の表に 1 行足す。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/citycar/citycars/draw_citycars.py
"""
import argparse
import importlib.util
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..", "..")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import vehicles as V  # noqa: E402

# 面の向き・色・枠の決まりは道路の車両の道具を読んで使う（道具を写して増やさない）
_spec = importlib.util.spec_from_file_location("draw_vehicles", os.path.join(ROOT, "objects", "vehicle", "road", "draw_vehicles.py"))
R = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(R)

TIRE = (24, 24, 28)
LAMP = (246, 232, 176)
TAIL = (176, 36, 30)

# 車の表。値（distributionweight・speed）と大きさの手本は pak128 の citycars（docs/vehicles.md の表）。
# cabin: 屋根のある客室の、車体の前からの位置の始め・終わり（0〜1）
CARS = [
    {
        "name": "pak256_citycar_small", "stem": "small", "title": "小型の街の車",
        "reference": "MS_30s_car_white", "ref_px": (24, 11, 8.5), "target_px": (48, 22, 17),
        "color": (70, 112, 82), "cabin": (0.30, 0.82),
        "distributionweight": 3, "speed": 50, "intro_year": 1930,
    },
    {
        "name": "pak256_citycar_sedan", "stem": "sedan", "title": "セダンの街の車",
        "reference": "ms_1932_dodge_green", "ref_px": (27, 11, 8), "target_px": (54, 22, 16),
        "color": (58, 78, 128), "cabin": (0.30, 0.74),
        "distributionweight": 3, "speed": 50, "intro_year": 1930,
    },
    {
        "name": "pak256_citycar_large", "stem": "large", "title": "大型の街の車",
        "reference": "MS_28_mercedes_brown", "ref_px": (32, 11, 7.5), "target_px": (64, 22, 16),
        "color": (112, 70, 52), "cabin": (0.40, 0.80),
        "distributionweight": 3, "speed": 50, "intro_year": 1930,
    },
]


def size_m(spec):
    """絵の車体の大きさ（長さ・幅・高さ）。長さは単位（端数のまま）、幅と高さは m。"""
    length_px, width_px, height_px = spec["target_px"]
    units = length_px / V.PX_PER_UNIT_SIDE
    width_m = width_px / V.PX_PER_UNIT_SIDE * V.M_PER_UNIT
    height_m = height_px / V.PX_PER_M_Z
    return units, width_m, height_m


def footprint(spec, direction):
    units, width_m, _ = size_m(spec)
    return V.footprint(direction, units, width_m, V.FRONT_UNITS)


def narrow(box, k):
    """四隅（前の右・前の左・後の左・後の右）の幅を、中心線に向けて k だけ（片側の割合）狭める。"""
    fr, fl, bl, br = box
    return (R.lerp(fr, fl, k), R.lerp(fl, fr, k), R.lerp(bl, br, k), R.lerp(br, bl, k))


def center(box):
    return (box[0][0] + box[2][0]) / 2, (box[0][1] + box[2][1]) / 2


def face_quad(c, a, b, t0, t1, z0, z1, color):
    c.quad(R.lerp(a, b, t0), R.lerp(a, b, t1), z0, z1, color)


def wheel(c, a, b, mid, half, radius):
    """側面 a-b の、位置 mid（0〜1）に車輪（下が地面の 8 角形）を描く。half は面の長さに対する半径の割合。"""
    pts = []
    for dt, dz in ((-1, 0.6), (-0.55, 1.3), (0, 1.5), (0.55, 1.3), (1, 0.6), (0.7, 0.0), (-0.7, 0.0)):
        p = R.lerp(a, b, mid + dt * half)
        pts.append(c.scr(p, dz * radius))
    c.d.polygon(pts, fill=TIRE)


def draw_cell(spec, direction):
    """1 方向のセル（256x256、RGBA）を描く。下の車体の箱（全長）の上に、客室の箱を重ねる。"""
    _, _, height = size_m(spec)
    color = spec["color"]
    body_top = height * 0.60
    floor = height * 0.14
    whole = footprint(spec, direction)
    c = R.Canvas()
    cx, cy = center(whole)
    for a, b, k, is_front in R.visible_faces(whole, cx, cy):
        c.quad(a, b, floor, body_top, R.shade(color, k))
        c.quad(a, b, 0.0, floor, R.shade(R.SKIRT, k))
        if is_front:
            face_quad(c, a, b, 0.10, 0.28, body_top * 0.55, body_top * 0.80, LAMP)
            face_quad(c, a, b, 0.72, 0.90, body_top * 0.55, body_top * 0.80, LAMP)
        elif a is whole[2]:  # 後ろの面
            face_quad(c, a, b, 0.10, 0.26, body_top * 0.55, body_top * 0.80, TAIL)
            face_quad(c, a, b, 0.74, 0.90, body_top * 0.55, body_top * 0.80, TAIL)
        else:  # 側面。車輪は前と後ろの寄り
            for mid in (0.18, 0.82):
                wheel(c, a, b, mid, 0.11, height * 0.17)
    c.top(whole, body_top, R.shade(color, 1.15))

    t0, t1 = spec["cabin"]
    cabin = narrow(R.part_corners(whole, t0, t1), 0.06)
    cx, cy = center(cabin)
    for a, b, k, is_front in R.visible_faces(cabin, cx, cy):
        c.quad(a, b, body_top, height, R.shade(color, k))
        if a is cabin[1] or a is cabin[3]:  # 側面は柱で 2 枚の窓に分ける
            face_quad(c, a, b, 0.10, 0.46, body_top + height * 0.05, height * 0.90, R.shade(R.GLASS, k))
            face_quad(c, a, b, 0.54, 0.90, body_top + height * 0.05, height * 0.90, R.shade(R.GLASS, k))
        else:
            face_quad(c, a, b, 0.12, 0.88, body_top + height * 0.05, height * 0.90, R.shade(R.GLASS, k))
    c.top(cabin, height, R.shade(color, 1.3))
    return c.finish()


def draw_sheet(spec):
    sheet = Image.new("RGBA", (V.CELL * len(V.DIRECTIONS), V.CELL), (0, 0, 0, 0))
    for i, direction in enumerate(V.DIRECTIONS):
        sheet.paste(draw_cell(spec, direction), (i * V.CELL, 0))
    return sheet


def yaml_lines(spec):
    """表（yaml）の全文。citycar に length・emptyimage は無い（makeobj の citycar_writer のキー）。"""
    stem = spec["stem"]
    lines = [
        f"# {spec['title']}（絵は仮）。この表と PNG は draw_citycars.py が書き出す。直すときはスクリプトを直して流し直す。",
        f"# 画面の大きさは pak128 の手本（{spec['reference']}）の 2 倍（docs/vehicles.md の「街の車」）。値は手本に合わせた。",
        "obj: citycar",
        f"name: {spec['name']}",
        "copyright: pak256.LongScale チーム",
        f"distributionweight: {spec['distributionweight']}",
        f"intro_year: {spec['intro_year']}",
        "intro_month: 1",
        f"speed: {spec['speed']}",
        "image:            # 向きごとの絵",
    ]
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: {stem}.0.{i}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=HERE, help="書き出す場所（既定はこのフォルダ）")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for spec in CARS:
        draw_sheet(spec).save(os.path.join(args.out, spec["stem"] + ".png"))
        with open(os.path.join(args.out, spec["stem"] + ".yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(yaml_lines(spec))
        print("wrote", os.path.join(args.out, spec["stem"] + ".png"))


if __name__ == "__main__":
    main()
