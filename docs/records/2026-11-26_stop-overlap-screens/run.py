"""バス停・荷役所と道路の白線の重なりを撮る（#115）。MIT License。tools/game.py の Game の上で動く。

温帯（x<256）の平らな地図に、東西の道路と南北の道路を敷き、それぞれにバス停 1 つと荷役所 2 つを置いて、
バス・郵便のトラック・石炭のトラックを、ダイヤの積載の待ち 100% で停めて撮る。車両を停めない 3 タイル続きの停留所も撮る。

使い方: python -X utf8 run.py <検証環境> <ポート> <出力フォルダ>
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import game  # noqa: E402
from game import Game  # noqa: E402

_day_night_off = game.append_day_night_off


def _no_names(simuconf):
    """停留所の名前の札を消す（札が絵に重なるため。作業フォルダの写しだけ）。"""
    _day_night_off(simuconf)
    with open(simuconf, "a", encoding="utf-8") as f:
        f.write("show_names = 0" + chr(10))


game.append_day_night_off = _no_names

ap = argparse.ArgumentParser()
ap.add_argument("env")
ap.add_argument("port", type=int)
ap.add_argument("out")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

ROAD = "ami_road_local"
EY = 60          # 東西の道路の y（x=52〜76）
NX = 90          # 南北の道路の x（y=50〜74）
# (停留所, 車両, 東西の道路の x, 南北の道路の y)。車庫から遠い停留所から先に出す
PLAN = [
    ("pak256_truck_stop", "pak256_coal_truck", 70, 56),
    ("pak256_truck_stop", "pak256_mail_truck", 65, 61),
    ("pak256_bus_stop", "pak256_bus", 60, 66),
]


def c(x, y):
    return f"coord3d({x},{y},0)"


def depot(g, road_tile, depot_tile):
    g.road(road_tile[0], road_tile[1], depot_tile[0], depot_tile[1], ROAD)
    code = ('local dd=null; foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) '
            'if (d.get_name()=="ami_road_depot") dd=d; '
            f'return command_x.build_depot(player_x(0), {c(*depot_tile)}, dd)')
    print("[depot]", g.sq(code))


def convoy(g, depot_tile, stop, back, name):
    code = (f"local pl=player_x(0); local depot=depot_x({depot_tile[0]},{depot_tile[1]},0); local v=null; "
            f'foreach (d in vehicle_desc_x.get_available_vehicles(wt_road)) if (d.get_name()=="{name}") v=d; '
            f'if (v==null) return "no vehicle"; depot.append_vehicle(pl, convoy_x(0), v); '
            "local l=depot.get_convoy_list(); local cnv=l[l.len()-1]; "
            f"cnv.change_schedule(pl, schedule_x(wt_road, [schedule_entry_x({c(*stop)},100,0), schedule_entry_x({c(*back)},0,0)])); "
            'depot.start_convoy(pl, cnv); return "ok"')
    print("[convoy]", name, g.sq(code, timeout=60))


def shot(g, name, x, y, zoom=3):
    g.sq(f"gui.close_all_windows(); gui.set_zoom({zoom}); gui.jump({c(x, y)}); return 1")
    time.sleep(2)
    g.capture(os.path.join(a.out, name))
    print("[shot]", name)


with Game(a.env, "flat_512_left_v64", a.port) as g:
    print("[way]", g.road(52, EY, 76, EY, ROAD))
    print("[way]", g.road(NX, 50, NX, 74, ROAD))
    for stop, _, x, y in PLAN:
        print("[stop]", stop, g.station(x, EY, stop), g.station(NX, y, stop))
    # 車両を停めない 3 タイル続きの停留所（中ほどと端の絵を見る）
    for i in range(3):
        print("[empty]", g.station(73 + i, EY, "pak256_bus_stop"), g.station(NX, 50 + i, "pak256_truck_stop"))
    ew_depot, ns_depot = (54, EY + 1), (NX + 1, 72)
    depot(g, (54, EY), ew_depot)
    depot(g, (NX, 72), ns_depot)
    for _, veh, x, y in PLAN:
        convoy(g, ew_depot, (x, EY), (53, EY), veh)
        convoy(g, ns_depot, (NX, y), (NX, 73), veh)
        g.settle(3)
    g.settle(30)
    print("[convoys]", g.sq('local s=""; foreach (cv in world.get_convoy_list()) { local p=cv.get_pos(); '
                            's += cv.get_name()+"@"+p.x+","+p.y+" v="+cv.get_speed()+"; "; } return s'))
    # 東西の道路: バス停（x=60）・郵便の荷役所（x=65）・石炭の荷役所（x=70）
    shot(g, "ew_bus.png", 60, EY)
    shot(g, "ew_mail.png", 65, EY)
    shot(g, "ew_coal.png", 70, EY)
    # 南北の道路: 石炭の荷役所（y=56）・郵便の荷役所（y=61）・バス停（y=66）
    shot(g, "ns_coal.png", NX, 56)
    shot(g, "ns_mail.png", NX, 61)
    shot(g, "ns_bus.png", NX, 66)
    shot(g, "ew_empty.png", 74, EY)
    shot(g, "ns_empty.png", NX, 51)
