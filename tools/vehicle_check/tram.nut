// 路面電車の確かめ（#153）。MIT License。tools/vehicle_check/tram_run.py が Game.sq で流す。
// 軌道と車庫の前には AMI の架線（ami_tram_catenary。#189）を張る。
// 先頭に足す変数: OX, OY（コースの西の端）, CARS（1 編成の両数）, CATENARY（0 なら架線なし・1 全部・2 道路の区間と車庫だけ）。街は、この後 tram_cities.nut を公共のプレーヤーで流して置く。
// コース: 道路（ami_road_local）の上に軌道（ami_tram）を敷いた区間（東へ 16 タイル、南へ 8 タイル。角 1 つ）の続きに、
// 土の上の専用の軌道（南へ 6 タイル、東へ 20 タイル、北へ 6 タイル。角 2 つ）をつなぐ。停留所は 2 タイルずつ、道路の区間（西）と
// 専用の区間（東の北へ向かう辺）に置き、車庫は西の端の先（土の上）に置く。1 編成が 2 つの停留所の間を往復する。
local pl = player_x(0);
local s = "";
function r(name, v) { if (v != null) s += name + "=[" + v + "]\n"; }
local way = function(x1, y1, x2, y2, name) { return command_x(tool_build_way).work(pl, coord3d(x1, y1, 0), coord3d(x2, y2, 0), name); };
local TOP = OY, MID = OY + 8, LOW = OY + 14, CX = OX + 16, EX = OX + 36;
// 道路が先、軌道は後に重ねる
r("road1", way(OX, TOP, CX, TOP, "ami_road_local"));
r("road2", way(CX, TOP, CX, MID, "ami_road_local"));
r("tram1", way(OX, TOP, CX, TOP, "ami_tram"));
r("tram2", way(CX, TOP, CX, MID, "ami_tram"));
r("own1", way(CX, MID, CX, LOW, "ami_tram"));
r("own2", way(CX, LOW, EX, LOW, "ami_tram"));
r("own3", way(EX, LOW, EX, MID, "ami_tram"));
// 架線は軌道を敷いた区間ごとに張る。橋・トンネル・高架の架線は無い
local cat = function(x1, y1, x2, y2) { return command_x.build_wayobj(pl, coord3d(x1, y1, 0), coord3d(x2, y2, 0), wayobj_desc_x("ami_tram_catenary")); };
if (CATENARY > 0) {
  r("cat1", cat(OX, TOP, CX, TOP));
  r("cat2", cat(CX, TOP, CX, MID));
}
if (CATENARY == 1) {
  r("cat3", cat(CX, MID, CX, LOW));
  r("cat4", cat(CX, LOW, EX, LOW));
  r("cat5", cat(EX, LOW, EX, MID));
}
// 停留所: 道路の区間（西）と専用の区間（東の北向きの辺）。2 タイルずつ
foreach (p in [[OX + 4, TOP], [OX + 5, TOP], [EX, MID + 1], [EX, MID + 2]]) {
  local e = command_x(tool_build_station).work(pl, coord3d(p[0], p[1], 0), "pak256_tram_stop");
  if (e != null) return s + "stop " + p[0] + "," + p[1] + ": " + e;
}
// 車庫: 西の端の先（土の上）の行き止まり
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_name() == "ami_tram_depot") { depot_desc = d; break; }
}
if (depot_desc == null) return s + "no tram depot";
local dx = OX - 3;
r("depot_way", way(dx, TOP, OX, TOP, "ami_tram"));
local e = command_x.build_depot(pl, coord3d(dx, TOP, 0), depot_desc);
if (e != null) return s + "depot: " + e;
if (CATENARY > 0) r("cat_depot", cat(dx, TOP, OX, TOP));
local depot = depot_x(dx, TOP, 0);
local car = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_tram)) if (v.get_name() == "pak256_tram") car = v;
if (car == null) return s + "no vehicle";
depot.append_vehicle(pl, convoy_x(0), car);
local list = depot.get_convoy_list();
if (list.len() == 0) return s + "vehicle not appended (needs_electrification=" + car.needs_electrification() + ")";
local cnv = list[list.len() - 1];
for (local i = 1; i < CARS; i++) depot.append_vehicle(pl, cnv, car);
cnv.change_schedule(pl, schedule_x(wt_tram, [schedule_entry_x(coord3d(OX + 4, TOP, 0), 0, 0), schedule_entry_x(coord3d(EX, MID + 1, 0), 0, 0)]));
depot.start_convoy(pl, cnv);
s += "two_ways=" + tile_x(OX + 8, TOP, 0).has_two_ways() + " own_two_ways=" + tile_x(OX + 22, LOW, 0).has_two_ways() + "\n";
return s + "ok";
