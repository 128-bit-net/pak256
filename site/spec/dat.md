# dat の共通のキー

種類をまたぐキーと書き方です。

## どの物にも書くキー

| キー | 内容 |
|---|---|
| `obj` | 物の種類。`vehicle`・`building`・`factory`・`tree`・`way` など |
| `name` | 物の名前。本体と保存データはこの名前で物を指すので、配った後は変えない |
| `copyright` | 作者の名前。pak256 に入れる物の書き方は [参加のしかた](https://github.com/128-bit-net/pak256/blob/main/CONTRIBUTING.md) |

pak256 の自前の物の `name` は、多くが `pak256_` で始まります（貨物など、本体や pak128 の名前に合わせる物を除く）。外の作者が付ける名前の決まりは**未定**です。ほかの物と重ならない名前にしてください。

## 登場と引退

| キー | 既定 |
|---|---|
| `intro_year`・`intro_month` | 1900 年 1 月（歩行者だけ、年の既定が 1） |
| `retire_year`・`retire_month` | 2999 年 1 月 |

建物・車両・道などで読まれます。pak256 の仮の物は 1900 年か 1930 年にしています。年代の決め方は**未定**です。

## 気候と季節

`climates` は、`water`・`desert`・`tropic`・`mediterran`・`temperate`・`tundra`・`rocky`・`arctic` をカンマで区切って並べます。

| 種類 | 省いたとき |
|---|---|
| 建物 | 水を除く全部（値が 4 文字以下だと無視して、この既定になる） |
| 木・地面の飾り | **どの気候も無い**扱いになるので、必ず書く（ゲームでは確かめていません） |

`seasons` は、木と地面の飾りで使います。建物は画像の添字で季節の数が決まります（[絵の共通の決まり](./drawing.md) の「冬と雪の絵」）。

## 費用と性能

`cost`・`runningcost`・`maintenance`・`level` などの値の目安は**未定**です。pak256 の今の値は仮で、[docs/](https://github.com/128-bit-net/pak256/tree/main/docs) の各文書の表にあります。

## 画像の指定

画像は、dat のあるフォルダからの相対の PNG の名前と、セルの行・列で指します。

| 書き方 | 意味 |
|---|---|
| `shop.0.1` | `shop.png` の 0 行目・1 列目のセル（どちらも 0 始まり） |
| `railcar.0.0,-128,-128` | 位置合わせ（px）。正の値は右・下、負の値は左・上にずらす |
| `-` | 画像なし |
| `> icon.0.0` | 拡大・縮小しない画像（アイコンなど） |

- PNG の幅と高さは、セルの大きさで割り切れる必要があります。
- 拡張子の `.png` は書きません。ファイル名にも `.` を入れないでください（ファイル名の最初の `.` の後ろを行・列と読みます）。
- `名前.番号`（数字が 1 つ）の形は、正方形でないシートでは、エラーになるか別のセルを指すので使わないでください。
- セルの大きさは、makeobj の `pak256` などの数字で決まり、物ごとに `cell_size` で変えられます。

## 例

20m の車両を 512 のセルに描くときの形です。性能や貨物のキーは省いています。makeobj 60.12 で警告なく組めることは確かめましたが、ゲームでは試していません（2026-11-27）。

```
obj=vehicle
name=example_railcar
copyright=あなたの名前
waytype=track
cell_size=512
length=12
emptyimage[s]=railcar.0.0,-128,-128
emptyimage[w]=railcar.0.1,-128,-128
emptyimage[sw]=railcar.0.2,-128,-128
emptyimage[se]=railcar.0.3,-128,-128
emptyimage[n]=railcar.0.4,-128,-128
emptyimage[e]=railcar.0.5,-128,-128
emptyimage[ne]=railcar.0.6,-128,-128
emptyimage[nw]=railcar.0.7,-128,-128
```

## 書き方の癖

- `#` か空白で始まる行は読み飛ばされます。
- `-` で始まる行で、1 つの物が終わります。
- キーの大文字と小文字は区別されません。

## 組み方

```
makeobj pak256 vehicle.example.pak railcar.dat
```

- `pak256` の数字がセルの既定の大きさです（`cell_size` を書いた物は、その値）。
- makeobj の `Warning` は、終了コードに出ないことがあります。出力を読んで、警告が無いことを確かめてください。
- できた pak は、配布版を入れた pak のフォルダ（`pak256/`）に写して確かめます。
