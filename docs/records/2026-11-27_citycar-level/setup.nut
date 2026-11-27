// pak256#182: 街を 3 つ置き、2 つの街にバスを走らせる
local pl = player_x(0);
local s = "";
local towns = [[60, 60, 40, 80, 4500], [160, 160, 130, 190, 45000]];
foreach (i, t in towns) {
  local cx = t[0], cy = t[1];
  command_x(tool_build_way).work(pl, coord3d(t[2], cy, 0), coord3d(t[3], cy, 0), "ami_road_local");
  command_x(tool_add_city).work(pl, coord3d(cx, cy - 3, 0));
}
command_x(tool_add_city).work(pl, coord3d(60, 200, 0));
foreach (i, t in towns) {
  local cy = t[1];
  local stops = [coord3d(t[2] + 3, cy, 0), coord3d(t[3] - 3, cy, 0)];
  foreach (p in stops) {
    local e = command_x(tool_build_station).work(pl, p, "pak256_bus_stop");
    if (e != null) s += "stop err " + e + " ; ";
  }
  local dd = null;
  foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_waytype() == wt_road && d.get_name() == "ami_road_depot") dd = d;
  local depot = null;
  foreach (dx in [8, 9, 10, 11, 12, 13, -8, -9, -10, -11, 7, 14]) {
    local x = t[0] + dx;
    command_x(tool_build_way).work(pl, coord3d(x, cy + 1, 0), coord3d(x, cy, 0), "ami_road_local");
    local e = command_x.build_depot(pl, coord3d(x, cy + 1, 0), dd);
    if (e == null) { depot = depot_x(x, cy + 1, 0); break; }
    s += "depot " + x + " " + e + " ; ";
  }
  if (depot == null) continue;
  local v = null;
  foreach (d in vehicle_desc_x.get_available_vehicles(wt_road)) if (d.get_name() == "pak256_bus") v = d;
  for (local k = 0; k < 2; k++) {
    depot.append_vehicle(pl, convoy_x(0), v);
    local list = depot.get_convoy_list();
    local cnv = list[list.len() - 1];
    cnv.change_schedule(pl, schedule_x(wt_road, [schedule_entry_x(stops[0], 0, 0), schedule_entry_x(stops[1], 0, 0)]));
    depot.start_convoy(pl, cnv);
  }
  s += "convoys " + i + " ok ; ";
}
foreach (c in city_list_x()) {
  local p = c.get_pos();
  if (p.x > 100) c.change_size(45000); else if (p.y < 120) c.change_size(4500); else c.change_size(400);
}
foreach (c in city_list_x()) { local p = c.get_pos(); s += p.x + "," + p.y + ":" + c.get_citizens()[0] + " "; }
return s;
