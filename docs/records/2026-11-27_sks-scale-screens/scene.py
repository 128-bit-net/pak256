"""MIT License。#164 の並べ撮りを 1 回で行う。船 4 隻（pak256 の旅客船・貨物船、SKS フェリー等倍・2 倍）と飛行機 5 機を、名札を消した大きい画面で撮る。
使い方: python -X utf8 scene.py <検証環境> <sks の pak の場所> <出す先（git 管理外）>。先に tools/build.py。mcp_client.py は環境変数 MCP_CLIENT。ポートは 47820。"""
import glob
import os
import sys
import time

env, paks, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")))
import game  # noqa: E402

SHIPS = [("pak256_ferry", 40), ("pak256_cargo_ship", 44), ("sks_ferry_x1", 49), ("sks_ferry_x2", 56)]
PLANES = [("pak256_airliner", 38), ("sks_atr42_x1", 41), ("sks_atr72_x1", 44), ("sks_atr42_x2", 47), ("sks_atr72_x2", 50)]

SEA = r'''
local pu = player_x(1), pl = player_x(0), s = "";
for (local y = 60; y <= 68; y++) for (local x = 20; x <= 80; x++) command_x.grid_lower(pu, coord3d(x, y, 0));
command_x(tool_change_water_height).work(pu, coord3d(50, 64, -1), "1");
foreach (x in [40, 44, 49, 56]) {
  local g = square_x(x, 59).get_ground_tile();
  local e = command_x(tool_build_station).work(pl, coord3d(x, 59, g.z), "pak256_pier");
  if (e != null) s += "pier" + x + "=" + e + " ";
}
command_x(tool_add_city).work(pu, coord3d(60, 40, 0));
local names = ["pak256_house_small", "pak256_apartment", "pak256_office", "pak256_warehouse", "pak256_store", "pak256_townhall", "pak256_house_wide"];
local i = 0, ok = 0;
foreach (y in [58, 56]) for (local x = 30; x <= 66; x += 2) {
  if (y == 58 && (x == 40 || x == 44 || x == 56)) continue;
  if (command_x(tool_build_house).work(pu, coord3d(x, y, square_x(x, y).get_ground_tile().z), "00" + names[i % names.len()]) == null) ok++;
  i++;
}
local dd = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_canal_depot") dd = d;
local e = command_x.build_depot(pl, coord3d(21, 60, -1), dd);
if (e != null) s += "depot=" + e;
return s + " houses=" + ok;
'''

AIR = r'''
local pl = player_x(0), s = "";
function way(a, b, name) { local e = command_x(tool_build_way).work(player_x(0), a, b, name); return e == null ? "" : "[" + name + ": " + e + "]"; }
local y = 130;
s += way(coord3d(30, y, 0), coord3d(70, y, 0), "pak256_runway");
s += way(coord3d(32, y + 3, 0), coord3d(68, y + 3, 0), "pak256_taxiway");
s += way(coord3d(32, y + 3, 0), coord3d(32, y, 0), "pak256_taxiway");
s += way(coord3d(68, y + 3, 0), coord3d(68, y, 0), "pak256_taxiway");
foreach (x in [38, 41, 44, 47, 50, 60]) {
  s += way(coord3d(x, y + 3, 0), coord3d(x, y + 5, 0), "pak256_taxiway");
  local e = command_x(tool_build_station).work(pl, coord3d(x, y + 5, 0), "pak256_airport");
  if (e != null) s += "stop" + x + ":" + e;
}
s += way(coord3d(64, y + 3, 0), coord3d(64, y + 5, 0), "pak256_taxiway");
local dd = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "pak256_hangar") dd = d;
local e = command_x.build_depot(pl, coord3d(64, y + 5, 0), dd);
if (e != null) s += "depot:" + e;
command_x(tool_add_city).work(player_x(1), coord3d(50, 118, 0));
local names = ["pak256_house_small", "pak256_apartment", "pak256_office", "pak256_warehouse", "pak256_store", "pak256_townhall", "pak256_house_wide"];
local i = 0;
foreach (yy in [138, 140]) for (local x = 34; x <= 56; x += 2) {
  command_x(tool_build_house).work(player_x(1), coord3d(x, yy, 0), "00" + names[i % names.len()]);
  i++;
}
return s + " ok";
'''

START = r'''
local pl = player_x(0), s = "", vs = {};
foreach (v in vehicle_desc_x.get_available_vehicles(WT)) vs[v.get_name()] <- v;
for (local k = LIST.len() - 1; k >= 0; k--) {
  try {
    local d = depot_x(DX, DY, DZ);
    d.append_vehicle(pl, convoy_x(0), vs[LIST[k]]);
    local l = d.get_convoy_list(); local c = l[l.len() - 1];
    c.change_schedule(pl, schedule_x(WT, [schedule_entry_x(coord3d(STOPS[k], SY, DZ), 100, 0), schedule_entry_x(coord3d(EX, EY, DZ), 0, 0)]));
    d.start_convoy(pl, c);
  } catch (x) { s += LIST[k] + ":" + x + " "; }
}
return s + "ok";
'''
POS = 'local s = ""; foreach (c in world.get_convoy_list()) { local p = c.get_pos(); s += p.x + "," + p.y + " "; } return s;'


def head(wt_name, items, dx, dy, dz, sy, ex, ey):
    names = ", ".join(f'"{n}"' for n, _ in items)
    stops = ", ".join(str(x) for _, x in items)
    return (f"local WT = {wt_name}; local LIST = [{names}]; local STOPS = [{stops}]; local DX = {dx}, DY = {dy}, DZ = {dz};"
            f" local SY = {sy}, EX = {ex}, EY = {ey};")


def flat(s):
    return "\n".join(line for line in s.splitlines() if line.strip())


with game.Game(env, "flat_512_left_v64", 47820, extra_paks=glob.glob(os.path.join(paks, "*.pak")),
               screensize="2800x1600", simuconf_extra=["show_names = 0"]) as g:
    def run(code, **kw):
        tmp = os.path.join(out, "_tmp.nut")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(code)
        print(g.sq_file(tmp, **kw), flush=True)

    def shot(name, x, y, z, zoom=3):
        g.sq(f"gui.close_all_windows(); gui.set_zoom({zoom}); gui.jump(coord3d({x},{y},{z})); return 1")
        time.sleep(4)
        g.capture(os.path.join(out, name + ".png"))

    run(SEA, timeout=120)
    run(AIR, timeout=120)
    g.settle(25)
    run(head("wt_water", SHIPS, 21, 60, -1, 60, 76, 64) + START, timeout=90)
    run(head("wt_air", PLANES, 64, 135, 0, 135, 60, 135) + START, timeout=90)
    g.sq("debug.set_game_speed(64); return 1")
    time.sleep(60)
    g.sq("debug.set_game_speed(1); return 1")
    time.sleep(10)
    print("[pos]", g.sq(POS), flush=True)
    for z in (5, 6, 7):
        shot(f"ships_z{z}", 49, 60, -1, z)
        shot(f"planes_z{z}", 45, 135, 0, z)
    shot("ships_all", 48, 59, -1)
    shot("planes_all", 44, 135, 0)
    for n, x in SHIPS:
        shot("ship_" + n, x, 60, -1)
    for n, x in PLANES:
        shot("plane_" + n, x, 135, 0)
if g.left_over:
    sys.exit(1)
