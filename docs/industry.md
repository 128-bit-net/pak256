# 産業（炭鉱と発電所）

最初の産業の連鎖（炭鉱 → 発電所。[goods.md](goods.md) の「最初の産業の連鎖」）の dat と絵の決め事。[#43](https://github.com/128-bit-net/pak256/issues/43) で足した。絵は仮（箱を数式で描いた物）で、見た目は後から描き直す。pak128 の絵は使っていない。ゲームでの確かめは [記録](records/2026-11-25_coal-industry.md)。

置き場は `objects/industry/coal_chain/`。`draw_industry.py`（MIT）が PNG と表（`.yaml`）を書き出す。直すときはスクリプトを直して流し直す（`python -X utf8 objects/industry/coal_chain/draw_industry.py`。Pillow が要る）。

## 種類

| 名前 | 画面の名前（ja / en） | 大きさ | 見た目 | 高さ |
|---|---|---|---|---|
| `pak256_coal_mine` | 炭鉱 / Coal Mine | 2x2 タイル（52.8m 四方） | 立坑の櫓・巻上げ小屋・積込み小屋・石炭の山 | 櫓の上まで 17m |
| `pak256_coal_power_plant` | 石炭火力発電所 / Coal Power Plant | 3x3 タイル（79.2m 四方） | ボイラー棟・タービン棟・煙突・石炭の搬入棟・開閉所・石炭置き場 | 煙突 28m、ボイラー棟 20m |

- 縮尺は [buildings.md](buildings.md) と同じ（1 タイル = 26.4m、高さ 1m = 5.94px）。建物は 1 通りの向きだけ（`backimage[0]` のみ。正方形の足跡なので、回しても足跡は変わらない）。
- 絵は 256x256 のセルを、タイルごとに 1 枚。シートは（列 = x のタイル、行 = y のタイル）の並びで、セルの名前は `<名前>.<行>.<列>`。物はメートルの座標で並べ、タイルごとに、そのタイルの上に立つ部分だけを描く（壁は壁の端があるタイル、屋根はタイルの範囲で切る）。屋根の継ぎ目に薄い線が見える（仮の絵なので直さない）。
- 高さはセルに収まる範囲にした（`draw_industry.py` が、セルの上をはみ出すと止まる）。実物の煙突は 100m 前後あるが、28m にした。高い物は大きいセル（`cell_size`。[layout.md](layout.md)）に描き直す。
- 煙（`smoke`）・畑（`fields`）・夜の灯りは付けていない。煙の物（`base.smokes` 相当）は pak256 にまだ無い。

## 値

pak128 の炭鉱（`shaft_coal_mine`）と石炭火力の発電所（`old_powerplant_kraftwerk`）の dat の値（機能上の数値）を、同じにした。dat の文・コメント・絵は写していない。concept の E（pak128 に寄せる）に沿う。値の釣り合いは、車両がそろってから見直す（roadmap の段階 4）。

| キー | 炭鉱 | 発電所 | 意味（本体のコードで確かめたのは名前の読みだけ。値は pak128 のまま） |
|---|---|---|---|
| `location` | `Land` | `Land` | 陸に置く |
| `distributionweight` | 1 | 2 | 地図に出る数の重み（大きいほど出やすい）。炭鉱 : 発電所 = 1 : 2 |
| `productivity` | 80 | 600 | 基本の生産量 |
| `range` | 50 | 40 | 生産量の振れ幅（地図を作るときの乱数の幅） |
| `outputgood` / `outputcapacity` | `Kohle` / 300 | | 炭鉱が出す貨物と、蓄えられる量 |
| `inputgood` / `inputcapacity` | | `Kohle` / 8000 | 発電所が受ける貨物と、蓄えられる量 |
| `inputfactor` | | 50 | 入力の割合（pak128 と同じ値。本体での意味は確かめていない） |
| `electricity_amount` | 150 | 800 | 電気（炭鉱は使う量、発電所は作る量） |
| `electricity_boost` | 800 | 0 | 電気が来たときの生産の増え |
| `passenger_demand` / `passenger_boost` | 20 / 500 | 20 / 800 | 旅客が着いたときの生産の増え |
| `mail_demand` / `mail_boost` | 0 / 0 | 5 / 500 | 郵便が着いたときの生産の増え |
| `mapcolor` | 176 | 131 | 地図の窓の色（パレットの番号） |
| `intro_year` | 1700 | 1890 | 登場年 |
| `needs_ground` | 1 | 1 | 地面が要る |

- 気候（`climates`）は書かない。pak128 の発電所は温帯・ツンドラ・岩山・地中海に限るが、地面の種類が少ない今は、全気候にした。
- 炭鉱は 2x2（大・小で 2 種ある pak128 の `shaft_coal_mine` に合わせた）。pak128 の露天掘り（`open_coal_mine`）と小さな炭鉱（`shaft_coal_mine_small`）は足していない。

## 地図に出る数

新しい地図を作るとき、本体は `distributionweight` に応じて産業を置く。炭鉱 1 : 発電所 2 の比は pak128 と同じ。実際に地図の作成画面でどう出るかは確かめていない（起動画面の間は MCP が答えないため）。炭鉱と発電所のつながり（炭鉱が出した石炭を発電所が受ける）は、本体が地図を作るときに産業をつなぐ（`tools` では確かめられない。ゲームでの確かめは、つなぎを `tool_link_factory` で手で付けた）。
