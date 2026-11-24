// MIT License。2026-11-25 の地面の確認で、地図の地形を作るのに使った Squirrel（MCP の run_squirrel で流した。行頭の // の行は流すときに外した）
local pl = player_x(0);
local r = "";
for (local x = 300; x <= 303; x++) for (local y = 300; y <= 303; y++) {
  local e = command_x.set_slope(pl, coord3d(x, y, 0), slope.all_up_slope);
  if (e) r += x + "," + y + ":" + e + " ";
}
local e2 = command_x.set_slope(pl, coord3d(301, 301, 1), slope.all_up_slope);
if (e2) r += "up2:" + e2;
return "done " + r;
