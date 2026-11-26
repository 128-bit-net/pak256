"""鉄道は pak128.Japan の 2 倍、自動車は pak128 の 2 倍の大きさ（1 タイルの幅に対する割合を手本と同じ）の試し絵を作り、
寸法を測って、今の車両と並べてゲームで撮る（#104）。MIT License。

使い方: python -X utf8 bigger2.py <検証環境> <ポート> <出力フォルダ（git 管理外）>   （先に tools/build.py。makeobj は PATH か MAKEOBJ）
検証環境に "-" を渡すと、絵を作って測るだけでゲームは起動しない。試し絵は出力フォルダにだけ書き、素材は変えない。
"""
import argparse
import copy
import importlib.util
import os
import subprocess
import sys
import time

from PIL import Image

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


def load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, *path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


dv = load("draw_vehicles", "objects", "vehicle", "road", "draw_vehicles.py")
dt = load("draw_trains", "objects", "vehicle", "rail", "draw_trains.py")
V = dv.V
PX_Z = V.PX_PER_M_Z

# 手本の画面の px を 2 倍した目標（長さ, 幅, 高さ）。手本は vehicle_sizes.py の表の値
TARGET = {
    "bus": (100, 22, 24),     # pak128 の路線バス 2 種（49,11,12 と 51,11,12）の平均の 2 倍
    "mail": (68, 24, 22),     # pak128 の Mail_Truck_2（34,12,11。今の値の手本）の 2 倍
    "coal": (86, 22, 28),     # pak128 の Bulk_Truck_2（43,11,14。今の値の手本）の 2 倍
    "rail": (132, 28, 24),    # pak128.Japan の yoshi_kiha35_m（66,14,12）の 2 倍
}
# 試し絵の length（単位）。車体は length × 1.65m に描くので、画面の長さは length × 約 11.3px
LENGTH = {"bus": 9, "mail": 6, "coal": 8, "rail": 12}
# 幅と高さの倍率（今の絵に掛ける。測った値が目標に合うように決めた）
FACTOR = {"bus": (1.22, 1.30), "mail": (1.62, 1.18), "coal": (1.22, 1.87), "rail": (1.40, 1.20)}


def road_spec(name):
    return copy.deepcopy(next(s for s in dv.VEHICLES if s["name"] == name))


def road_mock(key, base):
    kw, kh = FACTOR[key]
    s = road_spec(base)
    length = LENGTH[key]
    s.update(name=f"mock2x_{key}", stem=f"mock2x_{key}", width_m=s["width_m"] * kw, real_length_m=length * V.M_PER_UNIT)
    if s["style"] == "boxes":  # 石炭のトラック: 箱の前後を新しい長さに、幅を倍率に合わせる（運転席は 1.3 倍の長さ）
        total, old = length * V.M_PER_UNIT, V.length_units(dv.COAL_REAL_LENGTH_M) * V.M_PER_UNIT
        cab_old, cab = dv.CAB_M, dv.CAB_M * 1.3

        def move(x):  # 後ろ向きに負。運転席の部分と荷台の部分を別々に伸ばす
            if -x <= cab_old:
                return x * cab / cab_old
            return -(cab + (-x - cab_old) * (total - cab) / (old - cab_old))

        for k in ("boxes_empty", "boxes_loaded"):
            s[k] = tuple((move(p[0]), move(p[1]), p[2] * kw) + p[3:] for p in s[k])
    V.PX_PER_M_Z = PX_Z * kh
    sheet = dv.draw_sheet(s)
    V.PX_PER_M_Z = PX_Z
    return s, sheet, dv.yaml_lines(s), 256


def rail_mock(base):
    kw, kh = FACTOR["rail"]
    s = copy.deepcopy(next(v for v in dt.VEHICLES if v["name"] == base))
    name = base.replace("pak256_", "mock2x_")
    s.update(name=name, stem=name)
    width, bogie = dt.WIDTH_M, dt.BOGIE_WIDTH_M
    dt.WIDTH_M, dt.BOGIE_WIDTH_M, V.PX_PER_M_Z = width * kw, bogie * kw, PX_Z * kh
    sheet = dt.draw_sheet(s)
    text = dt.yaml_lines(s).replace("pak256_railcar", "mock2x_railcar")
    dt.WIDTH_M, dt.BOGIE_WIDTH_M, V.PX_PER_M_Z = width, bogie, PX_Z
    return s, sheet, text, 512


def to_dat(text):
    """表の yaml（描くスクリプトが書く形だけ）を dat にする。"""
    import yaml
    dat = []
    for k, v in yaml.safe_load(text).items():
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if isinstance(v2, dict):
                    dat += [f"{k}[{k2}][{k3}]={v3}" for k3, v3 in v2.items()]
                else:
                    dat.append(f"{k}[{k2}]={v2}")
        else:
            dat.append(f"{k}={v}")
    return "\n".join(dat) + "\n"


def sizes(sheet, cell):
    """シートの sw（列 2）と se（列 3）の外接枠から、長さ・幅・高さ（vehicle_sizes.py と同じ測り方）。"""
    def box(col):
        part = sheet.crop((col * cell, 0, (col + 1) * cell, cell))
        return part.getchannel("A").point(lambda v: 255 if v > 127 else 0).getbbox()
    sw, se = box(V.DIRECTIONS.index("sw")), box(V.DIRECTIONS.index("se"))
    length, width = sw[2] - sw[0], se[2] - se[0]
    return length, width, round(sw[3] - sw[1] - width / 2)


MOCKS = [("bus", road_mock("bus", "pak256_bus")), ("mail", road_mock("mail", "pak256_mail_truck")),
         ("coal", road_mock("coal", "pak256_coal_truck")), ("rail", rail_mock("pak256_railcar")),
         ("rail", rail_mock("pak256_railcar_trailer"))]
extra = []
with open(os.path.join(out, "sizes.log"), "w", encoding="utf-8", newline="\n") as log_:
    for key, (s, sheet, text, cell) in MOCKS:
        name = s["name"]
        L, W, H = sizes(sheet, cell)
        line = (f"{name} length={LENGTH[key]} 長さ {L}px 幅 {W}px 高さ {H}px（{L / 256:.0%} {W / 256:.0%} {H / 256:.0%}）"
                f" 目標 {TARGET[key]}")
        print(line)
        log_.write(line + "\n")
        sheet.save(os.path.join(out, s["stem"] + ".png"))
        with open(os.path.join(out, name + ".dat"), "w", encoding="utf-8", newline="\n") as f:
            f.write(to_dat(text))
        pak = f"vehicle.{name}.pak"
        r = subprocess.run([os.environ.get("MAKEOBJ", "makeobj"), "pak256", pak, name + ".dat"], cwd=out,
                           capture_output=True)
        msg = (r.stdout + r.stderr).decode("utf-8", errors="replace")
        if r.returncode or "Warning" in msg or "ERROR" in msg:
            sys.exit(msg)
        extra.append(os.path.join(out, pak))
if a.env == "-":
    sys.exit(0)

_day_night_off = game.append_day_night_off


def _no_names(simuconf):
    _day_night_off(simuconf)
    with open(simuconf, "a", encoding="utf-8") as f:
        f.write("show_names = 0" + chr(10))


game.append_day_night_off = _no_names

ROAD, RAIL, X0 = "ami_road_local", "ami_rail_ballast", 50
# (道路の y, [(停留所の x, 停留所, 車両)])
ROADS = [
    (60, [(58, "pak256_bus_stop", "pak256_bus"), (60, "pak256_bus_stop", "mock2x_bus"),
          (62, "pak256_bus_stop", "pak256_mail_truck"), (64, "pak256_bus_stop", "mock2x_mail")]),
    (66, [(59, "pak256_truck_stop", "pak256_coal_truck"), (62, "pak256_truck_stop", "mock2x_coal")]),
]
# (線路の y, 駅の西の端の x, 編成)
RAILS = [
    (72, 56, ["pak256_railcar", "pak256_railcar_trailer"]),
    (74, 60, ["mock2x_railcar", "mock2x_railcar_trailer"]),
]
BUILDINGS = [(57, 59, "pak256_house_small"), (59, 59, "pak256_shop"), (61, 59, "pak256_house_wide"),
             (63, 59, "pak256_apartment"), (58, 65, "pak256_workshop"), (61, 65, "pak256_house_wide"),
             (57, 71, "pak256_row_house"), (61, 71, "pak256_store")]


def c(x, y):
    return f"coord3d({x},{y},0)"


def depot(g, name, x, y, way):
    g.road(x, y + 1, x, y, way)
    r = g.sq(f'local dd=null; foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) '
             f'if (d.get_name()=="{name}") dd=d; return command_x.build_depot(player_x(0), {c(x, y + 1)}, dd)')
    print("depot", y, r)


def convoy(g, wt, dep_y, stop, names):
    adds = " ".join(
        f'v=null; foreach (d in vehicle_desc_x.get_available_vehicles({wt})) if (d.get_name()=="{n}") v=d; '
        f'if (v==null) return "no vehicle {n}"; depot.append_vehicle(pl, cnv, v); '
        f'if ({i}==0) {{ local l=depot.get_convoy_list(); cnv=l[l.len()-1]; }}'
        for i, n in enumerate(names))
    code = (f"local pl=player_x(0); local depot=depot_x({X0},{dep_y},0); local cnv=convoy_x(0); local v=null; {adds} "
            f"cnv.change_schedule(pl, schedule_x({wt}, [schedule_entry_x({c(*stop)},100,0), "
            f"schedule_entry_x({c(X0 + 2, stop[1])},0,0)])); depot.start_convoy(pl, cnv); return \"ok\"")
    print(names, g.sq(code, timeout=60))


with game.Game(a.env, "flat_512_left_v64", a.port, extra_paks=extra) as g:
    for y, stops in ROADS:
        print(g.road(X0, y, 72, y, ROAD))
        for x, stop, _ in stops:
            print(g.station(x, y, stop))
        depot(g, "ami_road_depot", X0, y, ROAD)
    for y, x0, _ in RAILS:
        print(g.road(X0, y, 72, y, RAIL))
        for x in range(x0, x0 + 3):
            print(g.station(x, y, "pak256_train_station"))
        depot(g, "ami_rail_depot", X0, y, RAIL)
    g.sq(f"return command_x(tool_add_city).work(player_x(0), {c(200, 200)})")
    for y, stops in ROADS:
        for x, _, name in reversed(stops):
            convoy(g, "wt_road", y + 1, (x, y), [name])
    for y, x0, names in RAILS:
        convoy(g, "wt_rail", y + 1, (x0 + 1, y), names)
    g.settle(25)
    g.sq("debug.set_game_speed(64); return 1")
    for _ in range(900):  # 夏まで進める
        if int(g.sq("return world.get_time().month")) == 5:
            break
        time.sleep(0.5)
    g.sq("debug.set_game_speed(1); return 1")
    for x, y, name in BUILDINGS:
        print(name, g.sq(f'return command_x(tool_build_house).work(player_x(0), {c(x, y)}, "00{name}")'))
    g.settle(14)
    print(g.sq('local s=""; foreach (cv in world.get_convoy_list()) { local p=cv.get_pos(); '
               's += cv.get_name()+"@"+p.x+","+p.y+" v="+cv.get_speed()+"; "; } return s'))
    for name, x, y in (("road", 61, 59), ("coal", 61, 65), ("rail", 60, 72)):
        g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump({c(x, y)}); return 1")
        time.sleep(2)
        g.capture(os.path.join(out, f"{name}_z3.png"))
        print("shot", name)
