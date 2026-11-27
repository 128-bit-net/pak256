# アドオン作者向けの仕様: 道路の車両・街の車・歩行者（#205）

道路の車両・街の車・歩行者の決まりを、公開のサイト（`site/spec/vehicle-road.md`・`citycar.md`・`pedestrian.md`）へ移した。2026-11-27。構成は [#177 の記録](2026-11-27_spec-common.md)、線路の車両は [#204 の記録](2026-11-27_spec-rail-vehicles.md)。

## 置き場の分け方

- 車線のずれの 8 方向の表は、検査が読まないので、`docs/vehicles.md` からサイトの「道路の車両」へ移した。#204 では `docs/` に残していたが、道具を使わない作者が描くのに要るため。
- 車両・街の車・歩行者の値の表は `docs/` に残した（検査が名前で行を読む）。
- 歩行者の背丈の 3 案の比べは [#172 の記録](2026-11-27_pedestrians.md) にある。`docs/pedestrians.md` から消した表は次のとおり。

| 案 | 大人の背丈 | 見え方 |
|---|---|---|
| 実物の大きさ（1 単位 = 1.65m） | 約 10px（1.7m） | 建物の扉（約 12px）に合うが、顔や服が見分けにくく、暗い路面では小さな点に見える |
| 中間（採った値） | 16px（実物なら約 2.7m） | 扉より少し高く、バス停の屋根（2.9m ≒ 17px）の下に収まる。人と分かる |
| 手本の 2 倍（道路の車両と同じ扱い） | 24px | 扉の 2 倍で、バス停の屋根を超える |

手本の背丈は pak128 の `base/pedestrians`（`base.pedestrians.all.pak`）の歩行者の画像の外接枠を `tools/pakimage.py` で測った（`pedestrian 1`〜`8` は 12px、4 だけ子どもで 10px、128px のセル）。車両の「手本の 2 倍」は道路と線路の車両だけの決まりで、建物は実物の大きさなので、人は実物と手本の間にした。

## 本体のコードで確かめた事（OTRP の fork を読んだだけ）

サイトのページには根拠の書き添えを付けない（2026-11-27、ユーザーの指示。#214）。根拠はここに残す。

- 左側通行のずれは、道路の車両（`vehicle/simvehicle.cc` の `road_vehicle_t::get_screen_offset`）と街の車（`vehicle/simroadtraffic.cc` の `private_car_t::get_screen_offset`）が `driveleft_base_offsets` を足す。歩行者（`vehicle/pedestrian.cc` の `get_screen_offset`）は足さず、左側を歩くときだけ `offset` から計算して左へずらす。
- 電化: `simconvoi.cc` の `check_electrification` は waytype を問わず、動力車がすべて `electric` の編成を電化の道だけにする。道路の車両も `need_electric && !is_electrified()` で進めない（`vehicle/simvehicle.cc`）。
- 画像: 車両は、無い向きを `dir - 4` の絵で代える（`descriptor/vehicle_desc.h`）。街の車（`descriptor/citycar_desc.h`）と歩行者は代えず、`citycar_writer.cc`・`pedestrian_writer.cc` は書かなかった向きも空の画像として書く（`image_writer.cc`）。ゲームで一部の向きを省いて見てはいない。
- 街の車の dat のキーと既定: `distributionweight` 1、`speed` 80、`intro_year`・`retire_year` は 1900・2999（`descriptor/writer/citycar_writer.cc`、`descriptor/intro_dates.h`）。速度は道路の上限で抑える（`private_car_t::calc_current_speed`）。年表を使う地図では、その月に使える物だけを重みつきで選ぶ（`build_timeline_list`）。
- 歩行者の dat のキーと既定: `distributionweight` 1、`offset` 20、`intro_year` 1、`steps_per_frame`、`image[向き]` か `image[向き][コマ]`（`descriptor/writer/pedestrian_writer.cc`）。動きの絵は、コマの無い向きがあると表示で 0 で割る作りに読める（`pedestrian_t::get_image`）ので、ページは 8 方向すべてに描くとした。
- 歩行者の出方: 建物が旅客を出すとき（`simcity.cc`、`random_pedestrians`）と停留所に旅客が着いたとき（`simhalt.cc`、`stop_pedestrians`）。二方向だけの道のタイルに出る（`pedestrian_t::generate_pedestrians_at`）。進めない向きでは折り返し、分かれ道は乱数で選ぶ（`hop`）。歩く速さは固定（`sync_step`）、寿命は 6000〜40000 の乱数。

## dat の例

3 ページの例 4 つは、仮の形の画像を使って makeobj 60.12 で組み、`Warning` と `ERROR` の行が無いことを確かめた（[組むスクリプト](2026-11-27_spec-road-vehicles-screens/page_dat.py)）。ゲームでは試していない。例を直したら流し直す。

## 元の文書の直し

- `docs/vehicles.md` の車線の中心との比べは、`ami-256-alpha.1` の値だったので、今の `ami-256-alpha.9` の生活道路の画像で測り直した（直線だけ。[測る道具](2026-11-27_spec-road-vehicles-screens/lines.py)）。画面で約 2.4px から約 3px になった。
- 歩行者の路肩（道路の端から 0〜0.156 タイル）は、同じ測り方で `ami-256-alpha.9` でも合った。
- `docs/standards.md`・`docs/vehicles.md` の「standards.md の 4 章」を指す道路の車両の参照は、サイトのページへ向けた。

## 図と画面

- 図: `site/figures/draw_spec_figures.py`（車線の位置、歩行者の足元、道路の車両の 8 方向）。8 方向の図は、このリポジトリの仮のバスと石炭のトラックのシートを使う。
- 画面: [`shoot.py`](2026-11-27_spec-road-vehicles-screens/shoot.py) を OTRP v64、`flat_512_left_v64` で流し（2026-11-27、pak は `tools/build.py` で組んだ今の物と AMI `ami-256-alpha.9`）、[`crop.py`](2026-11-27_spec-road-vehicles-screens/crop.py) で切り出した。

## 確かめていないこと

- 本家 125.0.1、右側通行。
- ページの dat の例をゲームで動かすこと。
- 電気の道路の車両、連節バス・トレーラー、動きの付いた歩行者、向きを省いた街の車と歩行者。
