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
- 大きさ・`length`・描く位置・セルの決まりは、サイトの [飛行機・空港](https://128-bit-net.github.io/pak256/spec/air)（元は [site/spec/air.md](../site/spec/air.md)）。手本の実物は Junkers Ju 52/3m の長さ 18.9m・翼の幅 29.25m・高さ 4.5m（[SKYbrary](https://skybrary.aero/index.php/JU52)・[Warbirds Resource Group](https://warbirdsresourcegroup.org/LRG/luftwaffe_junkers_ju52_specifications.html)。2026-11-26 に検索で確かめた。高さは別の型や測り方で 5.55m・6.1m とする資料もある）。`length` は 11。
- 置き場は `objects/vehicle/air/`。`draw_aircraft.py`（MIT）が書き出す。

## 空港の作り方・絵・飛行の高さ

決まりはサイトの [飛行機・空港](https://128-bit-net.github.io/pak256/spec/air)（元は [site/spec/air.md](../site/spec/air.md)）。経緯と本体の読みは [記録](records/2026-11-27_spec-ship-air.md)、ゲームの確かめは [記録](records/2026-11-26_air.md)。確かめた並びを作る道具は `tools/vehicle_check/air.nut`。絵の幅と停止線の値は `objects/airport/draw_airport.py`。

## 確かめていないこと

- 郵便や貨物を運ぶ飛行機は無い（飛行機は旅客だけ）。
- 雪の気候（道と建物に雪の絵は無い）と、地図の端の近くの空港。
- 複数の飛行機が同時に使う空港、滑走路の順番待ち。
- 古い保存データへの影響は無い見込み（物を足しただけ）。
