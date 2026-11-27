# 線路の車両

列車・路面電車・モノレールの作り方です。大きさと描く位置は、先に [車両の大きさ](./vehicle-size.md) を読んでください。

## 何が作れるか

| 種類 | `waytype` | pak256 の今の物 |
|---|---|---|
| 列車（気動車・電車・客車・貨車） | `track` | 気動車とその付随車 |
| 路面電車 | `tram_track` | 路面電車 1 種 |
| モノレール（跨座式） | `monorail_track` | モノレール 1 種 |
| リニア・狭軌 | `maglev_track`・`narrowgauge_track` | 車両は無い。大きさの目標は**未定** |

軌道は、pak256 に同梱の AMI（CC BY 4.0、作者 128na）の 256 版を使います。道路や線路は pak256 の物ではないので、幅や高さは AMI の版で変わります。この説明は 2026-11-27 の時点で pak256 に同梱している AMI に合わせています。

## 大きさと基準点

[車両の大きさ](./vehicle-size.md) の決まりのとおりです。たとえば 20m の車両は `length=12` で 512 のセル、12m は `length=7`、15m は `length=9` で、どちらも 256 のセルに収まります。今の物の寸法と値は、下の「この pak の値の例」の表にあります。

![線路の駅に停まる 20m の車両 2 両と、街の建物と木を並べた画面](/spec/scale-rail.png)

## 絵

### 向き

車両は **8 方向**の絵を描きます。キーは画面の上で進む向きです（[タイルとセル](./tile-and-cell.md) の「向きの呼び方」）。

![8 方向の絵のキー。pak256 の仮の気動車。十字は基準点で、車体は基準点から後ろへ伸びる](/spec/vehicle-directions.png)

- 本体は `s`・`w`・`sw`・`se` の 4 方向だけでも読み、北側の向きは `n`←`s`、`e`←`w`、`ne`←`sw`、`nw`←`se` の絵で代えます。
- ただし「前の端を基準点に置く」描き方で 4 方向だけにすると、代えた向きでは車体が基準点より前に出るはずです。**8 方向をすべて描いてください。**
- pak256 の今の車両は前後が同じ形なので、終点で折り返しても形は崩れません。

### 層と季節

- 車両の絵は 1 枚で、手前と奥に分ける層はありません。
- pak256 の車両は冬の絵を持ちません（雪の気候でも同じ絵です）。
- 積み荷の絵は `freightimage`（`freightimage[s]` など）で足せます。空の絵は `emptyimage` です。

### 路面電車の集電装置

屋根の上の集電装置は、架線のトロリ線に届く高さに描きます。同梱している AMI の路面軌道の架線は（2026-11-27 の時点で）、地面から **約 48px**（256px のタイル）です。これは AMI の版に依る値で、版が変わると合わなくなるかもしれません。

## dat のキー

書き方の共通の決まりは [dat の共通のキー](./dat.md) を見てください。車両で使うキー:

| キー | 内容 |
|---|---|
| `waytype` | 上の表 |
| `engine_type` | `diesel`（省いたとき）・`electric`・`steam` など。電化の扱いは下の「本体の動きの注意」 |
| `length` | 省くと 8。[車両の大きさ](./vehicle-size.md) の「長さ」 |
| `cell_size` | 512 のセルのときに書く |
| `emptyimage[向き]`・`freightimage[向き]` | 絵。512 のセルは位置合わせ `,-128,-128` |
| `freight`・`payload` | 運ぶ貨物の名前と量（`Passagiere` は旅客） |
| `speed`・`power`・`gear`・`weight`・`cost`・`runningcost` | 性能と費用。値の目安は**未定** |
| `intro_year`・`retire_year` | 登場と引退 |
| `constraint[prev][N]`・`constraint[next][N]` | 前・後ろにつなげる車両の名前。`none` は「車両が無い」（先頭・末尾になれる） |
| `smoke`・`sound` | 煙と発車の音（物があるとき） |

添字 `N` は 0 から続けて書きます（makeobj は、抜けた番号の所で読むのをやめます）。`constraint[prev]` を 1 つも書かなければ、どの車両の後ろにもつながり、先頭にもなれます。何か書くと、書いた物だけになります。先頭にさせるには `none` も並べます（`next` も同じ）。

### 例: 気動車と付随車

512 のセルの 8 方向を、1 枚の画像 `railcar.png` の 1 行に並べた形です。付随車は気動車か付随車の後ろだけにつながります。性能は例の値です。

```
obj=vehicle
name=example_railcar
copyright=あなたの名前
waytype=track
engine_type=diesel
freight=Passagiere
payload=80
speed=90
power=220
weight=21
length=12
cell_size=512
emptyimage[s]=railcar.0.0,-128,-128
emptyimage[w]=railcar.0.1,-128,-128
emptyimage[sw]=railcar.0.2,-128,-128
emptyimage[se]=railcar.0.3,-128,-128
emptyimage[n]=railcar.0.4,-128,-128
emptyimage[e]=railcar.0.5,-128,-128
emptyimage[ne]=railcar.0.6,-128,-128
emptyimage[nw]=railcar.0.7,-128,-128
-
obj=vehicle
name=example_trailer
copyright=あなたの名前
waytype=track
freight=Passagiere
payload=80
speed=90
weight=17
length=12
cell_size=512
constraint[prev][0]=example_railcar
constraint[prev][1]=example_trailer
emptyimage[s]=trailer.0.0,-128,-128
emptyimage[w]=trailer.0.1,-128,-128
emptyimage[sw]=trailer.0.2,-128,-128
emptyimage[se]=trailer.0.3,-128,-128
emptyimage[n]=trailer.0.4,-128,-128
emptyimage[e]=trailer.0.5,-128,-128
emptyimage[ne]=trailer.0.6,-128,-128
emptyimage[nw]=trailer.0.7,-128,-128
```

### 例: 路面電車

256 のセルに収まるので `cell_size` と位置合わせは要りません。`constraint` は、単独か路面電車どうしの連結だけにする書き方です。

```
obj=vehicle
name=example_tram
copyright=あなたの名前
waytype=tram_track
engine_type=electric
freight=Passagiere
payload=72
speed=50
power=113
weight=18
length=7
constraint[prev][0]=none
constraint[prev][1]=example_tram
constraint[next][0]=none
constraint[next][1]=example_tram
emptyimage[s]=tramcar.0.0
emptyimage[w]=tramcar.0.1
emptyimage[sw]=tramcar.0.2
emptyimage[se]=tramcar.0.3
emptyimage[n]=tramcar.0.4
emptyimage[e]=tramcar.0.5
emptyimage[ne]=tramcar.0.6
emptyimage[nw]=tramcar.0.7
```

## 本体の動きの注意

- **線路の車両は、左側通行でも線路の中心**に出ます。本体は左側通行のずれを道路の車両にしか足しません。
- **路面電車は線路の車両として扱われます。** `waytype=tram_track` で、道路に敷いた軌道でも道路の中央を走ります。
- **電化**: 動力のある車両がすべて `engine_type=electric` の編成は、電化した軌道だけを走ります。`electric` とそれ以外の動力車が混じる編成は、電化していない軌道も走れます。
- **路面電車の架線**: pak256 の路面電車は `electric` なので、AMI の `ami_tram_catenary` を張った軌道だけを走ります。架線は線路のツールバーの架線に並び、撤去も線路の架線の撤去です。架線が無いと、スクリプトで作った編成は車庫から出ませんでした（車庫の窓で買えるかは見ていません）。
- **連結の間隔**は、前の車両の `length` です。2 両目以降は前の車両の `length` だけ後ろに並びます。
- **曲がり**: 車体は 1 枚の絵で、角のタイルでは進む向きの斜めに描かれます。`length=12` の車両は 90° の曲がりで角の外へはみ出して見え、連結の継ぎ目も折れません。**受け入れる決まり**です（決定: 2026-11-25）。`length=7` の路面電車は、道路の舗装の中に収まります。
- **坂**: 車体は水平のまま走り、坂の変わり目で継ぎ目に段差や隙間が出て、車体がレールから外れて見える瞬間があります。1 タイルで 2 段の坂がいちばん大きく崩れます。路面電車の 1 段の坂（東西の向き）では、目立つ沈みや浮きはありません。
- **駅**: 20m の車両 2 両は 24 単位（1.5 タイル）です。駅は 2〜3 タイル並べて置きます。

![曲がりの角を通る気動車と付随車](/spec/rail-curve.png)

![道路の軌道を走る路面電車](/spec/rail-tram.png)

![跨座式の桁を走るモノレール](/spec/rail-monorail.png)

画面は OTRP の最新版、等倍です（2026-11-27）。絵はどれも仮です。軌道は同梱の AMI（CC BY 4.0、作者 128na）です。

## この pak の値の例

費用・性能・定員などは仮の値で、参考です（合わせる必要はありません）。

- [気動車と付随車](https://github.com/128-bit-net/pak256/blob/main/docs/vehicles.md#%E7%B7%9A%E8%B7%AF%E3%81%AE%E8%BB%8A%E4%B8%A1)
- [路面電車](https://github.com/128-bit-net/pak256/blob/main/docs/vehicles.md#%E8%B7%AF%E9%9D%A2%E9%9B%BB%E8%BB%8A)
- [モノレール](https://github.com/128-bit-net/pak256/blob/main/docs/vehicles.md#%E3%83%A2%E3%83%8E%E3%83%AC%E3%83%BC%E3%83%AB%E3%81%AE%E8%BB%8A%E4%B8%A1)
- 駅は [駅・停留所](./station.md)、信号は [信号](./signal.md)

## 確かめていないこと

- 本家の Simutrans、右側通行。
- 上の dat の例をゲームで動かすこと。
- 4 方向だけの絵の車両の見え方と、前後で形が違う車両が終点で折り返した見え方。
- 画面で縦向きの斜めと、分岐のタイルで斜めになる瞬間の見え方（直線・90° の曲がり・横向きの斜め・分岐・1 段と 2 段の坂は、主に列車で撮りました。[記録](https://github.com/128-bit-net/pak256/blob/main/docs/records/2026-11-27_standards-8-2.md)）。
- 逆向き運転（OTRP の機能）。前の端を基準点に置く描き方では、`simuconf.tab` に `reverse_base_offset_<向き>` が要る見込みです。
- リニア・狭軌の車両と、AMI の懸垂式のモノレール（絵は跨座式用の形なので、合わないはずです）。
- ツールバーのボタンを押して架線を置く・撤去する操作（置いたのと撤去したのはスクリプト）と、車庫の窓で架線の無い車庫の電車が買えるか。
