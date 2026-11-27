# 川

地図の地形の一部になる川の作り方です。運河はこのページでは扱いません（pak256 は同梱の AMI の運河を使います）。船は [船・港](./ship.md) です。

## 何が作れるか

`obj=way`・`waytype=water`・`system_type=255` の道が川です。

- 川は地図を作るときに本体が引きます。プレイヤーが敷く道ではないので、pak256 はツールバーとアイコンを作っていません。
- 本体が引くのは、pak の `simuconf.tab` の `river_type[0]`〜`river_type[9]` に**太い順**に名前を並べた川だけです。pak256 は 3 段です。
- 自分の川のアドオンを地図に出すには、この設定に名前が要ります。アドオンの側から足す方法は確かめていません。

![太さの違う川が合流している画面](/spec/river-screen.png)

画面は OTRP の最新版、等倍です（2026-11-27）。絵はどれも仮です。

## 大きさと基準点

川は 1 タイル分の地面の絵で、256 のセルに描きます（基準点は (128, 192)。[タイルとセル](./tile-and-cell.md)）。pak256 の今の物の幅（手本の値）です。

| 順 | 川 | 水面の幅（タイルの幅を 1） | 実物の寸法 | 速さの上限 |
|---|---|---|---|---|
| 0 | 大きな川 | 0.68 | 約 18m | 30km/h |
| 1 | 川 | 0.54 | 約 14m | 20km/h |
| 2 | 小川 | 0.40 | 約 11m | 10km/h |

![3 段の川の絵と水面の幅](/spec/river-widths.png)

- 水面の両側に、土の岸をタイルの 0.045 ずつ描いています。
- 隣のタイルと幅がそろうように、岸の凸凹はタイルの辺では 0 にしています。
- 曲がりは、タイルの角を中心にした半径 0.5 タイルの円弧です。
- pak256 の船の幅 7〜8m は、タイルの 0.27〜0.30 にあたります。

## 絵

- **向き**: つながる向きの 16 通り（`-`・`n`・`e`・`ne`・`s`・`ns`・`se`・`nse`・`w`・`nw`・`ew`・`new`・`sw`・`nsw`・`sew`・`nsew`）。
- **坂**: 1 段の坂は `imageup`、2 段の坂は `imageup2` の 4 方向（3 北・6 西・9 東・12 南の坂）です。坂は流れの向きに沿った白い筋を描いています（手本の値）。
- **季節と雪**: 画像のキーの 2 つめの添字が `0` で普段、`1` で雪の絵です。pak256 は雪の絵では岸を雪にしています。
- 層はありません。

## dat のキー

書き方の共通の決まりは [dat の共通のキー](./dat.md) を見てください。

| キー | 内容 |
|---|---|
| `waytype`・`system_type` | `water`・`255` |
| `topspeed` | **0 より大きくすると船が通れます** |
| `cost`・`maintenance` | pak256 は 0 |
| `max_weight`・`intro_year` | pak256 は 999 と 1 |
| `draw_as_ding` | pak256 は `1` |
| `image[向き][雪]`・`imageup[坂][雪]`・`imageup2[坂][雪]` | 上の「絵」 |

### 例: 川

画像 `river.png` が 8 列で、0・1 行目に向きの 16 通り、2 行目に坂（左の 4 列が 1 段、右の 4 列が 2 段）、3〜5 行目に同じ並びの雪の絵を置いた形です。

```
obj=way
name=example_river
copyright=あなたの名前
waytype=water
system_type=255
cost=0
maintenance=0
topspeed=10
max_weight=999
intro_year=1
draw_as_ding=1
image[-][0]=river.0.0
image[n][0]=river.0.1
image[e][0]=river.0.2
image[ne][0]=river.0.3
image[s][0]=river.0.4
image[ns][0]=river.0.5
image[se][0]=river.0.6
image[nse][0]=river.0.7
image[w][0]=river.1.0
image[nw][0]=river.1.1
image[ew][0]=river.1.2
image[new][0]=river.1.3
image[sw][0]=river.1.4
image[nsw][0]=river.1.5
image[sew][0]=river.1.6
image[nsew][0]=river.1.7
image[-][1]=river.3.0
image[n][1]=river.3.1
image[e][1]=river.3.2
image[ne][1]=river.3.3
image[s][1]=river.3.4
image[ns][1]=river.3.5
image[se][1]=river.3.6
image[nse][1]=river.3.7
image[w][1]=river.4.0
image[nw][1]=river.4.1
image[ew][1]=river.4.2
image[new][1]=river.4.3
image[sw][1]=river.4.4
image[nsw][1]=river.4.5
image[sew][1]=river.4.6
image[nsew][1]=river.4.7
imageup[3][0]=river.2.0
imageup[6][0]=river.2.1
imageup[9][0]=river.2.2
imageup[12][0]=river.2.3
imageup[3][1]=river.5.0
imageup[6][1]=river.5.1
imageup[9][1]=river.5.2
imageup[12][1]=river.5.3
imageup2[3][0]=river.2.4
imageup2[6][0]=river.2.5
imageup2[9][0]=river.2.6
imageup2[12][0]=river.2.7
imageup2[3][1]=river.5.4
imageup2[6][1]=river.5.5
imageup2[9][1]=river.5.6
imageup2[12][1]=river.5.7
```

## 本体の動きの注意

- **太さ**: 新しい川はいちばん下の順（いちばん細い川）で引かれ、合流するたびに下流の升が 1 段太くなります。合流の無い川は小川のままです。
- **船**: 速さの上限が 0 より大きい川だけを通れます。合流の無い川でも船が通れるように、pak256 は小川にも 10km/h を付けています。
- **川を引いた直後は、船が海から川へ入れないことがあります。** 保存して読み直すと通れるようになりました（地図の拡大で川を引いて確かめた動きです）。pak の側では直せません。
- **海が無い地図**には、川ができません。川の数と長さは新しい地図の窓の設定で、pak では `river_min_length`（pak256 は 8）を指定できます。
- `river_type[]` に並べた名前は、全部 pak にある川にしてください。無い名前があると、本体が落ちるおそれがあります。
- 太さの違う升の境では、岸に段が出ます（本体は隣の太さを見ないので、絵では合わせられません）。
- 運河の船着き場は運河の幅に合わせた絵なので、小川では板が水から離れて草の上に出ます。
- 川の水は、海のようには動きません。

## この pak の値の例

- [川の 3 段](https://github.com/128-bit-net/pak256/blob/main/docs/config.md#%E5%B7%9D)

## 確かめていないこと

- 本家の Simutrans、右側通行の地図。
- 上の dat の例をゲームで動かすこと。
- 新しい地図を作る窓で引いた川（拡大で確かめました）。
- 川をまたぐ道路・線路の橋と、川の脇の産業の置き場所。
- アドオンの側から `river_type` に足す方法。
- 冬の季節の見え方（雪の絵は北極の気候で見ました）。
