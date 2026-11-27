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
| `--port` | MCP のポート。必ず明示する。既定の範囲は 47800〜47999（pak256 の作業者全体の範囲。`game.py` の `PORT_MIN`・`PORT_MAX`）で、作業者ごとに割り当てられた範囲（進捗管理が渡す）を使う。範囲の外は止まる |
| `--port-range` | ポートの範囲を変える。`下限-上限`（例 `47200-47299`）。pak256 の外の作業者が、自分に割り当てられた範囲で使うとき（[#128](https://github.com/128-bit-net/pak256/issues/128)）。環境変数 `PAK256_PORT_RANGE` でも渡せる（`game.py` を読み込む別の道具にも効く）。`Game(..., port_range="47200-47299")` も同じ。引数が環境変数より先 |
| `--player-nr` | Squirrel（`--script`・`--send`・`--send-file`）を流すプレーヤー。公共は 1。省くと 0（下の「公共のプレーヤーで流す」） |
| `--pak` | `build/pak/` の代わりに入れる pak のフォルダ（下の「pak の場所を指定する」） |
| `--extra-pak` | 足りない物を別の pak から借りる（試験のときだけ。コミットしない） |
| `--night` | 昼夜の切り替えを止めない（夜の灯りを確かめるとき） |
| `--keep` | 閉じた後も作業フォルダ（既定は `work/game/<ポート>/`）を残す |
| `--keep-save-roads` | 保存データの写しの道路名を書き換えない（下の「保存データの道路名」） |
| `--interactive` | 起動して命令を待つ（下の「開いたまま使う」） |
| `--mcp-client` | OTRP 本体のリポジトリの `mcp_client.py`（環境変数 `MCP_CLIENT`。既定は pak256 の checkout の隣の `simutrans/` の中） |

## pak の場所を指定する（`--pak`、#170）

`--pak <フォルダ>` を付けると、`build/pak/` の代わりに、そのフォルダの直下の `*.pak` を入れる。省くと `build/pak/`。

```
python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47880 --pak <展開した所>/pak256 --capture <撮る PNG>
python -X utf8 tools/vehicle_check/rail_run.py --env <検証環境> --save flat_512_left_v64 --port 47880 --out work/rail --pak <展開した所>/pak256
```

- **フォルダに `config/` があるとき**（配布の zip を展開した `pak256/`）は、`config/`・`text/`・`sound/`・`demo.sve` もそのフォルダの物を使う。リポジトリの物は混ぜない。
- `config/` が無いとき（`build/pak/` の形）は、`config/`・`text/`・`sound/`・`demo/demo.sve` はリポジトリの物を使う。
- フォルダが無い・直下に `*.pak` が無い・`config/` に `simuconf.tab` が無い・作業フォルダの中にある、のときは、作業フォルダを消す前に止まる。zip のファイルは渡せない（先に展開する）。
- 受ける道具: `tools/game.py`（起動する呼び出し。`--send`・`--build` とは一緒に使えない）と、`tools/vehicle_check/` の `run.py`・`rail_run.py`・`rail_curve_run.py`・`air_run.py`・`monorail_run.py`・`tram_run.py`・`sound_run.py`、`tools/tree_check.py`（`--montage` とは一緒に使えない。#181）。`river_run.py` はゲームを起動しないので受けない（`game.py --interactive --pak <フォルダ>` で開いたゲームに流す）。
- 自分の道具からは `Game(…, pak_dir=<フォルダ>)`。

## やること・やらないこと

- 検証環境から写すのは、実行ファイル・DLL・`config/`・`font/`・`themes/`・`text/`・`script/`・`music/` と、指定した保存データだけ。**`settings.xml` は写さない**（本体が送信用の記録を持ち、起動のたびに使用状況を外へ送るため）。`pak128` などの絵・`addons/` も写さない。検証環境には書かない。
- 手元で組んだ pak（`build/pak/` の自前の物と AMI。`--pak` を付けたときはそのフォルダの pak）と `config/`・`text/`・`sound/` を、作業フォルダの `pak/` に入れる（配布の zip の `pak256/` と同じ中身）。
- `config/simuconf.tab`（本体の物と pak の物の両方）の末尾に `day_night_shift = 0` を足し、昼夜の切り替えを止める。昼まで早送りして撮り直さない。
- 写した保存データの街の道路・街どうしの道路の名前を、pak の `config/simuconf.tab` の指定に書き換える（下の「保存データの道路名」）。
- 起動は `-singleuser -set_workdir <作業フォルダ> -objects pak/ -load <保存データ> -freeplay -mute -lang ja -mcp-port <ポート> -screensize 1600x900`。MCP が答えるまで待つ（本体は起動画面の間は答えない。保存データを `-load` で読むので、新しい地図の作成画面は経由しない）。
- 音は既定で `-mute`。`--sound load`（`Game(sound="load")`）は音を読むだけで鳴らさず、`--sound on` はスピーカーから鳴る（[sound.md](sound.md)）。
- ゲームは**起動したときの PID で閉じる**（実行ファイルの名前では止めない）。閉じた後に `tasklist` で残りを確かめ、残ったら知らせて終了コード 1 で終わる（その作業フォルダは消せないので残す）。
- **本体が FATAL ERROR・通知の窓で止まったら、待たずに閉じて失敗で終わる**（[#132](https://github.com/128-bit-net/pak256/issues/132)・[#142](https://github.com/128-bit-net/pak256/issues/142)）。本体は、起動した後の失敗では「PRESS ANY KEY」の画面のまま残って MCP に答えない。起動の途中の失敗（pak が無いなど）では「Fatal Error」の通知の窓（`dr_fatal_notify`）が出る。窓のまま残った回（45 秒以上）と、12〜24 秒で本体が自分で終了コード 1 になった回があり、違いの理由は分かっていない。`game.py` は MCP の答えや `settle` を待つ間も起動のログ（`game.log`）を見て、`FATAL ERROR` か `dr_fatal_notify: ERROR:` が出ていたら、起動した PID を閉じ、その行から後ろのエラーの文を出して終了コード 1 で終わる。起動の待ち・Squirrel・撮影・`settle`・`--interactive` の見張りで同じ。ほかの道具から `Game` を使うときは `game.GameFatalError`（`RuntimeError` の一種）が上がる。見るのはこの 2 つの文だけ。通知の窓を実機で確かめたのは、`ground.Outside.pak` を抜いた起動だけ（2026-11-26、OTRP v64。起動から約 1 秒で文がログに出て、コマンドは終了コード 1）。フォントが無いときなど、ほかの `dr_fatal_notify` は本体のソースを読んで同じ文が出ると見ている。

- 画面は `Game.capture`（本体の `capture_screen`）で撮る。PowerShell の画面全体の撮影は真っ黒になる。

### 道具が行っていること（作業フォルダを手で組むとき）

上の一覧のほか、`game.py` が中で済ませていて、手で組むと踏むこと。起動の手順を自分で組むのは、道具を直すときだけにする。

- 起動に `-singleuser` を付ける。無いと本体が作業フォルダでなく別の場所を見て、`settings.xml`・`themes/`・`save/` が見つからない（2026-11-25、#8）。
- `themes/` を写す。無いと本体が止まる（2026-11-25、#6）。`settings.xml` は無くても起動する（#8）。
- `settings.xml` を写して送信用の記録を消すときは、CDATA ごと消さず、中身だけを空にする。ごと消すと設定が壊れる（2026-11-25、#6）。
- 昼夜は `config/simuconf.tab` の末尾の `day_night_shift = 0` で止める（pak の側の `<pak>/config/simuconf.tab` に足しても効く）。夜の灯りを確かめるときだけ外す（`--night`）。昼まで早送りして撮り直すのは、昼夜が飛んで当てにならない（2026-11-25、#44）。
- `-load` の保存データの名前は、拡張子なしで渡すと確実。
- 本体は起動画面（地図を作る前）の間は MCP に答えないので、スクリプトで新しい地図は作れない。平らな保存データを `-load` で読み、地形はスクリプトで作る（2026-11-25、#5）。新しい地図の作成画面で生える物（木など）はスクリプトで確かめられないので、PR の「確かめていないこと」に書く。

## 保存データの道路名（#151）

保存データは、街の道路（`city_road`）と街どうしの道路（`intercity_road`）の名前の一覧を自分で持つ。`flat_512_left_v64` の一覧は pak128 の道路の名前で、pak256 には無いので、そのまま読むと本体が代わりの道路を選び、街の道路が壁用の `ami_road_local_base_single` になる（2026-11-26、#147。[記録](records/2026-11-26_town-road.md)）。

`game.py` は、起動の前に**作業フォルダの写し**の 2 つの一覧を、作業フォルダの `pak/config/simuconf.tab` の指定（名前・登場年・退役年）に丸ごと書き換える。検証環境の保存データは変えない。書き換えたときは `[game] 保存データの写しの道路名を書き換えた（…）` と出る。pak256 の指定のとおりなら、街の道路は新しい地図の指定と同じ `ami_road_local` になる（2026-11-26、OTRP v64、`flat_512_left_v64`。街の道路の道具と `tool_add_city` の後の道で確かめた。本体が保存し直した物の 2 つの一覧が指定の値になることも見た）。

- **既定で書き換える。** 指定しないと気づかずに違う絵を見ることになるため。
- **保存された名前そのものを確かめるときは止める**: コマンドは `--keep-save-roads`、`Game`・`prepare_workdir` は `rewrite_roads=False`。下の「保存データの互換の確かめ」はこれに当たる。`docs/records/` の古いスクリプトは書き換える前の道具に合わせてあり、流し直すと既定の書き換えが効く（保存データを比べる物は `rewrite_roads=False` を足す。`2026-11-26_town-road/check.py` は古い名前があることを確かめるので、そのままでは流れない）。
- `simuconf.tab` に指定（`city_road[0]`・`intercity_road[0]` の行）の無い方の一覧は、保存データのまま残す。
- 扱う保存データは、gzip・bzip2・無圧縮のバイナリの形。ほかの圧縮の形や、一覧が 1 か所に決まらないときは、写しに触らずに「保存データの道路名は書き換えていない（理由）」と出して、そのまま起動する。XML の形は試していない。

## 起動の画面を撮る

**`-load` を付けない起動では、起動の窓が出ている間、本体は MCP に答えない**（2026-11-27、OTRP v64、[#79](https://github.com/128-bit-net/pak256/issues/79)）。`game.py` の起動の待ちは時間切れになり、`capture_screen` も使えない。**その間の画面は `tools/title_shot.py` で撮る**（MIT。Windows だけ。Pillow が要る）。自分で起動した窓の中身を読むだけで、キーやクリックなどの入力は送らない。

```
python -X utf8 tools/title_shot.py --env <検証環境> --out work/title.png                     # 組み済みの build/pak/ などを入れる
python -X utf8 tools/title_shot.py --env <検証環境> --out work/title.png --zip <配布の zip>
```

- 保存データの無い作業フォルダ（既定は `work/title_shot/`）を作る。写すのは実行ファイル・DLL・`config/` などで、`save/` と `settings.xml` は写さない。pak は `pak256/` に入れる（`demo.sve` を含む）。
- 起動は `-singleuser -set_workdir <作業フォルダ> -objects pak256/ -lang ja -mute -screensize 1600x900`。`-load` と `-mcp-port` は付けないので、ポートは使わない。
- 起動から 30 秒（`--wait`）待って撮る。真っ黒なら撮り直す（描き直しの前に読むことがある）。本体が終わったときと、起動のログに `FATAL ERROR` か `dr_fatal_notify: ERROR:` が出たときは失敗にする（`game.py` と同じ印）。この印の出ない窓は見分けないので、撮った画像は開いて見る。
- 撮ったら起動した PID を閉じ、作業フォルダを消す（`--keep` で残す）。

## 道路と線路の道が無い pak では起動できない

`flat_512_left_v64` を指定して起動するとき、pak に次の 2 つが無いと本体が止まる（理由は `game.py` が出す `FATAL ERROR` の文。`game.py` は待たずに閉じる。2026-11-26、OTRP v64、[#128](https://github.com/128-bit-net/pak256/issues/128)・[#132](https://github.com/128-bit-net/pak256/issues/132)）。

| 足りない物 | ログ |
|---|---|
| 道路の way | `No road found at all!` |
| 線路の種類の way | `schiene_t::schiene_t() - No rail way available!` |

`tools/build.py --no-ami` で組む pak には、どちらの way も無い。AMI の 256 版の `ami_road.pak` と `ami_rail.pak` を `--extra-pak` で足すと読める。道路の way が 1 つだけのときは、`ami_rail.pak` を足すと読めた（AMI の `ami_road_local` を抜き出して確かめた。手元で組んだ道路では試していない）。2 つは次のように取り出す。

```
python -X utf8 tools/fetch_ami.py work/ami
python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47880 \
    --extra-pak work/ami/ami_road.pak --extra-pak work/ami/ami_rail.pak --capture work/shot.png
```

`ami_road.pak` だけを足しても読めた。AMI の路面表示の way は路面軌道（`tram_track`）なので、それが線路の種類の way になっていると見ている（本体の処理は追っていない）。道路の way を 1 つだけ抜き出して足した場合は、`No rail way available!` で止まった。`ami_rail.pak` だけでは、道路が無いので止まった。

## スクリプトで物を置くときの癖

- 保存データ `flat_512_left_v64` は x が 256 以上が雪の気候。温帯の物は x<256 に置く（2026-11-25、#11）。
- `flat_512_left_v64` の街の道路（街の道路の道具・街が建てる道）は、`game.py` が道路名を書き換えるので `ami_road_local`。書き換えを止めると `ami_road_local_base_single`（上の「保存データの道路名」）。
- **公共のプレーヤーで流す**: Squirrel の道具は、呼び出しの `player_nr`（MCP の `run_squirrel` の引数）のプレーヤーで使われる。スクリプトの中で `player_x(1)` と書くだけでは変わらない。`Game.sq`・`sq_file`・`road`・`station`・`climate` は `player_nr=1` を、コマンドは `--player-nr 1` を渡す（開いたまま使うときは `--send` の側に付ける。`--interactive` には付けない。2026-11-26、[#142](https://github.com/128-bit-net/pak256/issues/142)）。
- **歩道つきの街の道路**は `Game.city_road(x1, y1, x2, y2)`（公共のプレーヤーで `tool_build_cityroad`）。公共でないと歩道は付かず、`road(..., player_nr=1)`（`tool_build_way`）でも付かない（2026-11-26、`flat_512_left_v64` に AMI の道路を足した組で `has_sidewalk()` を比べた。#142）。
- 道路は `command_x(tool_build_way).work(pl, 座標1, 座標2, "<道路の name>")`、停留所は `command_x(tool_build_station).work(pl, coord3d, "<停留所の name>")`。停留所の引数に番号を付けた `"1,<name>"` は失敗する（2026-11-25、#44。`Game.road`・`Game.station`）。
- 建物（車庫・停留所など）は、置いた直後は建設中の縞。`debug.set_game_speed(64)` で進めてから撮る（2026-11-25、#58。`Game.settle`）。
- `run_squirrel` に渡す文字列の中に改行を入れない。呼ぶ側で書いた `\n` が本物の改行になって、コンパイルが通らない（`Game.sq` は流す前に止める。2026-11-25、#59）。
- 街は `command_x(tool_add_city).work(pl, coord3d)`。最後の引数の文字列は省いてよい。`""+数値` の連結は Squirrel でエラーになる（2026-11-25、#11）。
- 街は旅客などの輸送が無いと育たない。輸送の無い確かめでは `city_list_x()` の `change_size` で人口を足し、PR にそう書く（2026-11-25、#7〜#9）。
- 街の建物を置く道具（`tool_build_house`）の引数は、建物の名前の前に 2 文字を付ける。1 文字目は気候の制限を外すか（`0` は外さない）、2 文字目は向き（`00<name>` は向き 0）。街の建物は、近くに街が無いと置けない（2026-11-26、#104。形は本体の `simtool.cc` の `tool_build_house_t::work_on_ground`）。
- 木を植える道具は、公共のプレーヤーで呼ぶ（2026-11-26、#104）。地図の木の設定が「無し」だと、ほかのプレーヤーは植えられない（本体の `tool_plant_tree_t::work`）。森は `tool_forest`（`tools/tree_check.py`）。
- 地形は `command_x.grid_raise`・`command_x.grid_lower` で作る。`grid_lower` は地下水位 −3 まで（2026-11-25、#5）。水は `command_x(tool_change_water_height).work(pl, pos, "1")`（#5）。
- **`run_squirrel` に渡すコードの日本語の文字列リテラルは、本体に化けて届く**（窓の題 `マップの拡張` が 18 バイトなのに、同じ字のリテラルは 30 バイトで一致しなかった）。画面の日本語と比べず、英字の文字列（部品の `text` が `enlarge map` など）か位置・並びで見分ける（2026-11-27、#158、OTRP v64）。
- **`grid_lower` で地下水位まで掘っても水にならない。** 掘った後に `command_x(tool_change_water_height).work(pl, coord3d, "1")` で水を入れ、`is_water()` で確かめる。海が無い地図では川も引かれない（2026-11-27、#158）。
- **窓の位置は開くたびに違うことがあるので、`gui.click` の座標を決め打ちしない。** `gui.get_windows()` と `gui.get_window_components(id)` の `screen_bounds` から部品を探して押す（2026-11-27、#158）。地図の拡大の窓（`gui.open_dialog_tool(24)`）はこの形で操作でき、拡大で川を引かせられる（例は `tools/vehicle_check/river_enlarge.nut`・`river_run.py`）。
- 画面に出る名札を消すには、`Game(..., simuconf_extra=["show_names = 0"])` で起動する（下の「設定を足す」。2026-11-26、#122）。
- 長い確かめは `tools/game.py` を動かす Python を強制終了せずに待つ。強制終了するとゲームが閉じられず、ポートを握ったまま残ることがある（Job Object に入れられた場合は閉じる。下の「別の道具から使う」）。止めたときは、起動した PID を `tasklist` で探して閉じる（2026-11-25、#30）。

- 街の車は、公共のプレーヤーで `command_x(tool_add_citycar).work(pl, tile_x(x, y, 0), "<citycar の name>")` を呼ぶと、名前を指定して置ける。二方向の道のタイルで、街の車が無い所だけに置ける（2026-11-27、#173）。
- 追い越し禁止の道は `command_x(tool_build_way).work(pl, 座標1, 座標2, "<道路の name>," + prohibited_mode + ",0,0,0")` で敷く。停留所で満載待ちの車両の後ろに、街の車が詰まって止まる（2026-11-27、#173）。
- pak の絵の色は各色 5 ビット（緑も）。画面の画素と元の PNG を照らし合わせるときは、RGB の下 3 ビットを落とす（2026-11-27、#173）。

## 歩行者を出す・探す（#184）

歩行者の絵と動きの決まりは [pedestrians.md](pedestrians.md)。ここは確かめの手順（出る条件は OTRP の `vehicle/pedestrian.cc`・`simcity.cc`・`simhalt.cc` を読んだ物）。

**歩行者を直接置くスクリプトの命令は見つかっていない**（本体の `script/` を `pedestrian` で探して、`mo_pedestrian` と道の「歩行者の立ち入り禁止」の値だけ。2026-11-27）。旅客が出る場面を作って、出てくるのを待つ。

出る条件:

- 出るきっかけは 2 つ。街の建物が旅客を出したとき（本体の設定 `random_pedestrians`）と、旅客が目的地の停留所に着いたとき（`stop_pedestrians`。乗り換えで着いただけでは出ない）。`flat_512_left_v64` は、設定を足さなくても出た（きっかけがどちらかは分けて確かめていない）。
- 出る場所は、その建物（停留所はそのタイル）と、東西南北の隣のタイル。そこに道路が無いと出ない。出る数は旅客の数までで、1 回に 1 タイル 4 人まで。
- 道路のうち、つながりが 2 方向のタイル（直線と角）だけ。行き止まり・交差点・歩行者の立ち入り禁止の道には出ない（出た後で交差点を通ることはある）。
- 歩行者の pak が要る（年代が有効な地図では、登場している物）。寿命があり、しばらくすると消える（[pedestrians.md](pedestrians.md)）。

街と道とバス停は `tools/vehicle_check/road_stop_bus.nut`（道は y=60、街は x=60 と x=100）が置く。次の形で、出して探して撮る（リポジトリの直下から。`env` は検証環境）。

```python
import sys, time
sys.path.insert(0, "tools")
from game import Game

with Game(env, "flat_512_left_v64", 47880, simuconf_extra=["show_names = 0"]) as g:
    g.sq_file("tools/vehicle_check/road_stop_bus.nut")
    g.settle(20)   # 建物が建ちきるまで進める
    scan = ('local s=""; for(local x=50;x<=110;x++) for(local y=54;y<=66;y++){ local t=square_x(x,y).get_ground_tile(); '
            'if (t.find_object(mo_pedestrian)) s+=x+","+y+" "; } return s')
    found = []
    for _ in range(60):
        found = g.sq(scan).split()
        if found:
            break
        time.sleep(2)
    x, y = found[0].split(",")
    g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(0.5)
    g.capture("work/pedestrian.png")
```

- 向きを絞るときは、`t.get_way_dirs(wt_road)` を一緒に返す（5・10 が直線、3・6・9・12 が角）。
- 歩行者は歩いて動き、消える。探してからすぐ撮り、写っていなければ撮り直す。大人が 16px と小さいので、撮った画像は切り抜いて拡大して見る。
- 歩く位置の測り方・向き色の印の pak・斜めの道などは、#172 の[記録](records/2026-11-27_pedestrians.md)のスクリプト（記録の時点の物で、直さない）。

### 画面の中心（`gui.jump` で飛んだタイル）

1600x900・拡大 3 では、`gui.jump` で飛んだタイル（地面の高さ 0）の中心は画面の **(896, 575)**。画面の真ん中 (800, 450) から右へ 96・下へ 125px（2026-11-27、OTRP v64、`flat_512_left_v64`。飛んだタイルを中心に道路を十字の 5 タイルで敷き、前後の画像の差分の外接枠 (640, 446)〜(1152, 704) の中心を取った。2 か所で同じ値）。`tools/vehicle_check/run.py` の `JUMP_X, JUMP_Y` はこの値。#172 の記録のスクリプトの (895, 576) とは 1px 違い。

## 別の道具から使う

```python
sys.path.insert(0, "tools")
from game import Game
with Game(env, "flat_512_left_v64", 47880) as g:
    g.sq("return 1")                       # Squirrel（戻り値の文字列）
    g.sq_file("course.nut", head="OX <- 40;\n")
    g.road(40, 40, 48, 40, "ami_road_local")   # 道路を敷く（command_x(tool_build_way)）
    g.city_road(40, 42, 48, 42)                # 歩道つきの街の道路（公共のプレーヤー）
    g.sq("return 1", player_nr=1)              # 公共のプレーヤーで流す
    g.station(44, 40, "<停留所の name>")         # 停留所を置く（command_x(tool_build_station)）
    g.settle(10)                           # 建物を置いた後、建設中の絵が終わるまで進める（速さ 64 → 1 に戻す）
    g.dialog("finances")                   # 窓を開く（名前か番号。下の表）
    g.capture("out/shot.png")              # capture_screen
```

- 建物（車庫・停留所など）は、置いた直後は建設中の絵（黄と黒の縞）で、速さ 1 のままだと終わらない（#58）。撮る前に `g.settle(秒)` を呼ぶ（既定は実時間 15 秒、速さ 64。建物 1 つで約 12 秒、AMI の車庫は工事がゲーム内の約 100 秒かかるので `g.settle(20)` にする（stations.md）。途中で止まっても速さ 1 に戻す）。待つ間に本体が止まったら、秒数を待ち切らずに `GameFatalError`（#142）。
- Squirrel の文字列の中に改行を入れると、本体でコンパイルが通らない。Python の通常の文字列に書いたバックスラッシュ n は本物の改行になるので、`sq`・`sq_file` は流す前に `ValueError` で止める（文字列の外の改行・注釈の中・`@"…"` は構わない）。区切りに改行を使わないか、raw 文字列で渡す。
- 親が強制終了されても閉じる: ゲームは起動のとき Windows の Job Object（`KILL_ON_JOB_CLOSE`）に入れる。`tools/game.py` を動かす Python を `TaskStop` などで強制終了しても、OS がゲームを終わらせ、ポートを握ったまま残らない（#30 で 47810 が残った）。それでも、長い確かめは強制終了せず待つ。入れられなかったときは `[game] Job Object に入れられなかった` と出る（Python が別の Job の中で、入れ子にできない環境）。
- `tools/vehicle_check/run.py`（[vehicles.md](vehicles.md) の「試験」）はこの上で動く。
- 配布の zip の中身だけで起動するときは、zip を展開して `Game(..., pak_dir=<展開した pak256/>)` を渡す（上の「pak の場所を指定する」）。手元で組んだ物（`build/pak/`）やリポジトリの `config/` を混ぜずに確かめられる。
- 停留所の名前は物の `name` だけ（`"1,<name>"` の形は失敗する）。
- 本体の 1 か月は約 13 分。街の育ちは `debug.set_game_speed(128)`（1 年が約 50 秒）で早送りして見る。

## 設定を足す（`simuconf_extra`、#122）

```python
with Game(env, "flat_512_left_v64", 47880, simuconf_extra=["show_names = 0"]) as g:
    ...
```

- 起動の前に、作業フォルダの本体と pak の両方の `config/simuconf.tab` の**先頭**へ、渡した行を足す。1 要素が「キー = 値」の 1 行（違う形は `ValueError`）。`--night` でも足す。`prepare_workdir` にも同じ引数がある。コマンドの引数は無い。
- 先頭に足すのは、本体が 1 つのファイルの中の同じキーを先に書いた行から取るため（`tabfile.cc` の `tabfileobj_t::put`）。末尾に足すと、元からその行があるファイルの中では効かない（検証環境の本体の `simuconf.tab` の `show_names = 3`、pak の `simuconf.tab` の `tile_height = 8` など）。本体の物の後に pak の物が読まれるので、両方にあるキーは pak の側が決める。
- ゲームの画面で確かめたのは `show_names = 0` だけ（`--night` との組み合わせは `tools/test_game.py` のファイルの中身まで）。
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
| `@player <番号> <Squirrel>` | そのプレーヤーで Squirrel を流す（`--send` の `--player-nr` はこれになる） |
| `@quit` | ゲームを閉じて終わる |

- 仕組み: 見張る側は作業フォルダ（既定 `work/game/<ポート>/`）の `inbox/` に置かれた命令のファイルを番号順に 1 つずつ流し、結果を `.out` に書く。`--send` は同じポート（`--work` を使ったなら同じ値）を渡す。
- 命令の失敗（Squirrel の誤り・知らない指示）では見張りは止まらず、次の命令を受ける。
- **必ず閉じる**: 終わったら `@quit` を送る。見張りの Ctrl+C、命令が `--idle-limit` 秒（既定 3600）来ないとき、ゲームが落ちたときも、起動した PID で閉じて作業フォルダを消す（`--keep` なら残す）。本体が FATAL ERROR で止まったときは、命令の途中ならその `--send` にエラーの文を返し（終了コード 1）、見張りの側もエラーの文を出して終了コード 1 で終わる。見張りの Python が強制終了されても、Job Object で閉じる。起動は `-load` と写した作業フォルダなので、自動保存は失わない。
- 同じポートで 2 台は起動できない。ポートは割り当てられた範囲の中。
- 複数の `--send` を同時に流さない（順に流す）。流してしまったときは、後の命令は順番を待つ。待ちが `--timeout` を超えると取り下げて、実行中の命令の 1 行目を理由にして失敗する。本体が FATAL ERROR・通知の窓で止まったときは、順番を待っていた命令にも、流さなかったことと理由を返す（#142）。
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
python -X utf8 tools/install_local.py <テストプレイのフォルダ> --build           # build.py で組んでから、build/pak/ と config/・text/・demo.sve を入れる
python -X utf8 tools/install_local.py <テストプレイのフォルダ>                    # 組み済みの build/pak/ を入れる
python -X utf8 tools/install_local.py <テストプレイのフォルダ> --zip <配布の zip>  # Release の zip などを直接入れる
```

- 入れ先の形: `<dest>/<本体の実行ファイル>`・`<dest>/pak256/`（この道具が入れる）・`<dest>/play.bat`（無ければ作る。`-singleuser -objects pak256/ -sound` を付けて起動する。`-sound` が無いと効果音が消音で始まる（[sound.md](sound.md)）。音楽の `-midi` は付けない。既にあれば触らず、`-objects pak256/` や `-sound` が無ければ注意を出す）。`save/`・`settings.xml` には触らない。
- `pak256/VERSION` に入れた物の版の名前を書く（手元で組んだ物は `local-<短いコミット>`、作業ツリーに変更があれば `-dirty`。zip は `zip-<zip のファイル名>`）。
- `package.py` は通さない（配布用の許諾の検査・zip への固めと展開は、ゲームで試すだけの用途に要らないため。`build.py` の後の `build/pak/` と `config/`・`text/`・`sound/`・`demo/demo.sve` を、配布の zip と同じ一覧から直接入れる）。
- 入れ替えるとき、`pak256/` の最上段の古い `*.pak`・`demo.sve`・`config/`・`text/`・`sound/`・`VERSION` は消す。`pak256/` の下位のフォルダなどほかの物は残す（pak を下位のフォルダに置かない）。入れる物が揃わない（pak が無い・zip に pak が無い）ときは、消す前に止まる。
- 入れ先に本体の実行ファイルが無い・このリポジトリの中なら止まる（間違った場所へ入れない）。
- zip は、消す前に壊れていないか・危ない名前が無いかを調べる。先頭が `pak256/` の形（`package.py` の物）でも、先頭の無い形でもよい。入れるのは最上段の `*.pak`・`demo.sve`・`config/`・`text/`・`sound/` だけ（許諾の文などは入れない）。`..`・絶対パスの名前は止める。
- 配布用の許諾の文の検査（`LICENSE.md` の例外など）は通さない。ゲームで試すだけで、配るわけではない。配るのは `package.py`。

pak を入れる処理は `game.install_pak(dest, zip_path=…, clean=…)` で、`Game` の作業フォルダ（`<作業フォルダ>/pak/`）も同じ関数で入れる。配布の zip の一覧のうち、ゲームが読む物だけを返す `package.collect_runtime` を土台にしていて、許諾の検査（`package.collect`）とは切り離してある。

## pak の中の画像を見る（`tools/pakimage.py`、#148）

組んだ pak の画像を、ゲームを起動せずに PNG に取り出す。画像の端の画素や、物どうしの違いを調べるときに使う（#141 の暗い線は、この見方で切り分けた）。Pillow が要る。

```
python -X utf8 tools/build.py                                   # 先に pak を組む（build/pak/）
python -X utf8 tools/pakimage.py list --name ami_road_local     # 物の種類・名前・画像の数・pak
python -X utf8 tools/pakimage.py tree ami_road_local            # 画像の道筋・大きさ・ずらし
python -X utf8 tools/pakimage.py export pak256_bus:4 -o work/pakimage
python -X utf8 tools/pakimage.py sheet ami_road_local:6/8 ami_road_local_base_single:6/8 \
    -o work/snow.png --scale 8 --crop 30,195,80,235             # 並べて拡大（雪の直線の下の端）
```

| 引数 | 意味 |
|---|---|
| `指定` | `名前` か `名前:道筋`。道筋は `tree` に出る子の番号を `/`（か `.`）でつなぐ。途中までならその下の全部、`*` はその段の全部（`pak256_birch:2/*/0` は全部の樹齢の最初の季節） |
| `--pak` | 読む pak のファイルかフォルダ（何回でも）。省くと `build/pak/`。Release の zip を展開した物なども読める |
| `--type` | 同じ名前の物が 2 つ以上あるときに、種類（`WAY`・`VHCL` など）で絞る。同じ種類なら `--pak` で絞る |
| `-o` | `export` は出力のフォルダ（`<名前>_<道筋>.png`）、`sheet` は出力の PNG |
| `--cell` | 画像を置くマスの大きさ（既定 256）。512 のセルに描いた物は 512。はみ出す画像があると、範囲をマスの単位で広げて知らせる |
| `--scale`・`--cols`・`--crop` | `sheet` だけ。最近傍の拡大の倍率、横に並べる数、マスの中の `x0,y0,x1,y1` |

- `export` の PNG は RGBA で、透明な画素は透明のまま。画像はマスの中の元の位置に置く（dat のずらしが効いた位置）。`sheet` の透明な所は緑で塗り、下に名前と道筋を書く（画像の無い番号は `(empty)`）。
- 色は pak の中の値で、ゲームの画面の色ではない。普通の色は 15bit（元の PNG の下位 3 ビットは落ちる）。書き出す PNG は 5 ビットの値を 0〜255 に広げる（`(v << 3) | (v >> 2)`。元の 248 は 255 になる）ので、元の PNG と値で比べるときは両方を `>> 3` してそろえる。プレーヤー色・灯りの色は dat に描く元の色で出る（ゲームではプレーヤーと昼夜で変わる）。半透明の画素は不透明度に直す。
- 読むのは pak の版 1003 まで、画像の版 2・3（makeobj 60.12 は 3）。

道筋の番号の意味（本体の `descriptor/writer/` で書く順を確かめた種類。0 始まり。下に無い種類は `tree` の大きさと枚数で見る）:

| 種類 | 道筋 | 意味 |
|---|---|---|
| `WAY` | `2`〜`4` | 夏の奥の側（`image`）の平ら・坂・斜め。平らの番号は `-,n,e,ne,s,ns,se,nse,w,nw,ew,new,sw,nsw,sew,nsew` の順（16 以降は分岐の絵）、坂は `imageup` の 3・6・9・12（続きは `imageup2`）、斜めは `ne,se,nw,sw` |
| `WAY` | `5` | カーソルとアイコン |
| `WAY` | `6`〜 | 季節（雪）の絵がある物は、`6` 雪の平ら・`7` 坂・`8` 斜め、`9`〜`11` が手前の側（`frontimage`）の夏、`12`〜`14` が手前の雪。季節の無い物は `6`〜`8` が手前の側 |
| `VHCL` | `4/<向き>` | 空の絵。向きは `s,w,sw,se,n,e,ne,nw` の順 |
| `VHCL` | `5/<向き>` か `5/<向き>/<貨物の番号>` | 積んだ絵（`freightimage`）。後者は `freightimage[番号][向き]` で書いた物 |
| `BUIL` | `<2+タイル>/<2×季節+(0 奥・1 手前)>/<高さ>/<コマ>` | タイルは向き（layout）・y・x の順に数える。奥は `backimage`、手前は `frontimage` |
| `TREE` | `2/<樹齢>/<季節>` | `image[樹齢][季節]` |
| `GRND` | `2/<坂の番号>/<コマ>` | `image[番号][コマ]` |
| `SIGN` | `2/<番号>` | `image[番号]` の順。`image[向き][状態]` で書いた物は、状態ごとに向きの順（ふつうは `n,s,e,w`、`image[ne][0]` がある物は `n,s,e,w,ne,sw,se,nw`、私有の道は `ns,ew`） |

## 保存データの互換の確かめ

版を出す前に、前の版の保存データが読めることを確かめる（例: [v0.4.0 の記録](records/2026-11-26_v040-check.md)。スクリプトはその記録のフォルダ）。保存データを読み込む側は、道路名の書き換えを止める（`--keep-save-roads`・`Game(..., rewrite_roads=False)`。遊ぶ人の読み込みと同じにする）。

1. **物の名前を先に比べる。** 前の版の Release の zip と、今の main の CI の zip を展開し、`makeobj list` で物の種類と名前の違いを出す。保存データは名前で引くので、無くなった名前・変わった名前が、確かめる対象になる。前の版の説明や記録でなく、zip の中身で判断する（AMI の pak の中の物は、pak256 の側で使っていなくても置ける。v0.3.1 の AMI の停留所がそうだった）。
2. **無くなる物を置いた保存データを作る。** 前の版の zip の中身だけで起動し（`Game(build=…, root=…)`）、いつもの運送の場面に加えて、無くなる物を置き、それを使う路線も出して、`world.save_game` で保存する。いつもの場面のスクリプトを流すだけでは、消える物を確かめたことにならない。
3. **保存データを渡す。** 検証環境には書かない。実行ファイル・DLL・`config/` などを写した環境を作業フォルダに作り、その `save/` に置いて `--env` に渡す（記録の `mkenv.py`）。
4. **今の版で読み込み、走らせる。** 本体が止まらないか、置いた升の物（建物・車庫は `mo_depot_road`・`mo_depot_rail`・木）、停留所の一覧、編成と収入を、読み込みの前後で比べる。同じ位置の画面も撮る。物が消えるときは、代わりの物を置き直して直るかを見る。
5. **ログを比べる。** `game.log` には本体の警告が出ない。起動の引数に `-log -debug 3` を足し（`game.launch_command` を包む。記録の `run2_log.py`）、作業フォルダの `simu.log` の `Warning`・`ERROR` を、同じ保存データを前の版で読んだログと比べる。
6. **運送は「運べたか」を見る。** 編成ごとに、運んだ数と収入が 0 でないことを確かめる。`get_revenue()` の今月の値は読みの時点で 0 になりやすいので、月ごとの値（`get_transported_goods()`・`get_revenue()`）の 12 か月分で見る。**版どうしの運んだ数を、1 回ずつ走らせて多い少ないと言わない。** 街の育ちで駅の範囲の建物が数軒しか無いと、同じ版でも大きく違い、偶然の差を版の違いと読む（#105 で起き、[#131](records/2026-11-26_passengers.md) で回数を増やすと再現しなかった）。0 になった編成があるときも、1 回では版のせいと決めず、前の版と一緒に走らせ直す。
   - **数を比べるときは、駅と停留所の範囲の建物をそろえた場面で何回も走らせる**（#131 のスクリプト。下のコマンド。リポジトリの直下から）。測る場面は α0.3 の `setup.nut`（道路・線路の運送 3 編成）に固定で、置き場所も決め打ちなので、手順 2 の「消える物を置いた場面」とは別に走らせる。`prep.py` が組を作り（A = 前の版の zip、B = 今の zip。C・D は街の建物の pak を入れ替えた組で、要らなければ `--conds` に書かない）、`measure.py --fixed` が走らせる。ポートは `--port` から `--jobs` の数だけ使う。10 回ずつで 20〜30 分かかる（`--jobs 4`。#131 の実績）ので、背景で流す。出力の `.jsonl` は追記するので、流し直すときは消すか別の名前にする。「そろえた」場面でも、置けた住宅の数は回ごとに違う。10 回前後では、気動車で 2〜3 割、バスで 3〜4 割程度までの違いは分からない。失敗した回は `error` の行になり、まとめは読み飛ばすので、回数が減っていないかを見る。建物を足した版では、`measure.py` の建物の表（`RES`・`COM`・`IND`・`LEVEL`）にも足す。まとめは `summary2.py`（中央値と並べ替え検定）と `stats.py`（差の区間）。`prep.py` は配布の zip の形（`pak256/` と `ami_license.txt`）を前提にする。そろえた場面は、街が駅の周りに建てる場所の違いを消すので、それを見るときは `--fixed` を付けない。

```
python -X utf8 docs/records/2026-11-26_passengers/prep.py <前の版の zip> <今の zip> <作業フォルダ>
python -X utf8 docs/records/2026-11-26_passengers/measure.py <検証環境> <作業フォルダ> <出力.jsonl> --conds A,B --reps 10 --jobs 4 --port <割り当ての先頭> --fixed
python -X utf8 docs/records/2026-11-26_passengers/summary2.py <出力.jsonl>
python -X utf8 docs/records/2026-11-26_passengers/stats.py <出力.jsonl>
```

7. **zip を取り違えない。** タグを打った後、下書きの Release の zip と、確かめた zip の中身の SHA-256 を比べる。

## 検査

`tools/test_frames.py`: 地面の印・格子の線・タイルのカーソルの枠が地面の縁の画素と一致する（[ground.md](ground.md) の「枠の線」）。`tools/test_ground.py`: コミットしてある `ClimateTexture` の模様 8 枚が、斜め格子の周期（(128,64)・(128,-64)）でずらしても同じで、透明な画素が無い（Water は菱形なので見ない）。`tools/test_town_buildings.py`: 街の建物の `backimage` の季節の添字が 4 枚（夏・秋・冬・春）で、冬だけが右の絵を指し、右の絵が左と違う。

`tools/test_title_shot.py`（ゲームは起動しない）: `title_shot.py` の作業フォルダ（保存データと `settings.xml` を写さない・他の物を消さない）、起動の引数（`-load`・`-mcp-port` を付けない）、黒い画面の撮り直し、本体の終了と `FATAL ERROR` で失敗すること、失敗しても閉じて片付けること。

`tools/test_check_demo.py`: `check_demo.py` の保存データの名前の読み方（長さつきの名前・圧縮の形）と `makeobj list` の読み方、コミットしてある `demo/demo.sve` が読めること。

`tools/test_package.py`: `package.py` の入れる物（`demo/demo.sve` が無ければ止まること）と、`build.py` が makeobj の `Warning`・`ERROR` の行で（終了コードが 0 でも）止まること。

`tools/test_game.py`（ゲームは起動しない）: `player_nr`（クライアントへの渡し・道具のスクリプトの中の番号との一致・`city_road`・`@player`・`--player-nr`）、通知の窓の印（読みの境目・先に出た印）、`settle` の途中の FATAL、前の命令の実行中に順番が来なかった送りの理由・止まったときに待っていた命令へ返す理由、`work/` が無いときに作ること・作れないときに起動せず失敗すること、気候を塗る Squirrel と番号の検査、月の早送り（速さの戻し・時間切れ・中断・既にその月）、開いたまま使う入口（`run_command`・`serve_inbox`・`send_command`。偽のゲームで往復・失敗の後の継続・`@quit`・無音の終了）、窓の番号（`Game.dialog`・表との一致）、`settle` の速さの戻し、Squirrel の文字列の改行の検査、Job Object（親を強制終了すると子が終わる。Windows だけ）、写す物と写さない物（`settings.xml`・保存データの他の物）、`simuconf.tab` への追記（両方・重ねて足さない・CRLF を保つ・`--night`）、`simuconf_extra`（両方の先頭・`--night`・行の形の検査・起動に渡ること）、借りる pak、保存データの写しの道路名の書き換え（合成の保存データ。gzip・bzip2・無圧縮、元のファイルが変わらないこと、扱えない形・一覧が無い・2 か所のとき触らないこと、止める指定）、起動の引数、ポートの範囲（既定・引数・環境変数・形の誤り）、FATAL ERROR の検知（ログの読み・起動の前の古いログを見ないこと・MCP の答えの待ちを打ち切ること・見張りの終わり方・コマンドの終了コード。偽のゲームを起動して待たずに閉じることは Windows だけ）。起動から閉じるまでは、ゲームで確かめる（PR の画面）。`tools/test_run_pak.py`（ゲームは起動しない）: `--pak` を各道具が `Game` に渡すこと（省くと `None`）、`game.py` が `--build`・`--send` との組み合わせを止めること、フォルダに `config/` がある・無いときに入る物、入れられないフォルダで作業フォルダに触る前に止まること。`vehicle_check/` に `*run.py` を足したら、この検査の一覧にも足す。`tools/test_install_local.py`: `install_local.py` と `install_pak`（入れる物・`save/`・`settings.xml` に触らない・`play.bat`・入れ替え・zip・危ない名前・失敗のとき消さない）。
