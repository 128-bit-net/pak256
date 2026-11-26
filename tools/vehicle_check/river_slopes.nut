// 坂の絵（imageup の 4 方向・1 段と 2 段）の確かめ（#158）。MIT License。
// 平らな所に高さ H の台を作り、台の 4 辺を川が上り下りするように置く。先頭で OX・OY・H・WAY を定義して流す。
local pu = player_x(1);
for (local i = 0; i < H; i++)
	for (local y = OY; y <= OY + 8; y++)
		for (local x = OX; x <= OX + 8; x++) command_x.grid_raise(pu, coord3d(x, y, i));
local t = function(x, y) { return square_x(x, y).get_ground_tile(); };
local c = function(x, y) { return coord3d(x, y, t(x, y).z); };
local out = "";
local build = function(x1, y1, x2, y2) {
	local r = command_x(tool_build_way).work(player_x(1), c(x1, y1), c(x2, y2), WAY);
	out += "[" + r + "]";
};
// 台の北・南・西・東の辺をまたぐ 4 本
build(OX + 3, OY - 3, OX + 3, OY + 2);
build(OX + 5, OY + 5, OX + 5, OY + 11);
build(OX - 3, OY + 4, OX + 2, OY + 4);
build(OX + 5, OY + 3, OX + 11, OY + 3);
out += " slopes:";
// 台の格子点は x が OX〜OX+8、y が OY〜OY+8。坂の升は北が y = OY-1、南が y = OY+8、西が x = OX-1、東が x = OX+8
foreach (p in [[OX + 3, OY - 1], [OX + 5, OY + 8], [OX - 1, OY + 4], [OX + 8, OY + 3]]) {
	local g = t(p[0], p[1]);
	out += " " + p[0] + "," + p[1] + ",z" + g.z + ",s" + g.get_slope() + ",way=" + (g.get_way(wt_water) != null);
}
return out;
