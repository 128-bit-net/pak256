"""駅（線路）の絵と表を書き出す（docs/stations.md）。道路の停留所は AMI の物（ami_road_bus_stop・ami_road_truck_stop）に置き換えた（#72）。MIT License。絵は仮（箱を数式で描いた物）。

- 縮尺・タイルの座標は objects/city/town_buildings/draw_buildings.py と同じ（1 タイル = 26.4m、高さ 1m = 5.94px）。
- 駅は 1x1 タイル。線路の向きごとに 8 通り（本体の決まり。0 NS 中、1 EW 中、2 NS 南端、3 EW 東端、4 NS 北端、5 EW 西端、
  6 NS 両端、7 EW 両端）。NS は v の向き（左下）、EW は u の向き（右下）。南は +v、東は +u。
- 絵は 後ろ（車の下）と 前（車の上）の 2 枚に分ける。シートは 8 列（向き）× 3 行（0 行 = 後ろ、1 行 = 前、2 行 = 道具の絵）。
  セルの名前は <名前>.<行>.<列>。道具の絵（icon）は 2 行 0 列。
- 線路そのものは描かない（線路は AMI が持つ）。線路はタイルの中央を通ると見て、その近い側（見える側）にホームを置く。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/station/rail_stops/draw_stops.py
"""
import importlib.util
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
_B = os.path.join(os.path.dirname(os.path.dirname(HERE)), "city", "town_buildings", "draw_buildings.py")
_spec = importlib.util.spec_from_file_location("draw_buildings", _B)
db = importlib.util.module_from_spec(_spec)
sys.modules["draw_buildings"] = db
_spec.loader.exec_module(db)

CELL = db.CELL
CLEAR = db.CLEAR
LAYOUTS = 8  # 向きの数
# 向きごとの (線路の軸, 南（+v）または東（+u）が連なりの端か, 北（-v）または西（-u）が連なりの端か)
LAYOUT = [
    ("NS", False, False), ("EW", False, False),
    ("NS", True, False), ("EW", True, False),
    ("NS", False, True), ("EW", False, True),
    ("NS", True, True), ("EW", True, True),
]

CONCRETE = (172, 170, 164)
KERB = (190, 188, 182)
POST = (88, 92, 98)
SIGN = (232, 200, 60)

def box_a_c(cv, axis, a0, a1, c0, c1, z0, z1, wall, roof):
    """線路の軸 a（along）と、軸に直交する c（across）で書いた箱を、向きに合わせて描く。"""
    if axis == "NS":  # a = v, c = u
        db.flat_box(cv, c0, c1, a0, a1, z0, z1, wall, roof)
    else:  # a = u, c = v
        db.flat_box(cv, a0, a1, c0, c1, z0, z1, wall, roof)


def platform(cv, axis, south_end, north_end, z, wall, roof, near):
    """近い側の帯。連なりの端では、端の手前で止め、帯の上だけに小さな縁を置く（線路はふさがない）。"""
    a0 = 0.05 if north_end else 0.0
    a1 = 0.95 if south_end else 1.0
    box_a_c(cv, axis, a0, a1, near[0], near[1], 0, z, wall, roof)
    if north_end:
        box_a_c(cv, axis, 0.0, 0.05, near[0], near[1], 0, z + 0.2, KERB, KERB)
    if south_end:
        box_a_c(cv, axis, 0.95, 1.0, near[0], near[1], 0, z + 0.2, KERB, KERB)


# ---- 駅（線路）: 線路の脇の高さ 0.9m のホームに、屋根つきの待合 ----
# 線路はタイルの中央（c = 0.43〜0.57。道床の幅 約 3.4m）を通ると見て、近い側にホームを置く。
RAIL_NEAR = (0.66, 0.98)
ROOF_STATION = (60, 96, 140)
PLATFORM_Z = 0.9


def station_back(cv, axis, s, n):
    platform(cv, axis, s, n, PLATFORM_Z, (176, 174, 168), CONCRETE, RAIL_NEAR)  # ホーム（高さ 0.9m）


def station_front(cv, axis, s, n):
    c0, c1 = 0.78, 0.94
    z0, z1 = PLATFORM_Z, PLATFORM_Z + 2.7
    for a in (0.2, 0.8):  # 柱 4 本
        for c in (c0, c1 - 0.02):
            box_a_c(cv, axis, a - 0.01, a + 0.01, c, c + 0.02, z0, z1, POST, POST)
    box_a_c(cv, axis, 0.12, 0.88, c0 - 0.02, c1 + 0.02, z1, z1 + 0.3, ROOF_STATION, ROOF_STATION)  # 屋根
    box_a_c(cv, axis, 0.40, 0.60, c1 - 0.03, c1, z0, z0 + 0.5, (140, 100, 70), (150, 110, 80))  # ベンチ
    box_a_c(cv, axis, 0.04, 0.045, c1 - 0.02, c1 - 0.015, z0, z0 + 3.2, POST, SIGN)  # 駅名の標識


STOPS = {
    "train_station": dict(
        name="pak256_train_station", back=station_back, front=station_front,
        dat={"waytype": "track", "enables_pax": 1, "level": 2, "intro_year": 1900},
        note="駅（旅客）。線路の脇の高さ 0.9m のホームに、屋根つきの待合",
    ),
}


def cell(draw_fn, layout):
    axis, s, n = LAYOUT[layout]
    cv = db.Canvas()
    draw_fn(cv, axis, s, n)
    return cv.finish()


def sheet(stop):
    """8 列 × 3 行のシート。0 行 = 後ろ、1 行 = 前、2 行 = 道具の絵（2 行 0 列）。"""
    out = Image.new("RGB", (CELL * LAYOUTS, CELL * 3), CLEAR)
    for i in range(LAYOUTS):
        out.paste(cell(stop["back"], i), (i * CELL, 0))
        out.paste(cell(stop["front"], i), (i * CELL, CELL))
    # 道具の絵: 向き 0（NS 中）の後ろと前を重ねる
    art = Image.new("RGB", (CELL, CELL), CLEAR)
    for row in (0, 1):
        part = out.crop((0, row * CELL, CELL, row * CELL + CELL))
        art.paste(part, (0, 0), _mask(part))
    out.paste(tool_icon(art, ICON_BG), (0, CELL * 2))
    return out


ICON_SIZE = 192  # 本体はアイコンを表示の高さ（48）に収まる倍率で縮める。192 なら 1/4 でちょうど 48 になる
ICON_BG = (84, 104, 134)


def tool_icon(art, bg):
    """道具の絵: 地の色の角丸の四角（192px）に、駅の絵を収めて置く。

    絵に透明な所があると、本体は絵の見える範囲だけを縮めて置くので、アイコンの枠がずれて灰色の空きに見える（#71）。
    四角を左上の角（0, 0）から置き、見える範囲の始まりを 0 にする。四角の外と角は透明色。
    """
    box = Image.new("RGB", (CELL, CELL), CLEAR)
    mask = Image.new("L", (ICON_SIZE, ICON_SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, ICON_SIZE - 1, ICON_SIZE - 1), 24, fill=255)
    dark = db.safe(tuple(int(v * 0.65) for v in bg))
    plate = Image.new("RGB", (ICON_SIZE, ICON_SIZE), db.safe(bg))
    ImageDraw.Draw(plate).rounded_rectangle((0, 0, ICON_SIZE - 1, ICON_SIZE - 1), 24, outline=dark, width=4)
    box.paste(plate, (0, 0), mask)
    bbox = _mask(art).getbbox()
    if bbox:
        part = art.crop(bbox)
        k = min(150 / part.width, 150 / part.height)
        size = (max(1, round(part.width * k)), max(1, round(part.height * k)))
        alpha = _mask(part).resize(size, Image.LANCZOS).point(lambda v: 255 if v >= 128 else 0)
        small = part.resize(size, Image.LANCZOS)
        px = small.load()
        for y in range(size[1]):
            for x in range(size[0]):
                px[x, y] = db.safe(px[x, y])
        box.paste(small, ((ICON_SIZE - size[0]) // 2, (ICON_SIZE - size[1]) // 2), alpha)
    return box


def _mask(im):
    """透明色以外を不透明にするマスク。"""
    px = im.load()
    m = Image.new("L", im.size, 0)
    mp = m.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if px[x, y] != CLEAR:
                mp[x, y] = 255
    return m


def fmt(v):
    return str(v)


def table(key, o):
    lines = [
        "# 駅（絵は仮。AMI の物が出たら置き換えて消す。docs/stations.md）。この表と PNG は draw_stops.py が書き出す。",
        "# 1 タイル = 26.4m の縮尺（docs/buildings.md）。",
        "obj: building",
        f"name: {o['name']}",
        "copyright: pak256.LongScale チーム",
        f"# {o['note']}",
        "type: stop",
    ]
    for k, v in o["dat"].items():
        lines.append(f"{k}: {fmt(v)}")
    lines += [
        "noinfo: 1",
        "allow_underground: 2",
        f"dims: 1,1,{LAYOUTS}",
        f"icon: \"> {key}.2.0\"",
        "backimage:        # backimage[向き][y][x][高さ][コマ]。向きの順は draw_stops.py の先頭に書いた",
    ]
    for i in range(LAYOUTS):
        lines.append(f"  {i}: {{0: {{0: {{0: {{0: {key}.0.{i}}}}}}}}}")
    lines.append("frontimage:")
    for i in range(LAYOUTS):
        lines.append(f"  {i}: {{0: {{0: {{0: {{0: {key}.1.{i}}}}}}}}}")
    return "\n".join(lines) + "\n"


def main():
    for key, o in STOPS.items():
        sheet(o).save(os.path.join(HERE, f"{key}.png"))
        with open(os.path.join(HERE, f"{key}.yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(table(key, o))


if __name__ == "__main__":
    main()
