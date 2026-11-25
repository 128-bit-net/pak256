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
| `--port` | MCP のポート。47800〜47899（pak256 の作業者全体の範囲。`game.py` の `PORT_MIN`・`PORT_MAX`）の中で必ず明示する。作業者ごとに割り当てられた範囲（進捗管理が渡す）を使う。範囲の外は止まる |
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
    g.settle(10)                           # 建物を置いた後、建設中の絵が終わるまで進める（速さ 64 → 1 に戻す）
    g.dialog("finances")                   # 窓を開く（名前か番号。下の表）
    g.capture("out/shot.png")              # capture_screen
```

- 建物（車庫・停留所など）は、置いた直後は建設中の絵（黄と黒の縞）で、速さ 1 のままだと終わらない（#58）。撮る前に `g.settle(秒)` を呼ぶ（既定は実時間 15 秒、速さ 64。建物 1 つで約 12 秒、AMI の車庫は工事がゲーム内の約 100 秒かかるので `g.settle(20)` にする（stations.md）。途中で止まっても速さ 1 に戻す）。
- Squirrel の文字列の中に改行を入れると、本体でコンパイルが通らない。Python の通常の文字列に書いたバックスラッシュ n は本物の改行になるので、`sq`・`sq_file` は流す前に `ValueError` で止める（文字列の外の改行・注釈の中・`@"…"` は構わない）。区切りに改行を使わないか、raw 文字列で渡す。
- 親が強制終了されても閉じる: ゲームは起動のとき Windows の Job Object（`KILL_ON_JOB_CLOSE`）に入れる。`tools/game.py` を動かす Python を `TaskStop` などで強制終了しても、OS がゲームを終わらせ、ポートを握ったまま残らない（#30 で 47810 が残った）。それでも、長い確かめは強制終了せず待つ。入れられなかったときは `[game] Job Object に入れられなかった` と出る（Python が別の Job の中で、入れ子にできない環境）。
- `tools/vehicle_check/run.py`（[vehicles.md](vehicles.md) の「試験」）はこの上で動く。
- 配布の zip の中身だけで起動するときは、zip を展開して `*.pak`（と `ami_license.txt`）を 1 つのフォルダに集め、`Game(..., build=<その pak のフォルダの親>, root=<config/ と text/ のある所>)` を渡す。手元で組んだ物（`build/pak/`）や作業フォルダの `config/` を混ぜずに確かめられる（2026-11-25、#70。手順は `records/2026-11-25_alpha03-check.md` の 1）。
- 停留所の名前は物の `name` だけ（`"1,<name>"` の形は失敗する）。
- 本体の 1 か月は約 13 分。街の育ちは `debug.set_game_speed(128)`（1 年が約 50 秒）で早送りして見る。

## 窓の番号（`Game.dialog`）

`gui.open_dialog_tool(番号)` で開く窓。番号は本体の `simmenu.h` の `DIALOG_*` を 0 から数えた物（OTRP v64）。`Game.dialog` は名前か番号を取る。名前は `game.DIALOGS`。収入・編成・産業の窓を撮るときは 5・15・18。

| 番号 | 名前 | 窓 |
|---|---|---|
| 0 | `help` | ヘルプ |
| 1 | `options` | 設定 |
| 2 | `minimap` | ミニマップ |
| 3 | `lineoverview` | 路線一覧 |
| 4 | `messages` | メッセージ |
| 5 | `finances` | 財務（収入・支出） |
| 6 | `players` | プレイヤー一覧 |
| 7 | `displayoptions` | 表示の設定 |
| 8 | `sound` | 音 |
| 9 | `language` | 言語 |
| 10 | `playercolor` | プレイヤーの色 |
| 11 | `jump` | 座標へ移動 |
| 12 | `load` | 読み込み |
| 13 | `save` | 保存 |
| 14 | `list_halt` | 停留所一覧 |
| 15 | `list_convoi` | 編成一覧 |
| 16 | `list_town` | 街一覧 |
| 17 | `list_goods` | 貨物一覧 |
| 18 | `list_factory` | 産業一覧 |
| 19 | `list_curiosity` | 名所一覧 |

20 番より先（編集用の窓・車庫一覧など）は、必要になったときに `DIALOGS` と、この表へ足す。

## ツールバーを押す（`gui.click`）

- `gui.click(x, y)` は座標だけ渡す。3 つめ以降は真偽値（`shift`・`ctrl`）で、数を渡すと `Call function failed` になる（2026-11-25、#66）。
- 編集のサブメニュー（`EDITTOOLS`）は公共プレイヤーのときだけ出る。特別のサブメニューのプレイヤーの切り替え（`simple_tool[5]`）を押して公共プレイヤーにしてから開く（#66。記録は `docs/records/2026-11-25_toolbar-icons.md`）。

## テストプレイのフォルダに入れる道具（`tools/install_local.py`、#38）

手元で組んだ pak、または配布の zip を、テストプレイのフォルダ（本体の実行ファイルの横）の `pak256/` に入れる。ゲームは起動しない。

```
python -X utf8 tools/install_local.py <テストプレイのフォルダ> --build           # build.py で組んでから、build/pak/ と config/・text/ を入れる
python -X utf8 tools/install_local.py <テストプレイのフォルダ>                    # 組み済みの build/pak/ を入れる
python -X utf8 tools/install_local.py <テストプレイのフォルダ> --zip <配布の zip>  # Release の zip などを直接入れる
```

- 入れ先の形: `<dest>/<本体の実行ファイル>`・`<dest>/pak256/`（この道具が入れる）・`<dest>/play.bat`（無ければ作る。`-singleuser -objects pak256/` を付けて起動する。既にあれば触らない）。`save/`・`settings.xml` には触らない。
- `pak256/VERSION` に入れた物の版の名前を書く（手元で組んだ物は `local-<短いコミット>`、作業ツリーに変更があれば `-dirty`。zip は `zip-<zip のファイル名>`）。
- `package.py` は通さない（配布用の許諾の検査・zip への固めと展開は、ゲームで試すだけの用途に要らないため。`build.py` の後の `build/pak/` と `config/`・`text/` を、配布の zip と同じ一覧から直接入れる）。
- 入れ替えるとき、`pak256/` の最上段の古い `*.pak`・`config/`・`text/`・`VERSION` は消す。`pak256/` の下位のフォルダなどほかの物は残す（pak を下位のフォルダに置かない）。入れる物が揃わない（pak が無い・zip に pak が無い）ときは、消す前に止まる。
- 入れ先に本体の実行ファイルが無い・このリポジトリの中なら止まる（間違った場所へ入れない）。
- zip は、消す前に壊れていないか・危ない名前が無いかを調べる。先頭が `pak256/` の形（`package.py` の物）でも、先頭の無い形でもよい。入れるのは最上段の `*.pak`・`config/`・`text/` だけ（許諾の文などは入れない）。`..`・絶対パスの名前は止める。
- 配布用の許諾の文の検査（`LICENSE.md` の例外など）は通さない。ゲームで試すだけで、配るわけではない。配るのは `package.py`。

pak を入れる処理は `game.install_pak(dest, zip_path=…, clean=…)` で、`Game` の作業フォルダ（`<作業フォルダ>/pak/`）も同じ関数で入れる。配布の zip の一覧のうち、ゲームが読む物だけを返す `package.collect_runtime` を土台にしていて、許諾の検査（`package.collect`）とは切り離してある。

## 検査

`tools/test_game.py`（ゲームは起動しない）: 窓の番号（`Game.dialog`・表との一致）、`settle` の速さの戻し、Squirrel の文字列の改行の検査、Job Object（親を強制終了すると子が終わる。Windows だけ）、写す物と写さない物（`settings.xml`・保存データの他の物）、`simuconf.tab` への追記（両方・重ねて足さない・CRLF を保つ・`--night`）、借りる pak、起動の引数、ポートの範囲。起動から閉じるまでは、ゲームで確かめる（PR の画面）。`tools/test_install_local.py`: `install_local.py` と `install_pak`（入れる物・`save/`・`settings.xml` に触らない・`play.bat`・入れ替え・zip・危ない名前・失敗のとき消さない）。
