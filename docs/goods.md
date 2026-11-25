# 貨物

貨物の dat（`objects/goods/goods.yaml`）の決め事。[#4](https://github.com/128-bit-net/pak256/issues/4) で足した。concept の E（pak128 に寄せる）に沿う。pak128 の dat の値（名前・分類・単位・値段・速度ボーナス・重さ。機能上の数値）を、同じにした。dat の文・コメント・絵は写していない（貨物に絵は無い）。名前と数値だけなので、元の作者の記載は要らないと判断した（法律の専門家には確かめていない）。

## 置いた貨物

| name | 画面の名前（ja / en） | 分類 `catg` | 単位 `metric` | `value` | `speed_bonus` | `weight_per_unit` |
|---|---|---|---|---|---|---|
| `Passagiere` | 旅客 / Passengers | 0（専用） | なし | 14 | 18 | 85 |
| `Post` | 郵便 / Mail | 0（専用） | `sack` | 16 | 15 | 50 |
| `None` | （出ない） | 0 | なし | 0 | | 1 |
| `Kohle` | 石炭 / Coal | 2（ばら積み） | `tonnen` | 32 | 0 | 1000 |

- `Passagiere`・`Post`・`None` は、本体が必ず求める（`bauer/goods_manager.cc`）。
- `name` は本体の名前に合わせる必要がある物（上の 3 つ）と、pak128 と同じ綴りの `Kohle`。移行する人が貨物名で探せるようにした。名前の画面表示は `text/ja.tab`・`en.tab`。
- 貨物の窓の色の線は、dat に `mapcolor` を書かないので本体が貨物の並びから自動で決める（貨物を足すと色が変わりうる）。
- 別の物として、`Passagiere`・`Post`・`Waren` の記号の絵は GUI にある（[gui.md](gui.md)）。貨物の dat に絵は持たせない。
- 分類の名前（`CATEGORY_01`〜`07`）の訳も `text/` に足した（貨物の窓に出る）。pak128 の分類 7 つの分け方を使う（[concept.md](concept.md) の「2.3」）。

## 最初の産業の連鎖（仮）

**炭鉱 → 発電所**。炭鉱が `Kohle` を出し、発電所が `Kohle` を受けて電気を出す（電気は貨物ではないので、貨物の dat は `Kohle` 1 つで足りる）。roadmap の「産業 1 本の連鎖（例: 炭鉱 → 発電所）」のとおり。pak128 にも同じ連鎖がある。産業の dat は `objects/industry/coal_chain/` にある（[industry.md](industry.md)）。

- 値の釣り合い（`value`・`speed_bonus`）は、産業と車両がそろってから見直す（roadmap の段階 4）。
- 足す貨物・変える名前は、産業の組み方を決めるときに決める（concept の E）。それまでは pak128 のまま。
