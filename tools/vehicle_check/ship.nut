// 船と港の確かめ（docs/vehicles.md の「船」・#154）。MIT License。
// tools/game.py を開いたまま、`--send-file tools/vehicle_check/ship.nut` で流す（flat_512_left_v64）。
// flat_512_left_v64（平らな地図）の温帯の所に、深さ 1 段の海（x 40〜59, y 80〜92）を掘り、坂の岸に桟橋、平らな岸に岸壁、
// 陸の運河（ami_canal。y=104）に船着き場 2 つを置く。旅客船は桟橋と岸壁の間、貨物船は炭鉱の脇の桟橋から発電所の脇の岸壁へ石炭を、
// 運河では旅客船が 2 つの船着き場の間を往復する。車庫は ami_canal_depot（海につながる運河と陸の運河の行き止まり）。
// 地形・産業・街は公共のプレーヤー、港と船は player_x(0) で置く。街の建物が停留所の届く範囲に無いと旅客が乗らないので、住宅を脇に置く。
local pu = player_x(1), pl = player_x(0);
local s = "";
function r(name, v) { if (v != null) s += name + "=[" + v + "]\n"; }

// 海: 地面を 1 段掘り、水位を -1 にする。南側の 3 行は後から掘り足して、海面と同じ高さの平らな岸にする
for (local y = 80; y <= 92; y++) for (local x = 40; x <= 60; x++) command_x.grid_lower(pu, coord3d(x, y, 0));
r("water", command_x(tool_change_water_height).work(pu, coord3d(50, 86, -1), "1"));
for (local y = 93; y <= 99; y++) for (local x = 40; x <= 60; x++) command_x.grid_lower(pu, coord3d(x, y, 0));

// 産業と街（炭鉱は桟橋の脇、発電所は岸壁の脇）
r("mine", command_x(tool_build_factory).work(pu, coord3d(46, 76, 0), "0050,pak256_coal_mine"));
r("plant", command_x(tool_build_factory).work(pu, coord3d(45, 95, -1), "0050,pak256_coal_kraftwerk"));
r("link", command_x(tool_link_factory).work(pu, coord3d(46, 76, 0), coord3d(45, 95, -1), ""));

// 港: 桟橋（坂の岸。水が南・東・西の 3 通り）、岸壁（平らな岸）
r("pier_s", command_x(tool_build_station).work(pl, coord3d(49, 79, -1), "pak256_pier"));
r("pier_e", command_x(tool_build_station).work(pl, coord3d(39, 84, -1), "pak256_pier"));
r("pier_w", command_x(tool_build_station).work(pl, coord3d(60, 84, -1), "pak256_pier"));
r("quay", command_x(tool_build_station).work(pl, coord3d(49, 93, -1), "pak256_quay"));

// 車庫: 海につながる短い運河（南の岸）の行き止まり。本体は開けた海の上には車庫を置かせない
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_canal_depot") depot_desc = d;
if (depot_desc == null) return s + "no ami_canal_depot";
r("sea_canal", command_x(tool_build_way).work(pl, coord3d(55, 92, -1), coord3d(55, 94, -1), "ami_canal"));
r("sea_depot", command_x.build_depot(pl, coord3d(55, 94, -1), depot_desc));

// 運河: 東西の直線、両端の近くに船着き場、中ほどの南の脇に車庫
r("canal", command_x(tool_build_way).work(pl, coord3d(70, 104, 0), coord3d(100, 104, 0), "ami_canal"));
foreach (x in [74, 96]) for (local i = 0; i < 2; i++)
  r("wharf" + (x + i), command_x(tool_build_station).work(pl, coord3d(x + i, 104, 0), "pak256_canal_wharf"));
r("canal_branch", command_x(tool_build_way).work(pl, coord3d(85, 104, 0), coord3d(85, 105, 0), "ami_canal"));
r("canal_depot", command_x.build_depot(pl, coord3d(85, 105, 0), depot_desc));

// 船
local pick = function(name) { foreach (v in vehicle_desc_x.get_available_vehicles(wt_water)) if (v.get_name() == name) return v; return null; };
local ferry = pick("pak256_ferry"), cargo = pick("pak256_cargo_ship");
if (ferry == null || cargo == null) return s + "no ships";
local start = function(dx, dy, dz, veh, entries) {
  local depot = depot_x(dx, dy, dz);
  depot.append_vehicle(pl, convoy_x(0), veh);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  cnv.change_schedule(pl, schedule_x(wt_water, entries));
  depot.start_convoy(pl, cnv);
};
start(55, 94, -1, ferry, [schedule_entry_x(coord3d(49, 80, -1), 0, 0), schedule_entry_x(coord3d(49, 92, -1), 0, 0)]);
start(55, 94, -1, cargo, [schedule_entry_x(coord3d(49, 80, -1), 20, 0), schedule_entry_x(coord3d(49, 92, -1), 0, 0)]);
start(85, 105, 0, ferry, [schedule_entry_x(coord3d(74, 104, 0), 0, 0), schedule_entry_x(coord3d(97, 104, 0), 0, 0)]);

// 街（旅客を出す）
r("cityA", command_x(tool_add_city).work(pu, coord3d(54, 72, 0)));
r("cityB", command_x(tool_add_city).work(pu, coord3d(54, 100, 0)));
r("cityC", command_x(tool_add_city).work(pu, coord3d(72, 100, 0)));
r("cityD", command_x(tool_add_city).work(pu, coord3d(102, 100, 0)));
foreach (c in city_list_x()) c.change_size(300);
// 停留所の届く範囲（約 2 升）に住宅を置く。画面で港と船を隠さないように奥の側（座標の小さい側）に置く。置けない升は飛ばす
foreach (p in [[50, 78], [48, 78], [51, 77], [50, 77], [47, 93], [48, 93], [47, 94], [47, 92],
               [73, 103], [74, 103], [75, 103], [76, 103], [73, 102], [75, 102],
               [95, 103], [96, 103], [97, 103], [98, 103], [96, 102], [98, 102]]) {
  local g = square_x(p[0], p[1]).get_ground_tile();
  command_x(tool_build_house).work(pu, coord3d(p[0], p[1], g.z), "00pak256_house_small");
}
gui.close_all_windows();
return s + "ok";
