# リポジトリの形

物の置き場と、表から dat、dat から pak を作る形。2026-11-25 にユーザーが決めた（[#1](https://github.com/128-bit-net/pak256/issues/1)。案と理由は issue のコメント）。決めたことの背景は [concept.md](concept.md)、道筋は [roadmap.md](roadmap.md)。

## フォルダ

```
objects/<種類>/<物>/   物。表・描く元・描いた PNG を一緒に置く
config/               設定ファイル（simuconf.tab など。#3）
text/                 物の名前の訳と街の名前（#10）
vendor/ami/           同梱する AMI の版の指定と許諾の文（下の「AMI の 256 版を同梱する」）
tools/                道具（下の「道具」）
docs/                 文書
build/                作った dat・pak（git に入れない）
```

許諾は拡張子で決まる（[LICENSE.md](../LICENSE.md)）。`objects/` の絵・dat・表・`.blend` は CC BY-SA 4.0、`objects/` の中でも描く・書き出すスクリプト（`.py` など）は MIT。

### 物の種類

| フォルダ | 中身 | issue |
|---|---|---|
| `objects/ground/` | 地面・水・坂・海岸・基礎・柵・印・境界・地図の外 | #5 |
| `objects/gui/` | 記号・カーソル・ツールバーのアイコン | #6 |
| `objects/goods/` | 貨物（`Passagiere`・`Post`・`None` を含む） | #4 |
| `objects/city/` | 役場・住宅・商業・工業の建物・記念物・本社 | #8 |
| `objects/industry/` | 産業（工場・発電所） | |
| `objects/vehicle/<rail\|road\|…>/` | 車両。乗り物の種類で 1 段下に分ける | |
| `objects/scenery/` | 木・岩などの景観の物 | #9 |

- 物のフォルダ 1 つが、[CREDITS.md](../CREDITS.md) の「物（フォルダ）」の 1 行に当たる。作者が違う物は、別のフォルダにする。
- 種類が足りなくなったら、`objects/` の下に足し、この表に書く。
- 道路・線路・駅などのインフラは置かない（AMI に任せる。[roadmap.md](roadmap.md) の「進め方」）。

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
  name: pak256_sample
  copyright: pak256.LongScale チーム
  image:              # image[0][0]=sample_marker.0.0 になる
    0: {0: sample_marker.0.0}
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
| `package.py` | `build/` の pak と `config/`・`text/`・許諾の文を配布の zip にまとめる（下の「配布の zip と CI」） |
| `ci/setup_makeobj.sh` | CI の Linux に makeobj を用意する |
| `fetch_ami.py` | AMI の 256 版の pak を取る（下の「AMI の 256 版を同梱する」）。`build.py` が使う |
| `test_datgen.py` | `datgen.py` の検査。`python -X utf8 -m unittest discover -s tools -p "test_*.py"` |
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
pak256/CREDITS.md
pak256/ami_license.txt  AMI の pak を入れたときだけ
```

CI は `.github/workflows/ci.yml`。

- PR と main への push: 表の検査（`test_datgen.py`）→ `tools/build.py`（pak を組む）→ `tools/package.py`。zip は artifact `pak256-zip` に置く。
- makeobj は警告（`Warning`）でも終了コード 0 なので、`build.py` がログの `Warning`・`ERROR` の行で失敗にする。CI も同じ。
- makeobj は本家（`simutrans/simutrans`）のリリースの Linux 版（`ci.env` の `MAKEOBJ_TAG`）。道具の版は `ci.env` に置き、workflow に直に書かない。
- `v*` のタグを打つと、同じ zip を添えた Release を **下書き** で作る。説明は手で書いて公開する。タグに `-` を含むもの（`v0.0.0-test` など）はプレリリースにする。
- AMI は `vendor/ami/ami.env` が空の間は入らない。埋めれば次の組みから同梱される。

## AMI の 256 版を同梱する

AMI（`128na/simutrans-addon-dev` の `addons/ami`）は、pak256 の git に入れない。版を固定して取ってくる。

- `vendor/ami/ami.env` に AMI の版・Release の zip の URL・その SHA-256 を書く。`tools/fetch_ami.py`（`tools/build.py` から呼ぶ）が zip を取り、SHA-256 を確かめて、中の pak を `build/pak/` に置く。取った zip は `build/cache/` に残す（SHA-256 が合わなければ消して止まる）。
- AMI が 256 版を Release に上げるまでは、`ami.env` を空のままにし、手元で組んだ AMI の pak のフォルダか zip を環境変数 `AMI_DIST` で渡す。
- どちらの取り方でも、pak を 1 つも取れなければ止まる。どちらも指定が無いときは、AMI 抜きで組む。
- AMI の pak を入れたときは、AMI の許諾の文 `vendor/ami/ami_license.txt`（AMI の `addons/ami/release/license.txt` の写し）を `build/ami_license.txt` に写す。AMI の zip に許諾の文が入っているかに頼らない（256 版の zip は pak だけの予定）。無ければ止まる。AMI の許諾の文が変わったら写し直す。
- 帰属の書き方（AMI を初めて同梱するとき。#7）:
  - [CREDITS.md](../CREDITS.md) に 1 行: 物 `AMI（vendor/ami）`、作者 128na、連絡先 `128na/simutrans-addon-dev`、許諾 CC BY 4.0。
  - [LICENSE.md](../LICENSE.md) に例外を書く: 同梱する AMI の pak と絵は CC BY 4.0（CC BY-SA ではない）。今の「配布物（`.pak`）にも同じ許諾が及びます」の例外にする。
  - 配布の zip に、`build/ami_license.txt` を `ami_license.txt` の名前で入れる（`tools/package.py`）。

## 見本の物

`objects/scenery/sample_marker/` は、この形で dat → pak が通ることを見せる仮の物（木、名前 `pak256_sample`）。絵は `draw.py` が描く。#9 で木が入ったら消す。
