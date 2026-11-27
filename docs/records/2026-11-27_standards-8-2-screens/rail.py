"""MIT License。#176: 線路の斜め・分岐・2 段の坂と、路面電車の坂の見え方を撮る。

使い方: python -X utf8 rail.py <検証環境> <撮る場所（git 管理外）> <ポート>。先に tools/build.py。
コース（OX, OY が西北の角）:
- 北の辺（y=OY）: 高さ 2 の丘。地面を 1 マスごとに 1 段ずつ上げ下げする（1 段の坂が 2 つ続く）。
- 東の辺から南西へ向かう階段（斜め）。南の辺（y=OY+14）の x=OX+10 で南へ分かれる分岐。
- 路面電車（OY+30）: 道路（ami_road_local）に重ねた軌道と専用の軌道（ami_tram）に、高さ 1 の丘が 1 つずつ。
"""
import os
import sys
import time

env, out, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.makedirs(out, exist_ok=True)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")))
from game import Game  # noqa: E402

OX, OY, TY = 40, 40, 70
COMMON = r'''
local pl = player_x(0), s = "";
function r(name, v) { if (v != null) s += name + "=[" + v + "] "; }
function z(x, y) { return square_x(x, y).get_ground_tile().z; }
function raise(x0, x1, y) { for (local x = x0; x <= x1; x++) foreach (yy in [y, y + 1]) r("raise" + x + "," + yy, command_x.grid_raise(player_x(0), coord3d(x, yy, z(x, yy)))); }
function lay(x0, y0, x1, y1, way) {
  local dx = x1 > x0 ? 1 : (x1 < x0 ? -1 : 0), dy = y1 > y0 ? 1 : (y1 < y0 ? -1 : 0), x = x0, y = y0;
  while (x != x1 || y != y1) {
    r("lay" + x + "," + y, command_x(tool_build_way).work(player_x(0), coord3d(x, y, z(x, y)), coord3d(x + dx, y + dy, z(x + dx, y + dy)), way));
    x += dx; y += dy;
  }
}
function run(wt, dep, vehicles, stops) {
  local depot = depot_x(dep.x, dep.y, dep.z), cnv = null;
  foreach (name in vehicles) {
    local d = null;
    foreach (v in vehicle_desc_x.get_available_vehicles(wt)) if (v.get_name() == name) d = v;
    depot.append_vehicle(player_x(0), cnv == null ? convoy_x(0) : cnv, d);
    local l = depot.get_convoy_list(); cnv = l[l.len() - 1];
  }
  local e = [];
  foreach (p in stops) e.append(schedule_entry_x(coord3d(p[0], p[1], 0), 0, 0));
  cnv.change_schedule(player_x(0), schedule_x(wt, e));
  depot.start_convoy(player_x(0), cnv);
}
function depot_at(x, y, name, way) {
  local d = null;
  foreach (b in building_desc_x.get_building_list(building_desc_x.depot)) if (b.get_name() == name) d = b;
  lay(x, y + 1, x, y, way);
  r("depot", command_x.build_depot(player_x(0), coord3d(x, y + 1, 0), d));
}
'''

RAIL = COMMON + f'''
local OX = {OX}, OY = {OY}, W = "ami_rail_ballast";
// 丘: 外側から 1 段、内側をもう 1 段
raise(OX + 15, OX + 22, OY);
raise(OX + 16, OX + 21, OY);
lay(OX, OY, OX + 30, OY, W);
lay(OX + 30, OY, OX + 30, OY + 6, W);
for (local i = 0; i < 8; i++) {{
  lay(OX + 30 - i, OY + 6 + i, OX + 29 - i, OY + 6 + i, W);
  lay(OX + 29 - i, OY + 6 + i, OX + 29 - i, OY + 7 + i, W);
}}
lay(OX + 22, OY + 14, OX, OY + 14, W);
lay(OX + 10, OY + 14, OX + 10, OY + 20, W);
foreach (p in [[2, 0], [3, 0], [4, 0], [2, 14], [3, 14], [4, 14]]) r("st", command_x(tool_build_station).work(pl, coord3d(OX + p[0], OY + p[1], 0), "pak256_train_station"));
foreach (p in [[10, 18], [10, 19], [10, 20]]) r("st", command_x(tool_build_station).work(pl, coord3d(OX + p[0], OY + p[1], 0), "pak256_train_station"));
depot_at(OX + 8, OY, "ami_rail_depot", W);
run(wt_rail, coord3d(OX + 8, OY + 1, 0), ["pak256_railcar", "pak256_railcar_trailer"],
    [[OX + 3, OY], [OX + 10, OY + 19], [OX + 3, OY], [OX + 3, OY + 14]]);
local h = ""; for (local x = OX + 13; x <= OX + 24; x++) h += z(x, OY) + "/" + tile_x(x, OY, z(x, OY)).get_slope() + " ";
return s + "heights: " + h;
'''

TRAM = COMMON + f'''
local OX = {OX}, TY = {TY};
raise(OX + 12, OX + 15, TY);   // 道路に重ねた軌道の丘
raise(OX + 28, OX + 31, TY);   // 専用の軌道の丘
lay(OX, TY, OX + 20, TY, "ami_road_local");
lay(OX, TY, OX + 40, TY, "ami_tram");
foreach (x in [2, 3, 37, 38]) r("st", command_x(tool_build_station).work(pl, coord3d(OX + x, TY, 0), "pak256_tram_stop"));
depot_at(OX + 7, TY, "ami_tram_depot", "ami_tram");
run(wt_tram, coord3d(OX + 7, TY + 1, 0), ["pak256_tram"], [[OX + 2, TY], [OX + 38, TY]]);
return s + "ok";
'''

# 撮る場所: (名前, 中心のタイル, 近さ, 編成の番号)。編成は線路（0）、路面電車（1）の順
SPOTS = [
    ("slope_up", (OX + 15, OY), 1, 0), ("slope_top", (OX + 18, OY), 1, 0), ("slope_down", (OX + 22, OY), 1, 0),
    ("diagonal", (OX + 26, OY + 10), 2, 0), ("switch", (OX + 10, OY + 14), 1, 0), ("branch", (OX + 10, OY + 16), 1, 0),
    ("tram_road_up", (OX + 12, TY), 1, 1), ("tram_road_down", (OX + 16, TY), 1, 1),
    ("tram_own_up", (OX + 28, TY), 1, 1), ("tram_own_down", (OX + 32, TY), 1, 1),
]
POS = 'local s = ""; foreach (c in world.get_convoy_list()) { local p = c.get_pos(); s += p.x + " " + p.y + " " + p.z + ";"; } return s'

with Game(env, "flat_512_left_v64", port, simuconf_extra=["show_names = 0"]) as g:
    for name, code in (("rail", RAIL), ("tram", TRAM)):
        tmp = os.path.join(out, name + ".nut")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"[{name}]", g.sq_file(tmp, timeout=120), flush=True)
    g.settle(25)
    g.sq("debug.set_game_speed(2); gui.set_zoom(3); return 1")
    done, t0 = {}, time.time()
    while time.time() - t0 < 420:
        rows = [tuple(int(v) for v in r.split()) for r in g.sq(POS).split(";") if r]
        for name, (sx, sy), near, k in SPOTS:
            if k >= len(rows):
                continue
            x, y, z = rows[k]
            if abs(x - sx) <= near and abs(y - sy) <= near and done.get(name, (0, None))[1] != (x, y) and done.get(name, (0, None))[0] < 4:
                n = done.get(name, (0, None))[0]
                g.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},{z})); return 1")
                g.capture(os.path.join(out, f"{name}_{n}_{x}_{y}.png"))
                done[name] = (n + 1, (x, y))
                print("[shot]", name, n, x, y, z, flush=True)
        if len(done) == len(SPOTS) and all(v[0] >= 4 for v in done.values()):
            break
        time.sleep(0.1)
    print("[done]", {k: v[0] for k, v in done.items()}, flush=True)
if g.left_over:
    sys.exit(1)
