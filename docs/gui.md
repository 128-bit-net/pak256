# GUI の絵

ツールバーのアイコン・記号・カーソル・その他の GUI の絵（`objects/gui/`）の決め事。[#6](https://github.com/128-bit-net/pak256/issues/6) で描いた。絵は仮（`draw_gui.py` が描いた、番号つきの色の四角など）で、見た目は後から描き直す。pak128 の絵は写していない。

本体の読み方は `simutrans/simskin.cc`・`simmenu.cc`・`gui/tool_selector.cc`・`display/simgraph16.cc`。

## 作り方

`python -X utf8 objects/gui/draw_gui.py`（Pillow だけで動く）が、PNG と dat を書き出す。書き出した物もコミットしてある。組むのは `python -X utf8 tools/build.py`（`build/pak/gui.pak` になる）。`objects/ground/temperate/draw_ground.py` の寸法の道具（`column_span` など）を使うので、その版と合わせて直す。

アイコンの番号は `config/menuconf.tab` から読み、使われる番号だけを描く（使わない番号は空き `-`）。

## 本体が必ず求める物と、置いた物

本体は、`simskin.cc` の表のうち、カーソル・記号・その他（`misc`）の全部が揃わないと起動の途中で止まる。メニュー（`menu`）の物は、無くても起動時には止まらない（ボタンの絵は theme から来る）。

| Obj | Name | 置いた dat | セル | 中身 |
|---|---|---|---|---|
| menu | `GeneralTools`・`SimpleTools`・`DialogeTools`・`BarTools` | `menu_general` など | 128px | 色つきの角丸の四角に番号。色は種類で変える（緑・橙・青・紫） |
| cursor | `GeneralTools` | `cursor_general` | 256px | タイルの菱形の輪郭（黄）に番号 0〜15 |
| cursor | `Builder`・`Marked` | `cursor_builder`・`cursor_marked` | 256px | 菱形の輪郭と薄い塗り（橙・赤） |
| symbol | `Passagiere`・`Post`・`Waren`・`Electricity`・`InTown`・`ColorOptions` | `sym_*` | 16px | 小さな記号 |
| symbol | `Seasons` | `sym_seasons` | 16px | 4 色の四角（番号 0 夏・1 秋・2 冬・3 春。本体の `season` は夏が 0） |
| symbol | `MessageOptions` | `sym_messageoptions` | 32px | 3 つの四角（本体は 3 枚以上あるときに並べる） |
| symbol | `Flags` | `sym_flags` | 32px | 旗 1 枚 |
| symbol | `Message`・`NewWorld`・`NewYear` | `sym_message` など | 64px | ニュースの窓に出る絵 |
| symbol | `Logo` | `sym_logo` | 128px | 起動画面の絵 |
| misc | `Construction` | `construction` | 256px | 工事中の地面 10 枚（0 基礎の穴・1 観光地(街)・2 観光地(田舎)・3 記念物・4 工場・5 役場・6 その他・7 住宅・8 商業・9 工業）。縞の菱形 |
| misc | `Sidewalk`・`TunnelTexture` | `sidewalk`・`tunnel_texture` | 256px | 坂ごとの地面 27 枚（下の「坂の番号」） |
| misc | `RibiArrow` | `ribi_arrow` | 256px | 一方通行の矢印。番号 = ribi（北 1・東 2・南 4・西 8） |
| misc | `PowerSource`・`PowerDest` | `power_source`・`power_dest` | 256px | 送電網の印の円 |

本体が無くても動く物（fakultative: `BigLogo`・`Mouse`・駅の種類の記号・`ToolsBackground`・コンパスなど）は、まだ描いていない。

### 一覧の数え方（本体の読み方）

- **道具の既定のアイコン**（`menuconf.tab` の `general_tool[N] = 番号,…`）は、道具の種類ごとの表（`GeneralTools`・`SimpleTools`・`DialogeTools`）の番号。
- **ツールバーの行**（`toolbar[段][位置] = 道具,番号,…`）で書いた番号は、道具の種類に関わらず **`BarTools`** の番号。表より大きい番号を書くと、本体は起動のログに警告（`wrong icon`）を出して 0 番にする。
- カーソルは、`general_tool[N] = アイコン,カーソル,…` の 2 つめが `cursor` の `GeneralTools` の番号。
- `cursor` の物は本体が Z_PLAN（4/64 タイル）だけ下げて描くので、`Builder` との間に 16px（256 のタイルで）の差が出る。絵は地面と同じ寸法（菱形は行 128〜255）で描いてある。

### 坂の番号（`Sidewalk`・`TunnelTexture`）

本体は `ground_desc_t::slopetable` で、単段の坂 15 通り（`sw + 3*se + 9*ne + 27*nw` が 0・1・3・4・9・10・12・13・27・28・30・31・36・37・39）を 0〜14、複段の坂を `slopetable + 12` で 12〜26 にする。12〜14 は単段と複段で重なる（本体の決まり）ので、単段の絵を置いた。雪の絵（`+1`・`+2`）は描いていない（本体は雪の絵が無いと通常の絵を使う）。

## アイコンの大きさ

絵は 128px の元で描く。本体は、ツールバーに出すとき `display_fit_img_to_width` で、`menuconf.tab` の `icon_width`（今は 32）に収まる最大の倍率（2・3/2・4/3・1・3/4・5/8・1/2・3/8・1/4・1/8）で縮める。128 の元は 1/2（64）・3/8（48）・1/4（32）で、どれもきれいに縮む。表示の大きさは `menuconf.tab` の `icon_width`・`icon_height` の 2 行で決まる（絵を描き直さなくてよい）。決める案は #6 のコメント。

## 確かめたこと・確かめていないこと

ゲームでの確認は [records/2026-11-25_gui-screens.md](records/2026-11-25_gui-screens.md)。ツールバー（`menuconf.tab`）が出ること、カーソル、`Flags`・`ColorOptions`・`Seasons` を見た。`Message`・`NewWorld`・`NewYear`・`Logo`・`MessageOptions`・`Electricity`・`InTown`・記号（`Passagiere` など）・`Construction`・`Sidewalk`・`TunnelTexture`・`RibiArrow`・`Power*` は、起動して読み込まれる（警告が出ない）ことだけで、画面では見ていない。
