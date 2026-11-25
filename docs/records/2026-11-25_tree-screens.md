# 木をゲームで確かめた記録（2026-11-25）

[#9](https://github.com/128-bit-net/pak256/issues/9) の温帯の木 3 種を、OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。決め事は [trees.md](../trees.md)。

## 手順

1. `python -X utf8 tools/build.py --no-ami` で組む。makeobj のログに `Warning`・`ERROR` は無い。
2. 検証環境（`addon_check`）の実行ファイル・`config/`・`themes/`・`font/`・`text/`・`script/` を写した作業フォルダ（`-set_workdir`）を作り、`pak/` に自前の pak（`gui.pak`・`ground.*.pak`・`scenery.temperate_trees.pak`）と `config/*.tab` を置いた。貨物（`Passagiere`）が無いと本体が止まる（#4 は未着手）ので、`work/pak256poc`（2 倍にした pak128）から、GUI・地面・`BigLogo`・**木（`landscape.trees`）を除いた**物を借りた。木は自前の 3 種だけが読まれる。`settings.xml` は `settings.xml.v64` を写し、送信用の記録を空にした。
3. 起動: `-objects pak/ -noaddons -load flat_512_left_v64 -freeplay -mute -mcp-port 47860 -screensize 1700x950`。
4. 地図の新規作成は MCP から出来ない（起動画面の間は答えない）ので、平らな保存データを読み、`command_x(tool_forest).work(pl, coord3d(246,246,0), coord3d(270,270,0), "")` で森を作った（本体の森を作る処理で、`tree_builder_t::create_forest`）。撮影は `gui.set_zoom(3)`・`gui.jump` と `capture_screen`。

## 画像

| 画像 | 場所 | 見所 |
|---|---|---|
| `1_forest.png` | 保存データ `flat_512_left_v64`、中心 (255, 255)、`gui.set_zoom(3)` | 3 種（広葉樹・針葉樹・シラカバ）と、育ちの違う木が混ざって生える。右下の白い所は、この保存データの雪の地面（木は温帯の地面だけに生える） |

## 確かめていないこと

- 新しい地図の作成（地図の新規作成の画面）で、木が自然に生えること。森を作る処理と同じ関数を使うが、地図の作成画面は通していない。
- 木が育つ（`age` が上がる）様子。木の大きさの違いは、森の画像に混ざった若木で見ただけ。
- 大きな森での描画の重さと、木の数の設定（`max_no_of_trees_on_square`、[config.md](../config.md)）。
- 季節（冬など）の絵。`seasons=1` なので、冬も同じ絵で出る。
- 車両・建物と並べた大きさの釣り合い（車両が未着手）。
