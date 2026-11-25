// MIT License。2026-11-26（#101）の気候ごとの地面の確認で、地形と気候を作るのに使った Squirrel。
// 地図は flat_512_left_v64（平ら。x < 256 は温帯）。気候の番号: 0 水・1 砂漠・2 熱帯・3 地中海・4 温帯・5 ツンドラ・6 岩・7 雪。
local pl = player_x(0);
local errs = "";
local clim = command_x(tool_set_climate);
function setc(c, x1, y1, x2, y2) {
  return clim.work(player_x(0), coord3d(x1, y1, 0), coord3d(x2, y2, 0), "" + c);
}
function raise_rect(x1, y1, x2, y2, p) {
  local r = "";
  for (local x = x1; x <= x2; x++) for (local y = y1; y <= y2; y++) {
    local e = command_x.grid_raise(player_x(0), coord3d(x, y, p));
    if (e) r += x + "," + y + ":" + e + " ";
  }
  return r;
}
// 1) 平地の帯: 気候 1..7 を 8x8 ずつ x = 100.. に並べる（y = 100..107）。隣り合う 2 気候の境が 6 つできる
for (local i = 1; i <= 7; i++) {
  setc(i, 100 + 8 * (i - 1), 100, 107 + 8 * (i - 1), 107);
}
// 2) 1 段の丘: 気候 i の丘（8x8 の節）を、周りが温帯（温帯の丘の周りは熱帯）の所に作る。x0 = 100 + 14 * (i - 1)、y = 120..
for (local i = 1; i <= 7; i++) {
  local x0 = 100 + 14 * (i - 1);
  errs += raise_rect(x0, 120, x0 + 8, 128, 0);
  setc(i == 4 ? 2 : 4, x0 - 2, 118, x0 + 10, 130);
  setc(i, x0, 120, x0 + 7, 127);
}
// 3) 2 段の丘（同じ並び。y = 140..）
for (local i = 1; i <= 7; i++) {
  local x0 = 100 + 14 * (i - 1);
  errs += raise_rect(x0, 140, x0 + 10, 150, 0);
  errs += raise_rect(x0 + 2, 142, x0 + 8, 148, 1);
  setc(i == 4 ? 2 : 4, x0 - 2, 138, x0 + 12, 152);
  setc(i, x0, 140, x0 + 9, 149);
}
// 4) 海岸: 湖（12x12 の節。外側から 1,2,3,4,5,5 段下げて、水位を 2 回上げる）を、周りが砂漠・温帯・雪の所に作る。y = 170..
function ring(x, y, x0, y0) {
  local dx = (x - x0 < x0 + 11 - x) ? x - x0 : x0 + 11 - x;
  local dy = (y - y0 < y0 + 11 - y) ? y - y0 : y0 + 11 - y;
  return (dx < dy) ? dx : dy;
}
local tgt = [1, 2, 3, 4, 5, 5];
local lakes = [[1, 100], [4, 130], [7, 160], [5, 190]];
foreach (lk in lakes) {
  local x0 = lk[1]; local y0 = 170;
  for (local p = 1; p <= 5; p++) {
    for (local x = x0; x <= x0 + 11; x++) for (local y = y0; y <= y0 + 11; y++) {
      if (tgt[ring(x, y, x0, y0)] >= p) {
        local e = command_x.grid_lower(pl, coord3d(x, y, -(p - 1)));
        if (e) errs += x + "," + y + ":" + e + " ";
      }
    }
  }
  local t = command_x(tool_change_water_height);
  t.work(pl, coord3d(x0 + 5, y0 + 5, -5), "1");
  t.work(pl, coord3d(x0 + 5, y0 + 5, -5), "1");
  // 地形を変えると気候が高さで決まり直すので、気候は最後に塗る
  setc(lk[0], x0 - 3, y0 - 3, x0 + 14, y0 + 14);
}
return "done " + errs;
