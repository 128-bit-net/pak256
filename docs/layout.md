# リポジトリの形

物の置き場と、表から dat、dat から pak を作る形。2026-11-25 にユーザーが決めた（[#1](https://github.com/128-bit-net/pak256/issues/1)。案と理由は issue のコメント）。決めたことの背景は [concept.md](concept.md)、道筋は [roadmap.md](roadmap.md)。

## フォルダ

```
objects/<種類>/<物>/   物（素材。CC BY-SA 4.0）。表・描く元・描いた PNG を一緒に置く
config/               設定ファイル（simuconf.tab など。#3）
text/                 物の名前の訳と街の名前（#10）
vendor/ami/           同梱する AMI の版の指定（下の「AMI の 256 版を同梱する」）
tools/                道具（MIT）
docs/                 文書
build/                作った dat・pak（git に入れない）
```

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
- YAML は `yes`・`no`・`on`・`off` を真偽に読む。文字として渡すときは引用符で囲む。真偽は dat では `1`・`0` になる。
- 作った dat は `build/dat/` に置き、git に入れない。
- 値の釣り合い（費用・速さ）を一覧で比べたくなったら、表から CSV の一覧を書き出す道具を足す（今は無い）。

## 絵

- 描いた PNG は git に入れる。CI では描かない（CI は Python と makeobj だけで pak を作る。AMI も同じ）。PR で絵の差分が見える。
- 256 のシートは pak128 の 4 倍の画素なので、リポジトリが太る。大きくなりすぎたら Git LFS を考える（今は入れない）。
- 描く元は物のフォルダに置く。物をまたいで使う描画の道具は `tools/blender/` に置く（MIT。まだ無い）。
- 描いた PNG と元がずれていないかの検査は、まだ無い。

### セルの大きさ

makeobj の `pak256`・`pak512` などの数字は、PNG を何 px のマスで切るか（セル）だけを決める。タイルの大きさは、地面 `Outside` の絵の幅で本体が決める（OTRP の fork の `descriptor/ground_desc.cc` の `register_desc`）。

- 2026-11-25 の試し: 256px のタイルの菱形を、(a) 256 のセルに描いて `pak256`、(b) 512 のセルの中ほどに描いて `pak512`（位置合わせ `-128,-128`）、(c) (b) の絵を `pak256` で組み dat に `cell_size=512`、の 3 通りで組むと、pak は全バイト同じになった（makeobj 60.12）。
- 自前の物は 256 のセル（1 タイル）に描く。`tools/build.py` は `pak256` で組む。
- タイルからはみ出す物（大きな建物・長い車両など）は、大きいセルに描き、表に `cell_size`（例 `512`）と位置合わせを書く。makeobj は `cell_size` を物ごとに読む。
- AMI は 2 タイル分のセル（512）に描き、AMI の側で `pak512` で組む。

## 組み方

```
pip install -r tools/requirements.txt
python -X utf8 tools/build.py
```

- 物のフォルダごとに、`build/dat/<種類>/<物>/` へ PNG と dat を写し、`build/pak/<種類>.<物>.pak` を組む。
- makeobj が警告（`Warning`）か誤り（`ERROR`）を出したら止まる。綴りの違うキーも makeobj の警告で分かる。
- makeobj は `PATH` にあるものを使う。別の場所のときは環境変数 `MAKEOBJ` で渡す。
- 配布の形（pak のまとめ方、`config/`・`text/` と合わせたフォルダ、zip）は CI と一緒に決める（#2）。

## AMI の 256 版を同梱する

AMI（`128na/simutrans-addon-dev` の `addons/ami`）は、pak256 の git に入れない。版を固定して取ってくる。

- `vendor/ami/ami.env` に AMI の版・Release の zip の URL・その SHA-256 を書く。`tools/fetch_ami.py`（`tools/build.py` から呼ぶ）が zip を取り、SHA-256 を確かめて、中の pak を `build/pak/` に、許諾の文 `ami_license.txt` を `build/` に置く。取った zip は `build/cache/` に残す。
- AMI が 256 版を Release に上げるまでは、`ami.env` を空のままにし、手元で組んだ AMI の pak のフォルダか zip を環境変数 `AMI_DIST` で渡す。
- どちらも無いときは、AMI 抜きで組む。
- 帰属の書き方（AMI を初めて同梱するとき。#7）:
  - [CREDITS.md](../CREDITS.md) に 1 行: 物 `AMI（vendor/ami）`、作者 128na、連絡先 `128na/simutrans-addon-dev`、許諾 CC BY 4.0。
  - [LICENSE.md](../LICENSE.md) に例外を書く: 同梱する AMI の pak と絵は CC BY 4.0（CC BY-SA ではない）。今の「配布物（`.pak`）にも同じ許諾が及びます」の例外にする。
  - 配布の zip に、AMI の `ami_license.txt` を同じ名前で入れる。

## 見本の物

`objects/scenery/sample_marker/` は、この形で dat → pak が通ることを見せる仮の物（木、名前 `pak256_sample`）。絵は `draw.py` が描く。#9 で木が入ったら消す。
