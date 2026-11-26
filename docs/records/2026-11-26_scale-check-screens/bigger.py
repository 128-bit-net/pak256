"""バスを「一回り大きく」した試し絵を作り、今の絵と並べてゲームで撮る（#104）。MIT License。

使い方: python -X utf8 bigger.py <検証環境> <ポート> <出力フォルダ（git 管理外）>   （先に tools/build.py。makeobj は PATH か MAKEOBJ）
試し絵は出力フォルダにだけ書き、素材は変えない。objects/vehicle/road/draw_vehicles.py のバスを元に、
幅と高さ（最後の 1 つは長さも）に倍率を掛けた物を別の名前で組み、--extra-pak として足す。
"""
import argparse
import copy
import importlib.util
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import game  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("env")
ap.add_argument("port", type=int)
ap.add_argument("out")
a = ap.parse_args()
out = os.path.abspath(a.out)
os.makedirs(out, exist_ok=True)

spec_ = importlib.util.spec_from_file_location("dv", os.path.join(ROOT, "objects", "vehicle", "road", "draw_vehicles.py"))
dv = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(dv)
BUS = next(s for s in dv.VEHICLES if s["name"] == "pak256_bus")
PX_Z = dv.V.PX_PER_M_Z

# (名前, 幅と高さの倍率, 長さの倍率)
VARIANTS = [("pak256_bus", 1.0, 1.0), ("mock_bus_wh125", 1.25, 1.0), ("mock_bus_wh150", 1.5, 1.0), ("mock_bus_all125", 1.25, 1.25)]
extra = []
for name, wh, ln in VARIANTS[1:]:
    s = copy.deepcopy(BUS)
    s.update(name=name, stem=name, width_m=BUS["width_m"] * wh, real_length_m=BUS["real_length_m"] * ln)
    dv.V.PX_PER_M_Z = PX_Z * wh  # 高さ（車体・窓・帯）をまとめて倍にする
    dv.draw_sheet(s).save(os.path.join(out, name + ".png"))
    dv.V.PX_PER_M_Z = PX_Z
    lines = [l.split("#")[0].rstrip() for l in dv.yaml_lines(s).splitlines() if not l.startswith("#")]
    dat, images = [], False
    for l in lines:
        if l.startswith("emptyimage"):
            images = True
        elif images:
            k, v = l.strip().split(": ")
            dat.append(f"emptyimage[{k}]={v}")
        else:
            dat.append(l.replace(": ", "=", 1))
    with open(os.path.join(out, name + ".dat"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(dat) + "\n")
    pak = f"vehicle.road.{name}.pak"
    r = subprocess.run([os.environ.get("MAKEOBJ", "makeobj"), "pak256", pak, name + ".dat"], cwd=out, capture_output=True)
    log = (r.stdout + r.stderr).decode("utf-8", errors="replace")
    if r.returncode or "Warning" in log or "ERROR" in log:
        sys.exit(log)
    extra.append(os.path.join(out, pak))

_day_night_off = game.append_day_night_off


def _no_names(simuconf):
    _day_night_off(simuconf)
    with open(simuconf, "a", encoding="utf-8") as f:
        f.write("show_names = 0" + chr(10))


game.append_day_night_off = _no_names

Y, X0 = 60, 52
STOPS = [58, 60, 62, 64]


def c(x, y):
    return f"coord3d({x},{y},0)"


with game.Game(a.env, "flat_512_left_v64", a.port, extra_paks=extra) as g:
    print(g.road(X0, Y, 70, Y, "ami_road_local"))
    g.road(X0, Y + 1, X0, Y, "ami_road_local")
    for x in STOPS:
        print(g.station(x, Y, "pak256_bus_stop"))
    print(g.sq('local dd=null; foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) '
               'if (d.get_name()=="ami_road_depot") dd=d; '
               f'return command_x.build_depot(player_x(0), {c(X0, Y + 1)}, dd)'))
    g.sq(f"return command_x(tool_add_city).work(player_x(0), {c(200, 200)})")
    for (name, _, _), x in reversed(list(zip(VARIANTS, STOPS))):
        code = (f'local pl=player_x(0); local depot=depot_x({X0},{Y + 1},0); local v=null; '
                f'foreach (d in vehicle_desc_x.get_available_vehicles(wt_road)) if (d.get_name()=="{name}") v=d; '
                f'if (v==null) return "no vehicle"; depot.append_vehicle(pl, convoy_x(0), v); '
                f'local l=depot.get_convoy_list(); local cnv=l[l.len()-1]; '
                f'cnv.change_schedule(pl, schedule_x(wt_road, [schedule_entry_x({c(x, Y)},100,0), schedule_entry_x({c(X0 + 2, Y)},0,0)])); '
                f'depot.start_convoy(pl, cnv); return "ok"')
        print(name, g.sq(code))
    g.sq("debug.set_game_speed(64); return 1")
    for _ in range(900):  # 夏まで進める
        if int(g.sq("return world.get_time().month")) == 5:
            break
        time.sleep(0.5)
    g.sq("debug.set_game_speed(1); return 1")
    for x, name in ((57, "pak256_house_small"), (59, "pak256_shop"), (61, "pak256_house_wide"), (63, "pak256_apartment")):
        print(name, g.sq(f'return command_x(tool_build_house).work(player_x(0), {c(x, Y - 1)}, "00{name}")'))
    g.settle(14)
    print(g.sq('local s=""; foreach (cv in world.get_convoy_list()) { local p=cv.get_pos(); '
               's += cv.get_name()+"@"+p.x+","+p.y+" v="+cv.get_speed()+"; "; } return s'))
    g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump({c(61, Y)}); return 1")
    time.sleep(2)
    g.capture(os.path.join(out, "bigger_z3.png"))
