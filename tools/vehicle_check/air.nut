// 飛行機と空港の確かめ（docs/airport.md・#155）。MIT License。tools/vehicle_check/air_run.py が Game.sq で流す。
// 先頭に足す変数: AX, AY（空港 A の滑走路の西の端）, BX, BY（空港 B の同じ所）, LEN（滑走路の長さ。タイル）。
// 空港は、東西の滑走路 1 本、3 タイル南の平行な誘導路、滑走路へつなぐ 2 本の短い誘導路、行き止まりの駅 1 つと格納庫 1 つ。
// 旅客機 1 機を A の格納庫から出して A と B の駅を往復させる。街は air_run.py が公共のプレーヤーで置く（会社の建設費に混ぜないため）。
local pl = player_x(0);
local s = "";
local cmd = command_x(tool_build_way);
function way(a, b, name) {
  local e = command_x(tool_build_way).work(player_x(0), a, b, name);
  return e == null ? "" : "[" + name + ": " + e + "]";
}
local airports = [[AX, AY], [BX, BY]];
foreach (a in airports) {
  local x = a[0], y = a[1];
  s += way(coord3d(x, y, 0), coord3d(x + LEN, y, 0), "pak256_runway");
  s += way(coord3d(x + 2, y + 3, 0), coord3d(x + LEN - 2, y + 3, 0), "pak256_taxiway");
  s += way(coord3d(x + 2, y + 3, 0), coord3d(x + 2, y, 0), "pak256_taxiway");
  s += way(coord3d(x + LEN - 2, y + 3, 0), coord3d(x + LEN - 2, y, 0), "pak256_taxiway");
  // 駅と格納庫は、誘導路から南へ出した行き止まり
  s += way(coord3d(x + 6, y + 3, 0), coord3d(x + 6, y + 5, 0), "pak256_taxiway");
  s += way(coord3d(x + 11, y + 3, 0), coord3d(x + 11, y + 5, 0), "pak256_taxiway");
  // 街の人が使えるように、駅を 3 つ並べて 1 つの駅にする（拾う範囲は 2 タイル）
  s += way(coord3d(x + 5, y + 3, 0), coord3d(x + 5, y + 5, 0), "pak256_taxiway");
  s += way(coord3d(x + 7, y + 3, 0), coord3d(x + 7, y + 5, 0), "pak256_taxiway");
  local e = null;
  foreach (dx in [6, 5, 7]) {
    e = command_x(tool_build_station).work(pl, coord3d(x + dx, y + 5, 0), "pak256_airport");
    if (e != null) return s + "stop: " + e;
  }
  local depot_desc = null;
  foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) {
    if (d.get_name() == "pak256_hangar") { depot_desc = d; break; }
  }
  if (depot_desc == null) return s + "no hangar";
  e = command_x.build_depot(pl, coord3d(x + 11, y + 5, 0), depot_desc);
  if (e != null) return s + "depot: " + e;
}// 滑走路の物がそのまま残っているか（誘導路をつないだ升）
foreach (a in airports) {
  local t = tile_x(a[0] + 2, a[1], 0).find_object(mo_way);
  s += "junction=" + (t == null ? "none" : t.get_desc().get_name()) + "\n";
}
local depot = depot_x(AX + 11, AY + 5, 0);
local plane = null;
foreach (v in vehicle_desc_x.get_available_vehicles(wt_air)) if (v.get_name() == "pak256_airliner") plane = v;
if (plane == null) return s + "no plane";
depot.append_vehicle(pl, convoy_x(0), plane);
local list = depot.get_convoy_list();
local cnv = list[list.len() - 1];
cnv.change_schedule(pl, schedule_x(wt_air, [schedule_entry_x(coord3d(AX + 6, AY + 5, 0), 0, 0), schedule_entry_x(coord3d(BX + 6, BY + 5, 0), 0, 0)]));
depot.start_convoy(pl, cnv);
return s + "ok";
