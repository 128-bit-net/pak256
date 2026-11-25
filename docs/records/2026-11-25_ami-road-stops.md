# 仮の道路の停留所を AMI の停留所に置き換えた確かめの記録（2026-11-25）

## 背景

[#72](https://github.com/128-bit-net/pak256/issues/72)。仮のバス停・荷役所（`pak256_bus_stop`・`pak256_truck_stop`。#44）を消し、AMI の 256 版 `ami-256-alpha.3`（128na/simutrans-addon-dev#277）の `ami_road_bus_stop`・`ami_road_truck_stop` に置き換えた。`vendor/ami/ami.env` を alpha.3（pak256 の非公開の Release `vendor-ami-256-alpha.3` の zip。SHA-256 は ami.env のとおり）に上げた。

## 手順

1. `python -X utf8 tools/build.py`。makeobj のログに `Warning`・`ERROR` は無い。AMI の pak は 7 つ入り、`ami_road.pak` に `ami_road_bus_stop`・`ami_road_truck_stop` がある。`station.road_stops.pak` は組まれなくなった。`tools/test_*.py` は 193 件が通る。
2. `tools/game.py` の `Game`（検証環境 `addon_check`、保存データ `flat_512_left_v64`、昼夜は止める、ポート 47880）。
   - バス・郵便: [bus.nut](2026-11-25_ami-road-stops-screens/bus.nut)（#41 の確かめの手順で、停留所の名前だけ AMI の物）。街を 2 つ置いて東西の道でつなぎ、各街の中心の南の道の上に `ami_road_bus_stop` を置き、AMI の車庫でバスと郵便のトラックを買って 2 つの停留所を往復させた。
   - 石炭: [coal.nut](2026-11-25_ami-road-stops-screens/coal.nut)（#42 の確かめの手順で、荷役所の名前だけ AMI の物）。炭鉱と発電所の脇の道に `ami_road_truck_stop` を置き、石炭トラック 2 台を走らせた。
3. `Game.settle(25)` で工事中を終わらせ、速さ 16 で走らせ、5 秒ごとに編成の位置・速さ・積載を読んだ。
4. 道路の見た目: alpha.2 と alpha.3 の `ami_road.pak` で、同じ道（東西の道に南北の道を T 字・十字、斜めの道と Y 字）を敷いて撮り比べた。十字・Y 字の周りの画面は、時計の表示を除いて同じ画素だった（画像は残していない）。

## 結果

- AMI の停留所が置けた（`tool_build_station` で名前を渡す）。
- バス: 2 つの停留所の間を往復し、積載が 1〜5 で増減した（旅客を積み降ろした）。郵便のトラックも積載 2 を積んだ。
- 石炭トラック: 炭鉱の脇の荷役所で積み（積載 83%）、発電所の脇の荷役所で降ろして（積載 0）戻った。
- 道路の見た目は alpha.2 と同じ。

| 画像 | 見所 |
|---|---|
| `2026-11-25_ami-road-stops-screens/bus.png` | 街の道の上の AMI のバス停の絵（青い屋根。一部は建物に隠れる。バスは写っていない） |
| `2026-11-25_ami-road-stops-screens/toolbar_road.png` | 道路のツールバー。右端に AMI の車庫・バス停（「停」）・荷役所（「荷」）の道具の絵が出る（灰色でない） |
| `2026-11-25_ami-road-stops-screens/coal.png` | 炭鉱（右上）の脇の道の AMI の荷役所に停まる石炭トラック |

## 確かめていないこと

- ツールバーから停留所を置く操作と、置くときのカーソル。AMI の dat（`ami_road_bus_stop`・`ami_road_truck_stop`）も、車庫・標識と同じく `cursor=` に位置の指定が付いていない。置くときにカーソルの絵がずれる見込みで、既知（[#76](https://github.com/128-bit-net/pak256/issues/76)・128na/simutrans-addon-dev#282 で直す。#72 では直さない）。
- 仮の停留所を置いた保存データを読んだときの動き（[stations.md](../stations.md)。本体のコードの読みだけ。置いて確かめてはいない）。
- 停留所の向き 8 通りの見え方（撮った画面に写る範囲だけ）。右側通行の地図、本家 125.0.1。
- 荷役所の 1 つだけの物・連なりの端の絵。駅の範囲（集客の範囲）の表示。
