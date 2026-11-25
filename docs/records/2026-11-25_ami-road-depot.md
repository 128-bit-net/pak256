# AMI の道路の車庫で車両を買えることを、ゲームで確かめた記録（2026-11-25）

## 背景

[#64](https://github.com/128-bit-net/pak256/issues/64)。仮の道路の車庫（`pak256_road_depot`。#58）を消し、AMI の 256 版 `ami-256-alpha.2` の `ami_road_depot` に置き換えた。pak256 だけ（借りる pak なし）で、車庫を置いてバスを買い、走らせられるかを OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。

## 手順

1. `python -X utf8 tools/build.py`。AMI の zip は `vendor/ami/ami.env` の URL（pak256 の非公開の Release `vendor-ami-256-alpha.2`）から、`gh release download` で取れた（SHA-256 が合った）。makeobj のログに `Warning`・`ERROR` は無い。AMI の pak は 7 つ（`ami_road.pak`・`ami_rail.pak` など）入った。`tools/test_*.py` は 187 件が通る。
2. `tools/game.py` の `Game`（検証環境 `addon_check`、保存データ `flat_512_left_v64`、昼夜は止める、ポート 47880）。[setup.nut](2026-11-25_ami-road-depot-screens/setup.nut) を流した。東西の道（`ami_road_local`、x=50〜80・y=60）の 55,60 から南へ 1 タイルの枝を出し、その端（55,61）に車庫（`building_desc_x.get_building_list(depot)` で見つかった道路の車庫）を置き、道の上にバス停を 2 つ（60,60 と 78,60）置いた。
3. `Game.settle(20)` で工事中を終わらせ、車庫を撮った。車庫でバス（`pak256_bus`）を買い、2 つのバス停を回るダイヤを組んで出し、速さ 8 で約 56 秒走らせた。

## 結果

- 道路の車庫は `ami_road_depot` ただ 1 つで、`build_depot` が成功した（pak256 に仮の車庫は無い）。
- 車庫でバスを買えた（`append_vehicle`。車庫の窓で見える買える道路車両は 4 つ）。編成は車庫から出て、2 つのバス停の間（60,60〜78,60）を往復した（速さ 32〜43、78,60 のバス停で速さ 0 に止まった）。

画像（1930 年。`gui.set_zoom(3)`）:

| 画像 | 見所 |
|---|---|
| `2026-11-25_ami-road-depot-screens/depot.png` | 道の南の脇（55,61）に置いた AMI の道路の車庫 |
| `2026-11-25_ami-road-depot-screens/bus_run.png` | 車庫から出て、バス停（60,60）を走るバス |

## 確かめていないこと

- 車庫の向き 4 通りの見え方（南西の面のみ撮った）。ツールバーから車庫を置く操作と、置くときのカーソル。
- 仮の車庫を置いた保存データを読んだときの動き（[stations.md](../stations.md) の「保存データへの影響」。本体のコードの読みだけ。タイルが住宅に差し替わる見込み）。
- 車庫の窓でバスを買う画面（買えたことは `append_vehicle` の成功と、車庫の窓で見える道路車両の数 4 つ）。
- `ami-256-alpha.2` の `ami_road.pak` には `ami_road_general` も入るので、街どうしの道路が変わる（街の成長・車線の位置は `alpha.1` のときの確かめのまま。再確認は別に行う）。
- 右側通行の地図、本家 125.0.1。
