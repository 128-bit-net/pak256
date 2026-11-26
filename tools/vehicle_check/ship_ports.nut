// 港の残りの向き（桟橋の水が北、岸壁の水が西）の確かめ（#154）。MIT License。
// ship.nut の後に、同じゲームへ `--send-file tools/vehicle_check/ship_ports.nut` で流す。
local pu = player_x(1), pl = player_x(0);
local s = "";
foreach (x0 in [120, 140]) {
  for (local y = 60; y <= 68; y++) for (local x = x0; x <= x0 + 8; x++) command_x.grid_lower(pu, coord3d(x, y, 0));
  command_x(tool_change_water_height).work(pu, coord3d(x0 + 4, 64, -1), "1");
}
// 2 つめの池の東は掘り足して、水面と同じ高さの平らな岸にする
for (local y = 60; y <= 68; y++) for (local x = 149; x <= 151; x++) command_x.grid_lower(pu, coord3d(x, y, 0));
local g = square_x(124, 68).get_ground_tile();
s += "pier_n=[" + command_x(tool_build_station).work(pl, coord3d(124, 68, g.z), "pak256_pier") + "] ";
s += "quay_w=[" + command_x(tool_build_station).work(pl, coord3d(149, 64, -1), "pak256_quay") + "]";
gui.close_all_windows();
return s;
