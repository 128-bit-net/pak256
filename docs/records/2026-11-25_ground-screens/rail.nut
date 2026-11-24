// MIT License。2026-11-25 の地面の確認で、地図の地形を作るのに使った Squirrel（MCP の run_squirrel で流した。行頭の // の行は流すときに外した）
local pl = player_x(0);
local r = "";
local ami = way_desc_x("ami_rail_ballast");
// 丘 1 を東西（x 方向）に横切る線: y=236, x=228..246
local a = square_x(228, 236).get_ground_tile();
local b = square_x(246, 236).get_ground_tile();
r += "a.z=" + a.z + " b.z=" + b.z + " ";
r += "" + command_x.build_way(pl, coord3d(228, 236, a.z), coord3d(246, 236, b.z), ami, true);
// 丘 1 を南北（y 方向）に横切る線: x=234, y=228..246
local c = square_x(234, 228).get_ground_tile();
local d = square_x(234, 246).get_ground_tile();
r += " " + command_x.build_way(pl, coord3d(234, 228, c.z), coord3d(234, 246, d.z), ami, true);
// 丘 2（複段）: y=235, x=218..233
local e = square_x(218, 235).get_ground_tile();
local f = square_x(233, 235).get_ground_tile();
r += " " + command_x.build_way(pl, coord3d(218, 235, e.z), coord3d(233, 235, f.z), ami, true);
return r;
