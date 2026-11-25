"""道路の車庫の絵と表を書き出す（docs/stations.md の「仮の道路の車庫」）。MIT License。絵は仮（箱と屋根を数式で描いた物）。

- 縮尺・タイルの座標は objects/city/town_buildings/draw_buildings.py と同じ（1 タイル = 26.4m、高さ 1m = 5.94px）。
- 車庫は 1x1 タイル、向きは 4 通り（本体の決まり。`dims` の 3 つめが 4）。向きごとに、戸（車の出入り口）の面を変える。
  戸の面は LAYOUT_SIDE の順（0〜3）。南西・南東の面は戸が見え、北東・北西の面は隠れるので、そちらは地面の舗装（後ろの絵）だけで入口を示す。
- シートは 4 列（向き）× 3 行（0 行 = 後ろ（舗装）、1 行 = 前（建物）、2 行 = 道具の絵）。セルの名前は <名前>.<行>.<列>。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/depot/road_depot/draw_depot.py
"""
import importlib.util
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
_B = os.path.join(os.path.dirname(os.path.dirname(HERE)), "city", "town_buildings", "draw_buildings.py")
_spec = importlib.util.spec_from_file_location("draw_buildings", _B)
db = importlib.util.module_from_spec(_spec)
sys.modules["draw_buildings"] = db
_spec.loader.exec_module(db)

CELL = db.CELL
CLEAR = db.CLEAR
LAYOUTS = 4
# 向き 0〜3 の、戸の面（道路につながる側）。ゲームで置いて、道路の向きと合う順を確かめて決めた（docs/stations.md）。
LAYOUT_SIDE = ["sw", "se", "ne", "nw"]

WALL = (176, 170, 156)
ROOF_A = (118, 84, 70)
ROOF_B = (96, 68, 58)
DOOR = (62, 66, 72)
ASPHALT = (92, 94, 98)
SIGN = (232, 200, 60)

EDGE = 0.12  # 建物の足跡の余白（タイルの端から）
DOOR_W = 7.0  # 戸の幅（m）
DOOR_H = 4.0  # 戸の高さ（m）
WALL_H = 4.6  # 壁の高さ（m）
RIDGE_H = 2.0  # 棟の高さ（壁の上から、m）


def back(cv, side):
    """後ろの絵: 戸の側のタイルの端から戸までの舗装。"""
    lo, hi = 0.5 - 0.2, 0.5 + 0.2
    e = EDGE + 0.04  # 建物の足元まで届かせる
    if side == "sw":
        db.flat_box(cv, lo, hi, 1 - e, 1.0, 0, 0.05, ASPHALT, ASPHALT)
    elif side == "se":
        db.flat_box(cv, 1 - e, 1.0, lo, hi, 0, 0.05, ASPHALT, ASPHALT)
    elif side == "ne":
        db.flat_box(cv, lo, hi, 0.0, e, 0, 0.05, ASPHALT, ASPHALT)
    else:
        db.flat_box(cv, 0.0, e, lo, hi, 0, 0.05, ASPHALT, ASPHALT)


def front(cv, side):
    """前の絵: 切妻の車庫。戸のある面を切妻の妻側にする。"""
    u0, u1, v0, v1 = EDGE, 1 - EDGE, EDGE, 1 - EDGE
    ridge = "v" if side in ("sw", "ne") else "u"
    db.gable_box(cv, u0, u1, v0, v1, 0, WALL_H, RIDGE_H, ridge, WALL, ROOF_A, ROOF_B)
    w = db.m2t(DOOR_W) / 2
    if side == "sw":
        db.face_sw(cv, 0.5 - w, 0.5 + w, v1 + 0.002, 0, DOOR_H, DOOR)
        db.face_sw(cv, 0.5 - 0.02, 0.5 + 0.02, v1 + 0.003, WALL_H - 0.6, WALL_H + 0.6, SIGN)
    elif side == "se":
        db.face_se(cv, u1 + 0.002, 0.5 - w, 0.5 + w, 0, DOOR_H, DOOR)
        db.face_se(cv, u1 + 0.003, 0.5 - 0.02, 0.5 + 0.02, WALL_H - 0.6, WALL_H + 0.6, SIGN)


def cell(draw_fn, layout):
    cv = db.Canvas()
    draw_fn(cv, LAYOUT_SIDE[layout])
    return cv.finish()


def _mask(im):
    px = im.load()
    m = Image.new("L", im.size, 0)
    mp = m.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if px[x, y] != CLEAR:
                mp[x, y] = 255
    return m


def sheet():
    out = Image.new("RGB", (CELL * LAYOUTS, CELL * 3), CLEAR)
    for i in range(LAYOUTS):
        out.paste(cell(back, i), (i * CELL, 0))
        out.paste(cell(front, i), (i * CELL, CELL))
    icon = Image.new("RGB", (CELL, CELL), CLEAR)
    for row in (0, 1):
        part = out.crop((0, row * CELL, CELL, row * CELL + CELL))
        icon.paste(part, (0, 0), _mask(part))
    out.paste(icon, (0, CELL * 2))
    return out


def table():
    lines = [
        "# 道路の車庫（絵は仮。AMI の物が出たら置き換えて消す。docs/stations.md）。この表と PNG は draw_depot.py が書き出す。",
        "# 1 タイル = 26.4m の縮尺（docs/buildings.md）。",
        "obj: building",
        "name: pak256_road_depot",
        "copyright: pak256.LongScale チーム",
        "type: depot",
        "waytype: road",
        "intro_year: 1900",
        "noinfo: 1",
        f"dims: 1,1,{LAYOUTS}",
        "icon: \"> road_depot.2.0\"",
        "backimage:        # backimage[向き][y][x][高さ][コマ]。向きの順は draw_depot.py の LAYOUT_SIDE",
    ]
    for i in range(LAYOUTS):
        lines.append(f"  {i}: {{0: {{0: {{0: {{0: road_depot.0.{i}}}}}}}}}")
    lines.append("frontimage:")
    for i in range(LAYOUTS):
        lines.append(f"  {i}: {{0: {{0: {{0: {{0: road_depot.1.{i}}}}}}}}}")
    return "\n".join(lines) + "\n"


def main():
    sheet().save(os.path.join(HERE, "road_depot.png"))
    with open(os.path.join(HERE, "road_depot.yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(table())


if __name__ == "__main__":
    main()
