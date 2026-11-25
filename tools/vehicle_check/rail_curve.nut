// 線路の曲がり・坂での列車の確かめ（#71）。MIT License。tools/vehicle_check/rail_curve_run.py が Game.sq で流す。
// 先頭に足す変数: OX, OY（コの字の西北の角）, WAY（線路の名前）, TRAILER（1 なら気動車に付随車をつなぐ）。
// コの字の線路: 北の辺（y=OY、x=OX〜OX+30）・東の辺（x=OX+30、y=OY〜OY+10）・南の辺（y=OY+10）。曲がりは東の 2 つの角。
// 北の辺の x=OX+20〜23 に高さ 1 の丘（手前と先は 1 段の坂）。駅は北と南の西寄りに 3 タイルずつ。車庫は北の辺の南の脇。
// 気動車 + 付随車の 1 編成が、北の駅と南の駅の間を往復する（コの字を回る）。
local pl = player_x(0);
local s = "";
function r(name, v) { if (v != null) s += name + "=[" + v + "]\n"; }
local W = 30, H = 10;
// 丘（先に地面を上げる。線路を敷いた後では、本体は地面を上げない）
for (local x = OX + 20; x <= OX + 23; x++) {
  for (local y = OY; y <= OY + 1; y++) r("raise " + x + "," + y, command_x.grid_raise(pl, coord3d(x, y, 0)));
}
// 線路は隣のタイルへ 1 つずつ敷く（長く敷くと、本体が丘をよけて曲がる経路を選ぶ）
function lay(x0, y0, x1, y1) {
  local dx = x1 > x0 ? 1 : (x1 < x0 ? -1 : 0), dy = y1 > y0 ? 1 : (y1 < y0 ? -1 : 0);
  local x = x0, y = y0;
  while (x != x1 || y != y1) {
    local z = square_x(x, y).get_ground_tile().z, z2 = square_x(x + dx, y + dy).get_ground_tile().z;
    r("lay " + x + "," + y, command_x(tool_build_way).work(pl, coord3d(x, y, z), coord3d(x + dx, y + dy, z2), WAY));
    x += dx; y += dy;
  }
}
lay(OX, OY, OX + W, OY);
lay(OX + W, OY, OX + W, OY + H);
lay(OX + W, OY + H, OX, OY + H);
local A = OX + 6;
foreach (y0 in [OY, OY + H]) {
  for (local i = 0; i < 3; i++) {
    local e = command_x(tool_build_station).work(pl, coord3d(A + i, y0, 0), "pak256_train_station");
    if (e != null) return s + "station " + (A + i) + "," + y0 + ": " + e;
  }
}
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_waytype() != wt_rail) continue;
  if (d.get_name() == "ami_rail_depot") { depot_desc = d; break; }
}
if (depot_desc == null) return s + "no rail depot";
local dx = OX + 12;
r("depot_way", command_x(tool_build_way).work(pl, coord3d(dx, OY + 1, 0), coord3d(dx, OY, 0), WAY));
local e = command_x.build_depot(pl, coord3d(dx, OY + 1, 0), depot_desc);
if (e != null) return s + "depot: " + e;
local depot = depot_x(dx, OY + 1, 0);
local pick = function(name) { foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail)) if (v.get_name() == name) return v; return null; };
local car = pick("pak256_railcar"), tr = pick("pak256_railcar_trailer");
if (car == null || tr == null) return s + "no vehicles";
depot.append_vehicle(pl, convoy_x(0), car);
local list = depot.get_convoy_list();
local cnv = list[list.len() - 1];
if (TRAILER == 1) depot.append_vehicle(pl, cnv, tr);
cnv.change_schedule(pl, schedule_x(wt_rail, [schedule_entry_x(coord3d(A + 1, OY, 0), 0, 0), schedule_entry_x(coord3d(A + 1, OY + H, 0), 0, 0)]));
depot.start_convoy(pl, cnv);
return s + "ok";
