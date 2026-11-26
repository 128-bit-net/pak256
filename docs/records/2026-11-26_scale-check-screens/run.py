"""縮尺の見比べの場面を組んで撮る（#104）。MIT License。tools/game.py の Game の上で動く。

温帯（x<256）の平らな地図に、道路（バス停・荷役所にバスと 2 台のトラックを待たせる）、線路（3 タイルの駅に気動車と付随車を待たせる）、
産業（炭鉱と発電所）を並べ、その脇に街の建物と成木を置いて、夏の昼に撮る。
車両は、ダイヤの積載の待ちを 100% にして停留所・駅で止めたままにする。

使い方: python -X utf8 run.py <検証環境> <ポート> <出力フォルダ>
注意: run_squirrel に渡す文字列にバックスラッシュを入れない。
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
    """game.py の昼夜の停止に加えて、停留所の名前の札を消す（札が建物に重なるため。作業フォルダの写しだけ）。"""
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

ROAD, RAIL = "ami_road_local", "ami_rail_ballast"
YA, YB, YC = 60, 66, 76        # 道路の列・線路の列・産業の列の道路の y
X0, X1 = 52, 74                # 道路・線路の西と東の端

# 街の建物（道路・線路の北の列）: (x, y, 名前)
BUILDINGS = [
    (58, YA - 1, "pak256_house_small"), (59, YA - 1, "pak256_house_wide"), (61, YA - 1, "pak256_shop"),
    (62, YA - 1, "pak256_apartment"), (64, YA - 1, "pak256_workshop"), (65, YA - 1, "pak256_townhall"),
    (67, YA - 1, "pak256_office"),
    (58, YB - 1, "pak256_row_house"), (63, YB - 1, "pak256_store"), (65, YB - 1, "pak256_warehouse"),
    (67, YB - 1, "pak256_factory"),
]
# 成木（age >= 576 か月）: (x, y, 名前)
TREES = [
    (60, YA - 1, "pak256_zelkova"), (63, YA - 1, "pak256_cedar"), (66, YA - 1, "pak256_birch"),
    (59, YA + 1, "pak256_birch"), (66, YA + 1, "pak256_zelkova"),
    (59, YB - 1, "pak256_cedar"), (64, YB - 1, "pak256_zelkova"), (66, YB - 1, "pak256_cedar"),
    (57, YC - 1, "pak256_zelkova"), (62, YC - 1, "pak256_cedar"),
]


def c(x, y):
    return f"coord3d({x},{y},0)"


def way(g, x1, y1, x2, y2, name):
    print(f"[way] {name} {x1},{y1}-{x2},{y2}:", g.road(x1, y1, x2, y2, name))


def build_house(g, x, y, name):
    r = g.sq(f'return command_x(tool_build_house).work(player_x(0), {c(x, y)}, "00{name}")')
    print(f"[house] {name} {x},{y}: {r}")


def plant_tree(g, x, y, name):
    """成木になるまで、植えては抜くを繰り返す（絵は age >= 576 か月で成木。tree_builder.cc の tree_age_index）。

    この保存データは「木なし」の設定なので、公共プレイヤー（--player-nr 1）として流す（植える道具が公共だけを通す）。
    """
    code = (f'local t=null; for (local i=0;i<80;i++) {{ command_x(tool_plant_tree).work(player_x(1), {c(x, y)}, "11,{name}");'
            f' t=square_x({x},{y}).get_ground_tile().find_object(mo_tree); if (t==null) return "no tree";'
            f' if (t.get_age()>=576) return "age="+t.get_age()+" tries="+(i+1);'
            f' command_x(tool_remover).work(player_x(1), {c(x, y)}); }} return "gave up"')
    out = g._client("--run-squirrel", code, "--player-nr", "1", timeout=60)
    print(f"[tree] {name} {x},{y}: {out.stdout.strip()}")


def convoy(g, wt, depot, stop, back, names):
    """車庫 depot (x,y) で names の車両をつないで、stop で積載 100% を待たせる。"""
    adds = " ".join(
        f'v=null; foreach (d in vehicle_desc_x.get_available_vehicles({wt})) if (d.get_name()=="{n}") v=d; '
        f'if (v==null) return "no vehicle {n}"; depot.append_vehicle(pl, cnv, v); '
        f'if ({i}==0) {{ local l=depot.get_convoy_list(); cnv=l[l.len()-1]; }}'
        for i, n in enumerate(names))
    code = (f"local pl=player_x(0); local depot=depot_x({depot[0]},{depot[1]},0); local cnv=convoy_x(0); local v=null; {adds} "
            f"cnv.change_schedule(pl, schedule_x({wt}, [schedule_entry_x({c(*stop)},100,0), schedule_entry_x({c(*back)},0,0)])); "
            f"depot.start_convoy(pl, cnv); return \"ok\"")
    print(f"[convoy] {names}: {g.sq(code, timeout=60)}")


def depot(g, wt, name, x, y, way_name):
    way(g, x, y + 1, x, y, way_name)
    code = (f'local dd=null; foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name()=="{name}") dd=d; '
            f'return command_x.build_depot(player_x(0), {c(x, y + 1)}, dd)')
    print(f"[depot] {name}: {g.sq(code)}")
    return (x, y + 1)


def shot(g, name, x, y, zoom=3):
    g.sq(f"gui.close_all_windows(); gui.set_zoom({zoom}); gui.jump({c(x, y)}); return 1")
    time.sleep(2)
    g.capture(os.path.join(a.out, name))
    print("[shot]", name)


with Game(a.env, "flat_512_left_v64", a.port) as g:
    # 道路・線路
    way(g, X0, YA, X1, YA, ROAD)
    way(g, X0, YB, X1, YB, RAIL)
    way(g, X0, YC, X1, YC, ROAD)
    # 駅と停留所
    for x in (60, 61, 62):
        print("[station]", g.station(x, YB, "pak256_train_station"))
    print("[stop]", g.station(60, YA, "pak256_bus_stop"))
    print("[stop]", g.station(63, YA, "pak256_truck_stop"))
    print("[stop]", g.station(65, YA, "pak256_truck_stop"))
    print("[stop]", g.station(60, YC, "pak256_truck_stop"))
    # 車庫
    rd = depot(g, "road", "ami_road_depot", X0, YA, ROAD)
    rl = depot(g, "rail", "ami_rail_depot", X0, YB, RAIL)
    rc = depot(g, "road", "ami_road_depot", X0, YC, ROAD)
    # 街の建物には最寄りの街が要るので、離れた所に街を 1 つ置く
    print("[city]", g.sq(f"return command_x(tool_add_city).work(player_x(0), {c(200, 200)})"))
    # 産業（足跡の左上の座標。炭鉱 2x2、発電所 3x3）
    print("[factory]", g.sq(f'return command_x(tool_build_factory).work(player_x(0), {c(58, YC - 2)}, "0050,pak256_coal_mine")'))
    print("[factory]", g.sq(f'return command_x(tool_build_factory).work(player_x(0), {c(63, YC - 3)}, "0050,pak256_coal_kraftwerk")'))
    # 車両
    convoy(g, "wt_road", rd, (65, YA), (X0 + 2, YA), ["pak256_coal_truck"])
    convoy(g, "wt_road", rd, (63, YA), (X0 + 2, YA), ["pak256_mail_truck"])
    convoy(g, "wt_road", rd, (60, YA), (X0 + 2, YA), ["pak256_bus"])
    convoy(g, "wt_rail", rl, (61, YB), (X0 + 2, YB), ["pak256_railcar", "pak256_railcar_trailer"])
    convoy(g, "wt_road", rc, (60, YC), (X0 + 2, YC), ["pak256_coal_truck"])
    g.settle(25)
    # 夏（月は 0 始まりで 5〜8）まで進める。街の建物は建て替わるので、その後に置く
    g.sq("debug.set_game_speed(64); return 1")
    for _ in range(900):
        if int(g.sq("return world.get_time().month")) == 5:
            break
        time.sleep(0.5)
    g.sq("debug.set_game_speed(1); return 1")
    for x, y, name in BUILDINGS:
        build_house(g, x, y, name)
    g.settle(14)  # 建設中の絵が終わるまで
    for x, y, name in TREES:
        plant_tree(g, x, y, name)
    time.sleep(3)
    # 置けた物の確かめ
    q = ('local s=""; foreach (p in [%s]) { local t=square_x(p[0],p[1]).get_ground_tile().find_object(mo_building);'
         ' s += p[0]+","+p[1]+"="+(t==null?"none":t.get_desc().get_name())+" "; } return s')
    print("[check]", g.sq(q % ",".join(f"[{x},{y}]" for x, y, _ in BUILDINGS)))
    print("[convoys]", g.sq('local s=""; foreach (cv in world.get_convoy_list()) { local p=cv.get_pos(); '
                            's += cv.get_name()+"@"+p.x+","+p.y+" v="+cv.get_speed()+"; "; } return s'))
    print("[month]", g.sq("return world.get_time().month"))
    shot(g, "A_road_z3.png", 62, YA - 1)
    shot(g, "B_rail_z3.png", 62, YB - 1)
    shot(g, "C_industry_z3.png", 62, YC - 1)
    shot(g, "D_overview_z6.png", 62, YB, zoom=6)
