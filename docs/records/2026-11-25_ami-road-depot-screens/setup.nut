// AMI の道路の車庫（ami_road_depot）の確かめ（#64）。MIT License。tools/game.py の Game.sq_file で流す。
// 先頭に足す変数: WAY（道路の名前）。道の端に車庫を置き、バスを買って、道の先のバス停との間を走らせる。
local pl = player_x(0);
local s = "";
function r(name, v) { if (v != null) s += name + "=[" + v + "]\n"; }
r("road", command_x(tool_build_way).work(pl, coord3d(50, 60, 0), coord3d(80, 60, 0), WAY));
r("road2", command_x(tool_build_way).work(pl, coord3d(55, 60, 0), coord3d(55, 61, 0), WAY));
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_waytype() == wt_road) { depot_desc = d; s += "depot desc: " + d.get_name() + "\n"; break; }
}
if (depot_desc == null) return s + "no road depot";
r("depot", command_x.build_depot(pl, coord3d(55, 61, 0), depot_desc));
r("stopA", command_x(tool_build_station).work(pl, coord3d(60, 60, 0), "pak256_bus_stop"));
r("stopB", command_x(tool_build_station).work(pl, coord3d(78, 60, 0), "pak256_bus_stop"));
return s + "ok";
