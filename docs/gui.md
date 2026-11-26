# GUI の絵

ツールバーのアイコン・記号・カーソル・その他の GUI の絵（`objects/gui/`）の決め事。[#6](https://github.com/128-bit-net/pak256/issues/6) で描いた。ツールバーのアイコンは、道具の分かる簡単な図形の絵（[#66](https://github.com/128-bit-net/pak256/issues/66)。`gui_icons.py` が描く。見た目の作り込みは後）。記号・カーソル・その他は仮の絵（番号つきの色の四角など）で、後から描き直す。pak128 の絵は写していない。

本体の読み方は `simutrans/simskin.cc`・`simmenu.cc`・`gui/tool_selector.cc`・`display/simgraph16.cc`。

## 作り方

検査は `tools/test_gui.py`（必須の物が dat にあること、`menuconf.tab` の番号が一覧に収まること、使うアイコンがすべて専用の絵を持ち同じ種類の中で重ならないこと、絵に半透明・特別な色が無いこと）。

`python -X utf8 objects/gui/draw_gui.py`（Pillow だけで動く）が、PNG と dat を書き出す。書き出した物もコミットしてある。組むのは `python -X utf8 tools/build.py`（`build/pak/gui.pak` になる）。`objects/ground/temperate/draw_ground.py` の寸法の道具（`column_span` など）を使うので、その版と合わせて直す。

アイコンの番号は `config/menuconf.tab` から読み、使われる番号だけを描く（使わない番号は空き `-`）。絵は `objects/gui/gui_icons.py` の `ICONS`（種類, 番号 → 描く関数）に 1 つずつある。番号を足したのに絵が無いと、検査が落ちる（番号だけの絵は作らない）。

## 本体が必ず求める物と、置いた物

本体が起動の途中で止まるのは、`cursor`・`symbol` の全部と、`misc` のうち `Construction`・`Sidewalk`・`TunnelTexture` が無いとき（`TunnelTexture` は無ければ `Sidewalk` で代用する）。`menu` の `BarTools` などは、`menuconf.tab` がある場合に本体が一覧の数を確かめずに使うので、無いと落ちる。駅・車庫の窓は、駅の種類の記号（`TrainStop` など 9 個）が無いと、開いたときに落ちる（`halt_info.cc`・`depotlist_frame.cc`・`depot_picker.cc`）ので、仮の絵を置いた。

| Obj | Name | 置いた dat | セル | 中身 |
|---|---|---|---|---|
| menu | `GeneralTools`・`SimpleTools`・`DialogeTools`・`BarTools` | `menu_general` など | 128px | 色つきの角丸の四角に番号。色は種類で変える（緑・橙・青・紫） |
| cursor | `GeneralTools` | `cursor_general` | 256px | タイルの菱形の輪郭（黄）に番号 0〜15。本体が 16px 下げて描くので、絵は 16px 上に描いてある |
| cursor | `Builder`・`Marked` | `cursor_builder`・`cursor_marked` | 256px | 菱形の輪郭と薄い塗り（橙・赤） |
| symbol | `Passagiere`・`Post`・`Waren`・`Electricity`・`InTown`・`ColorOptions` | `sym_*` | 16px | 小さな記号 |
| symbol | `Seasons` | `sym_seasons` | 16px | 4 色の四角（番号 0 夏・1 秋・2 冬・3 春。本体の `season` は夏が 0） |
| symbol | `MessageOptions` | `sym_messageoptions` | 32px | 3 つの四角（本体は 3 枚以上あるときに並べる） |
| symbol | `Flags` | `sym_flags` | 32px | 旗 1 枚 |
| symbol | `TrainStop`・`CarStop`・`BusStop`・`ShipStop`・`AirStop`・`MonorailStop`・`MaglevStop`・`NarrowgaugeStop`・`TramStop` | `sym_*stop` | 16px | 駅の種類の記号（仮は全部同じ絵） |
| symbol | `Message`・`NewWorld`・`NewYear` | `sym_message` など | 64px | ニュースの窓に出る絵 |
| symbol | `Logo` | `sym_logo` | 128px | バナー（起動後の最初の窓）の絵。`BigLogo` と同じ意匠 |
| symbol | `BigLogo` | `sym_biglogo` | 192px × 4 | 読み込み中の大きなロゴ。4 枚（左上・右上・左下・右下）を 2×2 に並べる。意匠は `logo.py`（#78、記録は [records/2026-11-25_logo-screens.md](records/2026-11-25_logo-screens.md)） |
| misc | `Construction` | `construction` | 256px | 工事中の地面 10 枚（0 基礎の穴・1 観光地(街)・2 観光地(田舎)・3 記念物・4 工場・5 役場・6 その他・7 住宅・8 商業・9 工業）。縞の菱形 |
| misc | `Sidewalk`・`TunnelTexture` | `sidewalk`・`tunnel_texture` | 256px | 坂ごとの地面。番号は 27（下の「坂の番号」） |
| misc | `RibiArrow` | `ribi_arrow` | 256px | 一方通行の矢印。番号 = ribi（北 1・東 2・南 4・西 8） |
| misc | `PowerSource`・`PowerDest` | `power_source`・`power_dest` | 256px | 送電網の印の円。0 止まっている・1 動いている（本体は動作中を 1 番で引く）。冬の絵（2）は無い |

本体が無くても動く物（fakultative: `Mouse`・`ToolsBackground`・コンパス・`Happy` など）は、まだ描いていない。

### 一覧の数え方（本体の読み方）

- **道具の既定のアイコン**（`menuconf.tab` の `general_tool[N] = 番号,…`）は、道具の種類ごとの表（`GeneralTools`・`SimpleTools`・`DialogeTools`）の番号。
- **ツールバーの行**（`toolbar[段][位置] = 道具,番号,…`）で書いた番号は、道具の種類に関わらず **`BarTools`** の番号。表より大きい番号を書くと、本体は起動のログに警告（`wrong icon`）を出して 0 番にする。
- カーソルは、`general_tool[N] = アイコン,カーソル,…` の 2 つめが `cursor` の `GeneralTools` の番号。道具の行が無い、またはカーソルの番号が空だと、本体はカーソルを出さない（ダイヤの編集の「駅を追加」・「駅を挿入」は `general_tool[12]`・`[13]`、気候は `[39]` の行が要る。窓から選ぶ道具のうち、街の建物・名所は `[22]`、産業は `[25]`、地面の物は `[44]`、本部は `[27]` の行が要る（窓が道具の行から写す）。[#77](https://github.com/128-bit-net/pak256/issues/77)、[記録](records/2026-11-25_schedule-cursor.md)、[#84](https://github.com/128-bit-net/pak256/issues/84)・[記録](records/2026-11-25_dialog-cursors.md)）。道の建設は道の dat の `cursor=`、水位・街の大きさの道具は本体が入れ替えるカーソルを使う。
- `GeneralTools` のカーソルは、本体が Z_PLAN（4/64 タイル = 256 のタイルで 16px）だけ下げて描く（`simconst.h`）。タイルの強調表示は下げない。そこで絵は菱形を 16px 上（行 113〜239）に描いた。`Builder`・`Marked` は地面と同じ寸法（行 129〜255）。
- カーソルの枠は、地面の縁の画素の内側に描く（`GeneralTools` は縦 6 行、`Builder`・`Marked` は 8 行。横 2px・縦 1px の階段。決まりは [ground.md](ground.md) の「枠の線」、[#112](https://github.com/128-bit-net/pak256/issues/112)）。カーソルの絵は坂でも平らな菱形のまま（本体が 1 枚の絵を出す）。坂に沿う線は地面の印（`Marker`）が出す。

### 坂の番号（`Sidewalk`・`TunnelTexture`）

本体は坂（`sw + 3*se + 9*ne + 27*nw`）を `ground_desc_t::slopetable` で番号にする（単段はその値、複段は半分の高さの坂の値 + 12）。道の乗る坂の番号は、すべて 3 の倍数になる。

| 坂 | 平ら | 単段 4 向き（4・12・28・36） | 複段 4 向き（8・24・56・72） |
|---|---|---|---|
| 番号 | 0 | 3・6・9・12 | 15・18・21・24 |

`Sidewalk` は、この番号を起点に 3 つずつ使う（`boden.cc` の `boden_t::calc_image_internal`。[#136](https://github.com/128-bit-net/pak256/issues/136)）。

| 置く番号 | 本体が引くとき | pak256 の中身 |
|---|---|---|
| 番号 + 0 | 下の 2 つ以外 | 夏の絵 |
| 番号 + 1 | 雪線以上か、雪の気候 | 雪の絵（夏と同じ形の仮の絵） |
| 番号 + 2 | 坂で、高さが雪線の 1 つ下 | 空き（本体は夏の絵を使う） |

`+1`・`+2` は、絵があると本体がそのまま使う。**別の坂の絵を置かない**（番号を詰めて並べると、雪の街の道路に別の坂の絵が出て、灰色の三角に見える）。並びは `tools/test_gui.py` の `test_sidewalk_numbers` が検査する。

`TunnelTexture` は、本体が番号 + 0 だけを引く（`tunnelboden.cc`）。27 個の番号の全部に絵があるが、使われるのは 3 の倍数の 9 個。

## アイコンの絵

128px の元を 512px で描いて縮め（縁はなめらか、半透明は切る）、地の色を種類で変えた角丸の四角に、白と数色の図形を置く。番号の意味は本体の `simmenu.h`（`GENERAL_TOOL`・`SIMPLE_TOOL`・`DIALOGE_TOOL` の列挙の番号）。画面の確認は [records/2026-11-25_toolbar-icons.md](records/2026-11-25_toolbar-icons.md)。

- **地の色**: 一般の道具は緑、1 回押す道具は橙、窓を開く道具は青、ツールバーの行（`BarTools`）は紫。撤去は赤、水位と気候は青や気候の色（水と水位は青・砂漠は黄土・熱帯は緑・地中海は黄緑・温帯は緑・ツンドラは灰青・岩は灰・北極は水色）。
- **飾り**: 右下の丸（緑の + ・赤の − ・赤の ×・橙の鉛筆・青の i）が「足す・引く・消す・直す・情報」。
- 主な絵: 問い合わせ=虫めがね、撤去=赤地に ×、土地の上げ下げ=地面の上下の矢印、目印=旗、街を足す=家に +、街の建物の購入=家にコイン、木=木、停留所の窓=標識に H、財務=コイン、予約の表示=レールの予約区間（赤）、路線=折れ線と駅、地図=地図、設定=歯車、坂の道具=地面の菱形に向きの矢印と N・E・S・W（2 段は矢印が 2 つ）。
- 道路の撤去（`bar` 20）は道路の帯に赤い ×、線路の撤去（`bar` 46。`toolbar[3][6]`）は線路の帯（道床・まくらぎ・レール）に赤い ×、信号の撤去（`bar` 47。`toolbar[3][8]`。#73）は信号の柱と灯りに赤い ×。線路のツールバーの撤去は、#46 までは道路の絵のままだった（[#71](https://github.com/128-bit-net/pak256/issues/71)）。
- 飛行機の段のアイコン（`bar` 52）は上から見た飛行機、滑走路・誘導路の撤去（`bar` 53。`toolbar[5][2]`）は滑走路の帯に赤い ×（[airport.md](airport.md)）。
- 絵で描き分けにくいものだけ文字を添える（`H`・`$`・`?`・`i`・`Ab`・`{ }` と、坂の向きの N・E・S・W）。
- 全部の絵の一覧は `records/2026-11-25_toolbar-icons-screens/` の `8_`〜`11_`（128px の元）。

## アイコンの大きさ

絵は 128px の元で描く。本体は、ツールバーに出すとき `display_fit_img_to_width` で、`menuconf.tab` の `icon_height`（今は 48。#6 でユーザーが決めた）に収まる最大の倍率（2・3/2・4/3・1・3/4・5/8・1/2・3/8・1/4・1/8）で縮める。128 の元は 1/2（64）・3/8（48）・1/4（32）で、どれもきれいに縮む。表示の大きさを決めるのは `menuconf.tab` の **`icon_height`**（0〜64。幅も同じ値になる。`icon_width` は menuconf.tab では読まれない。本体の `simmenu.cc` 1054〜1057 行）。絵を描き直さなくてよい。64 を超える大きさは使えない。48 で画面に出した見え方は、[records/2026-11-25_toolbar-icons.md](records/2026-11-25_toolbar-icons.md) で確かめた（上のツールバーと、設定・坂・道路・特別・一覧・編集のサブメニュー）。

## 確かめたこと・確かめていないこと

ゲームでの確認は [records/2026-11-25_gui-screens.md](records/2026-11-25_gui-screens.md)。ツールバー（`menuconf.tab`）が出ること、カーソル、`Flags`・`ColorOptions`・`Seasons` を見た。カーソルの 16px 上げは、直した後の画面で確かめた（記録の 1）。`Message`・`NewWorld`・`NewYear`・`MessageOptions`・`Electricity`・`InTown`・記号（`Passagiere` など）・`Construction`・`TunnelTexture`・`RibiArrow`・`Power*`・駅の種類の記号は、起動して読み込まれる（警告が出ない）ことだけで、画面では見ていない。`Sidewalk` は温帯と雪の街の道路（平らな所と単段の坂）を画面で見た（[records/2026-11-26_sidewalk-snow.md](records/2026-11-26_sidewalk-snow.md)）。`BigLogo`（読み込み中）と `Logo`（バナー）は画面で見た（[records/2026-11-25_logo-screens.md](records/2026-11-25_logo-screens.md)）。ロゴの絵の文字は Pillow が同梱するフォントで描いて、絵に焼き込んである。
