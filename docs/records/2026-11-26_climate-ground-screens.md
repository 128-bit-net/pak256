# 気候ごとの地面をゲームで確かめた記録（2026-11-26）

[#101](https://github.com/128-bit-net/pak256/issues/101)。7 気候の `ClimateTexture` を気候ごとの式で描き分けた（`objects/ground/temperate/draw_ground.py`）。寸法と本体の読み方は [ground.md](../ground.md)。

## 手順

1. `python -X utf8 objects/ground/temperate/draw_ground.py` で絵を書き出し、`python -X utf8 tools/build.py` で組んだ（makeobj の `Warning` は 0、終了コード 0）。
2. `tools/game.py --interactive`（`addon_check` の写し、ポート 47820、保存データ `flat_512_left_v64`）で起動し、`docs/records/2026-11-26_climate-ground-screens/terrain.nut` で地形と気候を作った（`tool_set_climate` で気候を塗る）。画面は `gui.set_zoom(3)`・`gui.jump` と `@capture`。
3. 地形を変えると気候が高さで決まり直すので、気候は地形の後に塗る（湖は、水位を上げた後に塗り直した）。

## 画像（地図の座標）

| 画像 | 見所 |
|---|---|
| `1_flat.png` | 7 気候の平地（砂漠・熱帯・地中海・温帯・ツンドラ・岩・雪の順。x = 100 + 8×(番号−1) + 4、y = 104） |
| `2_border.png` | 隣り合う 2 気候の境 6 つ（x = 108・116・…・148、y = 104） |
| `3_slope1.png` | 1 段の丘の縁（周りは温帯、温帯の丘の周りは熱帯。丘 i の x = 100 + 14×(i−1) + 1、y = 124）。雪の丘は雪線の上下 |
| `4_slope2.png` | 2 段の丘の縁（x = 100 + 14×(i−1) + 2、y = 145） |
| `5_coast.png` | 湖の海岸。砂漠（x=106）・温帯（136）・雪（166）・ツンドラ（196）、y = 176 |

## 分かったこと

- 気候の境の坂は、`SlopeTrans` が重なって気候どうしがなめらかにつながる。1 段・2 段の坂とも、隙間・重なり・継ぎ目のずれは見えなかった。
- 雪は、坂の明るい面（光の絵で 1.5 倍ほど明るくなる）で白く飛ぶ。雪の絵の明るさを 228 前後に抑えてある。

## 確かめていないこと

- 新しく生成した地図での気候の自動配分（保存データを読んで、気候を `tool_set_climate` で塗った）。
- 木・街の建物との見え方（#102・#103）。
- 気候の境の縁の小さな丸い突起は `SlopeTrans`（#5）の形のまま。直すかは見た目の判断。
