// α0.2 の確かめ（#45）。MIT License。tools/game.py の Game.sq_file で流す。借り物は無し（pak256 の車庫・停留所・バス・石炭のトラックだけ）。
// 先頭に足す変数: WAY（道路の名前）。
// 配置: 東西の道（y=60、x=50〜150）の北に、街 A（60,57）・B（100,57）と炭鉱（118,57。2x2）・発電所（138,57。3x3）。
// バス停を A・B の道の上、トラックの荷役所を炭鉱・発電所の脇の道の上に置く。車庫は道の南の脇（125,61）。
// 人口は足さない。バス 1 台（A と B のバス停の間）と石炭のトラック 1 台（炭鉱と発電所の荷役所の間）を出す。
local pl = player_x(0);
local s = "";
function r(name, v) { s += name + "=[" + v + "]\n"; }
local ax = 60, ay = 60, bx = 100, by = 60;

r("road", command_x(tool_build_way).work(pl, coord3d(ax - 10, ay, 0), coord3d(150, ay, 0), WAY));
r("cityA", command_x(tool_add_city).work(pl, coord3d(ax, ay - 3, 0)));
r("cityB", command_x(tool_add_city).work(pl, coord3d(bx, by - 3, 0)));
r("mine", command_x(tool_build_factory).work(pl, coord3d(118, 57, 0), "0050,pak256_coal_mine"));
r("plant", command_x(tool_build_factory).work(pl, coord3d(138, 57, 0), "0050,pak256_coal_kraftwerk"));
r("link", command_x(tool_link_factory).work(pl, coord3d(118, 57, 0), coord3d(138, 57, 0), ""));
r("stop_mine", command_x(tool_build_station).work(pl, coord3d(119, 60, 0), "pak256_truck_stop"));
r("stop_plant", command_x(tool_build_station).work(pl, coord3d(139, 60, 0), "pak256_truck_stop"));

// バス停: 各街の中心の真南の道の上（置けなければ隣のタイル）
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
return s + "ok";
