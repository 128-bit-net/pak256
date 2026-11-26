"""港（桟橋・岸壁・運河の船着き場）の絵と表を書き出す（docs/stations.md の「港」・#154）。MIT License。絵は仮（箱を数式で描いた物）。

- 縮尺・タイルの座標は objects/city/town_buildings/draw_buildings.py と同じ（1 タイル = 26.4m、高さ 1m = 5.94px）。
- 向き（桟橋・岸壁は 4 通り）は水のある側。本体の決まりで 0 = 南（+v。画面の左下）、1 = 東（+u。右下）、2 = 北（-v。右上）、
  3 = 西（-u。左上）。
- 桟橋（type=habour）は水に面した 1 段の坂に建てる。水の反対側の辺が 1 段（SLOPE_M）高い。坂の上の端から板の斜路で下り、
  水の側は杭の上の平らな板にする。
- 岸壁（type=dock）は水に面した平らな土地に建てる。コンクリートの敷き面と、水の側の係船柱、陸の側の上屋。
- 運河の船着き場（type=stop・waytype=water）は運河の道の上に建てる。向きは道路の停留所と同じ 8 通り。運河の両脇に板を張る。
- シートは 向きの数の列 × 3 行（0 行 = 後ろ、1 行 = 前、2 行 = 道具の絵）。セルの名前は <名前>.<行>.<列>。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/station/ports/draw_ports.py
"""
import importlib.util
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


stops = _load("road_draw_stops_for_ports", os.path.join(HERE, "..", "road_stops", "draw_stops.py"))
db = stops.db
CELL, CLEAR = db.CELL, db.CLEAR

SLOPE_M = 32 / db.PX_Z  # 地形の 1 段（32px）の高さ（m）
WATER_DIRS = ("s", "e", "n", "w")  # 向き 0〜3 の水のある側
TIMBER = (150, 112, 76)
TIMBER_LIGHT = (176, 138, 98)
PILE = (88, 66, 48)
CONCRETE = (172, 170, 164)
CONCRETE_DARK = (128, 126, 122)
BOLLARD = (52, 54, 60)
SHED = (190, 176, 150)
SHED_ROOF = (112, 76, 64)
POST, SIGN = stops.POST, stops.SIGN


def to_uv(water, s, t):
    """水の向きに合わせた座標。s は陸の端 0 → 水の端 1、t は岸に沿った座標 0〜1。"""
    if water == "s":
        return t, s
    if water == "n":
        return t, 1 - s
    if water == "e":
        return s, t
    return 1 - s, t


def poly(cv, water, pts, rgb):
    """pts は (s, t, 高さ m) の並び。"""
    cv.poly([db.P(*to_uv(water, s, t), z) for s, t, z in pts], rgb)


def box(cv, water, s0, s1, t0, t1, z0, z1, wall, roof):
    u0, v0 = to_uv(water, s0, t0)
    u1, v1 = to_uv(water, s1, t1)
    db.flat_box(cv, min(u0, u1), max(u0, u1), min(v0, v1), max(v0, v1), z0, z1, wall, roof)


def boxes_far_to_near(cv, water, items):
    """(s0, s1, t0, t1, z0, z1, 壁, 屋根) を、画面の奥の物から描く。"""
    def depth(item):
        u, v = to_uv(water, (item[0] + item[1]) / 2, (item[2] + item[3]) / 2)
        return u + v

    for item in sorted(items, key=depth):
        box(cv, water, *item)


# ---- 桟橋（坂の岸）----

PIER_DECK = 2.4  # 平らな板の高さ（m。水面から）
PIER_RAMP_END = 0.55  # 斜路の下の端（s）


def pier_back(cv, water):
    t0, t1 = 0.22, 0.78
    # 水の側の板の下の杭
    piles = [(s - 0.02, s + 0.02, t - 0.02, t + 0.02, 0.0, PIER_DECK - 0.4, PILE, PILE)
             for s in (0.70, 0.96) for t in (t0 + 0.03, t1 - 0.03)]
    boxes_far_to_near(cv, water, piles)
    # 坂の上の端から下る斜路
    poly(cv, water, [(0.0, t0, SLOPE_M + 0.1), (0.0, t1, SLOPE_M + 0.1),
                     (PIER_RAMP_END, t1, PIER_DECK), (PIER_RAMP_END, t0, PIER_DECK)], TIMBER)
    # 斜路の横板
    for i in range(1, 8):
        s = PIER_RAMP_END * i / 8
        z = SLOPE_M + 0.1 + (PIER_DECK - SLOPE_M - 0.1) * i / 8
        poly(cv, water, [(s, t0, z), (s, t1, z), (s + 0.008, t1, z), (s + 0.008, t0, z)], PILE)
    # 水の側の平らな板
    box(cv, water, PIER_RAMP_END, 1.0, t0, t1, PIER_DECK - 0.4, PIER_DECK, PILE, TIMBER_LIGHT)
    # 待合の小屋と標識
    items = [(0.60, 0.74, t0 + 0.04, t0 + 0.20, PIER_DECK, PIER_DECK + 2.6, SHED, SHED_ROOF),
             (0.93, 0.945, t1 - 0.06, t1 - 0.045, PIER_DECK, PIER_DECK + 3.0, POST, SIGN)]
    items += [(0.95, 0.99, t - 0.015, t + 0.015, PIER_DECK, PIER_DECK + 0.6, BOLLARD, BOLLARD)
              for t in (t0 + 0.12, t1 - 0.14)]
    boxes_far_to_near(cv, water, items)


# ---- 岸壁（平らな岸）----

QUAY_Z = 1.0


def quay_back(cv, water):
    # 敷き面（タイル全体）。水の側の端は暗い帯
    box(cv, water, 0.0, 1.0, 0.0, 1.0, 0.0, QUAY_Z, CONCRETE_DARK, CONCRETE)
    poly(cv, water, [(0.90, 0.0, QUAY_Z), (0.90, 1.0, QUAY_Z), (1.0, 1.0, QUAY_Z), (1.0, 0.0, QUAY_Z)], CONCRETE_DARK)
    items = [(0.08, 0.38, 0.12, 0.88, QUAY_Z, QUAY_Z + 4.0, SHED, SHED_ROOF)]  # 上屋（陸の側）
    items += [(0.92, 0.96, t - 0.02, t + 0.02, QUAY_Z, QUAY_Z + 0.7, BOLLARD, BOLLARD) for t in (0.12, 0.38, 0.62, 0.88)]
    items += [(0.52, 0.64, 0.20, 0.34, QUAY_Z, QUAY_Z + 1.2, (170, 126, 82), (184, 140, 94)),  # 荷
              (0.56, 0.70, 0.62, 0.74, QUAY_Z, QUAY_Z + 1.0, (170, 126, 82), (184, 140, 94)),
              (0.80, 0.815, 0.90, 0.915, QUAY_Z, QUAY_Z + 4.0, POST, SIGN)]
    boxes_far_to_near(cv, water, items)


# ---- 運河の船着き場（運河の道の上）----

WHARF_FAR = (0.0, 0.14)
WHARF_NEAR = (0.86, 1.0)
WHARF_Z = 0.5


def wharf_back(cv, axis, south_end, north_end):
    stops.platform(cv, axis, south_end, north_end, WHARF_Z, PILE, TIMBER_LIGHT, WHARF_FAR)
    stops.box_a_c(cv, axis, 0.36, 0.60, 0.015, 0.11, WHARF_Z, WHARF_Z + 2.4, SHED, SHED_ROOF)  # 待合の小屋
    stops.box_a_c(cv, axis, 0.14, 0.145, 0.10, 0.115, WHARF_Z, WHARF_Z + 3.0, POST, SIGN)
    for a in (0.24, 0.76):
        stops.box_a_c(cv, axis, a - 0.012, a + 0.012, 0.115, 0.135, WHARF_Z, WHARF_Z + 0.5, BOLLARD, BOLLARD)


def wharf_front(cv, axis, south_end, north_end):
    stops.platform(cv, axis, south_end, north_end, WHARF_Z, PILE, TIMBER_LIGHT, WHARF_NEAR, kerb_up=0.05)


PORTS = {
    "pier": dict(
        name="pak256_pier", type="habour", layouts=4, back=pier_back, front=None,
        note="桟橋。水に面した 1 段の坂に建てる。坂の上から下る斜路と、杭の上の平らな板・待合",
    ),
    "quay": dict(
        name="pak256_quay", type="dock", layouts=4, back=quay_back, front=None,
        note="岸壁。水に面した平らな土地に建てる。高さ 1m の敷き面と上屋・係船柱",
    ),
    "canal_wharf": dict(
        name="pak256_canal_wharf", type="stop", layouts=8, back=wharf_back, front=wharf_front,
        note="運河の船着き場。運河の道の上に建てる。運河の両脇の板と待合の小屋",
    ),
}


def cell(port, key, layout):
    fn = port[key]
    cv = db.Canvas()
    if fn is not None:
        if port["type"] == "stop":
            fn(cv, *stops.LAYOUT[layout])
        else:
            fn(cv, WATER_DIRS[layout])
    return cv.finish()


def sheet(port):
    n = port["layouts"]
    out = Image.new("RGB", (CELL * n, CELL * 3), CLEAR)
    for i in range(n):
        out.paste(cell(port, "back", i), (i * CELL, 0))
        out.paste(cell(port, "front", i), (i * CELL, CELL))
    out.paste(stops.tool_icon(out.crop((0, 0, CELL, CELL)), stops.ICON_BG), (0, CELL * 2))
    return out


def table(key, o):
    lines = [
        "# 港（絵は仮。docs/stations.md の「港」）。この表と PNG は draw_ports.py が書き出す。",
        "# 1 タイル = 26.4m の縮尺（docs/buildings.md）。",
        "obj: building",
        f"name: {o['name']}",
        "copyright: pak256.LongScale チーム",
        f"# {o['note']}",
        f"type: {o['type']}",
    ]
    if o["type"] == "stop":
        lines.append("waytype: water")
    lines += [
        "enables_pax: 1",
        "enables_post: 1",
        "enables_ware: 1",
        "level: 4",
        "intro_year: 1900",
        "noinfo: 1",
        f"dims: 1,1,{o['layouts']}",
        f"icon: \"> {key}.2.0\"",
        "backimage:        # backimage[向き][y][x][高さ][コマ]",
    ]
    for i in range(o["layouts"]):
        lines.append(f"  {i}: {{0: {{0: {{0: {{0: {key}.0.{i}}}}}}}}}")
    if o["front"] is not None:
        lines.append("frontimage:")
        for i in range(o["layouts"]):
            lines.append(f"  {i}: {{0: {{0: {{0: {{0: {key}.1.{i}}}}}}}}}")
    return "\n".join(lines) + "\n"


def main():
    for key, o in PORTS.items():
        sheet(o).save(os.path.join(HERE, f"{key}.png"))
        with open(os.path.join(HERE, f"{key}.yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(table(key, o))
        print("wrote", o["name"])


if __name__ == "__main__":
    main()
