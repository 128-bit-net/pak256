// 車両の描画位置の試験のコース（docs/vehicles.md の「試験」）。MIT License。
// tools/vehicle_check/run.py が、平らな保存データを読んだゲームに MCP の run_squirrel で流す。
//
// 道路の輪を 1 つ敷く。直線の 4 方向・斜め 2 本（SE と SW の向きの階段）・直角の曲がり 2 つを持つ:
//   P1(0,0) → 東 → P2(W,0) → 斜め → P3(W+D,D) → 南 → P4(W+D,D+H) → 斜め → P5(W,2D+H) → 西 → P6(0,2D+H) → 北 → P1
// 車庫は P1 と P2 の間の北の脇。編成は 3 つ: 時計回りの 1 両・時計回りの 2 両（連結のすき間を見る）・反時計回りの 1 両。
// 時計回りは 東・SE・南・SW・西・北、反時計回りは その逆の 8 方向のうち残りの向きを通る。
// ダイヤは輪の辺の中ほどの道路のタイルを順に回る。北の辺の 1 つは停留所（道路の停留所があれば置く）。
// 車庫と停留所は、pak256 にも AMI の 256 版にもまだ無いので、試験のときだけ別の pak から借りる（run.py）。
// 流す前に、次の 5 つの変数を run.py が先頭に足す: OX, OY（P1 の場所）, VEH（車両の名前）, DEPOT（車庫の名前。空なら道路の車庫を探す）,
// WAY（道路の名前。借りた pak の道路でなく AMI の道路に敷くため）
local W = 10, D = 6, H = 8;
local pl = player_x(0);
local s = "";
function c(x, y) { return coord3d(OX + x, OY + y, 0); }
function r(name, v) { if (v != null) s += name + "=[" + v + "]\n"; }

local way = null;
foreach (w in way_desc_x.get_available_ways(wt_road, st_flat)) if (w.get_name() == WAY) way = w;
if (way == null) return "no road " + WAY;
local line = function(x0, y0, x1, y1) { r("way " + x0 + "," + y0 + "-" + x1 + "," + y1, command_x.build_way(pl, c(x0, y0), c(x1, y1), way, true)); };
// 階段: (x0,y0) から k 段。sx は 1 段ごとの x の向き（+1 か -1）、まず x へ 1、次に y へ 1
local stair = function(x0, y0, k, sx) {
  for (local i = 0; i < k; i++) {
    local x = x0 + sx * i, y = y0 + i;
    line(x, y, x + sx, y);
    line(x + sx, y, x + sx, y + 1);
  }
};
line(0, 0, W, 0);                       // 東
stair(W, 0, D, 1);                      // SE の階段
line(W + D, D, W + D, D + H);           // 南
stair(W + D, D + H, D, -1);             // SW の階段
line(W, 2 * D + H, 0, 2 * D + H);       // 西
line(0, 2 * D + H, 0, 0);               // 北

// 車庫
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_waytype() != wt_road) continue;
  if (DEPOT == "" || d.get_name() == DEPOT) { depot_desc = d; break; }
}
if (depot_desc == null) return s + "no road depot";
line(3, -1, 3, 0);
r("depot", command_x.build_depot(pl, c(3, -1), depot_desc));
local depot = depot_x(OX + 3, OY - 1, 0);

local veh = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_road)) if (v.get_name() == VEH) veh = v;
if (veh == null) return s + "no vehicle " + VEH;

// 停留所（あれば）。北の辺の中ほど。どの編成もここに止まる（止まった所の描画位置を見る）
local stop_desc = null;
foreach (d in building_desc_x.get_available_stations(building_desc_x.station, wt_road, good_desc_x.passenger)) { stop_desc = d; break; }
if (stop_desc != null) r("stop", command_x.build_station(pl, c(W / 2, 0), stop_desc));
else s += "no road stop\n";

local cw = [c(W / 2, 0), c(W + D, D + H / 2), c(W / 2, 2 * D + H), c(0, D + H / 2)];
local ccw = [cw[3], cw[2], cw[1], cw[0]];
local convoys = [[cw, 1], [cw, 2], [ccw, 1]];
foreach (i, row in convoys) {
  local cnv = null;
  for (local n = 0; n < row[1]; n++) {
    depot.append_vehicle(pl, n == 0 ? convoy_x(0) : cnv, veh);
    local list = depot.get_convoy_list();
    cnv = list[list.len() - 1];
  }
  local entries = [];
  foreach (p in row[0]) entries.append(schedule_entry_x(p, 0, 0));
  if (entries[0].x != row[0][0].x) return s + "schedule_entry_x is broken: the game's script/ folder is not OTRP's";
  cnv.change_schedule(pl, schedule_x(wt_road, entries));
  depot.start_convoy(pl, cnv);
  s += "[convoy] " + i + " len=" + cnv.get_vehicles().len() + "\n";
}
gui.close_all_windows();
return s + "ok";
