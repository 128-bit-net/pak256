"""Release の説明に付ける画面を、今の配布の zip の中身だけで撮る。MIT License。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-26_v040-check-screens/shots.py <検証環境> <ポート> <配布の zip を展開して並べたフォルダ（build/ と x/pak256/）> <出力フォルダ>
撮る物: 乗り物と停留所（transport.png）、気候ごとの森の夏（forest_<気候>.png）と温帯の冬、街の商業・工業の夏と冬（town_*.png）。
昼夜は止めてある。街の建物は道具で置く（街の育ちは待たない）。"""
import os
import sys
import time

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, pak, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
W = "ami_road_local"
N = 14
PLOTS = [("tropic", 100), ("desert", 122), ("mediterran", 144), ("temperate", 166), ("tundra", 188), ("arctic", 210)]
Y0 = 100


def shot(g, x, y, name, zoom=3):
    g.sq(f"gui.set_zoom({zoom}); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(6)
    g.capture(os.path.join(out, name + ".png"))


def veh(wt, name):
    return f'local v=null; foreach (d in vehicle_desc_x.get_available_vehicles({wt})) if (d.get_name()=="{name}") v=d; '


def convoy(g, wt, depot, stop, back, names):
    """車庫 depot で names をつなぎ、stop で積載 100% を待たせる（撮る間、停留所に止まる）。"""
    code = f"local pl=player_x(0); local depot=depot_x({depot[0]},{depot[1]},0); local cnv=convoy_x(0); "
    for i, n in enumerate(names):
        code += "{ " + veh(wt, n) + "depot.append_vehicle(pl, cnv, v); } "
        if i == 0:
            code += "local l=depot.get_convoy_list(); cnv=l[l.len()-1]; "
    code += (f"cnv.change_schedule(pl, schedule_x({wt}, [schedule_entry_x(coord3d({stop[0]},{stop[1]},0),100,0), "
             f"schedule_entry_x(coord3d({back[0]},{back[1]},0),0,0)])); depot.start_convoy(pl, cnv); return 1")
    print(names, g.sq(code, timeout=60), flush=True)


def depot(g, wt, name, x, y, way):
    print("way", g.road(x, y + 1, x, y, way), flush=True)
    print("depot", g.sq(f'local d=null; foreach (b in building_desc_x.get_building_list(building_desc_x.depot)) '
                        f'if (b.get_name()=="{name}") d=b; return command_x.build_depot(player_x(0), coord3d({x},{y + 1},0), d)'), flush=True)


with Game(env, "flat_512_left_v64", port, work=out + "/_w", build=pak + "/build", root=pak + "/x/pak256",
          simuconf_extra=["show_names = 0"]) as g:
    # 乗り物と停留所
    print("road", g.road(40, 60, 90, 60, W), flush=True)
    for x, n in [(60, "pak256_bus_stop"), (64, "pak256_truck_stop"), (80, "pak256_bus_stop"), (84, "pak256_truck_stop")]:
        print("stop", x, g.station(x, 60, n), flush=True)
    depot(g, "wt_road", "ami_road_depot", 45, 60, W)
    print("rail", g.road(40, 66, 90, 66, "ami_rail_ballast"), flush=True)
    for x0 in (60, 80):
        for i in range(3):
            g.station(x0 + i, 66, "pak256_train_station")
    depot(g, "wt_rail", "ami_rail_depot", 45, 66, "ami_rail_ballast")
    g.settle(25)
    convoy(g, "wt_road", (45, 61), (60, 60), (80, 60), ["pak256_bus"])
    convoy(g, "wt_road", (45, 61), (64, 60), (84, 60), ["pak256_coal_truck"])
    convoy(g, "wt_rail", (45, 67), (61, 66), (81, 66), ["pak256_railcar", "pak256_railcar_trailer"])
    g.sq("debug.set_game_speed(16); return 1")
    time.sleep(15)
    g.sq("debug.set_game_speed(1); return 1")
    shot(g, 64, 62, "transport")

    # 街の商業・工業の建物（住宅と並べて置く）
    print("city", g.sq("return command_x(tool_add_city).work(player_x(0), coord3d(60,150,0))"), flush=True)
    g.road(66, 146, 82, 146, W)
    g.road(66, 150, 82, 150, W)
    rows = {145: ["pak256_shop", "pak256_store", "pak256_office", "pak256_house_small"],
            147: ["pak256_workshop", "pak256_warehouse", "pak256_factory", "pak256_apartment"],
            149: ["pak256_office", "pak256_shop", "pak256_row_house", "pak256_store"]}
    for y, names in rows.items():
        for i, n in enumerate(names):
            r = g.sq(f'return command_x(tool_build_house).work(player_x(0), coord3d({70 + i * 2},{y},0), "00{n}")')
            if r not in (None, "", "None", "null"):
                print("house", n, r, flush=True)
    g.settle(20)
    shot(g, 73, 147, "town_summer")

    # 気候ごとの森
    for name, x in PLOTS:
        g.climate(x, Y0, x + N - 1, Y0 + N - 1, name, timeout=120)
        r = g.sq(f'return command_x(tool_forest).work(player_x(0), coord3d({x},{Y0},0), coord3d({x + N - 1},{Y0 + N - 1},0), "")')
        print("forest", name, r, flush=True)
    for season, month in [("summer", 6), ("autumn", 9), ("winter", 0)]:
        g.wait_month(month)
        time.sleep(8)
        for name, x in PLOTS:
            if season == "summer" or name == "temperate":
                shot(g, x + N // 2, Y0 + N // 2, f"forest_{name}_{season}")
    shot(g, 73, 147, "town_winter")
    if g.left_over:
        sys.exit(1)
