# 道路の停留所・線路の駅（pak256 の物）

停留所と駅の、この pak の値と道具。決まりはサイトの [駅・停留所](https://128-bit-net.github.io/pak256/spec/station)（元は [site/spec/station.md](../site/spec/station.md)）。経緯は [記録](records/2026-11-27_spec-stations.md)。絵は簡単な物（箱を数式で描いた物）で、pak128 の絵は使っていない。

## 道路の停留所（pak256 の物）

pak256 の物（[#94](https://github.com/128-bit-net/pak256/issues/94)。AMI の停留所には頼らない）。置き場は `objects/station/road_stops/`。`draw_stops.py`（MIT）が PNG と表（`.yaml`）を書き出す（`python -X utf8 objects/station/road_stops/draw_stops.py`。Pillow が要る）。

| `name` | `obj` | `type` | `waytype` | 扱う貨物 | 画面の名前（ja / en） |
|---|---|---|---|---|---|
| `pak256_bus_stop` | `building` | `stop` | `road` | 旅客（`enables_pax`）・郵便（`enables_post`） | バス停 / Bus Stop |
| `pak256_truck_stop` | `building` | `stop` | `road` | 貨物（`enables_ware`。旅客・郵便は扱わない） | トラックの荷役所 / Truck Loading Bay |

- 値: `level` 2、登場年 1900（仮）、`allow_underground` 2、`noinfo` 1。建設費・維持費は書いていない。`cursor` は書かない。
- 置き方と高さの決まりは、サイトの [駅・停留所](https://128-bit-net.github.io/pak256/spec/station)の「大きさと基準点」。白線の位置は AMI の生活道路の 0.156・0.844。描く帯は `draw_stops.py` の `FAR`・`BUS_FAR`・`NEAR`、白線は `LINE_FAR`・`LINE_NEAR`。
- 検査 `tools/test_stations.py`: どの向きの絵も画面で白線の内側に画素を置かないこと。`test_bus_stop_back_edge` がバス停の歩道の奥の端（c = 0 まで。[#139](https://github.com/128-bit-net/pak256/issues/139)）を検査する。AMI の版を上げて道路の縁が動いたら、同じ場面を撮って奥に残る暗い行数を測り直す（[記録](records/2026-11-26_stop-back.md)）。
- ゲームでの確かめは [道路の停留所](records/2026-11-26_road-stops.md)・[白線に重ならない並び](records/2026-11-26_stop-overlap.md)の記録。

### pak256 の道路を作るときに見直す点

今の置き方は AMI の道路の形に合わせた物。pak256 専用の道路（[roadmap.md](roadmap.md) の「進め方」）を作るときは、次を見直す。

- 白線・路肩・奥の縁の位置（`draw_stops.py` の `LINE_FAR`・`LINE_NEAR`・`FAR`・`BUS_FAR`・`NEAR`。検査 `tools/test_stations.py` は `LINE_*` を読む）を、新しい道路の形に合わせる。道路の幅を実物に近づけて路肩が広くなれば、歩道を広げ、待合を手前の側にも置けるか（画面で白線に重ならないか）を確かめる。
- 道路の種類ごとに幅が違うなら、停留所は一番幅の広い道路に合わせる（1 つの停留所の絵はどの道路にも置かれる）。
- 道路の絵の側で停留所の分の路肩・歩道を持たせるかを決める（停留所の絵は道路を描かない）。
- 舗装がタイルの端まであるので、今の歩道は舗装の上に載る。道路の端に草地や歩道を残す形なら、設備をそこへ置ける。

### AMI の停留所の扱い・保存データへの影響

AMI の停留所は AMI の側で外した。経緯と、保存データを読んだときの動きは [記録](records/2026-11-27_spec-stations.md)。

## 線路の駅（pak256 の物）

置き場は `objects/station/rail_stops/`。`draw_stops.py`（MIT）が PNG と表（`.yaml`）を書き出す（`python -X utf8 objects/station/rail_stops/draw_stops.py`。Pillow が要る）。線路の信号は [signals.md](signals.md)。

## 駅の表

| `name` | `obj` | `type` | `waytype` | 扱う貨物 | 画面の名前（ja / en） |
|---|---|---|---|---|---|
| `pak256_train_station` | `building` | `stop` | `track` | 旅客（`enables_pax`。郵便・貨物は扱わない） | 駅 / Train Station |

- 値: `level` 2（容量 64。仮）、登場年 1900（仮）、`allow_underground` 2、`noinfo` 1。
- ホームの位置と高さの決まりは、サイトの [駅・停留所](https://128-bit-net.github.io/pak256/spec/station)の「大きさと基準点」。
- 確かめは [気動車の停車](records/2026-11-25_rail-train.md)・[信号と周回](records/2026-11-26_rail-signal.md)の記録。

## モノレールの駅

置き場は `objects/station/monorail_stops/`（[#156](https://github.com/128-bit-net/pak256/issues/156)）。`draw_stops.py`（MIT）が、線路の駅の道具を読んで PNG と表を書き出す（`python -X utf8 objects/station/monorail_stops/draw_stops.py`）。

| `name` | `obj` | `type` | `waytype` | 扱う貨物 | 画面の名前（ja / en） |
|---|---|---|---|---|---|
| `pak256_monorail_station` | `building` | `stop` | `monorail_track` | 旅客（`enables_pax`） | モノレールの駅 / Monorail Station |

- 値: `level` 2（仮）、登場年 1900（仮）、`allow_underground` 2、`noinfo` 1。車両は `length=9` なので、1 両なら 1 タイル、2〜3 両なら 2 タイル並べる。

## 下の地面

サイトの [駅・停留所](https://128-bit-net.github.io/pak256/spec/station)の「地面と季節」。道から離して置く拡張の建物を作るときは `needs_ground` が要る（[buildings.md](buildings.md) の「下の地面」。#126）。

## 向きの絵

8 通りの向きと、後ろと前の 2 層の決まりは、サイトの [駅・停留所](https://128-bit-net.github.io/pak256/spec/station)の「絵」。この pak の道具の並び:

- シートは 8 列（向き）× 3 行（0 行 = 後ろ、1 行 = 前、2 行 = 道具の絵）。セルの名前は `<名前>.<行>.<列>`。
- 道具の絵（`icon`）は 2 行 0 列のセルの左上の角に置いた 192px の角丸の四角（`draw_stops.py` の `tool_icon`）。道路の停留所は後ろ（奥の側）の絵だけ、線路の駅は向き 0 の後ろと前を重ねた絵から作る（理由は [記録](records/2026-11-27_spec-stations.md)）。192px にした理由は [記録](records/2026-11-25_rail-leftovers.md)（[#71](https://github.com/128-bit-net/pak256/issues/71)）。`cursor` は書かない。

## 港（pak256 の物）

[#154](https://github.com/128-bit-net/pak256/issues/154)。絵は仮（箱を数式で描いた物）で、pak128 の絵は使っていない。AMI の 256 版には港が無いので pak256 の物にした。置き場は `objects/station/ports/`。`draw_ports.py`（MIT）が PNG と表を書き出す。検査は `tools/test_stations.py` の `PortTest`。

| `name` | `type` | 建てる所 | 画面の名前（ja / en） |
|---|---|---|---|
| `pak256_pier` | `habour`（桟橋） | 水に面した 1 段の坂 | 桟橋 / Pier |
| `pak256_quay` | `dock`（岸壁） | 水に面した平らな土地（水面と同じ高さ） | 岸壁 / Quay |
| `pak256_canal_wharf` | `stop`・`waytype: water` | 運河（AMI の `ami_canal`）の道の上 | 運河の船着き場 / Canal Wharf |

- どれも 1x1 タイル、旅客・郵便・貨物を扱う（`enables_pax`・`enables_post`・`enables_ware`）。`level` 4、登場年 1900（値は仮）、建設費・維持費は書いていない（本体の既定）。
- 向きは桟橋・岸壁が 4 通り（水のある側が南・東・北・西の順）、運河の船着き場は停留所と同じ 8 通り。
- ダイヤの行き先は港の升でなく、手前の水面の升を指す（港の升を指すと、スクリプトでは「2 つ未満」と断られた）。
- 桟橋は、坂の上の端から板の斜路で下り、水の側は杭の上の平らな板。岸壁は 1m の敷き面と上屋・係船柱。船着き場は運河の両脇の板と待合の小屋で、船はその間を通る。
- 車庫は AMI の `ami_canal_depot`。**海では岸に接した升に置く**（四方のどこかが陸の水の升）。四方が水の升は、本体が「Depots must be built on flat dead-end way tiles!」で断った（OTRP v64、2026-11-26。辺 4 通りと角 4 通りは建ち、四方が水の 3 升は断られた）。海につながる短い運河の行き止まりにも建ち、そこから出た船が海を走った。陸の運河では行き止まりに置く。
- 川は確かめていない。川の物（`river_type` に指定する道）が pak に無いため。[#158](https://github.com/128-bit-net/pak256/issues/158) で行う。
- ゲームでの確かめは [記録](records/2026-11-26_ships.md)。

# 路面電車の停留所（pak256 の物）

置き場は `objects/station/tram_stops/`（[#153](https://github.com/128-bit-net/pak256/issues/153)）。`draw_stops.py`（MIT）が PNG と表（`.yaml`）を書き出す。道路の停留所の `draw_stops.py` の関数と定数を読んで使う（写して増やさない）。

| `name` | `obj` | `type` | `waytype` | 扱う貨物 | 画面の名前（ja / en） |
|---|---|---|---|---|---|
| `pak256_tram_stop` | `building` | `stop` | `tram_track` | 旅客（`enables_pax`。郵便・貨物は扱わない） | 路面電車の停留所 / Tram Stop |

- 値: `level` 2、登場年 1900（仮）、`allow_underground` 2、`noinfo` 1。建設費・維持費は書いていない。
- 置き方の決まり（白線の外、架線の柱の所を空ける）は、サイトの [駅・停留所](https://128-bit-net.github.io/pak256/spec/station)の「大きさと基準点」。柱の位置の値は AMI の `TRAM_CAT_POLE_U` 4.2・`CAT_POLE_S` 0.35（1 タイル 10）から出した a = 0.5・c = 0.08 で、`draw_stops.py` の `ROOFS` と `tools/test_stations.py` の `test_tram_stop_clear_of_catenary_pole` が読む。AMI の版を上げて柱の位置が動いたら、両方を直して撮り直す（[記録](records/2026-11-27_tram195.md)）。
- ゲームでの確かめは [記録](records/2026-11-26_tram.md)。

# 道路の車庫（AMI の物）

道路の車庫は、仮の物（`pak256_road_depot`。[#58](https://github.com/128-bit-net/pak256/issues/58)）を [#64](https://github.com/128-bit-net/pak256/issues/64) で消し、AMI の 256 版の `ami_road_depot`（`ami-256-alpha.2` の `ami_road.pak`。[layout.md](layout.md) の「AMI の 256 版を同梱する」）に置き換えた。pak256 には車庫を置かない。ゲームでの確かめは [記録](records/2026-11-25_ami-road-depot.md)。

- **保存データへの影響**: 保存データは建物を名前で引く。仮の車庫（`pak256_road_depot`）を置いた保存データを今の pak256 で読むと、その名前の建物が無い。本体（125.0.1）のコードの読みでは次のとおり（`gebaeude_t::rdwr`・`depot_t::rdwr_vehikel`。置いて確かめてはいない）。町の建物の名前の形でなければ、`gebaeude_t::rdwr` は「足りない pak」として記録し、タイルは空のまま抜ける。続く `depot_t::rdwr_vehikel` は「tile for depot not found」のエラーを記録したうえで、**その車庫のタイルを住宅（`city_res` の 1 つ目）に差し替え**、中の車両は普通に読み込む。つまり、仮の車庫があった場所は**住宅の見た目の車庫の入れ物**になり、中の編成は入ったまま（車両の定義が残っていれば。クリックすれば車庫の窓が開く）になるはず。町の建物として街に数えられるかは未確認。**α0.2（v0.2.0、2026-11-25 公開）は仮の車庫を含む**ので、α0.2 で車庫を置いた保存データを、この置き換えの後の版で読むと、このおかしな建物が残る。α0.2 の保存データは引き継げないと、次の版の説明（Release の本文）に書く。実際の動きは、v0.2.0 の保存データを今の pak で読んで確かめる（まだ）。
- 置いた直後は、本体が建設中の絵（黄黒の縞。`objects/gui/construction`）を出す。ゲームを進めると（AMI の車庫は置いてからゲーム内の約 100 秒。`Game.settle(20)` の速さ 64 で足りた）、車庫の絵になる。確認のときに待つ（`Game.settle`）。
