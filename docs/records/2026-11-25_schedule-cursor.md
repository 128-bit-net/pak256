# ダイヤの編集のカーソルをゲームで確かめた記録（2026-11-25）

[#77](https://github.com/128-bit-net/pak256/issues/77)「ダイヤの編集で停車地点を足すカーソルが出ない」の原因と直し、ゲームでの確認。

## 原因

本体は、ダイヤの窓（`gui/schedule_gui.cc`）で「駅を追加」「駅を挿入」を押すと、道具 `TOOL_SCHEDULE_ADD`（`general_tool[12]`）・`TOOL_SCHEDULE_INS`（`general_tool[13]`）を選び、地図の上のカーソルにその道具の `cursor` を使う（`tool_t::init_cursor`）。この `cursor` は `menuconf.tab` の `general_tool[N] = アイコン,カーソル,…` の 2 つめでしか決まらず、無いと空（`IMG_EMPTY`）のまま。pak256 の `menuconf.tab` に `general_tool[12]`・`[13]` の行が無かったので、カーソルが出なかった。`schedule_gui_stats_t` の `current_stop_mark`（ダイヤの停留所を地図に示す印）も同じ `cursor` を使う。

## ほかの道具の抜け

カーソルを `menuconf.tab` の指定に頼る道具を、本体の `simtool.cc`・`simworld.cc` で読んで調べた。どの道具も、選ぶと `init_cursor` でその道具の `cursor` が地図のカーソルになる。道具の `init()` が `cursor` を入れ替えるものは、`menuconf.tab` の指定が要らない。

| 道具 | 結果 |
|---|---|
| `general_tool[38]`（水位の上げ下げ） | 本体が `init()` で、土地の上げ・下げのカーソルに入れ替える（`simtool.cc` の `tool_change_water_height_t::init`）。指定は要らない |
| `general_tool[39]`（気候の塗り替え。ツールバーの 8 個） | 指定が無く、カーソルが出なかった。**直した**（番号 11） |
| `general_tool[10]`（街の大きさ。`toolbar[6]`） | 本体の `init()` が入れ替える。指定は要らない |
| `general_tool[14]`・`[36]`（道・都市道路の建設） | 道の種類の dat の `cursor=`（`desc->get_cursor()`）を使う（空のときは入れ替えない）。AMI の全部の道路・線路の dat に `cursor=` があるかは調べていない |
| `general_tool[29]`（街の車） | 道のタイルをクリックして使う道具なので、カーソルは使われる。今は出さない（`menuconf.tab` の行にカーソルが無い）。ツールバーには出していない |

## 窓から選ぶ道具（未確認）

ダイヤの編集の道具は、ツールバーでなく窓の操作から選ばれる。同じ型の道具が、`menuconf.tab` に行が無いまま残っている。`init()` がカーソルを入れず、窓も入れないなら、カーソルが出ない可能性がある。ゲームでは見ていない。

| 道具 | 選ぶ窓 | 届くか |
|---|---|---|
| `TOOL_BUILD_HOUSE`（22） | 街の建物・観光地の窓（`gui/citybuilding_edit.cc`・`gui/curiosity_edit.cc`） | 届く（`dialog_tool[22]`、`toolbar[6][4]`） |
| `TOOL_PLANT_GROUNDOBJ`（44） | 地面の物の窓（`gui/groundobj_edit.cc`） | 届く（`dialog_tool[35]`、`toolbar[6][10]`） |
| `TOOL_BUILD_FACTORY`（25）・`LAND_CHAIN`（23）・`CITY_CHAIN`（24） | 産業の窓（`gui/factory_edit.cc`） | 今のツールバーには無い |
| `TOOL_HEADQUARTER`（27） | 財務の窓・本部の窓 | 本部の建物が pak に入るまで届かない |

別の issue で、窓から選んで置いたときにカーソルが出るかを確かめる。

## 直し

`config/menuconf.tab`:

- `general_tool[12] = ,12,11,`（停車地点を足す。カーソル 12）
- `general_tool[13] = ,14,11,`（停車地点を挿入する。カーソル 14）
- `general_tool[39] = ,11,11,`（気候。カーソル 11。ツールバーの気候の 8 個が同じ道具の行を使う）

アイコンの番号は空（この道具はツールバーに出ない）。音は他の道具に合わせて 11。

## 手順

1. `python -X utf8 tools/build.py`（`Warning` なし）。
2. `tools/game.py` の `Game` で `flat_512_left_v64` を起動し、`tools/vehicle_check/course.nut` で道路・車庫・停留所・バスを置いた。
3. 編成の一覧（ツールバーの一覧 → 編成）から先頭の編成の窓を開き、「スケジュール」→「駅を追加」・「駅を挿入」を `gui.click` で押し、地図のカーソルを `capture_screen` で撮った。気候はスロープツールの窓の「気候: 砂漠」を押して撮った。

## 画像

画像は撮った画面の切り抜きを 2 倍（最近傍）にした物。保存データ `flat_512_left_v64`・`gui.set_zoom(3)`。

| 画像 | 見所 |
|---|---|
| `2026-11-25_schedule-cursor-screens/1_schedule-add-12.png` | 「駅を追加」を押した後の、道路のタイルの上の赤いカーソル（番号 12） |
| `2026-11-25_schedule-cursor-screens/2_schedule-insert-14.png` | 「駅を挿入」を押した後（番号 14） |
| `2026-11-25_schedule-cursor-screens/3_climate-11.png` | 気候の道具（砂漠）のカーソル（番号 11） |

## 確かめていないこと

- 直す前の画面（カーソルが出ないこと）は、画像に撮っていない。原因は本体のコードの読みと、直した後に出ることで確かめた。
- OTRP でない本家 125.0.1 の動き（`general_tool[12]`・`[13]` は両方で同じ番号。`TOOL_SCHEDULE_ADD` は `TOOL_PLANT_TREE` の次）。
- 成功音（11）が鳴ってよいか。`general_tool[12]`・`[13]` は行が無く、これまで成功音も無かった。
- 番号つきの四角は仮の絵（[gui.md](../gui.md)）。見た目を作り込むのは後。
