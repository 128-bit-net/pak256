# ゲームでの確認の道具

ゲームで物を確かめるときの、作業フォルダの用意・起動・閉じ方・後片付けを 1 つにした道具 `tools/game.py`（MIT。[#52](https://github.com/128-bit-net/pak256/issues/52)）。作業者が issue ごとに手で組み直していたものをまとめた（夜の絵での撮り直し、`-lang ja` 抜けの止まり、閉じられないプロセスなど）。

## 1 回の呼び出し

```
python -X utf8 tools/build.py          # 先に pak を組む（--build を付けると game.py が流す）
python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47880 \
    --script <流す Squirrel> --capture <撮る PNG>
```

起動 → Squirrel（`--script` は何本でも。順に流す）→ 撮影 → PID で閉じる → 作業フォルダを消す、まで行う。

| 引数 | 意味 |
|---|---|
| `--env` | 本体の検証環境（環境変数 `PAK256_GAME_ENV` でも渡せる）。個人の絶対パスはリポジトリに書かない |
| `--save` | 保存データの名前（拡張子なし）。指定した 1 つだけ写す |
| `--port` | MCP のポート。47880〜47899 の中で必ず明示する（範囲の外は止まる） |
| `--extra-pak` | 足りない物を別の pak から借りる（試験のときだけ。コミットしない） |
| `--night` | 昼夜の切り替えを止めない（夜の灯りを確かめるとき） |
| `--keep` | 閉じた後も作業フォルダ（既定は `work/game/<ポート>/`）を残す |
| `--mcp-client` | OTRP 本体のリポジトリの `mcp_client.py`（環境変数 `MCP_CLIENT`。既定は pak256 の checkout の隣の `simutrans/` の中） |

## やること・やらないこと

- 検証環境から写すのは、実行ファイル・DLL・`config/`・`font/`・`themes/`・`text/`・`script/`・`music/` と、指定した保存データだけ。**`settings.xml` は写さない**（本体が送信用の記録を持ち、起動のたびに使用状況を外へ送るため）。`pak128` などの絵・`addons/` も写さない。検証環境には書かない。
- 手元で組んだ pak（`build/pak/` の自前の物と AMI）と `config/`・`text/` を、作業フォルダの `pak/` に入れる（配布の zip の `pak256/` と同じ中身）。
- `config/simuconf.tab`（本体の物と pak の物の両方）の末尾に `day_night_shift = 0` を足し、昼夜の切り替えを止める。昼まで早送りして撮り直さない。
- 起動は `-singleuser -set_workdir <作業フォルダ> -objects pak/ -load <保存データ> -freeplay -mute -lang ja -mcp-port <ポート> -screensize 1600x900`。MCP が答えるまで待つ（本体は起動画面の間は答えない。保存データを `-load` で読むので、新しい地図の作成画面は経由しない）。
- ゲームは**起動したときの PID で閉じる**（実行ファイルの名前では止めない）。閉じた後に `tasklist` で残りを確かめ、残ったら知らせて終了コード 1 で終わる（その作業フォルダは消せないので残す）。

## 別の道具から使う

```python
sys.path.insert(0, "tools")
from game import Game
with Game(env, "flat_512_left_v64", 47880) as g:
    g.sq("return 1")                       # Squirrel（戻り値の文字列）
    g.sq_file("course.nut", head="OX <- 40;\n")
    g.road(40, 40, 48, 40, "ami_road_local")   # 道路を敷く（command_x(tool_build_way)）
    g.station(44, 40, "<停留所の name>")         # 停留所を置く（command_x(tool_build_station)）
    g.capture("out/shot.png")              # capture_screen
```

- `tools/vehicle_check/run.py`（[vehicles.md](vehicles.md) の「試験」）はこの上で動く。
- 停留所の名前は物の `name` だけ（`"1,<name>"` の形は失敗する）。
- 本体の 1 か月は約 13 分。街の育ちは `debug.set_game_speed(128)`（1 年が約 50 秒）で早送りして見る。

## テストプレイのフォルダに入れる道具（#38）との共通部分

pak を入れる処理は `game.install_pak(dest)`。`dest` に、配布の zip と同じ形（`*.pak`・`config/`・`text/`）で入れる。#38 の道具もこれを呼ぶ。ゲームの作業フォルダへ入れるときは `dest` が `<作業フォルダ>/pak/`。

## 検査

`tools/test_game.py`（ゲームは起動しない）: 写す物と写さない物（`settings.xml`・保存データの他の物）、`simuconf.tab` への追記（両方・重ねて足さない・CRLF を保つ・`--night`）、借りる pak、起動の引数、ポートの範囲。起動から閉じるまでは、ゲームで確かめる（PR の画面）。
