# 炭鉱と発電所をゲームで確かめた記録（2026-11-25）

## 背景

[#43](https://github.com/128-bit-net/pak256/issues/43) の炭鉱と石炭火力の発電所（[industry.md](../industry.md)）が、地図に置けて、石炭の連鎖が働くかを OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。

## 手順

1. `python -X utf8 tools/build.py` で組む（AMI の 256 版は Release の zip から取った）。makeobj のログに `Warning`・`ERROR` は無い（`industry.coal_chain.pak` ができた）。`tools/test_*.py` は 95 件通る。
2. 検証環境（`addon_check`）の実行ファイル・DLL・`themes/`・`font/`・`text/`・`script/` と、保存データ `flat_512_left_v64` を写した作業フォルダを作った（`settings.xml` は写していない）。`pak/` には自前の pak（`goods.pak`・`industry.coal_chain.pak`・`ground.*.pak`・`gui.pak`・`city.town_buildings.pak`・`scenery.temperate_trees.pak`）と `ami_road.pak`、`config/*.tab`（`pak/config/`）。貨物は #4 の `goods.pak` で足りたので、pak256poc は借りていない。
3. 起動: `-singleuser -objects pak/ -noaddons -load flat_512_left_v64 -freeplay -mute -mcp-port 47861 -screensize 1700x950`。AMI の道路が無いと本体が止まる（`No road found at all!`）。
4. 産業は MCP の `run_squirrel` で `command_x(tool_build_factory).work(player_x(0), coord3d(x,y,0), "0050,<名前>")`（先頭の 2 文字は気候無視と向き、続く数字が生産量、`,` の後が名前）。引数なしで呼ぶと、本体が無作為に選ぶ（発電所が建った）。

## 結果

- **炭鉱（2x2）と発電所（3x3）が地図に置けた。** 建っている間は工事中の絵（縞）が出て、しばらく（ゲーム内で 1 か月ほど）の後に絵が出る。
- **つながり**: 本体が地図を作るときの連結は、保存データへ後から置いた物には付かない（`factory_builder_t::build_link` だけが付ける）。そこで `command_x(tool_link_factory).work(player_x(0), 炭鉱の座標, 発電所の座標, "")`（引数 4 つ。3 つだと失敗する）で手でつなぐと、炭鉱の `get_consumers()` が 1、発電所の `get_suppliers()` が 1 になった。
- **炭鉱が石炭を作る**: 約 1 年 4 か月の間（本体の速さを 128 倍にして進めた）に、炭鉱の出力の `Kohle` の在庫（`output.Kohle.get_storage()`）が 94 になった。
- **発電所が受ける側になる**: 発電所の入力に `Kohle` の枠がある（`input.Kohle`）。在庫は 0 のまま（石炭を運ぶ車両と線路・駅が無いため、運んでいない）。
- 画像: 1931 年 5 月、`gui.set_zoom(3)`、中心 (103,132)。左が発電所（座標 100,130、3x3）、右が炭鉱（座標 105,130、2x2）。

| 画像 | 見所 |
|---|---|
| `2026-11-25_coal-industry-screens/1_chain.png` | 発電所（左）と炭鉱（右）。炭鉱の櫓・石炭の山、発電所の煙突・ボイラー棟 |

## 確かめていないこと

- **新しい地図の作成画面で、炭鉱と発電所が出ること・つながること。** 起動画面の間は MCP が答えないので、平らな保存データにスクリプトで置いた。つなぎは手で付けた。
- **石炭が実際に運べること**（車両・停留所が無い。運ぶと発電所の電気が出ること）。
- 夜・冬・雪の気候での見え方（昼の温帯の草の地面だけ撮った）。
- 産業の窓（情報の窓）の見え方、`mapcolor` の地図の色。
- 煙・畑が無いこと（意図的）。
- OTRP v64 だけで確かめた。本家 125.0.1 は未確認（[concept.md](../concept.md) の F）。
