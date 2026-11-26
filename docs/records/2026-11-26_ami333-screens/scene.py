"""#134（AMI #333 の直し）の前後を同じ位置で撮る: #111 の見本に、2 段の台の十字・路面軌道・T 字・道路の橋脚・停留所・2 段の高さの橋を足し、温暖と降雪に敷いて拡大 3 で撮る。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_ami333-screens/scene.py <本体の検証環境> <MCP のポート> <build のフォルダ> <出力のフォルダ>
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
# 撮る所の名前と、原点からのずれ。上の 15 個は #111 の scene.py と同じ
VIEWS = (("straight_road", 4, 0), ("diagonal_road", 14, 0), ("straight_rail", 4, 8), ("slope_road", 3, 18),
         ("slope_rail", 12, 18), ("canal", 4, 28), ("sidewalk", 16, 28), ("crossing", 5, 36), ("elevated", 5, 44),
         ("bridge", 5, 54), ("diagonal_rail", 14, 8), ("diagonal_canal", 9, 28), ("diagonal_sidewalk", 21, 28),
         ("elevated_curve", 9, 45), ("bridge_end", 2, 52),
         ("slope2_road", 3, 70), ("tram_road", 4, 80), ("tram_only", 4, 85), ("t_junction", 16, 80),
         ("pier", 5, 92), ("stop", 5, 100), ("bridge_high", 5, 108),
         ("bridge_slope2", 5, 116))


def lay(g, ox):
    log = []

    def check(label, r):
        if r not in ("None", "", "null"):
            log.append(f"{label}: {r}")

    def way(name, x1, y1, x2, y2, z=0):
        # straight=true で、坂を避けて回り道しないようにする
        check(f"{name} ({x1},{y1})-({x2},{y2})",
              g.sq(f'return command_x.build_way(player_x(0), coord3d({ox + x1},{OY + y1},{z}), coord3d({ox + x2},{OY + y2},{z}), '
                   f'way_desc_x("{name}"), true)'))

    def diagonal(name, x, y, steps):
        # 1 タイルずつ東・南を交互に敷くと斜めの絵になる
        for i in range(steps):
            way(name, x + i, y + i, x + i + 1, y + i)
            way(name, x + i + 1, y + i, x + i + 1, y + i + 1)

    def slope(x, y, z, value):
        check(f"set_slope ({x},{y},{z}) {value}",
              g.sq(f"return command_x.set_slope(player_x(0), coord3d({ox + x},{OY + y},{z}), {value})"))

    def bridge(name, x1, x2, y):
        check(name, g.sq(f'return command_x.build_bridge(player_x(0), coord3d({ox + x1},{OY + y},0), '
                         f'coord3d({ox + x2},{OY + y},0), bridge_desc_x("{name}"))'))

    # ここから #111 の scene.py と同じ配置
    for name, y in (("ami_road_local", 0), ("ami_rail_ballast", 8)):
        way(name, 0, y, 8, y)
        way(name, 4, y - 3, 4, y + 3)
        way(name, 8, y, 8, y + 3)
        diagonal(name, 11, y - 3, 6)
    for cx, name in ((3, "ami_road_local"), (12, "ami_rail_ballast")):
        cy = 18
        slope(cx, cy, 0, "slope.all_up_slope")
        for dx, dy, value in ((0, -1, 4), (0, 1, 36), (-1, 0, 12), (1, 0, 28)):
            slope(cx + dx, cy + dy, 0, value)
        way(name, cx, cy - 3, cx, cy + 3)
        way(name, cx - 3, cy, cx + 3, cy)
    for name, x in (("ami_canal", 0), ("ami_sidewalk", 12)):
        way(name, x, 28, x + 5, 28)
        way(name, x + 5, 28, x + 5, 31)
        diagonal(name, x + 7, 26, 4)
    way("ami_rail_ballast", 0, 36, 10, 36)
    way("ami_road_local", 3, 33, 3, 39)
    way("ami_rail_ballast", 8, 33, 8, 39)
    way("ami_road_local", 6, 38, 10, 38)
    for name, y in (("ami_road_local_elev_single", 43), ("ami_rail_ballast_elev_single", 46)):
        way(name, 0, y, 8, y)
        way(name, 8, y, 10, y + 2)
    for name, way_name, y in (("ami_road_local_bridge", "ami_road_local", 52),
                              ("ami_rail_ballast_bridge", "ami_rail_ballast", 56)):
        bridge(name, 2, 8, y)
        way(way_name, 0, y, 2, y)
        way(way_name, 8, y, 10, y)

    # 2 段の台の上の十字と、四方の 2 段の坂（#134）
    slope(3, 70, 0, "slope.all_up_slope")
    slope(3, 70, 1, "slope.all_up_slope")
    for dx, dy, value in ((0, -1, 8), (0, 1, 72), (-1, 0, 24), (1, 0, 56)):
        slope(3 + dx, 70 + dy, 0, value)
    way("ami_road_local", 3, 67, 3, 73)
    way("ami_road_local", 0, 70, 6, 70)
    # 路面軌道: 道路の上（直線・曲がり・坂なし）と、土の上
    way("ami_road_local", 0, 80, 8, 80)
    way("ami_road_local", 8, 80, 8, 82)
    way("ami_tram", 0, 80, 8, 80)
    way("ami_tram", 8, 80, 8, 82)
    way("ami_tram", 0, 85, 8, 85)
    way("ami_tram", 8, 85, 8, 87)
    # T 字
    way("ami_road_local", 12, 80, 20, 80)
    way("ami_road_local", 16, 80, 16, 83)
    # 道路の高架と、真下の橋脚。高架の前の地面に直線の道路を並べる
    way("ami_road_local_elev_single", 0, 92, 10, 92)
    way("ami_pier_road", 0, 92, 10, 92)
    way("ami_road_local", 0, 94, 10, 94)
    # 道路の停留所（pak256 の物）。道の縁に接して描く物を見る
    way("ami_road_local", 0, 100, 10, 100)
    g.station(ox + 4, OY + 100, "pak256_bus_stop")
    g.station(ox + 6, OY + 100, "pak256_truck_stop")
    # 高い橋: 途中に 1 段の台を置いて、橋の面を 2 段にする（橋の端の 2 段の坂。架けられないときは [log] に出る）
    slope(5, 108, 0, "slope.all_up_slope")
    check("ami_road_local_bridge (high)",
          g.sq(f'return command_x.build_bridge(player_x(0), coord3d({ox + 2},{OY + 108},0), '
               f'coord3d({ox + 8},{OY + 108},0), bridge_desc_x("ami_road_local_bridge"))'))
    way("ami_road_local", 0, 108, 2, 108)
    way("ami_road_local", 8, 108, 10, 108)
    # 2 段の高さの橋の端: 両側を 2 段の台にして、台の縁の 2 段の坂（56 は西が高い・24 は東が高い）から橋を架ける
    for x in (0, 1, 9, 10):
        slope(x, 116, 0, "slope.all_up_slope")
        slope(x, 116, 1, "slope.all_up_slope")
    slope(2, 116, 0, 56)
    slope(8, 116, 0, 24)
    bridge("ami_road_local_bridge", 2, 8, 116)
    way("ami_road_local", 0, 116, 1, 116, 2)
    way("ami_road_local", 9, 116, 10, 116, 2)
    return log


with Game(env, "flat_512_left_v64", port, build=build) as g:
    for climate, ox in ORIGINS.items():
        for line in lay(g, ox):
            print(f"[{climate}] {line}", flush=True)
    g.climate(ORIGINS["snow"] - 8, OY - 8, ORIGINS["snow"] + 26, OY + 122, "arctic")
    g.settle(10)
    for climate, ox in ORIGINS.items():
        for name, x, y in VIEWS:
            g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d({ox + x},{OY + y},0)); return 1")
            time.sleep(2)
            g.capture(os.path.join(out, f"{climate}_{name}.png"))
