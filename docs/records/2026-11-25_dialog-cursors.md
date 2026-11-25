# 窓から選ぶ道具のカーソルをゲームで確かめた記録（2026-11-25）

[#84](https://github.com/128-bit-net/pak256/issues/84)。[#77](2026-11-25_schedule-cursor.md) で、ダイヤの編集の道具は `menuconf.tab` に行が無く、カーソルが出なかった。窓から選ぶほかの道具にも同じ抜けがあるかを確かめた。

## 原因

窓から選ぶ道具のカーソルは、窓が本体の道具の行から写している（`gui/citybuilding_edit.cc:103`・`gui/curiosity_edit.cc:98`・`gui/groundobj_edit.cc:192`・`gui/factory_edit.cc:116`）。道具の行が無いと `cursor` は空になる。

| 窓 | 写す元 | 行 |
|---|---|---|
| 街の建物（`DIALOG_EDIT_HOUSE`）・名所（`DIALOG_EDIT_ATTRACTION`） | `general_tool[TOOL_BUILD_HOUSE]` = 22 | 無かった。**足した** |
| 産業（`DIALOG_EDIT_FACTORY`）の 3 つの道具（`fab_tool`・`land_chain_tool`・`city_chain_tool`） | `general_tool[TOOL_BUILD_FACTORY]` = 25（`TOOL_BUILD_LAND_CHAIN` 23・`TOOL_CITY_CHAIN` 24 の行は要らない） | 無かった。**足した** |
| 地面の物（`DIALOG_EDIT_GROUNDOBJ`） | `general_tool[TOOL_PLANT_GROUNDOBJ]` = 44 | 無かった。**足した** |
| 本部（財務の窓・本部の窓の「建設」） | `general_tool[TOOL_HEADQUARTER]` = 27（窓は `welt->set_tool` で道具の行のものをそのまま使う） | 無かった。**足した** |
| 木（`DIALOG_EDIT_TREE`） | `general_tool[TOOL_PLANT_TREE]` = 11 | あった（カーソル 9） |

各道具の `init()`（`simtool.cc`）は `cursor_area`（建物の大きさ）を決めるだけで、`cursor` は入れ替えない。

## 直し

`config/menuconf.tab`: `general_tool[22]`・`[25]`・`[27]` = `,8,11,`、`general_tool[44]` = `,9,11,`（アイコンは空。ツールバーには出ない）。カーソルの番号は、近い道具（街・建物 = 8、木・地面の物 = 9）に合わせた仮の絵。音は #77 と同じ 11。

## 確かめたこと

`tools/game.py` の `Game`（`flat_512_left_v64`、ポート 47920）で窓を開き、一覧から選んで地図の 1 マスをクリックし、`capture_screen` で撮った。

| 道具 | 直した後 | 直す前 |
|---|---|---|
| 街の建物（小さな家） | 黄色の菱形に「8」が出る（`2026-11-25_dialog-cursors-screens/1_house-8.png`） | 橙の枠だけで、番号の入った黄色の菱形が出ない |
| 産業（石炭火力発電所） | 建物の足跡に黄色の菱形と「8」（`2_factory-8.png`） | 橙の面だけで、黄色の菱形が出ない |

直す前の画面は撮って見たが、画像は残していない（上書きした）。橙の枠・面は、二度押しの道具が印を付ける物（`mark_tiles`）で、道具のカーソルではない。

## 確かめていないこと（コードの読みだけ）

- 地面の物の窓: pak256 に地面の物が 1 つも無いので、一覧が空で道具を選べない（`tool_plant_groundobj_t::init` は地面の物が 0 個だと `false` を返す）。行を足しただけ。
- 本部: 本部の建物が pak に入るまで届かない。行を足しただけ。
- 名所の窓・炭鉱（供給元の産業）・産業の連鎖の 2 つの道具は、撮っていない。窓が写す元は上の表のとおり同じ行。
- 音（11）が鳴ってよいか。

## AMI の dat の `cursor=`

AMI のソース（`simutrans-addon-dev/addons/ami/src/*.dat`、e66aace）の `way`（212）・`bridge`（11）・`tunnel`（12）・`roadsign`（6）・`way-object`（45）は、全部に `cursor=` がある。`icon=` と `cursor=` の片方だけの物も無い（`building` 6 も同じ）。踏切（`crossing` 19）は道具で選ぶ物ではないので、`icon`・`cursor` が要らない。128 に関わる抜けは無い。pak256 の 256 版の dat は、ここでは見ていない。
