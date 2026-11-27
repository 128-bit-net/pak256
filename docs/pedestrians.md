# 歩行者

街の道路の脇を歩く人（本体の `obj: pedestrian`。[#172](https://github.com/128-bit-net/pak256/issues/172)）の、この pak の値と道具。決まりはサイトの [歩行者](https://128-bit-net.github.io/pak256/spec/pedestrian)（元は [site/spec/pedestrian.md](../site/spec/pedestrian.md)）。絵は仮。置き場は `objects/pedestrian/walkers/` で、`draw_pedestrians.py`（MIT）が `walkers.png` と `walkers.yaml` を書き出す。

## 種類

背丈は `pak256` の 256px のセルでの px。子どもは大人の 0.75 倍、女性は 0.92 倍（四捨五入）。`distributionweight` は出やすさ。

| name | 種類 | 背丈 px | offset | distributionweight |
|---|---|---|---|---|
| `pak256_pedestrian_man` | 男性 | 16 | 18 | 8 |
| `pak256_pedestrian_woman` | 女性 | 15 | 24 | 8 |
| `pak256_pedestrian_child` | 子ども | 12 | 12 | 4 |

向きは 8 方向（`s`・`w`・`sw`・`se`・`n`・`e`・`ne`・`nw`）の止まった絵。歩く動き（`steps_per_frame`）は付けていない。

## 大きさ

サイトの [歩行者](https://128-bit-net.github.io/pak256/spec/pedestrian)の「大きさと基準点」（大人 16px。2026-11-27、ユーザーの決定。#172。3 案の比べは[記録](records/2026-11-27_pedestrians.md)）。大きさは `draw_pedestrians.py` の `ADULT_PX` の 1 か所で変えられる（`--adult` で試しに書き出せる）。

## 歩く位置

決まりと本体の動きは、サイトの [歩行者](https://128-bit-net.github.io/pak256/spec/pedestrian)の「足元の位置」と「本体の動きの注意」。足元の位置は `draw_pedestrians.py` の `foot_offset_px` が計算し、`tools/test_pedestrians.py` が検査する。`offset` は AMI の生活道路（`ami_road_local`）の路肩（道路の端から白線まで 0〜0.156 タイル。[stations.md](stations.md)）に収める。ゲームで確かめた範囲は[記録](records/2026-11-27_pedestrians.md)。

## 雪の気候

歩行者の絵に季節・気候の差はない（サイトの「歩行者」の「絵」）。雪の気候の路肩は明るいので、どの種類も見分けられる。
