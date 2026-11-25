# 道路の停留所を pak256 の物にしてゲームで確かめた記録（2026-11-26）

## 背景

[#94](https://github.com/128-bit-net/pak256/issues/94)。#72 で AMI の停留所（`ami_road_bus_stop`・`ami_road_truck_stop`）に置き換えていた道路の停留所を、pak256 の物（`pak256_bus_stop`・`pak256_truck_stop`）に戻した。絵は #44 の物（`objects/station/road_stops/`）で、`draw_stops.py` を道路の停留所だけにし、PNG・表は同じ内容を書き出した（表のコメントの語だけ違う）。

## 手順

1. `python -X utf8 tools/build.py`。makeobj のログに `Warning`・`ERROR` は無い（`station.road_stops.pak` が再び組まれる）。`tools/test_*.py` は通る。
2. `tools/game.py --save flat_512_left_v64 --port 47841 --interactive`（検証環境 `addon_check`。昼夜は止める）で開いたまま起動し、次を `--send-file` で流した。
   - バス・郵便: `tools/vehicle_check/road_stop_bus.nut`。街を 2 つ（x=60 と x=100、y=60）置いて東西の道でつなぎ、道の上に `pak256_bus_stop` を置き（x=60・x=100 は交差点で「通り抜けの駅は置けない」と出たので、隣の x=61・x=101 に置いた）、AMI の車庫でバス（`pak256_bus`）と郵便のトラック（`pak256_mail_truck`）を買って 2 つの停留所を往復させた。
   - 石炭: `tools/vehicle_check/road_stop_coal.nut`（原点 y=110 に直した写しで）。炭鉱（x=62）と発電所（x=82）の脇の道に `pak256_truck_stop` を置き、石炭のトラック（`pak256_coal_truck`）2 台を走らせた。
3. `@settle 25` の後、速さ 16 で走らせ、8 秒おきに編成の位置・速さ・積載を読んだ。速さ 2・`gui.set_zoom(3)` で撮った。

## 結果

- 自前の停留所が置け、バス・郵便のトラックが 2 つの停留所の間を往復して、積載が 2 になった（旅客・郵便を積み降ろした）。
- 石炭のトラックは、炭鉱の脇の荷役所で積み（積載 83%）、発電所の脇の荷役所へ運んで降ろし（積載 0）、戻った。
- 道路のツールバーに、pak256 の停留所（バス停・荷役所）と AMI の停留所（「停」「荷」）が両方並ぶ。AMI の停留所は AMI の側で外す（[stations.md](../stations.md) の「AMI の停留所の扱い」）。

| 画像 | 見所 |
|---|---|
| `2026-11-26_road-stops-screens/1_bus_stop.png` | 街（盛岡）の道の上のバス停（x=61, y=60）。赤い屋根の待合 |
| `2026-11-26_road-stops-screens/2_coal_stop.png` | 炭鉱の脇の荷役所（x=63, y=113）。小屋と木箱 |
| `2026-11-26_road-stops-screens/3_coal_plant_stop.png` | 発電所の脇の荷役所（x=83, y=113） |
| `2026-11-26_road-stops-screens/4_toolbar_road.png` | 道路のツールバー。右の下段に AMI の停留所と pak256 の停留所の道具が並ぶ |

## 確かめていないこと

- 英語の画面での画面の名前（`text/en.tab` の `Bus Stop`・`Truck Loading Bay`）。日本語の画面（`ja`）は、停留所の名前の窓の「停」の字と、表の訳（バス停・荷役所）で見た。
- ツールバーから停留所を置く操作（スクリプトの `tool_build_station` で置いた）。
- 保存データ（α0.2・α0.3 の仮の停留所、#72 以降の AMI の停留所）を読んだときの動き（[stations.md](../stations.md)。コードの読みだけ）。
- 停留所の向き 8 通りのうち、画面に写ったもの以外。右側通行の地図、本家 125.0.1、夜。
- 向きの絵は #44 の確かめ（`records/2026-11-25_road-stops.md`）に頼る。
