// 線路の信号の確かめ（#73）。MIT License。tools/game.py の Game.sq・--send で流す。
// 変数（下の 1 行。開いたまま `--send-file` で流すときはここを書き換える。別の道具から流すときは、先頭に同じ名前の変数を足して、下の 1 行を消す）:
// OX, OY（線路の周回の左上）, WAY（線路の名前）, CARS（編成の数）, SIGNALS（1 なら信号を置く）。
OX <- 40; OY <- 60; WAY <- "ami_rail_ballast"; CARS <- 4; SIGNALS <- 1;
// 横 W・縦 H の長方形の線路を 1 周敷き、上の辺に駅、下の辺に駅、左の辺の西の脇に車庫を置く。編成は 2 つの駅の間を周回する。
// 信号（pak256_rail_signal）は上の辺に 2 つ、左の辺に 2 つ置く。
local pl = player_x(0);
local s = "";
function r(name, v) { if (v != null) s += name + "=[" + v + "]\n"; }
local W = 24, H = 8;
r("top", command_x(tool_build_way).work(pl, coord3d(OX, OY, 0), coord3d(OX + W, OY, 0), WAY));
r("right", command_x(tool_build_way).work(pl, coord3d(OX + W, OY, 0), coord3d(OX + W, OY + H, 0), WAY));
r("bottom", command_x(tool_build_way).work(pl, coord3d(OX + W, OY + H, 0), coord3d(OX, OY + H, 0), WAY));
r("left", command_x(tool_build_way).work(pl, coord3d(OX, OY + H, 0), coord3d(OX, OY, 0), WAY));
// 駅: 上の辺と下の辺に 3 タイルずつ
local TA = OX + 5, BA = OX + 15;
foreach (p in [[TA, OY], [BA, OY + H]]) {
  for (local i = 0; i < 3; i++) {
    local e = command_x(tool_build_station).work(pl, coord3d(p[0] + i, p[1], 0), "pak256_train_station");
    if (e != null) return s + "station " + (p[0] + i) + ": " + e;
  }
}
// 車庫: 左の辺の西の脇
local depot_desc = null;
foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
  if (d.get_waytype() != wt_rail) continue;
  if (d.get_name() == "ami_rail_depot") { depot_desc = d; break; }
}
if (depot_desc == null) return s + "no rail depot";
// 車庫は左の辺の西の脇（上から 1 タイル目）。出口の先に信号があるので、信号の区間が空くまで出られない。
r("depot_way", command_x(tool_build_way).work(pl, coord3d(OX - 1, OY + 1, 0), coord3d(OX, OY + 1, 0), WAY));
local e = command_x.build_depot(pl, coord3d(OX - 1, OY + 1, 0), depot_desc);
if (e != null) return s + "depot: " + e;
// 信号
if (SIGNALS == 1) {
  local sig = null;
  foreach (d in sign_desc_x.get_available_signs(wt_rail)) if (d.get_name() == "pak256_rail_signal") sig = d;
  if (sig == null) return s + "no signal";
  // 1 回目は両方向、2 回目は片方向（列車が進む向きは、東西の線路なら西、南北の線路なら南。docs/signals.md の「置いたときの動き」）。
  // 上の辺は西向き、左の辺は南向きにそろえ、編成が反時計回りに 1 方向へ周回するようにする（両方向の信号だと、逆向きに入った編成どうしが向き合って止まる）。
  foreach (p in [[OX + 14, OY], [OX + 20, OY], [OX, OY + 3], [OX, OY + 6]]) {
    r("signal " + p[0] + "," + p[1], command_x.build_sign_at(pl, coord3d(p[0], p[1], 0), sig));
    r("signal " + p[0] + "," + p[1] + " (2)", command_x.build_sign_at(pl, coord3d(p[0], p[1], 0), sig));
  }
}
local depot = depot_x(OX - 1, OY + 1, 0);
local pick = function(name) { foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail)) if (v.get_name() == name) return v; return null; };
local car = pick("pak256_railcar"), tr = pick("pak256_railcar_trailer");
if (car == null || tr == null) return s + "no vehicles";
for (local n = 0; n < CARS; n++) {
  depot.append_vehicle(pl, convoy_x(0), car);
  local list = depot.get_convoy_list();
  local cnv = list[list.len() - 1];
  depot.append_vehicle(pl, cnv, tr);
  cnv.change_schedule(pl, schedule_x(wt_rail, [schedule_entry_x(coord3d(TA + 1, OY, 0), 0, 0), schedule_entry_x(coord3d(BA + 1, OY + H, 0), 0, 0)]));
  depot.start_convoy(pl, cnv);
  s += "[convoy]\n";
}
return s + "ok";
