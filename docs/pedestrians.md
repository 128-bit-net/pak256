# 歩行者

街の道路の脇を歩く人（本体の `obj: pedestrian`）の決まり（[#172](https://github.com/128-bit-net/pak256/issues/172)）。絵は仮。置き場は `objects/pedestrian/walkers/` で、`draw_pedestrians.py`（MIT）が `walkers.png` と `walkers.yaml` を書き出す。

## 種類

背丈は `pak256` の 256px のセルでの px。子どもは大人の 0.75 倍、女性は 0.92 倍（四捨五入）。`distributionweight` は出やすさ。

| name | 種類 | 背丈 px | offset | distributionweight |
|---|---|---|---|---|
| `pak256_pedestrian_man` | 男性 | 16 | 18 | 8 |
| `pak256_pedestrian_woman` | 女性 | 15 | 24 | 8 |
| `pak256_pedestrian_child` | 子ども | 12 | 12 | 4 |

向きは 8 方向（`s`・`w`・`sw`・`se`・`n`・`e`・`ne`・`nw`）の止まった絵。歩く動き（`steps_per_frame`）は付けていない。

## 大きさ

大人は **16px**（2026-11-27、ユーザーの決定。下の 3 案を比べて「16px（中間）」。#172。絵は仮）。

| 案 | 大人の背丈 | 見え方 |
|---|---|---|
| 実物の大きさ（1 単位 = 1.65m。[standards.md](standards.md) の 1 章） | 約 10px（1.7m） | 建物の扉（約 12px）に合うが、顔や服が見分けにくく、暗い路面では小さな点に見える |
| 中間（採った値） | 16px（実物なら約 2.7m） | 扉より少し高く、バス停の屋根（2.9m ≒ 17px）の下に収まる。人と分かる |
| 手本の 2 倍（道路の車両と同じ扱い） | 24px | 扉の 2 倍で、バス停の屋根を超える |

手本の背丈は pak128 の `base/pedestrians`（`base.pedestrians.all.pak`）の歩行者の画像の外接枠を `tools/pakimage.py` で測った: `pedestrian 1`〜`8` の高さは 12px（`pedestrian 4` だけ子どもで 10px）、128px のセルでの値。2 倍の 24px が 256px のタイルでの手本の 2 倍になる。

車両の「手本の 2 倍」（[standards.md](standards.md) の 4 章）は道路と線路の車両だけの決まりで、建物は実物の大きさで描いてある。人は建物・停留所のそばに立つので、実物と手本の間にした。大きさは `draw_pedestrians.py` の `ADULT_PX` の 1 か所で変えられる（`--adult` で試しに書き出せる）。比べた画像は[記録](records/2026-11-27_pedestrians.md)。

## 歩く位置

本体（OTRP の `vehicle/pedestrian.cc`）の動き:

- 歩行者は進む向きの右側の線か左側の線を歩く。左側のときは、本体が絵を (256 − 2 × `offset`)/256 タイル左へずらす。道路の車両の左側通行のずれは足されない。
- このため、**絵は進む向きの右側の、道路の端から `offset`/256 タイルの所に足元を描き**、同じ `offset` を表に書く。両方をそろえると、どちらの側でも道路の端から同じ距離になる。`foot_offset_px` が計算し、`tools/test_pedestrians.py` が検査する。
- `offset` は AMI の生活道路（`ami_road_local`）の路肩（道路の端から白線まで 0〜0.156 タイル。[stations.md](stations.md)）に収める。種類ごとに 12・18・24 と変えて、同じ所に重ならないようにした。
- 出るのは、建物が旅客を出したときと、停留所に旅客が着いたとき（本体の設定 `random_pedestrians`・`stop_pedestrians`）。寿命は数十秒で、直線と角の道路に出る。

ゲームで確かめた範囲と残った点（[記録](records/2026-11-27_pedestrians.md)）:

- 直線の道路では、両側とも白線の外の路肩を歩く。確かめたのは `ami_road_local` だけで、ほかの道路の種類は見ていない。
- 交差点では本体が進む先を乱数で選び、直進する人は交わる道路の舗装の上を通る。
- 1 タイルごとに曲がる斜めの道路では、車線の上を歩く人がいる。本体が歩行者の位置をタイルごとの向きで決めるためで、絵では直せない。
- 停留所のタイルでは、待合の絵と重なって手前に描かれる。

## 雪の気候

歩行者の絵に季節・気候の差はない（本体の `pedestrian` に持てない）。雪の気候の路肩は明るいので、どの種類も見分けられる。
