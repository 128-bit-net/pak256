# 仮の道路の車庫をゲームで確かめた記録（2026-11-25）

## 背景

[#58](https://github.com/128-bit-net/pak256/issues/58)。道路の車両（#41・#42）を買う車庫が無かったので、仮の道路の車庫 `pak256_road_depot`（[stations.md](../stations.md)）を足した。pak256 だけで、車庫を置いてバスと石炭のトラックを買い、走らせられるかを OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。

## 手順

1. `python -X utf8 tools/build.py`。makeobj のログに `Warning`・`ERROR` は無い。`tools/test_*.py` は 149 件が通る。
2. `tools/game.py` の `Game`（検証環境 `addon_check`、保存データ `flat_512_left_v64`、昼夜は止める、ポート 47880・47881）。**借りる pak は無し**（`--extra-pak` を使わない）。
3. 向きの確認: 道路の十字（中心 50,50、腕 3 タイル）の 4 つの袋小路の端に、`command_x.build_depot` で車庫を置いた。置いた直後は建設中の黄黒の縞なので、`debug.set_game_speed(64)` で約 12 秒進めてから撮った。
4. 走らせる確認: `tools/vehicle_check/run.py`（`--vehicle pak256_bus`、`--vehicle pak256_coal_truck`）。`course.nut` が車庫（`building_desc_x.get_building_list(depot)` で道路の車庫を探す）を道の脇に置き、`append_vehicle` で買い、編成を出して走らせる。

## 結果

- 車庫は置けた（`build_depot` が成功）。4 つの袋小路に置いた車庫は、どれも道路の側に建物の入口（戸のある面か、舗装）を向けて出た。戸が見える向き（戸が南東・南西の面）の車庫は、座標 47,50（道が南東へ）と 50,47（道が南西へ）で、戸が道路に向いて見えた。
- 車庫でバス（1 両・2 両連結）と石炭のトラック（同）を買えた。編成が車庫から出て、輪の道（直線 4 方向・斜め・曲がり）とバス停の上を走った（バス・トラックとも 8 方向のうち 7 方向の撮影が取れた）。
- 確かめていないこと: ツールバーから車庫を置く操作と置くときのカーソルの出方（スクリプトの `build_depot` だけ）、 北東・北西の側の戸（隠れる面）の見え方、右側通行の地図、本家 125.0.1。

画像（1930 年。`gui.set_zoom(3)`）:

| 画像 | 見所 |
|---|---|
| `2026-11-25_road-depot-screens/depot_four_sides.png` | 十字の道の 4 つの袋小路に置いた車庫（座標 53,50・47,50・50,53・50,47） |
| `2026-11-25_road-depot-screens/bus_depot.png` | 車庫（43,39）の脇から出るバス（2 両連結）と、バス停 |
| `2026-11-25_road-depot-screens/coal_truck_depot.png` | 同じ場所の石炭のトラック |
| `2026-11-25_road-depot-screens/bus_run.png` | 輪の道を走るバス |
| `2026-11-25_road-depot-screens/coal_truck_run.png` | 輪の道を走る石炭のトラック |
