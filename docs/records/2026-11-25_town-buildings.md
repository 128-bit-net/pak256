# 役場と住宅をゲームで確かめた記録（2026-11-25）

## 背景

[#8](https://github.com/128-bit-net/pak256/issues/8) の役場 1 種・住宅 4 種（[buildings.md](../buildings.md)）で、地図に街を置くと役場と住宅が建って街が育つか、OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。

## 手順

1. `python -X utf8 tools/build.py` で組む（AMI の 256 版は Release の zip から取った）。makeobj のログに `Warning`・`ERROR` は無い（`city.town_buildings.pak` ができた）。
2. 検証環境（`addon_check`）の実行ファイル・DLL・`themes/`・`font/`・`text/`・`script/` を写した作業フォルダを作り（`-set_workdir`）、`pak/` に自前の pak（`ami_road.pak`・`city.town_buildings.pak`・`ground.*.pak`・`gui.pak`・`scenery.temperate_trees.pak`）と `config/*.tab`（`pak/config/`）を置いた。貨物（`Passagiere` など）が無いと本体が止まる（#4 は未着手）ので、`work/pak256poc` の `factories.all.pak` と、それが求める煙（`base.smokes.all.pak`）だけを借りた。街の建物・道路・地面・木・GUI は借りていない。`settings.xml` は `settings.xml.v64` の写しで、送信用の記録は CDATA の中身だけ空にした。
3. 起動: `-singleuser -objects pak/ -noaddons -load flat_512_left_v64 -freeplay -mute -mcp-port 47860 -screensize 1700x950`。`-singleuser` が無いと、本体は作業フォルダでなくユーザーの設定の場所を見て、`settings.xml`・`themes/`・`save/` が見つからない。
4. 街は MCP の `run_squirrel` で `command_x(tool_add_city).work(player_x(0), coord3d(235,235,0))`。撮影は `gui.jump`・`gui.set_zoom` と `capture_screen`。建物の数と地図は `count_buildings.nut`（建物の名前ごとに数え、道・建物を文字で出す）。

## 結果

### 最初の規則（#3 の `cityrules.tab`）では街が育たなかった

保存データの雪と草の境目（255,255）に街を置くと、役場と家 3 軒が建ったところで止まった。人口を `city.change_size(150)` で足しても建物は 4 軒のまま。原因は 2 つ（本体のコード `simcity.cc`）。

1. 役場の脇に本体が作る道は、役場の大きさの長さだけ（`check_bau_townhall`）。役場が 1x1 なので道は 1 タイル。初版の道の延長の規則（`road_1`）は「後ろに道が 2 タイル続く」ことが前提で、一度も当てはまらなかった。
2. 行き止まりの家の規則（`house_3`）は、その 1 タイルの 3 つの側面を先に家で埋めた。道を延ばせる空き地が残らない。

直した内容は [config.md](../config.md) の `cityrules.tab` の節。後ろに道が 1 タイルあれば延ばす規則を足し、`house_3` は手前に道が 2 タイル続くときだけにした（`lint_config.py` と単体テストは通る）。

### 直した規則での街の育ち

- 草の地面の (235,235) に街を置いた（開始 1930 年 1 月）。置いた直後（人口 298）で、道が 4 方向に延び、建物 11 軒（役場 1・小さな戸建て 1・長屋 2・集合住宅 7）が建った。
- **旅客などの輸送が無いと、街は増えない**。本体は、満たされた需要（輸送された旅客・郵便・届いた貨物）が無いと成長しない（`city_growth_base` の最後の行のコメント「自己増殖する集落を防ぐ」）。最初の街（雪の境目、旧規則）で 1930〜1934 年、本体の速さを上げて 3 年半見たが、人口 244・建物 4 軒のまま変わらなかった。
- そこで、人口だけをスクリプトで足して建物の建ち方を見た（`city.change_size(40)` を、本体の約 7 か月ごと。本体の速さは `debug.set_game_speed(128)`）。1930 年から 1935 年 6 月まで約 5 年半で、人口 298 → 831、建物 11 → 34 軒（役場 1、小さな戸建て 3、やや大きな戸建て 4、長屋 9、集合住宅 18）。5 種類すべてが建った。建て替え（`renovation_percentage`）が起きたかは数えていない。
- 道は人口とともに延び、枝道も出た（`count_buildings.nut` の地図で確かめた）。

| 画像 | 見所 |
|---|---|
| `1_start.png` | 街「山平」（座標 235,235）、1930 年 1 月、`gui.set_zoom(3)`、中心 (236,234)。置いた直後。役場（時計塔のある建物）と集合住宅・長屋・戸建てが道に沿う |
| `2_after-5years.png` | 同じ位置、1935 年 9 月。道が延び、戸建て・長屋が増えた |
| `3_overview-zoom2.png` | 中心 (238,240)、`gui.set_zoom(2)`。建物が道に面して並ぶところ。高い集合住宅が奥の建物に重なる所もある |

## 確かめていないこと

- **新しい地図の作成画面で街が建つこと。** 起動画面の間は MCP が答えないので、平らな保存データに `tool_add_city` で置いた。
- **輸送で街が育つこと。** 実際に育つのは輸送（旅客・郵便）があるとき。この pak には車両も停留所も無く（停留所は AMI の 256 版にまだ無い）、輸送は試せなかった。上の「5 年」は、人口をスクリプトで足した結果で、本体の通常の速さの成長ではない。
- タイムライン有効（`intro_year=1900` の判定）。保存データは「年代設定: 無効」。
- 商業・工業の建物が無い街（`com_start_score = -10` で商業は選ばれにくい）の長い育ち。5 年半の間、住宅だけで建て続けた。
- 本体の速さ 128 倍の間、ログに `delta_t out of bounds` が出た（速さを上げすぎたときの本体の警告で、建物とは関係ない）。
- 建物の絵の細部（回転しても同じ 1 通りの絵であること、冬の地面との見え方）。
