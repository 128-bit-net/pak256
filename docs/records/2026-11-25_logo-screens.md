# 起動のロゴをゲームで確かめた記録（2026-11-25）

[#78](https://github.com/128-bit-net/pak256/issues/78) で描いた `BigLogo`・`Logo` を、OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。決め事は [gui.md](../gui.md)。

## 手順

1. `python -X utf8 objects/gui/draw_gui.py` でロゴの PNG と dat を書き、`python -X utf8 tools/build.py` で組んだ。makeobj のログに `Warning`・`ERROR` は無い。
2. `tools/game.py` の `prepare_workdir`・`launch_command` で作業フォルダを作った（ポートの範囲だけ作業者の割り当てに書き換えた）。起動のコマンドから `-load` と `-freeplay` を外した。保存データを読むと、読み込み中の画面の後にバナーが出ない（本体の `simmain.cc`。新しい世界のときだけバナーを出す）。
3. MCP は起動画面の間は答えないので、Windows の `PrintWindow` で本体のウィンドウを 0.15 秒ごとに撮り続け、読み込み中の画面とバナーの画面を拾った。昼夜は止めた。起動した PID で閉じた。

## 画像

| 画像 | 見所 |
|---|---|
| `1_loading.png` | 読み込み中の画面。`BigLogo` の 4 枚が 2×2 に並び、下に進みの帯。ロゴの下の小さな字は pak の著作権の行 |
| `2_banner.png` | 起動後のバナー。右に `Logo`（128px）が出る |
| `3_variants_ABC.png` | 意匠の 3 案（左から A・B・C）。ゲームには A を入れた |

## 分かったこと

- `BigLogo` は 4 枚の位置が、1 枚めの高さ（`image0->h + image0->y`）の繰り返しで決まる。4 枚とも全面不透明な正方形にして、makeobj が透明な縁を切っても継ぎ目がずれないようにした。
- 本体は `BigLogo` を `(幅/2 − w, 高さ/4 − w)` に置く（`w` は 1 枚の幅）。1 枚 192px（全体 384px）だと、高さ 900 の画面で進みの帯（画面の中央）に重ならない。256px にすると高さ 1px から始まって帯に重なる。
- `Logo` は `BigLogo` と同じ絵を 128px に縮めたもの。

## 確かめていないこと

- 画面の小さい（高さが 768 以下など）環境での `BigLogo` と進みの帯の重なり（高さ 900 だけ確かめた）。
- 本家 125.0.1 での見え方。
