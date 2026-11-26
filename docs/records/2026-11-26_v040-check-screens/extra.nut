// α0.4 の確かめ（#105）。MIT License。setup.nut の後に流す。
// v0.3.1 にだけある AMI の道路の停留所と、温帯の木 3 種を置き、AMI のバス停 2 つを往復するバスを出す。
local pl = player_x(0);
local s = "";
function r(name, v) { s += name + "=[" + v + "] "; }
r("road_v", command_x(tool_build_way).work(pl, coord3d(50, 60, 0), coord3d(50, 75, 0), "ami_road_local"));
r("road_h", command_x(tool_build_way).work(pl, coord3d(50, 75, 0), coord3d(90, 75, 0), "ami_road_local"));
r("cityC", command_x(tool_add_city).work(pl, coord3d(57, 79, 0)));
r("cityD", command_x(tool_add_city).work(pl, coord3d(84, 79, 0)));
foreach (c in city_list_x()) { local p = c.get_pos(); if (p.y > 70 && p.y < 90) c.change_size(300); }
r("ami_bus_w", command_x(tool_build_station).work(pl, coord3d(55, 75, 0), "ami_road_bus_stop"));
r("ami_truck", command_x(tool_build_station).work(pl, coord3d(70, 75, 0), "ami_road_truck_stop"));
r("ami_bus_e", command_x(tool_build_station).work(pl, coord3d(85, 75, 0), "ami_road_bus_stop"));
local depot = depot_x(125, 61, 0);
local bus = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_road)) if (v.get_name() == "pak256_bus") bus = v;
depot.append_vehicle(pl, convoy_x(0), bus);
local list = depot.get_convoy_list();
local cnv = list[list.len() - 1];
r("sched", cnv.change_schedule(pl, schedule_x(wt_road, [schedule_entry_x(coord3d(55, 75, 0), 0, 0), schedule_entry_x(coord3d(85, 75, 0), 0, 0)])));
r("start", depot.start_convoy(pl, cnv));
return s;
