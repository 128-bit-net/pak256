// 線路の列車の確かめ（#46）。MIT License。tools/vehicle_check/rail_run.py が Game.sq で流す。
// 先頭に足す変数: OX, OY（線路の西の端）, WAY（線路の名前）, CITIES（1 なら街を 2 つ置く）。
// 東西の直線の線路を敷き、両端の近くに 3 タイルの駅を置き、中ほどの南の脇に車庫を置く。気動車 + 付随車の 1 編成が 2 つの駅の間を往復する。
// 線路の上に置いた駅は、tool_build_station で名前を渡す（道路の停留所と同じ）。
local pl = player_x(0);
local s = "";
function r(name, v) { if (v != null) s += name + "=[" + v + "]\n"; }
local L = 60;
r("track", command_x(tool_build_way).work(pl, coord3d(OX, OY, 0), coord3d(OX + L, OY, 0), WAY));
if (CITIES == 1) {
  r("cityA", command_x(tool_add_city).work(pl, coord3d(OX + 8, OY - 4, 0)));
  r("cityB", command_x(tool_add_city).work(pl, coord3d(OX + L - 8, OY - 4, 0)));
  foreach (c in city_list_x()) c.change_size(300);
}
// 駅: 各端から 6〜8 タイル目（3 タイル）
local A = OX + 6, B = OX + L - 8;
foreach (x0 in [A, B]) {
  for (local i = 0; i < 3; i++) {
    local e = command_x(tool_build_station).work(pl, coord3d(x0 + i, OY, 0), "pak256_train_station");
    if (e != null) return s + "station " + (x0 + i) + ": " + e;
  }
}
// 車庫: 中ほどの南の脇
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_waytype() != wt_rail) continue;
  if (d.get_name() == "ami_rail_depot") { depot_desc = d; break; }
}
if (depot_desc == null) return s + "no rail depot";
local dx = OX + L / 2;
r("depot_way", command_x(tool_build_way).work(pl, coord3d(dx, OY + 1, 0), coord3d(dx, OY, 0), WAY));
local e = command_x.build_depot(pl, coord3d(dx, OY + 1, 0), depot_desc);
if (e != null) return s + "depot: " + e;
local depot = depot_x(dx, OY + 1, 0);
local pick = function(name) { foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail)) if (v.get_name() == name) return v; return null; };
local car = pick("pak256_railcar"), tr = pick("pak256_railcar_trailer");
if (car == null || tr == null) return s + "no vehicles";
for (local n = 0; n < CARS; n++) {
  depot.append_vehicle(pl, convoy_x(0), car);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  if (TRAILER == 1) depot.append_vehicle(pl, cnv, tr);
  cnv.change_schedule(pl, schedule_x(wt_rail, [schedule_entry_x(coord3d(A + 1, OY, 0), 0, 0), schedule_entry_x(coord3d(B + 1, OY, 0), 0, 0)]));
  depot.start_convoy(pl, cnv);
  s += "[convoy]\n";
}
return s + "ok";
