# ゲームでの確認の道具

ゲームで物を確かめるときの、作業フォルダの用意・起動・閉じ方・後片付けを 1 つにした道具 `tools/game.py`（MIT。[#52](https://github.com/128-bit-net/pak256/issues/52)）。作業者が issue ごとに手で組み直していたものをまとめた（夜の絵での撮り直し、`-lang ja` 抜けの止まり、閉じられないプロセスなど）。

## 1 回の呼び出し

```
python -X utf8 tools/build.py          # 先に pak を組む（--build を付けると game.py が流す）
python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47880 \
    --script <流す Squirrel> --capture <撮る PNG>
```

起動 → Squirrel（`--script` は何本でも。順に流す）→ 撮影 → PID で閉じる → 作業フォルダを消す、まで行う。

出力を `> work/…log` に残すときは、先に `mkdir -p work` する。作業フォルダの `work/` は `game.py` が自分で作るが、リダイレクトの先はシェルが `game.py` より前に開くので、作ったばかりの worktree（`work/` が無い）ではゲームが起動しない。後ろに別のコマンドを続けていると、全体の終了コードは 0 に見える（#109・#119）。

| 引数 | 意味 |
|---|---|
| `--env` | 本体の検証環境（環境変数 `PAK256_GAME_ENV` でも渡せる）。個人の絶対パスはリポジトリに書かない |
| `--save` | 保存データの名前（拡張子なし）。指定した 1 つだけ写す |
| `--port` | MCP のポート。47800〜47999（pak256 の作業者全体の範囲。`game.py` の `PORT_MIN`・`PORT_MAX`）の中で必ず明示する。作業者ごとに割り当てられた範囲（進捗管理が渡す）を使う。範囲の外は止まる |
| `--extra-pak` | 足りない物を別の pak から借りる（試験のときだけ。コミットしない） |
| `--night` | 昼夜の切り替えを止めない（夜の灯りを確かめるとき） |
| `--keep` | 閉じた後も作業フォルダ（既定は `work/game/<ポート>/`）を残す |
| `--interactive` | 起動して命令を待つ（下の「開いたまま使う」） |
| `--mcp-client` | OTRP 本体のリポジトリの `mcp_client.py`（環境変数 `MCP_CLIENT`。既定は pak256 の checkout の隣の `simutrans/` の中） |

## やること・やらないこと

- 検証環境から写すのは、実行ファイル・DLL・`config/`・`font/`・`themes/`・`text/`・`script/`・`music/` と、指定した保存データだけ。**`settings.xml` は写さない**（本体が送信用の記録を持ち、起動のたびに使用状況を外へ送るため）。`pak128` などの絵・`addons/` も写さない。検証環境には書かない。
- 手元で組んだ pak（`build/pak/` の自前の物と AMI）と `config/`・`text/` を、作業フォルダの `pak/` に入れる（配布の zip の `pak256/` と同じ中身）。
- `config/simuconf.tab`（本体の物と pak の物の両方）の末尾に `day_night_shift = 0` を足し、昼夜の切り替えを止める。昼まで早送りして撮り直さない。
- 起動は `-singleuser -set_workdir <作業フォルダ> -objects pak/ -load <保存データ> -freeplay -mute -lang ja -mcp-port <ポート> -screensize 1600x900`。MCP が答えるまで待つ（本体は起動画面の間は答えない。保存データを `-load` で読むので、新しい地図の作成画面は経由しない）。
- ゲームは**起動したときの PID で閉じる**（実行ファイルの名前では止めない）。閉じた後に `tasklist` で残りを確かめ、残ったら知らせて終了コード 1 で終わる（その作業フォルダは消せないので残す）。

- 画面は `Game.capture`（本体の `capture_screen`）で撮る。PowerShell の画面全体の撮影は真っ黒になる。

### 道具が行っていること（作業フォルダを手で組むとき）

上の一覧のほか、`game.py` が中で済ませていて、手で組むと踏むこと。起動の手順を自分で組むのは、道具を直すときだけにする。

- 起動に `-singleuser` を付ける。無いと本体が作業フォルダでなく別の場所を見て、`settings.xml`・`themes/`・`save/` が見つからない（2026-11-25、#8）。
- `themes/` を写す。無いと本体が止まる（2026-11-25、#6）。`settings.xml` は無くても起動する（#8）。
- `settings.xml` を写して送信用の記録を消すときは、CDATA ごと消さず、中身だけを空にする。ごと消すと設定が壊れる（2026-11-25、#6）。
- 昼夜は `config/simuconf.tab` の末尾の `day_night_shift = 0` で止める（pak の側の `<pak>/config/simuconf.tab` に足しても効く）。夜の灯りを確かめるときだけ外す（`--night`）。昼まで早送りして撮り直すのは、昼夜が飛んで当てにならない（2026-11-25、#44）。
- `-load` の保存データの名前は、拡張子なしで渡すと確実。
- 本体は起動画面（地図を作る前）の間は MCP に答えないので、スクリプトで新しい地図は作れない。平らな保存データを `-load` で読み、地形はスクリプトで作る（2026-11-25、#5）。新しい地図の作成画面で生える物（木など）はスクリプトで確かめられないので、PR の「確かめていないこと」に書く。

## スクリプトで物を置くときの癖

- 保存データ `flat_512_left_v64` は x が 256 以上が雪の気候。温帯の物は x<256 に置く（2026-11-25、#11）。
- 道路は `command_x(tool_build_way).work(pl, 座標1, 座標2, "<道路の name>")`、停留所は `command_x(tool_build_station).work(pl, coord3d, "<停留所の name>")`。停留所の引数に番号を付けた `"1,<name>"` は失敗する（2026-11-25、#44。`Game.road`・`Game.station`）。
- 建物（車庫・停留所など）は、置いた直後は建設中の縞。`debug.set_game_speed(64)` で進めてから撮る（2026-11-25、#58。`Game.settle`）。
- `run_squirrel` に渡す文字列の中に改行を入れない。呼ぶ側で書いた `\n` が本物の改行になって、コンパイルが通らない（`Game.sq` は流す前に止める。2026-11-25、#59）。
- 街は `command_x(tool_add_city).work(pl, coord3d)`。最後の引数の文字列は省いてよい。`""+数値` の連結は Squirrel でエラーになる（2026-11-25、#11）。
- 街は旅客などの輸送が無いと育たない。輸送の無い確かめでは `city_list_x()` の `change_size` で人口を足し、PR にそう書く（2026-11-25、#7〜#9）。
- 街の建物を置く道具（`tool_build_house`）の引数は、建物の名前の前に 2 文字を付ける。1 文字目は気候の制限を外すか（`0` は外さない）、2 文字目は向き（`00<name>` は向き 0）。街の建物は、近くに街が無いと置けない（2026-11-26、#104。形は本体の `simtool.cc` の `tool_build_house_t::work_on_ground`）。
- 木を植える道具は、公共のプレーヤーで呼ぶ（2026-11-26、#104）。地図の木の設定が「無し」だと、ほかのプレーヤーは植えられない（本体の `tool_plant_tree_t::work`）。森は `tool_forest`（`tools/tree_check.py`）。
- 地形は `command_x.grid_raise`・`command_x.grid_lower` で作る。`grid_lower` は地下水位 −3 まで（2026-11-25、#5）。水は `command_x(tool_change_water_height).work(pl, pos, "1")`（#5）。
- 画面に出る名札を消すには、`Game(..., simuconf_extra=["show_names = 0"])` で起動する（下の「設定を足す」。2026-11-26、#122）。
- 長い確かめは `tools/game.py` を動かす Python を強制終了せずに待つ。強制終了するとゲームが閉じられず、ポートを握ったまま残ることがある（Job Object に入れられた場合は閉じる。下の「別の道具から使う」）。止めたときは、起動した PID を `tasklist` で探して閉じる（2026-11-25、#30）。

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

## 設定を足す（`simuconf_extra`、#122）

```python
with Game(env, "flat_512_left_v64", 47880, simuconf_extra=["show_names = 0"]) as g:
    ...
```

- 起動の前に、作業フォルダの本体と pak の両方の `config/simuconf.tab` の**先頭**へ、渡した行を足す。1 要素が「キー = 値」の 1 行（違う形は `ValueError`）。`--night` でも足す。`prepare_workdir` にも同じ引数がある。コマンドの引数は無い。
- 先頭に足すのは、本体が 1 つのファイルの中の同じキーを先に書いた行から取るため（`tabfile.cc` の `tabfileobj_t::put`）。末尾に足すと、元からその行があるファイル（検証環境の本体の `simuconf.tab` の `show_names = 3` など）では効かない。
- 保存データが持つ設定は、保存データの値が使われることがある（足した行が効いたかは画面で確かめる）。
- `docs/records/` の古いスクリプトは `game.append_day_night_off` を包んで足している。記録はそのままで、新しいスクリプトはこの引数を使う。

## 気候と月（`Game.climate`・`Game.wait_month`、#109）

```python
g.climate(100, 100, 113, 113, "desert")   # 矩形の気候を塗る（番号 1〜7 か名前。z は既定 0）
g.wait_month(0)                          # 月が 0（1 月）になるまで早送りして、速さを 1 に戻す
time.sleep(8)                            # 木などの絵が季節に合わせて入れ替わるのを待つ
```

- **気候は地形の後に塗る。** 地形を変える（`grid_raise`・`grid_lower`・水位）と、気候が高さで決まり直して、塗った気候が消える（#101 で湖の水位を上げた後に塗り直した。[記録](records/2026-11-26_climate-ground-screens.md)）。
- 気候の番号は 1 砂漠・2 熱帯・3 地中海・4 温帯・5 ツンドラ・6 岩・7 雪（名前は `desert`・`tropic`・`mediterran`・`temperate`・`tundra`・`rocky`・`arctic`。`game.CLIMATES`）。0（水）は塗る手では扱わない（地面が水になる・水の上を塗ると水位が下がる）。水は `tool_change_water_height` で入れる。
- 本体は 1 タイルも変わらなくても成功を返すので、塗れたかは画面で見る。塗るのは道具 `tool_set_climate`（矩形）。
- 月は 0 始まり（0 = 1 月）。`world.get_time().month` で読める。本体の季節は月だけで決まり（OTRP の `simworld.cc` の `month_to_season`。`game.MONTH_TO_SEASON`）、スクリプトから季節を直に指定する手が無いので、目的の月まで早送りする。

| 季節（番号） | 月（0 始まり） | 撮るのに使う月（`game.SEASON_MONTHS`） |
|---|---|---|
| 夏（0） | 5〜8（6〜9 月） | 6 |
| 秋（1） | 9〜10（10〜11 月） | 9 |
| 冬（2） | 11・0〜2（12〜3 月） | 0 |
| 春（3） | 3〜4（4〜5 月） | 3 |

- `wait_month` は、既にその月なら何もしない。月の中の日付はそろえられない。目的の月が過ぎた直後なら約 1 年分を早送りする（本体の 1 か月は約 13 分で、速さ 64 なら 1 年は数分）。待ちの上限は `timeout`（実時間の秒。既定 420）。街の建物の絵の添字も、この季節の番号（[buildings.md](buildings.md)）。
- 開いたまま使うときは `--send "@month 0" --timeout 480`。気候は Squirrel を直に流す（`command_x(tool_set_climate).work(...)`）。

## 開いたまま使う（`--interactive`・`--send`、#85）

窓を `gui.click` で順に開いて撮るなど、結果を見ながら 1 つずつ進めたいときの入口。自作の枠は要らない。AMI の `ingame/game.sh`（起動 / `RUN` / `CAPTURE` / `STOP`）と同じ形で、`game.py` が起動・見張り・閉じるまでを持つ。

```
# 1) 起動して待つ（長く動くので背景で。起動は 30〜90 秒かかり、[interactive] 待っている と出たら流せる）
python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47900 --interactive
# 2) 別の呼び出しから、命令を 1 つずつ流す（結果が標準出力に出る。失敗は終了コード 1）
python -X utf8 tools/game.py --port 47900 --send "return world.get_time().year"
python -X utf8 tools/game.py --port 47900 --send "@dialog finances"
python -X utf8 tools/game.py --port 47900 --send "@capture out/a.png"
python -X utf8 tools/game.py --port 47900 --send-file tools/vehicle_check/signal.nut   # 変数を .nut の先頭に直に書いてあるファイルだけ（下の注意）
# 3) 終わったら閉じる
python -X utf8 tools/game.py --port 47900 --send "@quit"
```

| 命令 | 意味 |
|---|---|
| 普通の文 | Squirrel として流し、戻り値を返す（`gui.click(x, y)` もここ） |
| `@capture <PNG>` | 画面を撮る（パスは送る側の今のフォルダからの相対） |
| `@dialog <名前か番号>` | 窓を開く（下の表） |
| `@settle [秒]` | 建設中の絵が終わるまで進める（既定 15 秒） |
| `@month <月>` | 月が 0〜11（0 = 1 月）になるまで早送りする（上の「気候と月」。`--timeout` を長くする） |
| `@quit` | ゲームを閉じて終わる |

- 仕組み: 見張る側は作業フォルダ（既定 `work/game/<ポート>/`）の `inbox/` に置かれた命令のファイルを番号順に 1 つずつ流し、結果を `.out` に書く。`--send` は同じポート（`--work` を使ったなら同じ値）を渡す。
- 命令の失敗（Squirrel の誤り・知らない指示）では見張りは止まらず、次の命令を受ける。
- **必ず閉じる**: 終わったら `@quit` を送る。見張りの Ctrl+C、命令が `--idle-limit` 秒（既定 3600）来ないとき、ゲームが落ちたときも、起動した PID で閉じて作業フォルダを消す（`--keep` なら残す）。見張りの Python が強制終了されても、Job Object で閉じる。起動は `-load` と写した作業フォルダなので、自動保存は失わない。
- 同じポートで 2 台は起動できない。ポートは割り当てられた範囲の中。
- 複数の `--send` を同時に流さない（順に流す）。
- **`--send-file` では、変数を先頭に足せない**（`Game.sq_file` の `head=` に当たる物が無い）。流す `.nut` に、変数の定義を直に書く（例: 先頭に `OX <- 40; OY <- 60; CARS <- 4;`）。値を変えて流すときは、`sed` で写しを作って流す（`sed 's/OY <- 60/OY <- 110/' a.nut > work/b.nut`）。同じ `.nut` を `Game.sq_file(path, head=…)` から流すなら、先頭に同じ名前の変数を足し、`.nut` の定義の行を消す（二重に定義すると後の値が勝つ）。`tools/vehicle_check/signal.nut`・`road_stop_coal.nut` がこの形（`road_stop_bus.nut` は変数が `WAY`・`DEPOT` だけで、座標は中に書いてある）。
- **信号を置き直したときの向き**（本体の `simtool.cc` の `place_sign_intern` を読んで決めた。OTRP v64 で 2 回目までは画面で確かめた）: `command_x.build_sign_at` を同じ所に重ねて呼ぶと、1 回目は両方向、2 回目は片方向、3 回目は反対の片方向、4 回目は両方向に戻る。2 回目の列車が進む向きは、東西の線路なら西、南北の線路なら南（本体の中の向きは通れない向きの ribi で、東・北）。両方向の信号だけの 1 本の線路（周回）に、逆向きの編成が入ると、止まったまま動かなくなった（向き合ったのが原因と見ている）。周回させるときは、上の辺（東西）と左の辺（南北）だけに 2 回ずつ置くと、反時計回りにそろう。詳しくは [signals.md](signals.md) の「置いたときの動き」と `tools/vehicle_check/signal.nut`。
- 1 つの Squirrel は最大 300 秒（`CMD_TIMEOUT`）待つ。`--send` の `--timeout`（既定 120）は送る側の待ちで、超えると命令を取り下げる（見張りが取った後なら「実行された可能性がある」と出る）。見張りやゲームが閉じると、送る側はすぐ失敗する。

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

`tools/test_frames.py`: 地面の印・格子の線・タイルのカーソルの枠が地面の縁の画素と一致する（[ground.md](ground.md) の「枠の線」）。`tools/test_ground.py`: コミットしてある `ClimateTexture` の模様 8 枚が、斜め格子の周期（(128,64)・(128,-64)）でずらしても同じで、透明な画素が無い（Water は菱形なので見ない）。`tools/test_town_buildings.py`: 街の建物の `backimage` の季節の添字が 4 枚（夏・秋・冬・春）で、冬だけが右の絵を指し、右の絵が左と違う。

`tools/test_package.py`: `package.py` の入れる物と、`build.py` が makeobj の `Warning`・`ERROR` の行で（終了コードが 0 でも）止まること。

`tools/test_game.py`（ゲームは起動しない）: `work/` が無いときに作ること・作れないときに起動せず失敗すること、気候を塗る Squirrel と番号の検査、月の早送り（速さの戻し・時間切れ・中断・既にその月）、開いたまま使う入口（`run_command`・`serve_inbox`・`send_command`。偽のゲームで往復・失敗の後の継続・`@quit`・無音の終了）、窓の番号（`Game.dialog`・表との一致）、`settle` の速さの戻し、Squirrel の文字列の改行の検査、Job Object（親を強制終了すると子が終わる。Windows だけ）、写す物と写さない物（`settings.xml`・保存データの他の物）、`simuconf.tab` への追記（両方・重ねて足さない・CRLF を保つ・`--night`）、`simuconf_extra`（両方の先頭・`--night`・行の形の検査・起動に渡ること）、借りる pak、起動の引数、ポートの範囲。起動から閉じるまでは、ゲームで確かめる（PR の画面）。`tools/test_install_local.py`: `install_local.py` と `install_pak`（入れる物・`save/`・`settings.xml` に触らない・`play.bat`・入れ替え・zip・危ない名前・失敗のとき消さない）。
