# 産業（炭鉱と発電所）

最初の産業の連鎖（炭鉱 → 発電所。[goods.md](goods.md) の「最初の産業の連鎖」）の dat と絵の決め事。[#43](https://github.com/128-bit-net/pak256/issues/43) で足した。絵は仮（箱を数式で描いた物）で、見た目は後から描き直す。pak128 の絵は使っていない。ゲームでの確かめは [記録](records/2026-11-25_coal-industry.md)。

置き場は `objects/industry/coal_chain/`。`draw_industry.py`（MIT）が PNG と表（`.yaml`）を書き出す。直すときはスクリプトを直して流し直す（`python -X utf8 objects/industry/coal_chain/draw_industry.py`。Pillow が要る）。

## 種類

| 名前 | 画面の名前（ja / en） | 大きさ | 見た目 | 高さ |
|---|---|---|---|---|
| `pak256_coal_mine` | 炭鉱 / Coal Mine | 2x2 タイル（52.8m 四方） | 立坑の櫓・巻上げ小屋・積込み小屋・石炭の山 | 櫓の上まで 17m |
| `pak256_coal_kraftwerk`（名前の約束は下） | 石炭火力発電所 / Coal Power Plant | 3x3 タイル（79.2m 四方） | ボイラー棟・タービン棟・煙突・石炭の搬入棟・開閉所・石炭置き場 | 煙突 28m、ボイラー棟 20m |

- 縮尺は [standards.md](standards.md) の 1 章（1 タイル = 26.4m、高さ 1m = 5.94px）。建物は 1 通りの向きだけ（`backimage[0]` のみ。正方形の足跡なので、回しても足跡は変わらない）。
- 絵は 256x256 のセルを、タイルごとに 1 枚。シートは（列 = x のタイル、行 = y のタイル）の並びで、セルの名前は `<名前>.<行>.<列>`。物はメートルの座標で並べ、タイルごとに、そのタイルの上に立つ部分だけを描く（壁は壁の端があるタイル、屋根はタイルの範囲で切る）。屋根の継ぎ目に薄い線が見える（仮の絵なので直さない）。
- 高さはセルに収まる範囲にした（`draw_industry.py` が、セルの上をはみ出すと止まる）。実物の煙突は 100m 前後あるが、28m にした。高い物は大きいセル（`cell_size`。[layout.md](layout.md)）に描き直す。
- 発電所は煙突の口から煙を出す（`pak256_smoke_chimney`、`smoketile[0]=1,0`・`smokeoffset[0]=2,-26`・`smokeuplift=14`・`smokelifetime=6000`。[smoke.md](smoke.md)）。炭鉱は煙突が無いので煙も無い。畑（`fields`）・夜の灯りは付けていない。

## 値

pak128 の炭鉱（`shaft_coal_mine`）と石炭火力の発電所（`old_powerplant_kraftwerk`）の dat の値（機能上の数値）を、同じにした。dat の文・コメント・絵は写していない。concept の E（pak128 に寄せる）に沿う。値の釣り合いは、車両がそろってから見直す（roadmap の段階 4）。

| キー | 炭鉱 | 発電所 | 意味（本体のコードで確かめたのは名前の読みだけ。値は pak128 のまま） |
|---|---|---|---|
| `location` | `Land` | `Land` | 陸に置く |
| `distributionweight` | 1 | 2 | 同じ役の産業どうしの選ばれやすさ（終端の消費者どうし、同じ貨物の生産者どうし。本体の `bauer/fabrikbauer.cc`）。今は消費者が発電所 1 種、石炭の生産者が炭鉱 1 種なので、数の比には効かない |
| `inputsupplier` | | 0 | 地図を作るとき、発電所の消費量（`productivity`・`inputfactor`）から、つなぐ炭鉱の数が決まる |
| `productivity` | 80 | 600 | 基本の生産量 |
| `range` | 50 | 40 | 生産量に足す乱数の幅（0 から `range`−1。本体の `simfab.cc`） |
| `outputgood` / `outputcapacity` | `Kohle` / 300 | | 炭鉱が出す貨物と、蓄えられる量 |
| `inputgood` / `inputcapacity` | | `Kohle` / 8000 | 発電所が受ける貨物と、蓄えられる量 |
| `inputfactor` | | 50 | 入力の割合（pak128 と同じ値。本体での意味は確かめていない） |
| `electricity_amount` | 150 | 800 | 電気（炭鉱は使う量、発電所は作る量） |
| `electricity_boost` | 800 | 0 | 電気が来たときの生産の増え |
| `passenger_demand` / `passenger_boost` | 20 / 500 | 20 / 800 | 旅客が着いたときの生産の増え |
| `mail_demand` / `mail_boost` | 0 / 0 | 5 / 500 | 郵便が着いたときの生産の増え |
| `mapcolor` | 176 | 131 | 地図の窓の色（パレットの番号） |
| `intro_year` | 1700 | 1890 | 登場年 |
| `needs_ground` | 1 | 1 | 建物の絵の下に地面を残して描く（置ける条件ではない） |

- 気候（`climates`）は書かない。pak128 の発電所は温帯・ツンドラ・岩山・地中海に限るが、地面の種類が少ない今は、全気候（水を除く）にした。
- 炭鉱は 2x2（大・小で 2 種ある pak128 の `shaft_coal_mine` に合わせた）。pak128 の露天掘り（`open_coal_mine`）と小さな炭鉱（`shaft_coal_mine_small`）は足していない。

## 発電所の名前の約束

本体は、dat のキーでなく、**名前が `kraftwerk` か `Power Plant` で終わる**ことで発電所（電気を作る側）と見なす（OTRP の fork の `descriptor/reader/factory_reader.cc`。pak128 の `old_powerplant_kraftwerk` はこれで動く）。このため発電所は `pak256_coal_kraftwerk` と付けた。名前を変えると発電所でなくなり、電気の収支・変電所の置き方が変わる。名前を後から変えると保存データの互換も壊れる。`tools/test_industry.py` が、この約束を検査する。

## 地図に出る数

炭鉱の数は、地図を作るとき発電所の消費量から決まる（上の `inputsupplier`）。実際に地図の作成画面でどう出るかは確かめていない（起動画面の間は MCP が答えないため）。炭鉱と発電所のつながりは、本体が地図を作るときに付ける。ゲームでの確かめは、つなぎを `tool_link_factory` で手で付けた。
