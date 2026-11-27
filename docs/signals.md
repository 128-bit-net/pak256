# 線路の信号（pak256 の物）

線路の信号は、閉塞信号を 1 種だけ pak256 で作った（[#73](https://github.com/128-bit-net/pak256/issues/73)。2026-11-26、ユーザーの決定: pak256 は基本のアドオンを自分で作り、当面は絵より動くことを優先する。[roadmap.md](roadmap.md) の「進め方」）。AMI は信号を作らず、AMI の `ami_rail_signal` は使わない。絵は簡単な物（箱を数式で描いた物）で、pak128 の絵は使っていない。

置き場は `objects/signal/rail_signal/`。`draw_signal.py`（MIT）が PNG（`rail_signal.png`）と表（`rail_signal.yaml`）を書き出す。直すときはスクリプトを直して流し直す（`python -X utf8 objects/signal/rail_signal/draw_signal.py`。Pillow が要る）。

| `name` | `obj` | `waytype` | 種類 | 画面の名前（ja / en） |
|---|---|---|---|---|
| `pak256_rail_signal` | `roadsign` | `track` | 閉塞信号（`is_signal=1`） | 信号 / Signal |

- 値: 登場年 1900、建設費 `cost=500`（仮。`simuconf.tab` の `cost_signal` は別の値）。
- 絵の並び・立てる場所・置いたときの動きの決まりは、サイトの [信号](https://128-bit-net.github.io/pak256/spec/signal)（元は [site/spec/signal.md](../site/spec/signal.md)）。シートは 8 列 × 2 行で、0 行が信号の絵、1 行の 0 列が道具の絵（`icon`。192px の角丸の四角。駅と同じ作り）、1 列がカーソル（`cursor`）。セルは 256px で、位置合わせは付けない。
- 頭と柱の大きさ: 柱は高さ 5.0m（幅 0.06 タイル）、頭は高さ 1.6m（幅 0.14 タイル。約 3.7m）。灯りは頭の側面の色（赤か緑）、上面は暗い灰色。
- ツールバー: 線路のツールバー（`toolbar[3]`）の `signs(2)` に並ぶ。信号の撤去は `general_tool[46]`（アイコンはバーの 47 番。赤い地に信号と ×）。設定は [config.md](config.md)。

## 置いたときの動き（OTRP v64 で確かめた）

サイトの [信号](https://128-bit-net.github.io/pak256/spec/signal)の「本体の動きの注意」。確かめの範囲は [記録](records/2026-11-27_spec-stations.md)。

## 確かめ

[記録](records/2026-11-26_rail-signal.md)。`tools/vehicle_check/signal.nut`（開いたまま `tools/game.py --send-file` で流す。[game-check.md](game-check.md)）が、周回の線路・駅 2 つ・車庫・信号 4 つ・編成 4 つを置く。

## 確かめていないこと

- 坂・斜め（`diagonal` の絵は付けていない。曲がりの上では直線の絵が出る）・分岐の上の信号。
- 左右の逆側の通行（`is_signals_left`）、夜の見え方、本家 125.0.1。
- 画面からの置き方（ツールバーのボタンを押して置く操作）。スクリプトの `build_sign_at` で置いた。ボタンの絵と並びは画面で見た。
- 信号の撤去の道具の動き（ボタンの絵だけ見た）。
- 複数の信号の種類（先行信号・長閉塞・優先など）。作っていない。
