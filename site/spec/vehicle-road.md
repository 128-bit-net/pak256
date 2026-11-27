# 道路の車両

バス・トラックなど、プレーヤーが持つ道路の車両の作り方です。大きさと `length` は、先に [車両の大きさ](./vehicle-size.md) を読んでください。街の中を勝手に走る車は [街の車](./citycar.md) です。

## 何が作れるか

`obj=vehicle` で `waytype=road` の物です。

| 運ぶ物 | pak256 の今の物 |
|---|---|
| 旅客（`Passagiere`） | バス |
| 郵便（`Post`） | 郵便のトラック |
| 貨物 | 石炭のトラック |

道路と車庫は、pak256 に同梱の AMI（CC BY 4.0、作者 128na）の 256 版を使います。この説明は 2026-11-27 の AMI `ami-256-alpha.9` に合わせています。

## 大きさと基準点

長さ・幅・高さは「pak128 の同じ種類の車両の 2 倍」で、`length` は画面の長さから決めます（[車両の大きさ](./vehicle-size.md)）。今の物の目標は、同じページの表にあります。どれも 1 タイルに収まるので、256 のセルで描きます。

![バス停に停まるバスと、街の建物を並べた画面](/spec/road-vehicles.png)

![道路を走る郵便のトラック（赤）と街の車（緑）、路肩の歩行者の画面](/spec/road-trucks.png)

画面は OTRP の最新版、等倍です（2026-11-27）。絵はどれも仮です。道路は同梱の AMI（CC BY 4.0、作者 128na）です。

### 車線の位置

**絵は右側の車線に描きます。** 車体の前の端の中央を、基準点から次の分だけずらした点に置き、車体はそこから進む向きの後ろへ伸ばします。車輪の下端は路面の高さです。

| キー | 進む向き（画面） | 基準点からのずれ（px） | 256 のセルでの点 |
|---|---|---|---|
| `s` | 左下 | (-24, -12) | (104, 180) |
| `w` | 左上 | (24, -12) | (152, 180) |
| `sw` | 左 | (0, -12) | (128, 180) |
| `se` | 下 | (-24, 0) | (104, 192) |
| `n` | 右上 | (24, 12) | (152, 204) |
| `e` | 右下 | (-24, 12) | (104, 204) |
| `ne` | 右 | (0, 12) | (128, 204) |
| `nw` | 上 | (24, 0) | (152, 192) |

ずれは x が右、y が下を正にしています。道路の中心からの距離は、軸の向きで 3/16 タイル（約 4.95m）です。

![東へ進むバスの右側の車線の点と、左側通行で本体がずらした位置を示す図](/spec/road-lane.png)

- 左側通行の地図では、本体が絵をまとめて (±48, ±24) などずらし、道路の中心から同じ距離の反対側に出します。**左側通行用の絵は描きません。**
- ずれの量は本体の決まりです。OTRP では `simuconf.tab` の `driveleft_base_offset_<向き>` で変えられますが、pak256 は書いていません。書いて変えると、上の表の位置とは合わなくなります。

## 絵

- **8 方向**の絵を描きます。キーは画面の上で進む向きです（[タイルとセル](./tile-and-cell.md) の「向きの呼び方」）。本体は `s`・`w`・`sw`・`se` の 4 方向だけでも読み、残りの向きは `n`←`s`、`e`←`w`、`ne`←`sw`、`nw`←`se` の絵を使います。前の端を基準点に置く描き方では、この代わりの絵は位置が合わないはずなので、8 方向すべてを描いてください。
- 車両の絵は 1 枚で、手前と奥に分ける層はありません。
- pak256 の車両は冬の絵を持ちません（雪の気候でも同じ絵です）。
- 積み荷の絵は `freightimage` で足せます。pak256 では石炭のトラックだけが持ちます。

![pak256 の仮のバスと石炭のトラックの 8 方向の絵。十字は基準点](/spec/road-directions.png)

## dat のキー

書き方の共通の決まりは [dat の共通のキー](./dat.md) を見てください。車両で使うキー:

| キー | 内容 |
|---|---|
| `waytype` | `road` |
| `engine_type` | `diesel`（省いたとき）・`electric`・`steam` など。電化は下の「本体の動きの注意」 |
| `length` | 省くと 8。[車両の大きさ](./vehicle-size.md) の「長さ」 |
| `emptyimage[向き]`・`freightimage[向き]` | 絵 |
| `freight`・`payload` | 運ぶ貨物の名前と量 |
| `speed`・`power`・`gear`・`weight`・`cost`・`runningcost` | 性能と費用。値の目安は**未定** |
| `intro_year`・`retire_year` | 登場と引退 |
| `constraint[prev][N]`・`constraint[next][N]` | 連結できる車両。書き方は [線路の車両](./vehicle-rail.md) の「dat のキー」と同じ |
| `smoke`・`sound` | 煙と発車の音（物があるとき） |

### 例: バス

8 方向を 1 枚の画像 `bus.png` の 1 行に並べた形です。性能は例の値です。

```
obj=vehicle
name=example_bus
copyright=あなたの名前
waytype=road
freight=Passagiere
payload=70
speed=60
power=205
gear=80
weight=11
length=9
emptyimage[s]=bus.0.0
emptyimage[w]=bus.0.1
emptyimage[sw]=bus.0.2
emptyimage[se]=bus.0.3
emptyimage[n]=bus.0.4
emptyimage[e]=bus.0.5
emptyimage[ne]=bus.0.6
emptyimage[nw]=bus.0.7
```

### 例: 積み荷の絵のあるトラック

画像の 0 行目が空、1 行目が積んだ絵です。

```
obj=vehicle
name=example_coal_truck
copyright=あなたの名前
waytype=road
freight=Kohle
payload=12
speed=55
power=95
weight=8
length=8
emptyimage[s]=truck.0.0
emptyimage[w]=truck.0.1
emptyimage[sw]=truck.0.2
emptyimage[se]=truck.0.3
emptyimage[n]=truck.0.4
emptyimage[e]=truck.0.5
emptyimage[ne]=truck.0.6
emptyimage[nw]=truck.0.7
freightimage[s]=truck.1.0
freightimage[w]=truck.1.1
freightimage[sw]=truck.1.2
freightimage[se]=truck.1.3
freightimage[n]=truck.1.4
freightimage[e]=truck.1.5
freightimage[ne]=truck.1.6
freightimage[nw]=truck.1.7
```

## 本体の動きの注意

- **左側通行のずれが足されるのは、道路の車両（と街の車）だけ**です。線路の車両や船は中心に出ます。
- **停留所**: 旅客・郵便の車両と貨物の車両は、その貨物を扱う停留所で積み降ろします。pak256 では、旅客と郵便がバス停、貨物が荷役所です。
- **電化**: 動力のある車両がすべて `engine_type=electric` の編成は、電化した道路だけを走ります。pak256 と同梱の AMI には、道路の架線がありません。
- **曲がり**: 車体は 1 枚の絵で、角のタイルでは進む向きの斜めに描かれます。郵便と石炭のトラック（`length` 6 と 8）は舗装の中を走り、向かい合う 2 台のすれ違いでも重なりません。雪の気候の西北の角では、石炭のトラックを 2 両つなぐと、後ろの車両が白線の外に掛かる瞬間があります。
- **坂**: 車体は水平のまま走ります。
- **車線との見え方**: AMI の生活道路の車線の中心より、絵の位置はわずかに外側です（直線で画面の約 3px）。

## この pak の値の例

費用・性能・定員などは仮の値で、参考です（合わせる必要はありません）。

- [バス・郵便のトラック・石炭のトラック](https://github.com/128-bit-net/pak256/blob/main/docs/vehicles.md#%E9%81%93%E8%B7%AF%E3%81%AE%E8%BB%8A%E4%B8%A1)
- 停留所は [駅・停留所](./station.md)

## 確かめていないこと

- 本家の Simutrans、右側通行の地図。
- 上の dat の例をゲームで動かすこと。
- 4 方向だけの絵の車両の見え方。
- 電気の車両（トロリーバス）と、`constraint` で連結する連節バス・トレーラーの見え方。pak256 には物がありません。
- 追い越しの途中の車線の位置。
