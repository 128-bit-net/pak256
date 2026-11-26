// 路面電車の確かめの街（#153）。MIT License。tram.nut の後に、公共のプレーヤーで流す（会社の資金を使わないため）。
// 先頭に足す変数: OX, OY。停留所の置き場の脇に街を 2 つ置いて、人口を足す。
local pl = player_x(1);
local a = command_x(tool_add_city).work(pl, coord3d(OX + 4, OY - 3, 0));
local b = command_x(tool_add_city).work(pl, coord3d(OX + 39, OY + 10, 0));
foreach (c in city_list_x()) c.change_size(600);
return "a=[" + a + "] b=[" + b + "]";
