// 街の成長の確かめ（#30）。#41 の setup.nut から、人口を足す行を外した。MIT License.
// 先頭に足す変数: WAY（道路の名前）, DEPOT（車庫の名前）, NOBUS（true なら車両を出さない）, NOSTOP（true なら停留所も置かない。比較用）。街を 2 つ置いて道でつなぎ、道の上にバス停を置いて、バスとトラックを走らせる。
local pl = player_x(0);
local s = "";
function r(name, v) { if (v != null) s += name + "=[" + v + "]\n"; }
local ax = 60, ay = 60, bx = 100, by = 60;
// 街の間の道（東西の直線）を先に敷き、道のすぐ北に街を置く（街の建物が道をふさぐと、あとから道を敷けない）
r("road", command_x(tool_build_way).work(pl, coord3d(ax - 10, ay, 0), coord3d(bx + 10, by, 0), WAY));
r("cityA", command_x(tool_add_city).work(pl, coord3d(ax, ay - 3, 0)));
r("cityB", command_x(tool_add_city).work(pl, coord3d(bx, by - 3, 0)));
// 人口は足さない（輸送だけで育つかを見る。#30）
if (NOSTOP) return s + "no stops (control: no halts)";
// バス停: 各街の中心の真南の道の上（置けなければ隣のタイル。T は置けた所）
local T = [];
foreach (cx in [ax, bx]) {
  foreach (dx in [0, 1, -1, 2, -2, 3, -3]) {
    local e = command_x(tool_build_station).work(pl, coord3d(cx + dx, ay, 0), "pak256_bus_stop");
    if (e == null) { T.append(coord3d(cx + dx, ay, 0)); break; }
    s += "stop " + (cx + dx) + ": " + e + "\n";
  }
}
if (T.len() != 2) return s + "stops failed";
if (NOBUS) return s + "stops " + T.len() + " nobus (control)";
// 車庫: 道の南の脇
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_waytype() != wt_road) continue;
  if (DEPOT == "" || d.get_name() == DEPOT) { depot_desc = d; break; }
}
if (depot_desc == null) return s + "no road depot";
// 道の南の脇のどこかに置く（街の建物にふさがれていたら隣へ）
local depot = null;
foreach (dx in [8, 9, 10, 11, 12, 13, 7, 6, 5, -8, -9, -10, -11]) {
  local x = ax + dx;
  command_x(tool_build_way).work(pl, coord3d(x, ay + 1, 0), coord3d(x, ay, 0), WAY);
  local e = command_x.build_depot(pl, coord3d(x, ay + 1, 0), depot_desc);
  if (e == null) { depot = depot_x(x, ay + 1, 0); s += "depot " + x + "," + (ay + 1) + "\n"; break; }
  s += "depot " + x + ": " + e + "\n";
}
if (depot == null) return s + "depot failed";
local pick = function(name) { foreach (v in vehicle_desc_x.get_available_vehicles(wt_road)) if (v.get_name() == name) return v; return null; };
local stops = T;
foreach (name in ["pak256_bus", "pak256_mail_truck"]) {
  local v = pick(name);
  if (v == null) return s + "no vehicle " + name;
  depot.append_vehicle(pl, convoy_x(0), v);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  cnv.change_schedule(pl, schedule_x(wt_road, [schedule_entry_x(stops[0], 0, 0), schedule_entry_x(stops[1], 0, 0)]));
  depot.start_convoy(pl, cnv);
  s += "[convoy] " + name + "\n";
}
return s + "ok";
