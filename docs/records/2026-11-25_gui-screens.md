# GUI の絵をゲームで確かめた記録（2026-11-25）

[#6](https://github.com/128-bit-net/pak256/issues/6) の GUI の絵を、OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。決め事は [gui.md](../gui.md)。

## 手順

1. `python -X utf8 tools/build.py --no-ami` で `gui.pak`・`ground.*.pak` を組む。makeobj のログに `Warning`・`ERROR` は無い。
2. `F:\Simutrans\addon_check` の実行ファイル・`config/`・`themes/`・`font/`・`text/` などを写した作業フォルダ（`-set_workdir`）を作り、`pak/` に、`work/pak256poc`（2 倍にした pak128）から GUI（`base.misc_GUI*`）・地面（`ground.Outside`・`landscape.grounds`）・`symbol.BigLogo` を除いたものと、自前の pak（`gui.pak`・`ground.*.pak`）を入れ、`pak/config/` に `config/*.tab` を置いた。自前以外は借り物（#6 の範囲外）。`settings.xml` は `settings.xml.v64` を写し、送信用の記録（`registerOTRPUsage`）を空にした。
3. 本体は `-objects pak/ -noaddons -load flat_512_left_v64.sve -freeplay -mute -mcp-port 47840 -screensize 1700x950` で起動した。`themes/` が無いと「No GUI themes found」で止まる。
4. 画面は MCP の `run_squirrel`（`gui.jump`・`gui.set_zoom(3)`・`gui.click`・`gui.open_dialog_tool`）と `capture_screen`。ツールバーの項目とカーソルは、`gui.click` で道具を選び、地図を 1 回クリックして出した（道具は問い合わせで、地図は変わらない）。

## 画像

| 画像 | 見所 |
|---|---|
| `1_toolbar-cursor.png` | 上のツールバー（`toolbar[0]`）が自前のアイコンで出る。地図の上のカーソル（黄の菱形に番号 0 = `GeneralTools` の 0 番）と、橙の菱形（`Builder`）が重なる |
| `2_slope-bar.png` | 上のツールバーの 4 つめ（地形）を開いた `toolbar[2]`。ツールバーの行で書いた番号（10〜15・30〜43 など）が `BarTools` の番号で出る |
| `3_road-bar.png` | 上のツールバーの 5 つめ（道路）を開いた `toolbar[3]`。AMI の道路などは借り物の pak のもの。自前のアイコンは 33 番 |
| `4_symbols-flag-color.png` | 言語の窓（`Flags`）とプレイヤーの色の窓（`ColorOptions`） |

`1_toolbar-cursor.png` の左下の四角が `Seasons`（冬は白）。

## 分かったこと

- ツールバーの行（`toolbar[段][位置] = 道具,番号,…`）の番号は、道具の種類に関わらず `BarTools` の番号。最初は種類ごとの表に置いていて、地形のツールバーが全部 `BarTools` の 0 番で出た。
- 本体は `themes/` が無いと起動で止まる（pak ではなく本体のフォルダ）。
- 季節の番号は夏が 0（`simworld.cc` の `(2+月/3)&3`）。
- `cursor` の物は、本体が 4/64 タイル（256 のタイルで 16px）下げて描く。`GeneralTools` の菱形が `Builder` より 16px 下に出るのはこのため。

## 確かめていないこと

- `Message`・`NewWorld`・`NewYear`・`Logo`・`MessageOptions`・`Electricity`・`InTown`・`Passagiere`・`Post`・`Waren`・`Construction`・`Sidewalk`・`TunnelTexture`・`RibiArrow`・`PowerSource`・`PowerDest` の画面での見た目（起動して読み込まれることだけ）。
- 起動のログの警告（`wrong icon` など）。画面で見えるものだけを確かめた。
- アイコンの大きさ（`icon_width`）を 32 以外にしたときの見え方。
- CI（Linux 版 makeobj）。
