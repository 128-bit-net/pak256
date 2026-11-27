# 飛行機と空港（pak256 の物）

旅客を飛行機で運ぶ物。α0.5 で入れた（[#155](https://github.com/128-bit-net/pak256/issues/155)）。AMI の 256 版（`ami-256-alpha.9` の 9 つの pak）には飛行機の物が 1 つも無いので、全部 pak256 の物として持つ。絵は仮（色を塗った地面と箱、多角形の機体）で、他の pak の絵は使っていない。

## 物

| `name` | `obj` | 種類 | 画面の名前（ja / en） | `cost` | `maintenance` | `topspeed` | `max_weight` | `intro_year` |
|---|---|---|---|---|---|---|---|---|
| `pak256_runway` | `way` | `waytype: air`・`system_type: 1`（滑走路） | 滑走路 / Runway | 175000 | 3000 | 100 | 20 | 1900 |
| `pak256_taxiway` | `way` | `waytype: air`・`system_type: 0`（誘導路） | 誘導路 / Taxiway | 30000 | 500 | 30 | 20 | 1900 |
| `pak256_airport` | `building` | `type: stop`・旅客と郵便・`level` 2 | 空港 / Airport | — | — | — | — | 1900 |
| `pak256_hangar` | `building` | `type: depot` | 格納庫 / Hangar | — | — | — | — | 1900 |

- 単位は `cost`・`maintenance` が 1/100、`topspeed` は km/h、`max_weight` は t。駅と格納庫の建設費は `config/simuconf.tab` の `cost_multiply_airterminal`（× `level`）と `cost_depot_air`。
- 滑走路と誘導路の値は、pak128 の初期の物（`old_runway`・`old_taxiway`）の機能上の数値を目安にした。pak128 にある引退年は書いていない。登場年は pak256 の他の駅と同じ 1900（仮）。
- 置き場は `objects/airport/`。`draw_airport.py`（MIT）が 4 つの物の PNG と表を書き出す（`python -X utf8 objects/airport/draw_airport.py`。Pillow が要る）。

### 旅客機

| `name` | 画面の名前（ja / en） | `payload` | `speed` | `power` | `gear` | `weight` | `cost` | `runningcost` | `intro_year` | `length` |
|---|---|---|---|---|---|---|---|---|---|---|
| `pak256_airliner` | 旅客機 / Airliner | 18 | 211 | 1599 | 50 | 7 | 2110146 | 65 | 1930 | 11 |

- 値は pak128 の同じ時代の旅客機（Junkers Ju 52）の機能上の数値（dat の文・絵・作者名は写していない。[goods.md](goods.md) と同じ扱い）。登場年だけ pak256 の開始年にした。引退年は書かない。1 機で飛ぶ（前後につながない）。郵便の飛行機は無い。
- 大きさは**実物比例**（[standards.md](standards.md) の 4 章「船・飛行機」。車両の「手本の 2 倍」は当てはめない）。実物の Junkers Ju 52/3m の長さ 18.9m・翼の幅 29.25m・高さ 4.5m（[SKYbrary](https://skybrary.aero/index.php/JU52)・[Warbirds Resource Group](https://warbirdsresourcegroup.org/LRG/luftwaffe_junkers_ju52_specifications.html)。2026-11-26 に検索で確かめた）から、`length` = 18.9 ÷ 1.65 = 11（胴は 11 × 1.65 = 18.15m に描く）。翼の幅と高さは実物の値のまま（高さは別の型や測り方で 5.55m・6.1m とする資料もある）。
- 描画位置は機首が基準点で、胴は後ろへ伸びる。飛行機に車線のずれは無いので、道の中心に描く。翼がタイルを超えるので 512 のセル。
- 置き場は `objects/vehicle/air/`。`draw_aircraft.py`（MIT）が書き出す。

## 空港の作り方

本体の決まり（OTRP の `simvehicle.cc`・`simtool.cc` を読み、ゲームで下の並びを確かめた）。

- 離着陸は滑走路（`system_type: 1`）でする。滑走路の端（1 方向だけにつながる升）が要る。誘導路は、端でない升につなぐ。
- 駅と格納庫は誘導路の升に置く。駅は滑走路の上には置けない。
- pak256 の駅と格納庫は向き 4 通りで、**誘導路の行き止まり**に置く。
- 駅は並べると 1 つの駅になる。拾う範囲は 2 タイル（`station_coverage`）なので、街の建物の近くに置く。
- 着陸の前に、飛行機は滑走路の手前を大回りする。本体の読みでは、地図の端の近くの空港には着陸の経路が作れない（確かめていない）。
- 確かめた並び: 東西の滑走路 19 升、3 升南の平行な誘導路、両端の近くの 2 本の短い誘導路で滑走路へ、南への行き止まりに駅と格納庫（`tools/vehicle_check/air.nut`）。

## 絵の決まり

- 滑走路は幅がタイルの 0.72、誘導路は 0.40。滑走路の端には縦じま、誘導路には黄色い線。まっすぐ抜ける滑走路に脇からつながる枝は、誘導路の幅と色で描く。
- 坂の絵と雪の絵は無い（滑走路は平らな所に置く前提）。
- 駅は舗装の駐機場と、脇の奥の辺の細長いターミナル。黄色い停止線は、飛行機の機首が止まる所（つながる辺から 0.90 タイル）。ターミナルを手前や行き止まりの端に置くと、飛行機を隠すか機首と重なる。
- 格納庫は、口が画面の手前を向く向き（南・東につながる）では中が見え、奥を向く向きでは屋根と壁を飛行機の上に描く。

## 飛行の高さと影

256px のタイルでの見え方（2026-11-26、OTRP v64。[記録](records/2026-11-26_air.md)）。

- 影は本体が描く。飛んでいる間、機体と同じ絵を黒の半透明（75%）で地面に描く（OTRP と本家 125.0.1 の `get_outline_image`・`get_outline_colour` が同じ）。絵に影を入れない。
- OTRP v64 は、既定（`allow_higher_flight`）で高さが最高速で決まる: `max(5, speed / 33)` 段。旅客機（211km/h）は 6 段 = 192px（画面で機体と影が約 200px 離れて見えた）。1 段は 32px。
- 本家 125.0.1 は、ソースの読みでは 3 段（96px）で、速さによらない（ゲームでは確かめていない）。

## 確かめていないこと

- 郵便や貨物を運ぶ飛行機は無い（飛行機は旅客だけ）。
- 雪の気候（道と建物に雪の絵は無い）と、地図の端の近くの空港。
- 複数の飛行機が同時に使う空港、滑走路の順番待ち。
- 古い保存データへの影響は無い見込み（物を足しただけ）。
