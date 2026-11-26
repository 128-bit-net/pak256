// monorail_run.py が公共のプレーヤーで流す（会社のお金を街の設置に使わないため）。MIT License。
// 先頭に足す変数: OX, OY（地上の線の西の端）。地上の 2 つの駅の近くに街を置く。
local pl = player_x(1);
local s = "";
foreach (x in [OX + 8, OX + 52]) {
  local e = command_x(tool_add_city).work(pl, coord3d(x, OY - 4, 0));
  if (e != null) s += "city" + x + "=[" + e + "] ";
}
foreach (c in city_list_x()) c.change_size(600);
return s + "ok";
