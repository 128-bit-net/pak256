"""#111 の前後を同じ位置で撮る: 道路・線路・運河・歩道・踏切・高架・橋・坂・斜めの見本を温暖と降雪に敷いて、拡大 3 で撮る。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_road-edge-screens/scene.py <本体の検証環境> <MCP のポート> <build のフォルダ> <出力のフォルダ>
<build のフォルダ> は pak/ を持つフォルダ（tools/build.py の build/ か、その写し）。
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
OY = 60
ORIGINS = {"temperate": 60, "snow": 316}
# 撮る所の名前と、原点からのずれ
VIEWS = (("straight_road", 4, 0), ("diagonal_road", 14, 0), ("straight_rail", 4, 8), ("slope_road", 3, 18),
         ("slope_rail", 12, 18), ("canal", 4, 28), ("sidewalk", 16, 28), ("crossing", 5, 36), ("elevated", 5, 44),
         ("bridge", 5, 54), ("diagonal_rail", 14, 8), ("diagonal_canal", 9, 28), ("diagonal_sidewalk", 21, 28),
         ("elevated_curve", 9, 45), ("bridge_end", 2, 52))


def lay(g, ox):
    log = []

    def way(name, x1, y1, x2, y2):
        # straight=true で、坂を避けて回り道しないようにする
        r = g.sq(f'return command_x.build_way(player_x(0), coord3d({ox + x1},{OY + y1},0), coord3d({ox + x2},{OY + y2},0), '
                 f'way_desc_x("{name}"), true)')
        if r not in ("None", "", "null"):
            log.append(f"{name} ({x1},{y1})-({x2},{y2}): {r}")

    def diagonal(name, x, y, steps):
        # 1 タイルずつ東・南を交互に敷くと斜めの絵になる
        for i in range(steps):
            way(name, x + i, y + i, x + i + 1, y + i)
            way(name, x + i + 1, y + i, x + i + 1, y + i + 1)

    def slope(x, y, z, value):
        r = g.sq(f"return command_x.set_slope(player_x(0), coord3d({ox + x},{OY + y},{z}), {value})")
        if r not in ("None", "", "null"):
            log.append(f"set_slope ({x},{y},{z}): {r}")

    # 直線・十字・曲がりと、斜め
    for name, y in (("ami_road_local", 0), ("ami_rail_ballast", 8)):
        way(name, 0, y, 8, y)
        way(name, 4, y - 3, 4, y + 3)
        way(name, 8, y, 8, y + 3)
        diagonal(name, 11, y - 3, 6)
    # 1 段の台を越える道（坂の継ぎ目）
    for cx, name in ((3, "ami_road_local"), (12, "ami_rail_ballast")):
        cy = 18
        slope(cx, cy, 0, "slope.all_up_slope")
        for dx, dy, value in ((0, -1, 4), (0, 1, 36), (-1, 0, 12), (1, 0, 28)):
            slope(cx + dx, cy + dy, 0, value)
        way(name, cx, cy - 3, cx, cy + 3)
        way(name, cx - 3, cy, cx + 3, cy)
    # 運河と歩道（直線・曲がり・斜め）
    for name, x in (("ami_canal", 0), ("ami_sidewalk", 12)):
        way(name, x, 28, x + 5, 28)
        way(name, x + 5, 28, x + 5, 31)
        diagonal(name, x + 7, 26, 4)
    # 踏切（道路が南北・東西）
    way("ami_rail_ballast", 0, 36, 10, 36)
    way("ami_road_local", 3, 33, 3, 39)
    way("ami_rail_ballast", 8, 33, 8, 39)
    way("ami_road_local", 6, 38, 10, 38)
    # 高架（地面の座標で敷くと本体が 1 段上に架ける）
    for name, y in (("ami_road_local_elev_single", 43), ("ami_rail_ballast_elev_single", 46)):
        way(name, 0, y, 8, y)
        way(name, 8, y, 10, y + 2)
    # 橋（両端は平地。本体が端の坂を作る）。橋を架けてから前後に道を足す
    for name, way_name, y in (("ami_road_local_bridge", "ami_road_local", 52),
                              ("ami_rail_ballast_bridge", "ami_rail_ballast", 56)):
        r = g.sq(f'return command_x.build_bridge(player_x(0), coord3d({ox + 2},{OY + y},0), '
                 f'coord3d({ox + 8},{OY + y},0), bridge_desc_x("{name}"))')
        if r not in ("None", "", "null"):
            log.append(f"{name}: {r}")
        way(way_name, 0, y, 2, y)
        way(way_name, 8, y, 10, y)
    return log


with Game(env, "flat_512_left_v64", port, build=build) as g:
    for climate, ox in ORIGINS.items():
        for line in lay(g, ox):
            print(f"[{climate}] {line}", flush=True)
    g.climate(ORIGINS["snow"] - 8, OY - 8, ORIGINS["snow"] + 26, OY + 62, "arctic")
    for climate, ox in ORIGINS.items():
        for name, x, y in VIEWS:
            g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d({ox + x},{OY + y},0)); return 1")
            time.sleep(2)
            g.capture(os.path.join(out, f"{climate}_{name}.png"))
