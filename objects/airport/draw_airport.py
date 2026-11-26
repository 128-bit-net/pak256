"""空港の物（滑走路・誘導路・駐機場の駅・格納庫）の絵と表を書き出す（docs/airport.md・#155）。MIT License。
絵は仮（色を塗った地面と箱）で、見た目は後から描き直す。他の pak の絵は使わない。

- 縮尺・タイルの座標は objects/city/town_buildings/draw_buildings.py と同じ（1 タイル = 26.4m、高さ 1m = 5.94px）。
  u は右下（東）、v は左下（南）。北の辺は v = 0（右上）、西の辺は u = 0（左上）。
- 滑走路・誘導路の絵は、画素の中心がタイルの中（0 <= u < 1, 0 <= v < 1）にある画素だけを塗る。隣のタイルと隙間も重なりも出ない。
- 駅・格納庫は誘導路の行き止まりに置く（向き 4 通り。本体の並びは 0 = 南につながる、1 = 東、2 = 北、3 = 西）。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/airport/draw_airport.py
"""
import importlib.util
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OBJECTS = os.path.dirname(HERE)


def _load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(OBJECTS, *path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


db = _load("draw_buildings", "city", "town_buildings", "draw_buildings.py")
rail = _load("draw_rail_stops", "station", "rail_stops", "draw_stops.py")  # 道具の絵の作り方（tool_icon）

CELL = db.CELL
CLEAR = db.CLEAR
COPYRIGHT = "pak256.LongScale チーム"
ICON_BG = (96, 112, 128)
WAY_ICON_BG = (92, 150, 80)  # 道の道具の絵の地は草の色（灰色の舗装が見分けられるように）

# ---- 滑走路・誘導路 ----

# ribi の名前（本体の makeobj の並び。番号は 北 1・東 2・南 4・西 8 の和）
RIBI = ["-", "n", "e", "ne", "s", "ns", "se", "nse", "w", "nw", "ew", "new", "sw", "nsw", "sew", "nsew"]
N, E, S, W = 1, 2, 4, 8

ASPHALT = (96, 96, 100)
ASPHALT_TAXI = (132, 130, 126)
EDGE_LINE = (226, 226, 222)
YELLOW = (232, 196, 48)

WAYS = {
    # 値は pak128 の初期の滑走路・誘導路（old_runway・old_taxiway）の機能上の数値（docs/airport.md）
    "runway": dict(
        name="pak256_runway", half=0.36, surface=ASPHALT,
        dat={"system_type": 1, "cost": 175000, "maintenance": 3000, "topspeed": 100, "max_weight": 20, "intro_year": 1900},
        note="滑走路（system_type=1）。離着陸する道",
    ),
    "taxiway": dict(
        name="pak256_taxiway", half=0.20, surface=ASPHALT_TAXI,
        dat={"system_type": 0, "cost": 30000, "maintenance": 500, "topspeed": 30, "max_weight": 20, "intro_year": 1900},
        note="誘導路（system_type=0）。地上を走る道。駅と格納庫は誘導路に置く",
    ),
}


def _branch(sides, u, v):
    """滑走路の脇へ出る枝（誘導路の幅）。sides はつながる側のビット。"""
    half = WAYS["taxiway"]["half"]
    for bit, along, across, near in ((N, v, u, v < 0.5), (S, v, u, v >= 0.5), (W, u, v, u < 0.5), (E, u, v, u >= 0.5)):
        if sides & bit and near and abs(across - 0.5) <= half:
            return YELLOW if abs(across - 0.5) < 0.016 else ASPHALT_TAXI
    return None


def way_colour(key, ribi, u, v):
    """タイルの座標 (u, v) の色。道でなければ None。"""
    half = WAYS[key]["half"]
    lo, hi = 0.5 - half, 0.5 + half
    runway = key == "runway"
    in_u = lo <= u <= hi
    in_v = lo <= v <= hi
    end = runway and ribi in (N, E, S, W)  # 滑走路の端: つながる側の反対へ延ばし、端の印を描く
    if runway:
        # まっすぐ抜ける滑走路に脇からつながる枝（T 字・十字）は、誘導路の幅と色で描く
        for axis in (N | S, E | W):
            if ribi & axis == axis and ribi != axis:
                main = way_colour(key, axis, u, v)
                return main if main is not None else _branch(ribi & ~axis, u, v)

    arms = []  # 塗る長方形ごとの (軸, 進んだ位置, 軸に直交する位置)。位置はつながる辺からタイルの中へ
    if end:
        d = {N: v, S: 1 - v, W: u, E: 1 - u}[ribi]  # つながる辺からの距離
        across = u if ribi in (N, S) else v
        if d <= 0.94 and lo <= across <= hi:
            arms.append(("end", d, across))
    else:
        if ribi & N and in_u and v < 0.5:
            arms.append(("v", v, u))
        if ribi & S and in_u and v >= 0.5:
            arms.append(("v", v, u))
        if ribi & W and in_v and u < 0.5:
            arms.append(("u", u, v))
        if ribi & E and in_v and u >= 0.5:
            arms.append(("u", u, v))
    centre = in_u and in_v
    if not arms and not centre:
        return None
    if end and not arms:
        return None

    base = WAYS[key]["surface"]
    if end:
        _, d, across = arms[0]
        side = min(across - lo, hi - across)
        if 0.70 <= d <= 0.86 and side > 0.06 and int((across - lo) / 0.08) % 2 == 0:
            return EDGE_LINE  # 滑走路の端の縦じま
        if 0.015 <= side < 0.045:
            return EDGE_LINE
        if abs(across - 0.5) < 0.018 and d < 0.62 and (d * 4) % 1 < 0.6:
            return EDGE_LINE  # 中心の破線
        return base

    if runway:
        # 中心の破線（つながる向きだけ）と、両側の縁の線
        for axis, pos, across in arms:
            if abs(across - 0.5) < 0.018 and (pos * 4) % 1 < 0.6:
                return EDGE_LINE
        if ribi in (N | S, E | W):
            across = u if ribi == (N | S) else v
            if 0.015 <= min(across - lo, hi - across) < 0.045:
                return EDGE_LINE
    else:
        for axis, pos, across in arms:
            if abs(across - 0.5) < 0.016:
                return YELLOW  # 誘導の黄色い線
        if centre and abs(u - 0.5) < 0.03 and abs(v - 0.5) < 0.03 and ribi:
            return YELLOW
    return base


def ground_cell(colour):
    """colour(u, v) -> 色か None を、画素の中心で調べて地面の菱形に塗る。"""
    img = Image.new("RGB", (CELL, CELL), CLEAR)
    px = img.load()
    for y in range(128, 256):
        for x in range(CELL):
            a, b = (x + 0.5 - 128) / 128, (y + 0.5 - 128) / 64  # a = u - v, b = u + v
            u, v = (b + a) / 2, (b - a) / 2
            if 0 <= u < 1 and 0 <= v < 1:
                c = colour(u, v)
                if c is not None:
                    px[x, y] = db.safe(c)
    return img


def way_sheet(key):
    """4 列 × 5 行。0〜3 行は ribi の番号順（行 = 番号 // 4、列 = 番号 % 4）、4 行は 道具の絵（4.0）とカーソル（4.1）。"""
    out = Image.new("RGB", (CELL * 4, CELL * 5), CLEAR)
    for ribi in range(16):
        out.paste(ground_cell(lambda u, v: way_colour(key, ribi, u, v)), ((ribi % 4) * CELL, (ribi // 4) * CELL))
    straight = ground_cell(lambda u, v: way_colour(key, N | S, u, v))
    out.paste(rail.tool_icon(straight, WAY_ICON_BG), (0, CELL * 4))
    out.paste(straight, (CELL, CELL * 4))
    return out


def way_table(key):
    o = WAYS[key]
    lines = [
        "# 空港の道（絵は仮）。この表と PNG は ../draw_airport.py が書き出す（docs/airport.md）。",
        f"# {o['note']}",
        "obj: way",
        f"name: {o['name']}",
        f"copyright: {COPYRIGHT}",
        "waytype: air",
    ]
    lines += [f"{k}: {v}" for k, v in o["dat"].items()]
    lines.append("image:            # つながる向き（n 北・e 東・s 南・w 西）ごとの絵")
    for i, r in enumerate(RIBI):
        lines.append(f"  \"{r}\": {key}.{i // 4}.{i % 4}")
    lines.append(f"icon: \"> {key}.4.0\"")
    lines.append(f"cursor: {key}.4.1")
    return "\n".join(lines) + "\n"


# ---- 駅（駐機場）と格納庫 ----

# 向きごとの、誘導路がつながる側
SIDES = ["s", "e", "n", "w"]
# 止まった飛行機の機首（車両の基準点）の位置。つながる辺からの距離（タイル）。車両は出口の辺の約 1.6 単位手前で止まる（docs/vehicles.md）
STOP_AT = 0.90
APRON = (162, 160, 154)
WALL = (190, 184, 170)
ROOF = (60, 96, 140)
GLASS = (70, 88, 110)
HANGAR_WALL = (150, 156, 166)
HANGAR_ROOF = (142, 76, 62)
DARK = (46, 46, 52)


def from_open(side, along, across):
    """つながる辺からの距離 along と、それに直交する位置 across を (u, v) にする。"""
    return {"s": (across, 1 - along), "n": (across, along), "e": (1 - along, across), "w": (along, across)}[side]


def box(cv, side, a0, a1, c0, c1, z0, z1, wall, roof):
    p, q = from_open(side, a0, c0), from_open(side, a1, c1)
    db.flat_box(cv, min(p[0], q[0]), max(p[0], q[0]), min(p[1], q[1]), max(p[1], q[1]), z0, z1, wall, roof)


def apron_cell(side):
    """駐機場の地面: 舗装と、つながる辺から機首の止まる所までの黄色い線。"""

    def colour(u, v):
        along = {"s": 1 - v, "n": v, "e": 1 - u, "w": u}[side]
        across = u if side in ("s", "n") else v
        if not (0.02 <= u < 0.98 and 0.02 <= v < 0.98):
            along_edge = along < 0.02 and 0.30 <= across <= 0.70
            if not along_edge:
                return None
        if abs(across - 0.5) < 0.016 and along < STOP_AT:
            return YELLOW
        if STOP_AT - 0.02 <= along < STOP_AT + 0.02 and 0.30 <= across <= 0.70:
            return YELLOW  # 停止の線（飛行機の機首が止まる所）
        return APRON

    return ground_cell(colour)


def terminal(cv, side):
    """脇の奥の辺（誘導路が南北なら西、東西なら北）に沿った細長いターミナル。

    手前の辺に置くと飛行機を隠し、行き止まりの端に置くと止まった機首と重なるので、脇に置く。
    """
    edge = {"s": "w", "n": "w", "e": "n", "w": "n"}[side]
    tu, tv = (lambda a, c: (c, a)), (lambda a, c: (a, c))
    to_uv = tu if edge == "n" else tv  # a = 奥の辺からの距離、c = 辺に沿う位置

    def block(a0, a1, c0, c1, z0, z1, wall, roof):
        p, q = to_uv(a0, c0), to_uv(a1, c1)
        db.flat_box(cv, p[0], q[0], p[1], q[1], z0, z1, wall, roof)

    block(0.01, 0.15, 0.10, 0.90, 0.0, 4.0, WALL, ROOF)
    for i in range(6):
        c = 0.15 + i * 0.12
        block(0.15, 0.153, c, c + 0.07, 1.2, 2.8, GLASS, GLASS)
    block(0.04, 0.12, 0.12, 0.22, 4.0, 7.5, WALL, ROOF)  # 管制の塔


def paste_over(base, top):
    base.paste(top, (0, 0), rail._mask(top))
    return base


def airstop_cells(layout):
    """ターミナルは奥の辺にあるので、全部の向きが後ろの絵だけ（飛行機の下に描く）。"""
    side = SIDES[layout]
    cv = db.Canvas()
    terminal(cv, side)
    return paste_over(apron_cell(side), cv.finish()), Image.new("RGB", (CELL, CELL), CLEAR)


def hangar(cv, side):
    """つながる辺の側に口が開いた格納庫。"""
    # 奥の壁と両側の壁、屋根。口の側（along が 0 に近い側）は開ける
    walls = [
        (0.92, 0.95, 0.08, 0.92),  # 奥
        (0.12, 0.92, 0.08, 0.12),  # 片側
        (0.12, 0.92, 0.88, 0.92),  # もう片側
    ]
    # 画面の奥（x + y の小さい方）から描く
    def depth(w):
        u, v = from_open(side, (w[0] + w[1]) / 2, (w[2] + w[3]) / 2)
        return u + v

    for a0, a1, c0, c1 in sorted(walls, key=depth):
        box(cv, side, a0, a1, c0, c1, 0.0, 6.5, HANGAR_WALL, HANGAR_WALL)
    if side in ("s", "e"):  # 口が見える向き: 中を暗く塗り、屋根は奥の半分
        box(cv, side, 0.55, 0.92, 0.12, 0.88, 0.0, 0.05, DARK, DARK)
        box(cv, side, 0.50, 0.95, 0.08, 0.92, 6.5, 7.2, HANGAR_ROOF, HANGAR_ROOF)
        for c0, c1 in ((0.08, 0.13), (0.87, 0.92)):  # 口の柱
            box(cv, side, 0.08, 0.13, c0, c1, 0.0, 6.5, HANGAR_WALL, HANGAR_WALL)
        box(cv, side, 0.08, 0.13, 0.08, 0.92, 6.5, 7.2, HANGAR_ROOF, HANGAR_ROOF)  # 口の梁
    else:
        box(cv, side, 0.10, 0.95, 0.08, 0.92, 6.5, 7.2, HANGAR_ROOF, HANGAR_ROOF)


def hangar_cells(layout):
    side = SIDES[layout]
    apron = apron_cell(side)
    cv = db.Canvas()
    hangar(cv, side)
    house = cv.finish()
    blank = Image.new("RGB", (CELL, CELL), CLEAR)
    if side in ("s", "e"):
        return paste_over(apron, house), blank
    return apron, house


BUILDINGS = {
    "air_stop": dict(
        name="pak256_airport", cells=airstop_cells,
        dat=["type: stop", "waytype: air", "enables_pax: 1", "enables_post: 1", "level: 2", "intro_year: 1900", "noinfo: 1"],
        note="空港の駅（駐機場とターミナル）。誘導路の行き止まりに置く。向き 4 通り",
    ),
    "air_depot": dict(
        name="pak256_hangar", cells=hangar_cells, front=(2, 3),  # 口が奥を向く向きは、屋根と壁が飛行機の上
        dat=["type: depot", "waytype: air", "intro_year: 1900", "noinfo: 1"],
        note="格納庫（飛行機の車庫）。誘導路の行き止まりに置く。向き 4 通り",
    ),
}


def building_sheet(key):
    """4 列（向き）× 3 行（0 後ろ、1 前、2 道具の絵）。"""
    out = Image.new("RGB", (CELL * 4, CELL * 3), CLEAR)
    for i in range(4):
        back, front = BUILDINGS[key]["cells"](i)
        out.paste(back, (i * CELL, 0))
        out.paste(front, (i * CELL, CELL))
    art = paste_over(out.crop((0, 0, CELL, CELL)), out.crop((0, CELL, CELL, CELL * 2)))
    out.paste(rail.tool_icon(art, ICON_BG), (0, CELL * 2))
    return out


def building_table(key):
    o = BUILDINGS[key]
    lines = [
        "# 空港の建物（絵は仮）。この表と PNG は ../draw_airport.py が書き出す（docs/airport.md）。",
        f"# {o['note']}",
        "obj: building",
        f"name: {o['name']}",
        f"copyright: {COPYRIGHT}",
    ] + o["dat"] + [
        "dims: 1,1,4",
        f"icon: \"> {key}.2.0\"",
        "backimage:        # backimage[向き][y][x][高さ][コマ]。向きは 0 南につながる・1 東・2 北・3 西",
    ]
    for i in range(4):
        lines.append(f"  {i}: {{0: {{0: {{0: {{0: {key}.0.{i}}}}}}}}}")
    # 前の絵（車の上）は、描いた物がある向きだけ
    front = o.get("front", ())
    if front:
        lines.append("frontimage:")
        for i in front:
            lines.append(f"  {i}: {{0: {{0: {{0: {{0: {key}.1.{i}}}}}}}}}")
    return "\n".join(lines) + "\n"


def write(folder, key, img, table):
    out = os.path.join(HERE, folder)
    os.makedirs(out, exist_ok=True)
    img.save(os.path.join(out, key + ".png"))
    with open(os.path.join(out, key + ".yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(table)
    print("wrote", folder, key)


def main():
    for key in WAYS:
        write(key, key, way_sheet(key), way_table(key))
    for key in BUILDINGS:
        write(key, key, building_sheet(key), building_table(key))


if __name__ == "__main__":
    main()
