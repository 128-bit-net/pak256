// MIT License。2026-11-25 の地面の確認で、地図の地形を作るのに使った Squirrel（MCP の run_squirrel で流した。行頭の // の行は流すときに外した）
local pl = player_x(0);
local errs = "";
function ring(x, y) {
  local dx = (x - 256 < 267 - x) ? x - 256 : 267 - x;
  local dy = (y - 232 < 243 - y) ? y - 232 : 243 - y;
  return (dx < dy) ? dx : dy;
}
// 丘 1: 単段の坂（節 232..241 を 1 段、234..239 を 2 段、236..237 を 3 段）
for (local p = 0; p < 3; p++) {
  local lo = 232 + p * 2; local hi = 241 - p * 2;
  if (p == 2) { lo = 236; hi = 237; }
  for (local x = lo; x <= hi; x++) for (local y = lo; y <= hi; y++) {
    local e = command_x.grid_raise(pl, coord3d(x, y, p));
    if (e) errs += x + "," + y + ":" + e + " ";
  }
}
// 丘 2: 複段の坂（節 222..229 x 232..239 を一度に 2 段）
for (local p = 0; p < 2; p++) {
  for (local x = 222; x <= 229; x++) for (local y = 232; y <= 239; y++) {
    local e = command_x.grid_raise(pl, coord3d(x, y, p));
    if (e) errs += x + "," + y + ":" + e + " ";
  }
}
// 湖: 外側から 1,2,3,4,5,5 段下げる
local tgt = [1, 2, 3, 4, 5, 5];
for (local p = 1; p <= 5; p++) {
  for (local x = 256; x <= 267; x++) for (local y = 232; y <= 243; y++) {
    if (tgt[ring(x, y)] >= p) {
      local e = command_x.grid_lower(pl, coord3d(x, y, -(p - 1)));
      if (e) errs += x + "," + y + ":" + e + " ";
    }
  }
}
// 水を入れる（-5 の平らな所から 1 段ずつ 2 回上げる）
local t = command_x(tool_change_water_height);
local e1 = t.work(pl, coord3d(261, 237, -5), "1");
local e2 = t.work(pl, coord3d(261, 237, -5), "1");
return "done " + errs;
