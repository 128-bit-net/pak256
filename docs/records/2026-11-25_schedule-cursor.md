# ダイヤの編集のカーソルをゲームで確かめた記録（2026-11-25）

[#77](https://github.com/128-bit-net/pak256/issues/77)「ダイヤの編集で停車地点を足すカーソルが出ない」の原因と直し、ゲームでの確認。

## 原因

本体は、ダイヤの窓（`gui/schedule_gui.cc`）で「駅を追加」「駅を挿入」を押すと、道具 `TOOL_SCHEDULE_ADD`（`general_tool[12]`）・`TOOL_SCHEDULE_INS`（`general_tool[13]`）を選び、地図の上のカーソルにその道具の `cursor` を使う（`tool_t::init_cursor`）。この `cursor` は `menuconf.tab` の `general_tool[N] = アイコン,カーソル,…` の 2 つめでしか決まらず、無いと空（`IMG_EMPTY`）のまま。pak256 の `menuconf.tab` に `general_tool[12]`・`[13]` の行が無かったので、カーソルが出なかった。`schedule_gui_stats_t` の `current_stop_mark`（ダイヤの停留所を地図に示す印）も同じ `cursor` を使う。

## ほかの道具の抜け

`menuconf.tab` に行がある道具のうち、カーソルを `menuconf.tab` の指定に頼る物を、本体の `simtool.cc` で読んで調べた。

| 道具 | 結果 |
|---|---|
| `general_tool[38]`（水位の上げ下げ） | 本体が `init()` で、土地の上げ・下げのカーソルに入れ替える。指定は要らない |
| `general_tool[39]`（気候の塗り替え） | 指定が無く、カーソルが出なかった。**直した**（番号 11） |
| `general_tool[14]`・`[36]`（道・都市道路の建設） | 道の種類のカーソル（`desc->get_cursor()`）を使う。指定は要らない |
| `general_tool[29]`（街の車） | カーソルを使う道具ではない |

行が無い道具（`general_tool[7]`・`[8]`・`[10]` など）は、ツールバーに出していないので対象にしない。ツールバーに足すときに、カーソルの番号も付ける。

## 直し

`config/menuconf.tab`:

- `general_tool[12] = ,12,11,`（停車地点を足す。カーソル 12）
- `general_tool[13] = ,14,11,`（停車地点を挿入する。カーソル 14）
- `general_tool[39] = ,11,11,`（気候。カーソル 11）

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
- 番号つきの四角は仮の絵（[gui.md](../gui.md)）。見た目を作り込むのは後。
