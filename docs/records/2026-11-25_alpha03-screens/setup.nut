// α0.3 の確かめ（#70）。MIT License。tools/game.py の Game.sq_file で流す。借り物は無し。
// 先頭に足す変数: WAY（道路の名前）, RWAY（線路の名前）。
// 道路: 東西の道（y=60、x=50〜150）の北に街 A（60,57）・B（100,57）と炭鉱（118,57）・発電所（138,57）。バス 1 台・石炭のトラック 1 台。人口は足さない。
// 線路: 東西の線路（y=110、x=40〜100）。駅 2 つ（3 タイルずつ）、中ほどの南の脇に車庫、気動車 + 付随車の 1 編成が往復する。
//       線路の北に街 2 つ（48,106 と 92,106）を置き、人口を change_size(300) で足す（旅客を出すため）。
local pl = player_x(0);
local s = "";
function r(name, v) { s += name + "=[" + v + "]\n"; }
local ax = 60, ay = 60, bx = 100, by = 60;

// ---- 道路 ----
r("road", command_x(tool_build_way).work(pl, coord3d(ax - 10, ay, 0), coord3d(150, ay, 0), WAY));
r("cityA", command_x(tool_add_city).work(pl, coord3d(ax, ay - 3, 0)));
r("cityB", command_x(tool_add_city).work(pl, coord3d(bx, by - 3, 0)));
r("mine", command_x(tool_build_factory).work(pl, coord3d(118, 57, 0), "0050,pak256_coal_mine"));
r("plant", command_x(tool_build_factory).work(pl, coord3d(138, 57, 0), "0050,pak256_coal_kraftwerk"));
r("link", command_x(tool_link_factory).work(pl, coord3d(118, 57, 0), coord3d(138, 57, 0), ""));
r("stop_mine", command_x(tool_build_station).work(pl, coord3d(119, 60, 0), "pak256_truck_stop"));
r("stop_plant", command_x(tool_build_station).work(pl, coord3d(139, 60, 0), "pak256_truck_stop"));
local T = [];
foreach (cx in [ax, bx]) {
  foreach (dx in [0, 1, -1, 2, -2, 3, -3]) {
    local e = command_x(tool_build_station).work(pl, coord3d(cx + dx, ay, 0), "pak256_bus_stop");
    if (e == null) { T.append(coord3d(cx + dx, ay, 0)); s += "bus stop " + (cx + dx) + "," + ay + "\n"; break; }
    s += "stop " + (cx + dx) + ": " + e + "\n";
  }
}
if (T.len() != 2) return s + "stops failed";
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_waytype() == wt_road) { depot_desc = d; break; }
}
if (depot_desc == null) return s + "no road depot";
r("depot_road", command_x(tool_build_way).work(pl, coord3d(125, 60, 0), coord3d(125, 61, 0), WAY));
r("depot", command_x.build_depot(pl, coord3d(125, 61, 0), depot_desc));
s += "depot desc=" + depot_desc.get_name() + "\n";
local depot = depot_x(125, 61, 0);
local pick = function(name) { foreach (v in vehicle_desc_x.get_available_vehicles(wt_road)) if (v.get_name() == name) return v; return null; };
local go = function(name, entries) {
  local v = pick(name);
  if (v == null) { s += "no vehicle " + name + "\n"; return; }
  depot.append_vehicle(pl, convoy_x(0), v);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  cnv.change_schedule(pl, schedule_x(wt_road, entries));
  depot.start_convoy(pl, cnv);
  s += "[convoy] " + name + "\n";
};
go("pak256_bus", [schedule_entry_x(T[0], 0, 0), schedule_entry_x(T[1], 0, 0)]);
go("pak256_coal_truck", [schedule_entry_x(coord3d(119, 60, 0), 20, 0), schedule_entry_x(coord3d(139, 60, 0), 0, 0)]);

// ---- 線路 ----
local OX = 40, OY = 110, L = 60;
r("track", command_x(tool_build_way).work(pl, coord3d(OX, OY, 0), coord3d(OX + L, OY, 0), RWAY));
r("rcityA", command_x(tool_add_city).work(pl, coord3d(OX + 8, OY - 4, 0)));
r("rcityB", command_x(tool_add_city).work(pl, coord3d(OX + L - 8, OY - 4, 0)));
foreach (c in city_list_x()) { if (c.get_pos().y > 90) c.change_size(300); }
local A = OX + 6, B = OX + L - 8;
foreach (x0 in [A, B]) {
  for (local i = 0; i < 3; i++) {
    local e = command_x(tool_build_station).work(pl, coord3d(x0 + i, OY, 0), "pak256_train_station");
    if (e != null) return s + "station " + (x0 + i) + ": " + e;
  }
}
local rdesc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_waytype() == wt_rail && d.get_name() == "ami_rail_depot") { rdesc = d; break; }
}
if (rdesc == null) return s + "no rail depot";
local dx = OX + L / 2;
r("rdepot_way", command_x(tool_build_way).work(pl, coord3d(dx, OY + 1, 0), coord3d(dx, OY, 0), RWAY));
local e = command_x.build_depot(pl, coord3d(dx, OY + 1, 0), rdesc);
if (e != null) return s + "rail depot: " + e;
local rdepot = depot_x(dx, OY + 1, 0);
local car = null, tr = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail)) {
  if (v.get_name() == "pak256_railcar") car = v;
  if (v.get_name() == "pak256_railcar_trailer") tr = v;
}
if (car == null || tr == null) return s + "no rail vehicles";
rdepot.append_vehicle(pl, convoy_x(0), car);
local rl = rdepot.get_convoy_list();
local rc = rl[rl.len() - 1];
rdepot.append_vehicle(pl, rc, tr);
rc.change_schedule(pl, schedule_x(wt_rail, [schedule_entry_x(coord3d(A + 1, OY, 0), 0, 0), schedule_entry_x(coord3d(B + 1, OY, 0), 0, 0)]));
rdepot.start_convoy(pl, rc);
s += "[convoy] rail\n";
return s + "ok";
