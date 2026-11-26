# リポジトリの形

物の置き場と、表から dat、dat から pak を作る形。2026-11-25 にユーザーが決めた（[#1](https://github.com/128-bit-net/pak256/issues/1)。案と理由は issue のコメント）。決めたことの背景は [concept.md](concept.md)、道筋は [roadmap.md](roadmap.md)。

## フォルダ

```
objects/<種類>/<物>/   物。表・描く元・描いた PNG を一緒に置く
config/               設定ファイル（simuconf.tab など。#3）
text/                 物の名前の訳と街の名前（#10）
vendor/ami/           同梱する AMI の版の指定・組む元と許諾の文（下の「AMI の 256 版を同梱する」）
tools/                道具（下の「道具」）
docs/                 文書
build/                作った dat・pak（git に入れない）
dist/                 作った配布の zip（git に入れない）
ci.env                CI の道具の版（makeobj など）
.github/workflows/    CI
```

許諾は拡張子で決まる（[LICENSE.md](../LICENSE.md)）。`objects/` の絵・dat・表・`.blend` は CC BY-SA 4.0、`objects/` の中でも描く・書き出すスクリプト（`.py` など）は MIT。

### 物の種類

| フォルダ | 中身 | issue |
|---|---|---|
| `objects/ground/` | 地面・水・坂・海岸・基礎・柵・印・境界・地図の外。描き方は [ground.md](ground.md)。`Outside/` だけは別のフォルダ（本体が `ground.Outside.pak` を先に探すため） | #5 |
| `objects/gui/` | 記号・カーソル・ツールバーのアイコン | #6 |
| `objects/goods/` | 貨物（`Passagiere`・`Post`・`None` を含む）。[goods.md](goods.md) | #4 |
| `objects/city/` | 役場・住宅・商業・工業の建物・記念物・本社 | #8 |
| `objects/industry/` | 産業（炭鉱・発電所など）。[industry.md](industry.md) | #43 |
| `objects/vehicle/<rail\|road\|…>/` | 車両。乗り物の種類で 1 段下に分ける。長さと描画位置は [standards.md](standards.md)（確かめは [vehicles.md](vehicles.md)） | #40 |
| `objects/scenery/` | 木・岩などの景観の物 | #9 |
| `objects/station/` | 道路の停留所（`road_stops/`）と線路の駅（`rail_stops/`）。どちらも pak256 の物（AMI は駅を作らず、停留所は #94 で自前に戻した）。[stations.md](stations.md) | #44・#46・#73・#94 |
| `objects/signal/` | 線路の信号（閉塞信号 1 種）。[signals.md](signals.md) | #73 |

- 物のフォルダ 1 つが、[CREDITS.md](../CREDITS.md) の「物（フォルダ）」の 1 行に当たる。作者が違う物は、別のフォルダにする。
- 種類が足りなくなったら、`objects/` の下に足し、この表に書く。
- 道路・線路・駅などのインフラは置かない（AMI に任せる。[roadmap.md](roadmap.md) の「進め方」）。例外は、道路の停留所・線路の駅（`objects/station/`。#44・#46・#73・#94）と線路の信号（`objects/signal/`。#73）。pak256 の物として持つ（2026-11-26、ユーザー。[stations.md](stations.md)・[signals.md](signals.md)）。道路の車庫は #64 で AMI の物に置き換えた。

## 物のフォルダの中身

| ファイル | 中身 | git |
|---|---|---|
| `<物>.yaml` | 表。dat の元（下の「表から dat を作る」） | 入れる |
| `<物>.dat` | 手で書いた dat。表にしても得の無い物（地面・GUI など）に使う | 入れる |
| `<物>.png` | 描いた絵 | 入れる |
| 描く元 | `.blend`、Blender で形を作る Python のスクリプト、レイヤーのある元の絵、絵や dat を規則で書き出すスクリプトなど | 入れる |

- 1 つのフォルダに、表と手書きの dat を混ぜてよい。ただし同じ名前（`a.yaml` と `a.dat`）は置かない。
- 地面の坂の組み合わせのように規則で並ぶ物は、dat か表を書き出すスクリプトを物のフォルダに置き、書き出した物もコミットする。組むとき（`tools/build.py`）にはスクリプトを走らせない。

## 表から dat を作る

表は YAML。1 ファイルに物を 1 つ（マッピング）か、いくつか（マッピングの並び）書く。`tools/datgen.py` が dat にする。

- キーは dat のキーそのまま。値の入れ子は dat の添字になる。

  ```yaml
  obj: tree
  name: pak256_zelkova
  copyright: pak256.LongScale チーム
  image:              # image[0][0]=zelkova.0.0 になる
    0: {0: zelkova.0.0}
  freight: [a, b]     # freight[0]=a、freight[1]=b になる
  ```

- `obj`・`name`・`copyright` は必ず書く（無いと止まる）。`copyright` の書き方は [CONTRIBUTING.md](../CONTRIBUTING.md) の「クレジットの書き方」。
- YAML は `yes`・`no`・`on`・`off` を真偽に読む。文字として渡すときは引用符で囲む。真偽は dat では `1`・`0` になる。キーが真偽になったときは止まる。
- 数も YAML の決まりで読み替わる（`0123` は 8 進数で `83`、`0x10` は `16`、`1_0` は `10`）。書いたとおりに渡したいときは引用符で囲む。
- 空の値・空の並び・同じキーの 2 度書きは止まる。
- 作った dat は `build/dat/` に置き、git に入れない。
- 値の釣り合い（費用・速さ）を一覧で比べたくなったら、表から CSV の一覧を書き出す道具を足す（今は無い）。

## 絵

- 描いた PNG は git に入れる。CI では描かない（CI は Python と makeobj だけで pak を作る。AMI も同じ）。PR で絵の差分が見える。
- 256 のシートは pak128 の 4 倍の画素なので、リポジトリが太る。大きくなりすぎたら Git LFS を考える（今は入れない）。
- 描く元は物のフォルダに置く。物をまたいで使う描画の道具は `tools/blender/` に置く（MIT。まだ無い）。
- PNG は物のフォルダの下のフォルダ（`img/` など）に置いてもよい。dat からは `img/a.0.0` のように引く。表と dat は物のフォルダの直下に置く。
- 描いた PNG と元がずれていないかの検査は、まだ無い。

### セルの大きさ

makeobj の `pak256`・`pak512` などの数字は、PNG を何 px のマスで切るか（セル）だけを決める。タイルの大きさは、地面 `Outside` の絵の幅で本体が決める（OTRP の fork の `descriptor/ground_desc.cc` の `register_desc`）。

- 2026-11-25 の試し: 256px のタイルの菱形を、(a) 256 のセルに描いて `pak256`、(b) 512 のセルの中ほどに描いて `pak512`（位置合わせ `-128,-128`）、(c) (b) の絵を `pak256` で組み dat に `cell_size=512`、の 3 通りで組むと、pak は全バイト同じになった（makeobj 60.12）。
- 自前の物は 256 のセル（1 タイル）に描く。`tools/build.py` は `pak256` で組む。
- タイルからはみ出す物（大きな建物・長い車両など）は、大きいセルに描き、表に `cell_size`（例 `512`）と位置合わせを書く。makeobj は `cell_size` を物ごとに読む。
- AMI は 2 タイル分のセル（512）に描き、AMI の側で `pak512` で組む。

## 道具

`tools/` の道具は MIT。Python 3 で動く。使うライブラリは `tools/requirements.txt` に版を固定する（`pip install -r tools/requirements.txt`）。

| ファイル | すること |
|---|---|
| `build.py` | 物を dat にして pak に組む（下の「組み方」） |
| `datgen.py` | 表（YAML）から dat を作る。`build.py` が使う。1 ファイルだけ試すときは `python -X utf8 tools/datgen.py <表>` |
| `install_local.py` | 組んだ pak か配布の zip を、テストプレイのフォルダの `pak256/` に入れる（[game-check.md](game-check.md)） |
| `package.py` | `build/` の pak と `config/`・`text/`・許諾の文を配布の zip にまとめる（下の「配布の zip と CI」） |
| `ci/setup_makeobj.sh` | CI の Linux に makeobj を用意する |
| `fetch_ami.py` | AMI の 256 版の pak を取る（下の「AMI の 256 版を同梱する」）。`build.py` が使う |
| `test_datgen.py` | `datgen.py` の検査。`python -X utf8 -m unittest discover -s tools -p "test_*.py"` |
| `test_cityrules.py` | `cityrules.tab` の街の規則が、狙った盤面で当てはまる・当てはまらないことの検査（[buildings.md](buildings.md)） |
| `test_trees.py` | 木の絵の高さ・幅が [trees.md](trees.md) の表の ±5% に収まり、特別な色が混じらないこと、表（.yaml）の気候・季節、各気候の木と `simuconf.tab` の食い違いの検査（Pillow・PyYAML が要る） |
| `tree_check.py` | 木を各気候・各季節でゲームに撮る道具（[trees.md](trees.md)。`game.py` の上）。気候の区画を作って林を置き、月を進めて夏・秋・冬・春を撮り、`--montage` で PR に付ける画像を並べる |
| `test_stations.py` | 停留所・駅の表の検査: `type: stop`・`waytype`（`road_stops/` は `road`、`rail_stops/` は `track`）・向き 8 通りの絵が PNG にあること、`stations.md` の表に全部載っていること、道路の停留所の絵が画面で道路の白線の内側に掛からないこと（#115）（Pillow が要る） |
| `test_ground.py` | コミットしてある気候の地面の模様（`texture-climate.png`）が、斜め格子の周期で隣のタイルとつながり、透明な画素が無いことの検査（[ground.md](ground.md)。Pillow が要る） |
| `test_frames.py` | 地面の印（`Marker`）・格子の線（`Borders`）・タイルのカーソルの枠が、地面の絵の縁と画素単位で一致し、両端の高さが同じ辺が横 2px・縦 1px の階段であることの検査（[ground.md](ground.md) の「枠の線」。Pillow が要る） |
| `test_town_buildings.py` | 街の建物の季節の絵の添字（4 枚: 夏・秋・冬・春。冬だけが右の絵）の検査（[buildings.md](buildings.md)。Pillow・PyYAML が要る） |
| `docs-policy.json` | 文書の検査 docs-lint の設定（[../CONTRIBUTING.md](../CONTRIBUTING.md) の「文書の検査」） |
| `test_signals.py` | 線路の信号の表の検査: `obj: roadsign`・`waytype: track`・`is_signal`・状態 2 × 向き 4 の絵が PNG にあること、道具の絵とカーソル、`menuconf.tab` の信号の撤去（`general_tool[46]`）、`signals.md` の表（Pillow が要る） |
| `test_industry.py` | 産業の表の検査: 発電所の名前が `kraftwerk` / `Power Plant` で終わること（本体がそれで発電所と見なす）、絵の名前と PNG の大きさが `dims` と合うこと（[industry.md](industry.md)。Pillow が要る） |
| `check_way_edges.py` | AMI の 256 版の道（`obj=way`）の絵の縁が、横 4px・縦 2px の階段になっていないかの検査（256 の段は横 2px・縦 1px。#111）。`build_ami256.py` の `check` の段が流す。単独なら `python -X utf8 tools/check_way_edges.py <AMI の src256>` |
| `test_check_way_edges.py` | `check_way_edges.py` の検査（描いた菱形で確かめる。Pillow が要る） |
| `build_ami256.py` | AMI の 256 版の zip を、AMI の clone の一時の worktree で組み、置き場に上げる（下の「AMI の 256 版を組む」）。組む道具ではなく、AMI の版を上げるときに手で流す |
| `test_build_ami256.py` | `build_ami256.py` の検査: 描く順の分け方・子の環境から外す変数・アイコンの段の失敗（終了コード 0 の `Traceback`）・途中から続けるときの止め・描き直し（段の順）・AMI のコミットからの変更の拾い方・`ami.env` の書き換え・比べ方・上げる前の止め（試し・別のコミット・飛ばした段・道具の版の抜け・AMI の道具や dat の変更・変わった zip・既にあるタグ）。AMI・Blender・gh は使わない |
| `test_fetch_ami.py` | `ami.env` の値の形と、`fetch_ami.py` の SHA-256 の照合・展開の検査（取得は差し替える。外のネットには出ない） |
| `vehicles.py` | 車両の長さと描画位置の決まり（[standards.md](standards.md) の 4 章）の計算。車両を描くスクリプトと検査が使う |
| `test_vehicles.py` | 車両の決まりの計算と、見本のバス・バス・郵便のトラックの表の `length`・絵の位置（±2px）・特別な色・訳の検査（Pillow が要る） 。`TestRailVehicles` は線路の車両（#46）で、20m・512 のセル・位置合わせ・車線のずれ無しの位置|
| `game.py` | ゲームの起動と後片付け（作業フォルダの写し・pak の導入・昼夜を止める・MCP・PID で閉じる）。[game-check.md](game-check.md) |
| `test_game.py` | `game.py` の検査（ゲームは起動しない） |
| `vehicle_check/` | 車両を道路で走らせて向きごとに撮る試験（`course.nut`・`run.py`。[vehicles.md](vehicles.md) の「試験」。信号の周回は `signal.nut`（#73）、道路の停留所でバスと石炭のトラックを走らせる確かめは `road_stop_bus.nut`・`road_stop_coal.nut`（#94））と、線路で列車を往復させて撮る試験（`rail.nut`・`rail_run.py`。#46）。組む道具ではない |
| `poc_upscale_pak128.py` | pak128 を 2 倍にする試し（concept の 4 章）。組む道具ではない |

物をまたいで使う描画の道具は `tools/blender/` に置く（まだ無い）。

## 組み方

```
pip install -r tools/requirements.txt
python -X utf8 tools/build.py
```

- 物のフォルダごとに、`build/dat/<種類>/<物>/` へ PNG と dat を写し、`build/pak/<種類>.<物>.pak` を組む。
- makeobj が警告（`Warning`）か誤り（`ERROR`）を出したら止まる。綴りの違うキーも makeobj の警告で分かる。
- makeobj は `PATH` にあるものを使う。別の場所のときは環境変数 `MAKEOBJ` で渡す。
- 配布の形と CI は下の「配布の zip と CI」。

## 配布の zip と CI

`tools/package.py <版の名前>` が `dist/pak256-<版の名前>.zip` を作る（`dist/` は git に入れない）。先頭のフォルダは `pak256/` で、本体の pak のフォルダにそのまま置ける。

```
pak256/*.pak            build/pak/ の pak（自前の物と AMI）
pak256/config/          config/ の中身
pak256/text/            text/ の中身
pak256/LICENSE.md
pak256/LICENSES/        許諾の本文
pak256/CREDITS.md
pak256/ami_license.txt  AMI の pak を入れたときだけ
```

CI は `.github/workflows/ci.yml`。文書の検査（docs-lint）は別の `.github/workflows/docs-lint.yml`（全部の PR と main への push。版は `ci.env`）。

- PR と main への push: `tools/test_*.py` の検査（`test_datgen.py` など）→ `tools/build.py`（pak を組む）→ `tools/package.py`。zip は artifact `pak256-zip` に置く。
- makeobj は警告（`Warning`）でも終了コード 0 なので、`build.py` がログの `Warning`・`ERROR` の行で失敗にする。CI も同じ。
- CI の makeobj は本家 125.0 の Linux 版（60.10）で、手元の Windows 版（60.12）と版が違う。Release の pak は 60.10 で組まれる。
- makeobj は本家（`simutrans/simutrans`）のリリースの Linux 版（`ci.env` の `MAKEOBJ_TAG`）。道具の版は `ci.env` に置き、workflow に直に書かない。
- `v*` のタグを打つと、同じ zip を添えた Release を **下書き** で作る。説明は手で書いて公開する。タグに `-` を含むもの（`v0.0.0-test` など）はプレリリースにする。
- AMI は `vendor/ami/ami.env` で固定した版（今は `ami-256-alpha.5`）が同梱される。`ami.env` を空にすると入らない。AMI の pak を入れるには、`LICENSE.md` の例外と `CREDITS.md` の行（#7 で済み）が要る。`package.py` は、許諾の文が無ければ止まる。

## AMI の 256 版を同梱する

AMI（`128na/simutrans-addon-dev` の `addons/ami`）は、pak256 の git に入れない。版を固定して取ってくる。

- `vendor/ami/ami.env` に AMI の版・zip の置き場の URL・その SHA-256 を書く。`tools/fetch_ami.py`（`tools/build.py` から呼ぶ）が zip を取り、SHA-256 を確かめて、中の pak を `build/pak/` に置く。GitHub の Release の URL は `gh release download` で取る（それ以外の URL は urllib）。取った zip は `build/cache/` に残す（SHA-256 が合わなければ消して止まる）。
- 版は `ami.env` で固定してある（`ami-256-alpha.5`。路面・歩道の粒を 256 で細かくした直し（#81。AMI #288）を含む。256 版の zip で、`ami_road.pak`・`ami_rail.pak` など 7 つの pak が入る。`ami-256-alpha.1` は `ami_road.pak` だけだった）。AMI の版を上げるときは、`ami.env` の 3 つ（版・URL・SHA-256）と、組んだ元の `AMI_COMMIT` を書き換える（下の `upload` が書く）。手元で組んだ AMI の pak を試すときは、フォルダか zip を環境変数 `AMI_DIST` で渡す（`ami.env` より優先する）。
- **zip の置き場**（2026-11-25、ユーザーの決定）: 256 版は AMI（`128na/simutrans-addon-dev`）の Release に出さない（256 はローカルのみ）。pak256 の非公開の Release（タグ `vendor-<AMI の版>`、プレリリース・latest にしない。配布物ではない）に zip を 1 つ置き、`ami.env` の URL がそこを指す。取るのは `gh`（CI は workflow の `GH_TOKEN` に `github.token`、手元は `gh auth login`）。AMI の版を上げるときは、下の「AMI の 256 版を組む」の手順で zip を組んで上げ、`ami.env` を書き換える。
- どちらの取り方でも、pak を 1 つも取れなければ止まる。どちらも指定が無いときは、AMI 抜きで組む。
- AMI の pak を入れたときは、AMI の許諾の文 `vendor/ami/ami_license.txt`（AMI の `addons/ami/release/license.txt` の写し）を `build/ami_license.txt` に写す。AMI の zip に許諾の文が入っているかに頼らない（256 版の zip は pak だけ）。無ければ止まる。AMI の許諾の文が変わったら写し直す。
- 帰属の書き方（#7 で `ami-256-alpha.1` を同梱したときに入れた。AMI の版を変えても同じ）:
  - [CREDITS.md](../CREDITS.md) に 1 行: 物 `AMI（vendor/ami）`、作者 128na、連絡先 `128na/simutrans-addon-dev`、許諾 CC BY 4.0。
  - [LICENSE.md](../LICENSE.md) に例外を書く: 同梱する AMI の pak と絵は CC BY 4.0（CC BY-SA ではない）。今の「配布物（`.pak`）にも同じ許諾が及びます」の例外にする。
  - 配布の zip に、`build/ami_license.txt` を `ami_license.txt` の名前で入れる（`tools/package.py`）。

### AMI の 256 版を組む

AMI は 128 用で、256 は AMI の範囲外（2026-11-25、ユーザー。[roadmap.md](roadmap.md) の「進め方」）。256 版の zip は pak256 の側で組む（#83。alpha.3 までは AMI の進捗管理が手元で組んでいた）。組むのは `tools/build_ami256.py`。AMI の描く道具の 256 の倍率（`SHEET_PAK_SIZE=256`。AMI の `addons/ami/README.md` の「pak の大きさ」）をそのまま使う。

- **どの版から組むか**: `vendor/ami/build.env` の `AMI_COMMIT`（AMI のコミットの SHA）。AMI の新しい直しを取り込むときは、ここを書き換える PR を先に入れる。`--ref` で一度だけ別のコミットから組めるが、その zip は置き場に上げられない（`upload` が止まる）。
- **どこで動かすか**: AMI の手元の clone（`--ami-repo`・環境変数 `AMI_REPO`。既定は pak256 の本体の checkout の隣の `simutrans-addon-dev`）に、組む間だけ detached の worktree を `build/ami256/<SHA の頭 12 桁>/` に足し、終わったら消す。AMI のリポジトリにはコミット・push をせず、共有の checkout のブランチも切り替えない（`git fetch origin` と worktree の出し入れだけ）。
- **AMI の側との分担**（2026-11-25、pak256 と AMI の進捗管理で決めた）:
  - 大きさを選ぶ道具（`SHEET_PAK_SIZE`・`sheet_settings.SCALE`・256 の検査）は AMI のリポジトリに残る。AMI が守るのは、道具を壊さないことまで（AMI の今の CI の範囲）。道具の使い方を変えるときは、AMI から知らせが来る。
  - AMI の issue は、256 で組めることを受け入れ条件にしない。AMI の側では、256 の描き直しと `CHECK_256_FULL` をしない。AMI からは 256 の zip を出さない（alpha.2・alpha.3・alpha.5 は pak256 の置き場の Release にだけある）。
  - 256 の組み立て（このツール）と、ゲームでの見た目の確かめは pak256 が受け持つ。
  - 256 だけのために AMI の道具を直す必要が出たとき（#81 など）は、`--only` の試しで直し方を確かめ、128 の出力が変わらないことを確かめてから、進捗管理に知らせる。AMI の側で起票して直し、その後に `AMI_COMMIT` を上げる。pak256 の側に AMI の道具の直しを持たない。
- **組む段**（`build`。止まったら worktree を残すので、原因を直して `--resume --from <段>` で続ける。済んだ段は worktree の隣の `.steps.json` に控え、前の段が済んでいない `--from` は止める）:
  1. `dat`: `blender/ami_dat.py` で `src256/` の dat を書く。コミット済みの dat と（行末を除いて）違えば知らせる（AMI の書き忘れ。組む pak はこの dat で作る）。
  2. `render`: `render_parallel.py` で `catalog.SCALED_TARGETS`（8801a1e で 215 対象。`SCALED_SHEETS` の 252 名から、基盤の版と一緒に描かれる壁と絵を持たない dat を除いた物）を描く。先に描いた物の絵を読む物（踏切のシート 8 枚・跨座式のトンネル）は 2 回目にまとめて描く。描いた対象が自分のアイコンを書くときに、まだ描いていないほかのシート（twin の壁の front など）を読んで落ちることがある（シートは描けている）ので、失敗した対象は全部を描いた後に、同じ段の順で 1 回だけ描き直し、それでも落ちたら止まる（#83 の試しで 2 対象が落ちた）。描き直した対象はマニフェストの `retried` に書く（1 回目のログは上書きされる）。描画の枠はほかの作業者と分け合う（AMI の `render_slots.py`）。全部で 15〜25 分ほど。
  3. `icons`: `blender/icons.py` を全部のシートに流す（`render.py` は描いたシートの分しか書かない）。Blender は例外でも終了コード 0 なので、ログ（`work/icons.log`）の `Traceback` でも止める。
  4. `check`: AMI の 256 の検査（`check_scaled`・`check_icons`・`check_cells`・`check_crossing`・`check_depot`・`check_embankment`。`check_cells.py --self-test`、`dat_lint_extra.py`（`--self-test` と `src256`）、`dat_linter lint --tile-size 512`（`src256`）。AMI の `check.sh` の `CHECK_256_FULL=1` の 256 の分。ほかに pak256 の `check_way_edges.py` で道の縁の段を見る。`dat_linter` は環境変数 `DAT_LINTER_BIN`・`PATH`・`check.sh` の既定の置き場（`~/.cache/simutrans-addon-dev/ci-tools/dat_linter/`。AMI の clone で `check.sh` を一度流すと入る）の順に探し、無ければ描く前に止まる）。
  5. `build`: `build.py`（`dist256/` に pak。makeobj の警告で止まる。makeobj は `PATH` のもの）。
  6. `release`: `release.py --version <版> --paks <7 つ>`。7 つ（`ami_rail`・`ami_road`・`ami_tram`・`ami_extra`・`ami_monorail`・`ami_canal`・`ami_scenery`）がそろわなければ止まる。
  
  組んだ zip は `dist/ami-256-<版>.zip`、組んだ元（AMI のコミット・済んだ段・描き直した対象・AMI のコミットからの変更（描き直した `src256/` の絵とその控えを除く。手で直した道具や、`ami_dat.py` の出力とコミット済みの dat の違いを含む）・Blender と makeobj の版・zip の SHA-256・pak の大きさ）は `dist/ami-256-<版>.json` に置く。子の環境から `BUILD_SKIP_MISSING`・`CHECK_SKIP_MISSING`・`SHEET_LAYOUT`・`SHEET_ONLY` などを外す（残っていると、絵の無い物を黙って飛ばす）。
- **試し**: `--only <対象 ...>`（例 `ami_road_local`。約 2 分）は、その対象だけを描いて、絵のある物だけを組む（`BUILD_SKIP_MISSING=1`。アイコンの全体の段は飛ばす）。道具の確かめや、AMI の道具の直し方を早く見るのに使う（手元の AMI の worktree で直した物は、`--keep` と `--resume --from render` で描き直す）。置き場には上げられない。
- **比べる**: `compare <zip A> <zip B>` が、pak の名前・数・大きさと、物（`makeobj list` の種類と名前）の違いを出す。名前と数が違うと終了コード 1。前の版（`build/cache/` や `gh release download` で取った zip）と比べて、PR に書く。
- **置き場に上げる**: `upload --version <版>`（先に `--dry-run` で確かめる）。`build.env` の `AMI_COMMIT` から組んだ、試しでない zip で、全部の段を通して組み、道具の版が記録され、AMI のコミットから道具・dat が変わっておらず、組んだ後に zip が変わっていないときだけ、Release `vendor-ami-256-<版>`（プレリリース・latest にしない）を作って zip を置き、`vendor/ami/ami.env` の `AMI_VERSION`・`AMI_ZIP_URL`・`AMI_ZIP_SHA256` と `AMI_COMMIT`（組んだ元。`fetch_ami.py` は読まない）を書き換える。同じタグの Release が既にあれば止まる（上書きしない。版の名前を変える）。上げた後、`ami.env` の変更を PR にする。

```
python -X utf8 tools/build_ami256.py build --version alpha.4
python -X utf8 tools/build_ami256.py compare dist/ami-256-alpha.4.zip build/cache/ami-256-alpha.3.zip
python -X utf8 tools/build_ami256.py upload --version alpha.4 --dry-run
python -X utf8 tools/build_ami256.py upload --version alpha.4
```

要るもの: AMI の clone、Blender（`SHEET_BLENDER` か `--blender`。既定 `D:\bin\blender\blender.exe`）、makeobj（`PATH`）、Python と numpy・Pillow（AMI の検査）、`gh`（上げるとき）。pak の物の作りは AMI の版で決まるので、組んだ zip はゲームで道路・線路・車庫などを置いて確かめてから上げる（[game-check.md](game-check.md)）。

## 物の名前の訳と街の名前

`text/` に置く。本体が pak のフォルダの `text/` から読む（`dataobj/translator.cc`）。

- `ja.tab`・`en.tab`: 物の名前（dat の `name`）と訳の行が交互に並ぶ。本体が引く貨物の分類名（`CATEGORY_01`〜`07`）も入れる（貨物の窓に出る）。画面に出ない貨物 `None` は訳を置かない（`tools/test_text.py` の `UNTRANSLATED`）。先頭の `§` は UTF-8 の印。注釈は先頭の `#` の行にだけ書く（名前の位置の `#` 行だけが注釈で、訳の位置の `#` 行は訳として読まれる）。物を足した PR で、名前を足す。`tools/test_text.py` が、行の数・名前の抜け・ja と en のずれを検査する。
- `citylist_ja.txt`・`citylist_en.txt`: 街の名前。1 行に 1 つ。本体は、新しい街ごとに一覧から名前を選ぶ。一覧が空の言語では、本体の既定の音節の組み合わせで名前を作る。一覧を使い切ると、街の名前が全部同じ既定の名前になるので、地図の大きさに合わせて数を足す（今は 104）。利用者が自分の一覧を置くと、本体はそちらを先に読む。
- 名前が画面に出るのは、木のように選んで置く物。地面・GUI の物は画面に名前が出ないので、今は訳さない。
- AMI の物の名前は AMI の側（`ja_ami.tab` など）で持つ。ここには書かない。
- 訳語は、既存の訳にある名前を先に探して合わせる。ただし pak128 の訳の文・並びは写さない。一般名詞・地名のように誰が付けても同じになる語は、同じでよい。

## 見本の物

表から dat → pak が通る形の見本は、木 `objects/scenery/trees/`（[trees.md](trees.md)）。絵は `draw_trees.py` が描き、表も書き出す。
