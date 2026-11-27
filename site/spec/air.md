# 飛行機・空港

飛行機と、滑走路・誘導路・空港の駅・格納庫の作り方です。船と港は [船・港](./ship.md) です。

## 何が作れるか

| 種類 | `obj` と主なキー | pak256 の今の物 |
|---|---|---|
| 飛行機 | `vehicle`、`waytype=air` | 旅客機 |
| 滑走路（離着陸する道） | `way`、`waytype=air`、`system_type=1` | 滑走路 |
| 誘導路（地上を走る道） | `way`、`waytype=air`、`system_type=0` | 誘導路 |
| 空港の駅 | `building`、`type=stop`、`waytype=air` | 空港 |
| 格納庫（飛行機の車庫） | `building`、`type=depot`、`waytype=air` | 格納庫 |

同梱の AMI には飛行機の物が無いので、pak256 の空港の物は全部 pak256 の自前です。

![空港の滑走路と誘導路、駅と格納庫の画面](/spec/air-airport.png)

![駅に停まる旅客機と、飛んでいる旅客機の画面](/spec/air-plane.png)

画面は OTRP の最新版です（2026-11-27。1 枚目は縮小、2 枚目は等倍）。絵はどれも仮です。

## 大きさと基準点

### 飛行機

飛行機は、道路と線路の車両の「手本の 2 倍」ではなく、**実物の寸法**で描きます（決定: 2026-11-25）。

- `length` は実物の長さ ÷ 1.65 を四捨五入した値で、胴は `length` × 1.65m に描きます。翼の幅と高さは実物の値のままです。
- 例: 長さ 18.9m の旅客機は `length` 11、40m の機体は `length` 24 です。
- **機首を基準点に置き、胴を後ろへ伸ばします。** 横のずれは付けず、道の中心に描きます。
- **512 のセル**に描きます（`cell_size=512` と、位置合わせ `,-128,-128`）。翼はタイルの幅（26.4m）を超えて構いません。

![pak256 の仮の旅客機の 8 方向の絵。十字は基準点（機首）](/spec/air-directions.png)

### 滑走路と誘導路の幅

pak256 の物と同じ道でつながるように、幅と中心を合わせます。

| 道 | 幅（タイルの幅を 1） | 実物の寸法 |
|---|---|---|
| 滑走路 | 0.72 | 約 19m |
| 誘導路 | 0.40 | 約 10.6m |

どちらもタイルの中央に描きます。滑走路の端（1 方向だけにつながる升）には端の印を、まっすぐ抜ける滑走路に脇からつながる枝は誘導路の幅と色で描いています（手本の値）。

### 駅と格納庫

- 駅と格納庫は 1×1 タイルで、誘導路の行き止まりに置きます。誘導路がつながる辺の中央から、幅 0.40 の舗装を引き込みます。
- 飛行機は、**機首がつながる辺から約 0.90 タイル**の所で止まります。駅のターミナルは、手前や行き止まりの端ではなく**脇の奥の辺**に置いてください。手前に置くと飛行機を隠し、行き止まりの端に置くと機首と重なります。

![上から見た滑走路・誘導路の幅と、駅の停止線とターミナルの位置](/spec/air-widths.png)

## 絵

### 向き

- **飛行機**は 8 方向の絵を描きます。キーは画面の上で進む向きです（[タイルとセル](./tile-and-cell.md) の「向きの呼び方」）。
- **道**は、つながる向きの 16 通り（`-`・`n`・`e`・`ne`・`s`・`ns`・`se`・`nse`・`w`・`nw`・`ew`・`new`・`sw`・`nsw`・`sew`・`nsew`。n 北・e 東・s 南・w 西）です。
- **駅と格納庫**は 4 通りで、誘導路がつながる側で決まります。

| 番号 | つながる側 |
|---|---|
| 0 | 南（画面の左下） |
| 1 | 東（右下） |
| 2 | 北（右上） |
| 3 | 西（左上） |

### 層と季節

- **影は描きません。** 飛んでいる間の影は、本体が機体の絵から地面に描きます。
- 飛行機の絵は 1 枚で、層はありません。
- pak256 の駅は `backimage` だけです。格納庫は、口が奥を向く向き（2・3）で屋根と壁を `frontimage` にして、飛行機の上に描きます。口が手前を向く向き（0・1）は中が見えます。
- pak256 の空港の物は、坂の絵と雪の絵を持ちません（滑走路は平らな所に置く前提）。

## dat のキー

書き方の共通の決まりは [dat の共通のキー](./dat.md) を見てください。

| キー | 内容 |
|---|---|
| `waytype` | `air` |
| `system_type` | 道。`1` が滑走路、`0` が誘導路 |
| `topspeed`・`max_weight`・`cost`・`maintenance` | 道の速さの上限・重さの上限・費用。値の目安は**未定** |
| `image[向き]` | 道の絵（上の 16 通り） |
| `icon`・`cursor` | 道具の絵と、置くときのカーソル |
| `length`・`cell_size` | 飛行機。上の「飛行機」 |
| `constraint[prev][0]`・`constraint[next][0]` | 1 機で飛ぶ飛行機は `none` |
| `emptyimage[向き]` | 飛行機の絵 |
| `freight`・`payload`・`speed`・`power`・`gear`・`weight`・`runningcost` | 飛行機の性能。値の目安は**未定** |
| `type` | 駅は `stop`、格納庫は `depot` |
| `enables_pax`・`enables_post`・`level` | 駅で扱う物と大きさ |
| `dims` | `1,1,4` |
| `backimage[向き][y][x][高さ][コマ]`・`frontimage[…]` | 駅と格納庫の絵 |

駅と格納庫に `cost` を書かないと、建設費は pak の設定の値（`cost_multiply_airterminal`・`cost_depot_air`）になります。

### 例: 旅客機

512 のセルの 8 方向を、1 枚の画像 `plane.png` の 1 行に並べた形です。性能は例の値です。

```
obj=vehicle
name=example_airliner
copyright=あなたの名前
waytype=air
engine_type=diesel
freight=Passagiere
payload=18
speed=211
power=1599
gear=50
weight=7
length=11
cell_size=512
constraint[prev][0]=none
constraint[next][0]=none
emptyimage[s]=plane.0.0,-128,-128
emptyimage[w]=plane.0.1,-128,-128
emptyimage[sw]=plane.0.2,-128,-128
emptyimage[se]=plane.0.3,-128,-128
emptyimage[n]=plane.0.4,-128,-128
emptyimage[e]=plane.0.5,-128,-128
emptyimage[ne]=plane.0.6,-128,-128
emptyimage[nw]=plane.0.7,-128,-128
```

### 例: 誘導路

画像 `taxiway.png` の 4 列 × 4 行に向きの 16 通りを並べ、4 行目に道具の絵とカーソルを置いた形です。滑走路は `system_type=1` にします。

```
obj=way
name=example_taxiway
copyright=あなたの名前
waytype=air
system_type=0
cost=30000
maintenance=500
topspeed=30
max_weight=20
intro_year=1900
image[-]=taxiway.0.0
image[n]=taxiway.0.1
image[e]=taxiway.0.2
image[ne]=taxiway.0.3
image[s]=taxiway.1.0
image[ns]=taxiway.1.1
image[se]=taxiway.1.2
image[nse]=taxiway.1.3
image[w]=taxiway.2.0
image[nw]=taxiway.2.1
image[ew]=taxiway.2.2
image[new]=taxiway.2.3
image[sw]=taxiway.3.0
image[nsw]=taxiway.3.1
image[sew]=taxiway.3.2
image[nsew]=taxiway.3.3
icon=> taxiway.4.0
cursor=taxiway.4.1
```

### 例: 格納庫

画像 `hangar.png` の 4 列が向き、0 行目が奥の絵、1 行目が手前の絵、2 行目の 0 列が道具の絵の形です。駅は `type=stop` にして、`enables_pax=1` などを書きます。

```
obj=building
name=example_hangar
copyright=あなたの名前
type=depot
waytype=air
intro_year=1900
noinfo=1
dims=1,1,4
icon=> hangar.2.0
backimage[0][0][0][0][0]=hangar.0.0
backimage[1][0][0][0][0]=hangar.0.1
backimage[2][0][0][0][0]=hangar.0.2
backimage[3][0][0][0][0]=hangar.0.3
frontimage[2][0][0][0][0]=hangar.1.2
frontimage[3][0][0][0][0]=hangar.1.3
```

## 本体の動きの注意

- **離着陸は滑走路**でします。滑走路の端が要ります。誘導路は、滑走路の端でない升につなぎます。
- **駅と格納庫は誘導路の升**に置きます。滑走路の上には置けません。
- 駅は並べると 1 つの停留所になります。拾う範囲は pak256 では 2 タイルなので、街の建物の近くに置いてください。
- 着陸の前に、飛行機は滑走路の手前を大回りします。
- **飛行の高さ**は最高速で決まります。`speed` ÷ 33 段（5 段より低くは 5 段、30 段が上限）で、1 段は 32px です。211km/h の旅客機は 6 段（192px）です。pak や地図の設定で `allow_higher_flight` を無効にすると、速さによらず 3 段です。
- 確かめた並びは次の図のとおりです。東西の滑走路 19 升、3 升南の平行な誘導路、両端の近くの 2 本の短い誘導路、誘導路から南へ出た行き止まりに駅（並べた 3 つで 1 つの停留所）と格納庫です。

![確かめた空港の並び](/spec/air-layout.png)

## この pak の値の例

費用・性能・定員などは仮の値で、参考です（合わせる必要はありません）。

- [滑走路・誘導路・駅・格納庫・旅客機](https://github.com/128-bit-net/pak256/blob/main/docs/airport.md#%E7%89%A9)

## 確かめていないこと

- 本家の Simutrans、右側通行の地図、雪の気候。
- 上の dat の例をゲームで動かすこと。
- 地図の端の近くの空港（着陸できないおそれがあります）。
- 複数の飛行機が同時に使う空港と、滑走路の順番待ち。
- 郵便や貨物を運ぶ飛行機、前後に機体をつなぐ飛行機。
- `allow_higher_flight` を無効にした地図の高さ。
