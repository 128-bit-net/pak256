# 車両の長さと描画位置

車両を描くときの決まり。[#40](https://github.com/128-bit-net/pak256/issues/40) で、道路の車両（バス・トラック）の分を決めた。線路の車両の分は [#46](https://github.com/128-bit-net/pak256/issues/46) で足した（concept の D。下の「線路の車両」）。背景は [concept.md](concept.md) の C・D。

決まりは `tools/vehicles.py`（MIT）に計算として置いてある。描くスクリプトはそれを読み、`tools/test_vehicles.py` が絵と表を検査する。決まりを変えるときは、[standards.md](standards.md)・この文書・`vehicles.py` を一緒に直す。線路の車両（気動車・付随車）の分は下の「線路の車両」（[#46](https://github.com/128-bit-net/pak256/issues/46)）。

## 長さ・描画位置

大きさ（手本の 2 倍）・`length` の決め方・画面での 1 単位の長さ・描画位置（前後・車線・高さ）・セルの大きさの**決まりは [standards.md](standards.md) の 4 章**にある（#80 でまとめた）。計算は `tools/vehicles.py`。この文書には、決めたときの確かめと、standards.md に書ききれない細目（車線のずれの表・OTRP 固有の注意）を残す。

### 前後の位置（細目）

- 本体は連結の 2 両目以降の基準点を、前の車両の基準点から `length` 後ろに置くので、車体が隙間なく並ぶ。
- 止まったとき（停留所・駅・信号の手前）、先頭の基準点はタイルの出口の辺の近くに来る（試験の停留所で、出口の辺から約 1.6 単位手前）。車体はタイルの中に収まり、先へはみ出さない。
- pak64・pak128 で多い描き方（長さ 8 の車両をセルの真ん中に描く。前の端は基準点から 4 単位前。OTRP の逆向き運転の式もこの形を前提にしている）とは違う。そのため OTRP の逆向き運転（`reverse_base_offset`）で逆向きに走る車両を入れるときは `config/simuconf.tab` に `reverse_base_offset_<向き> = 0,0,-128` が要る見込み（コードを読んだだけ。そのときに確かめる）。

### 横の位置（車線）

- 絵は右側の車線に描く。本体は 1 組の絵を、右側通行ではそのまま、左側通行では決まったずれを足して描く。このずれ（64px のタイルで 12,6 など、`vehicles.py` の `DRIVELEFT_64`。256px のタイルでは 4 倍）は、本家 125.0.1（`vehicle_base.cc` で固定）と OTRP（`simuconf.tab` の `driveleft_base_offset_*` で変えられる既定）で同じ。
- 右側の車線の基準点は、このずれのちょうど半分を反対の向きに置いた所。左側通行でも道路の中心から同じ距離の反対側に来る。`simuconf.tab` の `driveleft_base_offset_*` は書かない（本家では効かないため）。

| 向き（dat の添字） | 進む向き（画面） | 右側の車線の点のずれ（px） |
|---|---|---|
| `n` | 右上 | (24, 12) |
| `s` | 左下 | (-24, -12) |
| `e` | 右下 | (-24, 12) |
| `w` | 左上 | (24, -12) |
| `ne` | 右 | (0, 12) |
| `sw` | 左 | (0, -12) |
| `se` | 下 | (-24, 0) |
| `nw` | 上 | (24, 0) |

- 道路の中心からの距離は、軸の向きで 3/16 タイル（4.95m）。AMI の 256 版の道路（`ami-256-alpha.1`）の車線の中心（路側の白線 3.37 の半分、タイルの 0.1685）より 0.5m 外で、画面では軸の向きで約 2.4px 外になる（白線との距離から測って 0.184 タイル）。斜めは、本体のずれで道路の中心から 0.133 タイル、AMI の斜めの車線の中心は断面の縮め方の読み方で 0.107〜0.119 タイルなので、画面で約 1〜5px 外（計算だけ。斜めは画面で測っていない）。ゲームで、左右どちらの通行でも 8 方向とも車線に乗って見えた（下の「試験」）。
- 車体の幅は実物の幅より広い（手本の 2 倍。[standards.md](standards.md) の 4 章。バスは 3.1m 相当）。

高さ（車輪の下端・1m = 5.94px）とセルの大きさ（256 か 512 か）は [standards.md](standards.md) の 2・4 章。512 のセルの作り方は [layout.md](layout.md) の「セルの大きさ」。

## 見本

見本のバス `objects/vehicle/road/sample_bus/`（`pak256_sample_bus`、実物 12m・幅 2.5m・高さ 3.2m、描く大きさはバスと同じで `length=9`）。絵は仮（箱を組んだ物）。`draw_bus.py`（MIT）が絵と表を書き出す。作り直すとき: `python -X utf8 objects/vehicle/road/sample_bus/draw_bus.py`（Pillow だけで動く）。新しい車両は、このスクリプトのように `tools/vehicles.py` の `footprint`・`to_screen` で車体の四隅を出して描く。

## 道路の車両

[#41](https://github.com/128-bit-net/pak256/issues/41)（バスと郵便のトラック）・[#42](https://github.com/128-bit-net/pak256/issues/42)（石炭のトラック）・[#59](https://github.com/128-bit-net/pak256/issues/59)（表と描く道具を 1 つにそろえた）。絵は仮（箱を組んだ物）で、pak128 の絵は使っていない。置き場は `objects/vehicle/road/<種類>/`（`bus`・`mail_truck`・`coal_truck`）。描く道具は `objects/vehicle/road/draw_vehicles.py`（MIT）の 1 本で、絵（PNG）と表（`.yaml`）を車両ごとに書き出す。直すときはスクリプトの表（`VEHICLES`）を直して流し直す（`python -X utf8 objects/vehicle/road/draw_vehicles.py`。Pillow だけで動く。1 台だけなら `--only pak256_coal_truck`）。車両を足すときは `VEHICLES` に 1 件足し、この表に 1 行足す。検査は `tools/test_vehicles.py`（表の値と、この表の値が同じこと・絵が決まりの位置にあること）。

| `name` | 画面の名前（ja / en） | `freight` | 実物の長さ・幅・高さ | `length` | `payload` | `speed` | `power` | `gear` | `weight` | `cost` | `runningcost` | `intro_year` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `pak256_bus` | バス / Bus | `Passagiere` | 12m・2.5m・3.2m | 9 | 70 | 60 | 205 | 80 | 11 | 661000 | 39 | 1930 |
| `pak256_mail_truck` | 郵便のトラック / Mail Truck | `Post` | 7m・2.2m・3.0m（運転席 2.3m） | 6 | 44 | 60 | 77 | 80 | 5 | 863000 | 38 | 1930 |
| `pak256_coal_truck` | 石炭トラック / Coal Truck | `Kohle` | 7m（仮。2 軸の貨物車の大きさ）・2.5m・2.7m（運転席の上） | 8 | 12 | 55 | 95 | 90 | 8 | 384000 | 24 | 1930 |

- 単位: `speed` は km/h、`weight` は t、`cost`・`runningcost` は 1/100 単位。
- 大きさと `length` の決まりは [standards.md](standards.md) の 4 章（手本は pak128。バス 9・郵便 6・石炭 8）。表の実物の寸法は元の値で、描く大きさではない。絵の車体は `length` × 1.65m に描く（バス 14.85m・郵便 9.9m・石炭 13.2m 相当）。絵は同じ「描画位置」の決まりのとおり（車体の前の端が基準点、右側の車線）。どれも 1 タイルに収まるので 256 のセル。
- **値の目安**（バスと郵便のトラック）: バスは pak128 の `NovaBus_RTS-06_WFD`（定員 70・速さ 60・出力 205・重さ 11・費用 661000・`RunningCost` 39）、郵便のトラックは pak128 の `Mail_Truck_2`（定員 44・出力 77・費用 863000・維持費 38）。速さは pak128 の郵便のトラック（74）より落として 60 にそろえた（AMI の道路 `ami_road_local` は 40km/h、`ami_road_general` は 120km/h。道路の上限で決まる）。重さは pak128 の郵便のトラックが 2t と軽すぎるので、7m の箱型のトラックとして 5t にした（根拠のある計算ではなく、仮の値）。`gear` は pak128 の 80（どちらも）。絵は使っていない。
- **値の目安**（石炭のトラック）: pak128 の石炭のトラックの 1 つ（`Bulk_Truck_2`、2 軸の貨物車）の dat の値（機能上の数値）を、同じにした。dat の文・コメント・絵・作者名は写していない（名前と機能上の数値だけなので、元の作者の記載は要らないと判断した。[goods.md](goods.md) と同じ。法律の専門家には確かめていない）。登場年だけは、見本のバスと同じ 1930 にした（pak128 は 1955。遊べる版の保存データが 1930 年代から始まるため）。値の釣り合いは、産業と車両がそろってから見直す（roadmap の段階 4）。
- **登場年は 1930**。pak256 の開始年（`config/simuconf.tab` の `starting_year`）に合わせた仮の値。pak128 の元の車は 1979 年（郵便のトラック）と 1992 年（バス）なので、時代の幅（初期の車・新しい車）は [roadmap.md](roadmap.md) の「車両の顔ぶれと時代」で決める。引退年は書かない。
- バス: 旅客を運ぶ。郵便のトラック: 運転席は前の 3 割（低い）、荷台の箱は後ろの 7 割。石炭のトラック: 赤い運転席と、上が開いた灰色の荷台。貨物は `Kohle` だけで、炭鉱の出力と発電所の入力と同じ貨物（本体は貨物の名前で結ぶ）。
- 積み荷の絵: 石炭のトラックだけが `freightimage`（シートの 2 行目。荷台に石炭の山）を持つ。バスと郵便のトラックは空の絵（`emptyimage`）だけ。連結（`constraint`）・煙・音・引退年も書いていない。
- 旅客と郵便は、バス停（`pak256_bus_stop`。[stations.md](stations.md)）で積み降ろす。トラックの荷役所（`pak256_truck_stop`）は貨物だけで、旅客・郵便は扱わない。石炭は、炭鉱の脇と発電所の脇に置いた荷役所（[stations.md](stations.md)）で行う（最初の産業の連鎖。[goods.md](goods.md)・[industry.md](industry.md)）。
- 車庫は AMI の 256 版の `ami_road_depot`（[stations.md](stations.md)）を使う。

## 線路の車両

[#46](https://github.com/128-bit-net/pak256/issues/46)（気動車と付随車）。線路は AMI の 256 版の `ami_rail_ballast`（`ami-256-alpha.2`）。絵は仮（箱を組んだ物）で、pak128 の絵は使っていない。置き場は `objects/vehicle/rail/<名前>/`（`railcar`・`railcar_trailer`）。描く道具は `objects/vehicle/rail/draw_trains.py`（MIT）で、道路の車両の道具（`draw_vehicles.py`）の箱を組む関数・色の決まりを読んで使う。直すときはスクリプトの表（`VEHICLES`）を直して流し直す（`python -X utf8 objects/vehicle/rail/draw_trains.py`。Pillow だけで動く）。車両を足すときは `VEHICLES` に 1 件足し、この表に 1 行足す。検査は `tools/test_vehicles.py` の `TestRailVehicles`。

| `name` | 画面の名前（ja / en） | `freight` | 実物の長さ・幅・高さ | `length` | `payload` | `speed` | `power` | `gear` | `weight` | `cost` | `runningcost` | `intro_year` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `pak256_railcar` | 気動車 / Railcar | `Passagiere` | 20m・2.8m・3.6m | 12 | 80 | 90 | 220 | 100 | 21 | 8959000 | 221 | 1930 |
| `pak256_railcar_trailer` | 気動車の付随車 / Railcar Trailer | `Passagiere` | 20m・2.8m・3.6m | 12 | 80 | 90 | 0 | 100 | 17 | 1894000 | 28 | 1930 |

- **値の目安**: pak128 の気動車（`Haru_VT98` とその付随車 `Haru_VT98_car`）の dat の値（機能上の数値）を、同じにした。dat の文・コメント・絵・作者名・連結の指定・煙・音は写していない（名前と機能上の数値だけなので、元の作者の記載は要らないと判断した。道路の車両の石炭のトラックと同じ扱い。法律の専門家には確かめていない）。登場年は pak256 の開始年に合わせて 1930（pak128 は 1952）。値の釣り合いは、産業と車両がそろってから見直す（roadmap の段階 4）。
- 気動車は動力あり（`engine_type: diesel`。架線の要らない種類にした）、付随車は動力なし。連結の指定は付随車の `constraint[prev]` だけ。付随車は気動車の後ろにしかつながない（付随車の `constraint[prev]` に気動車と付随車を書いた。先頭にはならない）。気動車 1 両だけの編成も、ゲームで走って往復した（`rail_run.py --trailer 0`）。煙・音は書かない（pak に無い物を引かない）。
- **長さ**: 20m → `length=12`（[standards.md](standards.md) の 4 章）。車体の絵は 12 × 1.65m = 19.8m に描く。幅と高さは実物の 1.40 倍・1.20 倍に描く（pak128.Japan の手本の 2 倍。描いた値で幅 3.9m・高さ 4.3m）。道床の見立て（約 3.4m）より幅が広いが、駅のホームには当たらない（[記録](records/2026-11-26_scale-check.md)）。
- **横の位置**: 線路の中心（基準点）に描く。本体は左側通行のずれを道路の車両（`road_vehicle_t`）にしか足さず（`simvehicle.cc` の `road_vehicle_t::get_screen_offset`）、線路の車両は通行の向きに関わらず線路の中心に出る。`tools/vehicles.py` の `footprint(…, centered=True)` が、このずれ無しの車体の枠を出す。
- **前後の位置**: 道路の車両と同じ（車体の前の端が基準点）。前後を同じ形に描いたので、逆向きに走っても形は崩れない。
- **高さ**: 車輪の下端は地面の高さ（`RAIL_WHEEL_DROP_PX = 0`）。AMI の線路は新描画位置でレールが地面より下がる（レールの基準面が `Datum(4,1)` で、256 版は 2 倍）が、ゲームで走らせて撮ると、車輪の下端が地面のままで、車体の下の暗い帯の下端がレールの上に乗って見えた（試験は [記録](records/2026-11-25_rail-train.md)）。
- **セル**: 20m の車体は、画面で横の斜め（11.3px/単位）で 136px 伸びて 1 タイルのセル（256）に収まらないので、512 のセルに描く。256 のセルの絵を 512 のセルの真ん中に置き（256 のセルの座標 + 128）、表に `cell_size: 512` と、各絵の位置合わせ `,-128,-128` を書く（[layout.md](layout.md) の「セルの大きさ」の試しと同じ形）。makeobj は警告なく組め、ゲームで 512 のセルの車両が線路の上の決まった位置に出ることを東西の直線で確かめた。
- 絵: 気動車は両端に運転席（前面ガラス）、付随車は両端に貫通扉の窓。クリーム色の車体に緑の帯、床の下に暗い台車の帯。
- **隣の線路**（[#104](https://github.com/128-bit-net/pak256/issues/104)）: 太くした車両を、1 タイル隣り合う 2 本の線路の 90° の曲がりで走らせても、はみ出しは隣の線路に届かなかった（[記録](records/2026-11-26_scale-check.md)）。
- **曲がり・坂**（[#71](https://github.com/128-bit-net/pak256/issues/71)。画面は [記録](records/2026-11-25_rail-leftovers.md)）: 車体は 1 枚の絵で、曲がりの角のタイルでは進む向きの斜めに描かれる。AMI の線路の 90° の曲がりは 1 タイルの中で折れるので、20m（`length=12`）の車体は角の外へはみ出して草地に掛かって見える（付随車との継ぎ目も折れない）。坂では車体が水平のまま走り、1 段の坂をまたぐ継ぎ目に段差が出るが、車輪はどちらの車もレールの上に乗った。**直さない**: 1 両 1 枚の絵はこの本体の決まりで、はみ出しを無くすには車両を短くして両数を増やすか、車両ごとに曲がり用の絵を足すしかなく、仮の絵の段階では釣り合わない。見えたことは記録に残した。
- 旅客は、駅（`pak256_train_station`。[stations.md](stations.md)）で積み降ろす。信号（`pak256_rail_signal`。[signals.md](signals.md)）を置き、1 本の線路に複数の編成を走らせる試験は `tools/vehicle_check/signal.nut`（#73）。車庫は AMI の `ami_rail_depot`（`ami_rail.pak`）。

## 試験

描画位置が道路に合うかを、ゲームで走らせて撮る道具が `tools/vehicle_check/`（MIT）にある。

- 要る物: OTRP 本体（MCP のある版）の検証環境と、OTRP 本体のリポジトリの `mcp_client.py`。Windows で動かす前提。ゲームの用意・起動・閉じ方は [game-check.md](game-check.md) の道具（`tools/game.py`）。
- `course.nut`: 道路の輪（道路は名前で選ぶ。既定は AMI の `ami_road_local`）（直線の 4 方向・SE と SW の向きの斜め・直角の曲がり 2 つ）と、停留所・車庫を置き、時計回りの 1 両・2 両連結と反時計回りの 1 両を走らせる。
- `run.py`: 検証環境を写した作業フォルダで本体を起動し、`course.nut` を流して、向きごとに撮る（夜は飛ばす）。ゲームは起動した PID で閉じる。使い方は `run.py` の先頭。
- 試験の印: `draw_bus.py --marker --out <場所>` で、車体の地面の枠（桃色）・前の端（青の線）・基準点（青の点）・タイルの中心（桃色の十字）を重ねた絵を書く（git に入れない）。
- 右側通行: 手元の右側通行の保存データは使えなかった（起動画面で止まる）。`draw_bus.py --emulate-right` で、左側通行のずれを先に引いた絵（名前に `_right_test`）を書き、左側通行の地図で走らせると、右側通行の地図での見え方と同じ所に出る（本体は左側通行で絵をずらすだけなので）。
- 線路の車両の試験は `tools/vehicle_check/rail_run.py` と `rail.nut`（#46）。東西の直線の線路に、駅 2 つ（3 タイルずつ）と AMI の車庫を置き、気動車 + 付随車の 1 編成を 2 つの駅の間で往復させて、一定の間隔で撮る（`--cities` で街を 2 つ置いて旅客を運ばせ、財務の窓も撮る。`--trailer 0` で 1 両だけ。`toolbar_rail.png` は線路のツールバー）。使い方は `rail_run.py` の先頭。曲がり・坂は `tools/vehicle_check/rail_curve_run.py` と `rail_curve.nut`（#71）。コの字の線路（東に 90° の曲がり 2 つ、北の辺に高さ 1 の丘）に、駅 2 つと車庫を置き、気動車 + 付随車が通るときに、先頭のタイルを真ん中にして撮る（使い方は `rail_curve_run.py` の先頭）。線路の丘は、先に地面を上げてから 1 タイルずつ敷く（線路を敷いた後では地面が上がらず、長く敷くと本体が丘をよける経路を選ぶ）。
- 道路の停留所は pak256 の物（#94。`tools/vehicle_check/road_stop_bus.nut`・`road_stop_coal.nut` で確かめた）、車庫（#64）は AMI の `ami_road_depot` を使う（借りる pak は要らない）。

#40 で撮った画面は [records/2026-11-25_vehicle-rules.md](records/2026-11-25_vehicle-rules.md)。#41 のバスと郵便のトラックをゲームで走らせた記録は [records/2026-11-25_bus-mail.md](records/2026-11-25_bus-mail.md)。

## 決めていないこと

- 線路の分岐・斜め（あれば）・2 段以上の坂での線路の車両の見え方（直線・90° の曲がり・1 段の坂は確かめた。上の「曲がり・坂」）。
- 逆向き運転の `reverse_base_offset`（上の「前後の位置（細目）」と [standards.md](standards.md) の 4 章）。線路の終点での折り返し（編成の向きを入れ替えない通常の折り返し）では、前後対称の絵で崩れは見えなかった。
- 長い連節バスを 512 のセルで描いたときの、曲がりでのはみ出しの見え方（列車は #71 で見た。上の「曲がり・坂」）。
- 追い越し（OTRP の `overtaking_base_offset`。既定では左側通行のずれと同じ値を足す）のときの車線の位置。
