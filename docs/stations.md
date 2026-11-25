# 仮の停留所（バス停・荷役所）

バス（[#41](https://github.com/128-bit-net/pak256/issues/41)）とトラック（[#42](https://github.com/128-bit-net/pak256/issues/42)）が客と荷を積み降ろしできるように、道路の上の停留所を pak256 に仮に置いた（[#44](https://github.com/128-bit-net/pak256/issues/44)）。AMI の 256 版の停留所はまだ無く、作るのは先になる（128na/simutrans-addon-dev#264）。**AMI の物が出たら、ここの物は置き換えて消す。** 絵は仮（箱を数式で描いた物）で、pak128 の絵は使っていない。ゲームでの確かめは [記録](records/2026-11-25_road-stops.md)。

置き場は `objects/station/road_stops/`。`draw_stops.py`（MIT）が PNG と表（`.yaml`）を書き出す。直すときはスクリプトを直して流し直す（`python -X utf8 objects/station/road_stops/draw_stops.py`。Pillow が要る）。

## 控え（置き換えのため）

| `name` | `obj` | `type` | `waytype` | 扱う貨物 | 画面の名前（ja / en） |
|---|---|---|---|---|---|
| `pak256_bus_stop` | `building` | `stop` | `road` | 旅客（`enables_pax`）・郵便（`enables_post`） | バス停 / Bus Stop |
| `pak256_truck_stop` | `building` | `stop` | `road` | 貨物（`enables_ware`。旅客・郵便は扱わない） | トラックの荷役所 / Truck Loading Bay |

- どちらも 1x1 タイル、`level` 2（容量。本体は level × 32。値は仮で、pak128 の荷役所に合わせた）、登場年 1900（仮）、`allow_underground` 2、`noinfo` 1。
- AMI の物に置き換えるときは、次を行う。`objects/station/` を消す・`tools/test_stations.py` を消す・`text/` の 2 行ずつ（ja・en）を消す・`CREDITS.md` の行を消す・この文書を消す・`layout.md` の物の種類の表の `objects/station/` の行、道具の表の `test_stations.py` の行、「例外は…」の文を消す。AMI の物の名前は AMI の側（`ja_ami.tab` など）が持つ。
- 保存データは物の名前で引くので、置き換えると、置いてあった停留所は消える（本体は見つからない物を外す）。置き換えは、遊べる版（α0.2）より前に行うのがよい（保存データでの挙動は本体のコードの読みで、置いて確かめてはいない）。

## 向きの絵

停留所の dat は、向きに応じて 8 通りの絵を持つ（本体の決まり。`dims` の 3 つめが 8）。「端」は道路の行き止まりでなく、並んだ停留所の連なりの端で、1 つだけ置くと両端（6・7）の絵が出る（ゲームで確かめた）。端の絵は、帯の端に小さな縁を置くだけで、道路はふさがない。

| 番号 | 向き |
|---|---|
| 0 | NS（左下〜右上の向き）の中ほど |
| 1 | EW（右下〜左上の向き）の中ほど |
| 2 | NS の南端 |
| 3 | EW の東端 |
| 4 | NS の北端 |
| 5 | EW の西端 |
| 6 | NS の両端（単独の停留所） |
| 7 | EW の両端（単独の停留所） |

- 絵は後ろ（車の下）と前（車の上）に分ける。シートは 8 列（向き）× 3 行（0 行 = 後ろ、1 行 = 前、2 行 = 道具の絵）。セルの名前は `<名前>.<行>.<列>`。
- 道路そのものは描かない（道路は AMI が持つ）。道路はタイルの中央を通ると見て、見える側（右下か左下）の脇に歩道（バス停）か積み降ろし場（荷役所。高さ 1m）を置いた。
- 道具の絵（`icon`）は、向き 0 の後ろと前を重ねた 256px のセル（GUI のアイコンは 128px の元を縮める決まり（[gui.md](gui.md)）なので、縮めたときの見え方は未確認の仮）。`cursor` は書かない（置くときのカーソルが出るかは未確認）。
