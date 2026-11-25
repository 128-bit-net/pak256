// 炭鉱 → 発電所の連鎖で石炭のトラックを走らせる確かめ（docs/records/2026-11-25_coal-truck.md）。MIT License。
// tools/game.py（docs/game-check.md）が、平らな保存データを読んだゲームに流す。先頭に OX, OY（道路の西の端）、VEH（車両の名前）、
// DEPOT（車庫の名前。空なら最初に見つかった道路の車庫）、ROAD（道路の名前）、TRUCKS（走らせる台数）を足す。
// 配置（OX,OY を原点として）: 東西の道路（y=3）の北に、炭鉱（2x2、x=2,y=0）と発電所（3x3、x=22,y=0）。
// 道路の上の荷役所を炭鉱の脇（x=3）と発電所の脇（x=23）に置き、道路の南の脇（x=12,y=4）に車庫を置く。
local pl = player_x(0);
local s = "";
function c(x, y) { return coord3d(OX + x, OY + y, 0); }
function r(name, v) { s += name + "=[" + v + "]\n"; }

r("road", command_x(tool_build_way).work(pl, c(0, 3), c(28, 3), ROAD));
r("mine", command_x(tool_build_factory).work(pl, c(2, 0), "0050,pak256_coal_mine"));
r("plant", command_x(tool_build_factory).work(pl, c(22, 0), "0050,pak256_coal_kraftwerk"));
r("link", command_x(tool_link_factory).work(pl, c(2, 0), c(22, 0), ""));
r("stop_mine", command_x(tool_build_station).work(pl, c(3, 3), "pak256_truck_stop"));
r("stop_plant", command_x(tool_build_station).work(pl, c(23, 3), "pak256_truck_stop"));

local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_waytype() != wt_road) continue;
  if (DEPOT == "" || d.get_name() == DEPOT) { depot_desc = d; break; }
}
if (depot_desc == null) return s + "no road depot";
r("depot_road", command_x(tool_build_way).work(pl, c(12, 3), c(12, 4), ROAD));
r("depot", command_x.build_depot(pl, c(12, 4), depot_desc));
local depot = depot_x(OX + 12, OY + 4, 0);

local veh = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_road)) if (v.get_name() == VEH) veh = v;
if (veh == null) return s + "no vehicle " + VEH;
s += "vehicle freight=" + veh.get_freight().get_name() + " capacity=" + veh.get_capacity() + " length=" + veh.get_length() + "\n";

// TRUCKS 台。炭鉱の荷役所で積み（20% 以上）、発電所の荷役所へ運ぶ
for (local i = 0; i < TRUCKS; i++) {
  depot.append_vehicle(pl, convoy_x(0), veh);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  local entries = [schedule_entry_x(c(3, 3), 20, 0), schedule_entry_x(c(23, 3), 0, 0)];
  cnv.change_schedule(pl, schedule_x(wt_road, entries));
  depot.start_convoy(pl, cnv);
}
gui.close_all_windows();
return s + "ok";
