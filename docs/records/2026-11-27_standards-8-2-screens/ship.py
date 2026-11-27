"""MIT License。#176: length 64 の船の形の箱を 2 隻（基準点が船首の先・船の中ほど）走らせて撮る。

使い方: python -X utf8 ship.py <検証環境> <build_test.py の出す先> <撮る場所（git 管理外）> <ポート> [<描画のスレッドの数>]。先に tools/build.py。
海を掘り、八角形の順に経由地を回らせて 8 方向を出す。撮るのは、前の撮影と違う向き（直前の位置との差）になったとき。
"""
import glob
import os
import sys
import time

env, t8, out, port = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
# 5 つ目に描画のスレッドの数を渡すと、simuconf.tab の threads を足す（省くと本体の既定 = 画面を縦の帯に分けて描く）
EXTRA = ["show_names = 0"] + ([f"threads = {int(sys.argv[5])}"] if len(sys.argv) > 5 else [])
os.makedirs(out, exist_ok=True)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")))
from game import Game  # noqa: E402

# 一度に掘ると本体の Squirrel が打ち切られるので、4 行ずつ掘ってから水を入れる
DIG = 'for (local y = {y0}; y < {y0} + 4; y++) for (local x = 30; x <= 66; x++) command_x.grid_lower(player_x(1), coord3d(x, y, 0)); return 1'
WATER = 'return "" + command_x(tool_change_water_height).work(player_x(1), coord3d(50, 50, -1), "1")'
# 水を入れた後に西の脇を掘ると、水面と同じ高さの平らな岸になる。そこに運河を引いて行き止まりに車庫を置く
SHORE = 'for (local y = 42; y <= 48; y++) for (local x = 26; x <= 29; x++) command_x.grid_lower(player_x(1), coord3d(x, y, 0)); return 1'
DEPOT = '''
local s = "canal=" + command_x(tool_build_way).work(player_x(0), coord3d(30, 45, -1), coord3d(28, 45, -1), "ami_canal");
local dd = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_canal_depot") dd = d;
return s + " depot=" + command_x.build_depot(player_x(0), coord3d(28, 45, -1), dd);
'''
# 八角形の頂点（西の辺から時計回り）。直線 4 本と斜め 4 本で 8 方向
ROUTE = [(40, 36), (54, 36), (62, 44), (62, 54), (54, 62), (44, 62), (36, 54), (36, 44)]


def start(name):
    entries = ", ".join(f"schedule_entry_x(coord3d({x},{y},-1), 0, 0)" for x, y in ROUTE)
    return (f'local pl = player_x(0); local d = depot_x(28, 45, -1); local v = null;'
            f' foreach (c in vehicle_desc_x.get_available_vehicles(wt_water)) if (c.get_name() == "{name}") v = c;'
            f' if (v == null) return "no {name}";'
            f' d.append_vehicle(pl, convoy_x(0), v); local l = d.get_convoy_list(); local c = l[l.len() - 1];'
            f' c.change_schedule(pl, schedule_x(wt_water, [{entries}])); d.start_convoy(pl, c); return "started {name}"')


POS = 'local s = ""; foreach (c in world.get_convoy_list()) { local p = c.get_pos(); s += p.x + " " + p.y + ";"; } return s'
for name in ("t8_ship_bow", "t8_ship_mid"):
    with Game(env, "flat_512_left_v64", port, extra_paks=glob.glob(os.path.join(t8, "pak", "*.pak")),
              simuconf_extra=EXTRA) as g:
        for y0 in range(30, 68, 4):
            g.sq(DIG.format(y0=y0), timeout=90, player_nr=1)
        print(g.sq(WATER, timeout=90, player_nr=1), flush=True)
        g.sq(SHORE, timeout=90, player_nr=1)
        print(g.sq(DEPOT, timeout=90), flush=True)
        print(g.sq(start(name), timeout=60), flush=True)
        g.sq("debug.set_game_speed(4); gui.set_zoom(5); return 1")
        prev, seen, t0 = None, {}, time.time()
        while time.time() - t0 < 200 and len(seen) < 8:
            time.sleep(1.5)
            row = [r for r in g.sq(POS).split(";") if r]
            if not row:
                continue
            x, y = (int(v) for v in row[0].split())
            if prev and (x, y) != prev:
                d = ((x > prev[0]) - (x < prev[0]), (y > prev[1]) - (y < prev[1]))
                if d == seen.get("_last") and d not in seen and y >= 36:  # 同じ向きが 2 回続いたら撮る
                    g.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},-1)); return 1")
                    time.sleep(0.4)
                    path = os.path.join(out, f"{name}_{d[0]}_{d[1]}.png")
                    g.capture(path)
                    seen[d] = (x, y)
                    print("[shot]", name, d, x, y, flush=True)
                seen["_last"] = d
            prev = (x, y)
        print("[done]", name, [k for k in seen if k != "_last"], flush=True)
    if g.left_over:
        sys.exit(1)
