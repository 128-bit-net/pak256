"""建物の下の地面（#126）の再現と確かめ。MIT License。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-26_building-ground-screens/scene.py <検証環境> <ポート> <build のフォルダ> <出力フォルダ>
同じ場面（街の建物 11 種・停留所・駅・車庫・産業）を、温帯（x<256）と雪の気候（x>=256）に置き、
黄色い砂漠の区画の画面からスクロール（座標へ移動）して撮る。夏と冬。地面が描かれない所には、前の画面の砂漠が残る。"""
import os
import sys
import time

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
W = "ami_road_local"
HOUSES = [["pak256_house_small", "pak256_house_wide", "pak256_row_house", "pak256_apartment"],
          ["pak256_shop", "pak256_store", "pak256_office"],
          ["pak256_workshop", "pak256_warehouse", "pak256_factory"]]
AREAS = {"temperate": 60, "snow": 300}
DESERT = (150, 100)


def say(*a):
    print(*a, flush=True)


def depot(g, name, x, y, way):
    g.road(x, y + 1, x, y, way)
    return g.sq(f'local d=null; foreach (b in building_desc_x.get_building_list(building_desc_x.depot)) '
                f'if (b.get_name()=="{name}") d=b; return command_x.build_depot(player_x(0), coord3d({x},{y + 1},0), d)')


def setup(g, x0):
    say("city", g.sq(f"return command_x(tool_add_city).work(player_x(0), coord3d({x0},140,0))"))
    g.road(x0 + 4, 138, x0 + 16, 138, W)
    for j, row in enumerate(HOUSES):
        for i, n in enumerate(row):
            r = g.sq(f'return command_x(tool_build_house).work(player_x(0), coord3d({x0 + 6 + i * 2},{139 + j * 2},0), "00{n}")')
            say(n, x0 + 6 + i * 2, 139 + j * 2, r)
    # 停留所・駅・車庫・産業
    g.road(x0, 160, x0 + 24, 160, W)
    for x, n in [(x0 + 8, "pak256_bus_stop"), (x0 + 11, "pak256_truck_stop")]:
        say(n, g.station(x, 160, n))
    g.road(x0, 164, x0 + 24, 164, "ami_rail_ballast")
    for i in range(3):
        say("station", g.station(x0 + 8 + i, 164, "pak256_train_station"))
    say("road depot", depot(g, "ami_road_depot", x0 + 15, 160, W))
    say("rail depot", depot(g, "ami_rail_depot", x0 + 15, 164, "ami_rail_ballast"))
    say("mine", g.sq(f'return command_x(tool_build_factory).work(player_x(0), coord3d({x0 + 6},155,0), "0050,pak256_coal_mine")'))
    say("plant", g.sq(f'return command_x(tool_build_factory).work(player_x(0), coord3d({x0 + 12},155,0), "0050,pak256_coal_kraftwerk")'))


def shot(g, x, y, name):
    """砂漠の区画を表示してから、目的の場所へスクロールして撮る。"""
    g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({DESERT[0]},{DESERT[1]},0)); return 1")
    time.sleep(3)
    g.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(4)
    g.capture(os.path.join(out, name + ".png"))


with Game(env, "flat_512_left_v64", port, work=out + "/_w", build=build, simuconf_extra=["show_names = 0"]) as g:
    g.climate(DESERT[0] - 20, DESERT[1] - 20, DESERT[0] + 20, DESERT[1] + 20, "desert", timeout=120)
    for x0 in AREAS.values():
        setup(g, x0)
    g.settle(25)
    for season, month in [("summer", 6), ("winter", 0)]:
        g.wait_month(month)
        time.sleep(8)
        for area, x0 in AREAS.items():
            shot(g, x0 + 10, 142, f"{season}_{area}_town")
            shot(g, x0 + 12, 159, f"{season}_{area}_infra")
            shot(g, x0 + 1, 140, f"{season}_{area}_townhall")
            shot(g, x0 + 11, 163, f"{season}_{area}_rail")
    if g.left_over:
        sys.exit(1)
