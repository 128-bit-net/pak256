// モノレールの確かめ（#156）。MIT License。tools/vehicle_check/monorail_run.py が Game.sq_file で流す。
// 先頭に足す変数: OX, OY（地上の線の西の端）。
// 4 本の線を作る。どれも駅（3 タイル）と車庫 1 つ、1 編成（高架だけ 1 両、ほかは 2 両）。
//   曲がり（y=OY+60）: 直角の曲がり・南北の駅・斜め。
//   地上（y=OY）: 旅客を運ぶ（駅の近くの街は monorail_city.nut が公共のプレーヤーで置く）。車庫は中ほどの南の脇。
//   高架（y=OY+20）: ami_monorail_straddle_elev_center。駅と車庫も高架の上（高さ 2）。地上との接続は作らない。
//   トンネル（y=OY+40）: 高さ 2 の丘を ami_monorail_straddle_tunnel で抜ける。
local pl = player_x(0);
local s = "";
local WAY = "ami_monorail_straddle";
local ELEV = "ami_monorail_straddle_elev_center";
local TUNNEL = "ami_monorail_straddle_tunnel";
local STOP = "pak256_monorail_station";
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) if (d.get_name() == "ami_monorail_depot") depot_desc = d;
if (depot_desc == null) return "no monorail depot";
local car = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_monorail)) if (v.get_name() == "pak256_monorail") car = v;
if (car == null) return "no vehicle";

local check = function(name, v) { return v == null ? "" : name + "=[" + v + "] "; };
// 駅を 3 タイルずつ置き、車庫に編成を入れて 2 つの駅の間を往復させる
local run = function(y, z, a, b, depot_pos, cars) {
  local e = "";
  foreach (x0 in [a, b]) {
    for (local i = 0; i < 3; i++) e += check("station" + (x0 + i) + "," + y, command_x(tool_build_station).work(pl, coord3d(x0 + i, y, z), STOP));
  }
  e += check("depot" + y, command_x.build_depot(pl, depot_pos, depot_desc));
  if (e != "") return e;
  local depot = depot_x(depot_pos.x, depot_pos.y, depot_pos.z);
  depot.append_vehicle(pl, convoy_x(0), car);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  for (local i = 1; i < cars; i++) depot.append_vehicle(pl, cnv, car);
  cnv.change_schedule(pl, schedule_x(wt_monorail, [schedule_entry_x(coord3d(a + 1, y, z), 0, 0), schedule_entry_x(coord3d(b + 1, y, z), 0, 0)]));
  depot.start_convoy(pl, cnv);
  return "";
};

// 地上
local y = OY;
s += check("track", command_x(tool_build_way).work(pl, coord3d(OX, y, 0), coord3d(OX + 60, y, 0), WAY));
s += check("depot_way", command_x(tool_build_way).work(pl, coord3d(OX + 30, y + 1, 0), coord3d(OX + 30, y, 0), WAY));
s += run(y, 0, OX + 6, OX + 52, coord3d(OX + 30, y + 1, 0), 2);

// 高架（敷くと高さ 2 になる）
y = OY + 20;
s += check("elev", command_x(tool_build_way).work(pl, coord3d(OX, y, 0), coord3d(OX + 20, y, 0), ELEV));
s += run(y, 2, OX + 1, OX + 16, coord3d(OX + 20, y, 2), 1);

// トンネル: 先に丘を高さ 2 まで上げる（2 回で、口の坂が 2 段になる）
y = OY + 40;
for (local k = 0; k < 2; k++) {
  for (local x = OX + 10; x <= OX + 15; x++) for (local yy = y - 2; yy <= y + 3; yy++) command_x.grid_raise(pl, coord3d(x, yy, 0));
}
s += check("t_west", command_x(tool_build_way).work(pl, coord3d(OX, y, 0), coord3d(OX + 9, y, 0), WAY));
s += check("tunnel", command_x(tool_build_tunnel).work(pl, coord3d(OX + 9, y, 0), TUNNEL));
s += check("t_east", command_x(tool_build_way).work(pl, coord3d(OX + 15, y, 0), coord3d(OX + 26, y, 0), WAY));
s += run(y, 0, OX, OX + 20, coord3d(OX + 26, y, 0), 2);

// 曲がり・南北・斜め（y=OY+60）: 東 → 角 → 南（途中に南北の駅）→ 南東への斜め → 東。車庫は西の端
y = OY + 60;
local lay = function(x0, y0, x1, y1) { return check("lay" + x0 + "," + y0, command_x(tool_build_way).work(pl, coord3d(x0, y0, 0), coord3d(x1, y1, 0), WAY)); };
s += lay(OX, y, OX + 14, y);
s += lay(OX + 14, y, OX + 14, y + 14);
s += lay(OX + 14, y + 14, OX + 22, y + 22);
s += lay(OX + 22, y + 22, OX + 32, y + 22);
foreach (p in [[OX + 2, y], [OX + 3, y], [OX + 4, y], [OX + 14, y + 8], [OX + 14, y + 9], [OX + 14, y + 10], [OX + 28, y + 22], [OX + 29, y + 22], [OX + 30, y + 22]]) {
  s += check("station" + p[0] + "," + p[1], command_x(tool_build_station).work(pl, coord3d(p[0], p[1], 0), STOP));
}
s += check("depot_curve", command_x.build_depot(pl, coord3d(OX, y, 0), depot_desc));
local cd = depot_x(OX, y, 0);
cd.append_vehicle(pl, convoy_x(0), car);
local cl = cd.get_convoy_list();
local cc = cl[cl.len() - 1];
cd.append_vehicle(pl, cc, car);
cc.change_schedule(pl, schedule_x(wt_monorail, [schedule_entry_x(coord3d(OX + 3, y, 0), 0, 0), schedule_entry_x(coord3d(OX + 14, y + 9, 0), 0, 0),
                                              schedule_entry_x(coord3d(OX + 29, y + 22, 0), 0, 0)]));
cd.start_convoy(pl, cc);

return s + "ok";
