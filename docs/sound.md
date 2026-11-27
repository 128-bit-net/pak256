# 音

車両と産業の効果音の付け方（[#175](https://github.com/128-bit-net/pak256/issues/175)）。音はどれも `tools/make_sounds.py` で合成した自作の物で、録音や他人の素材は使っていない（[../CREDITS.md](../CREDITS.md)）。

## 置き場と形

- `sound/` に WAV と `sound.tab` を置く。配布の zip の `pak256/sound/` に入り、本体が pak のフォルダの `sound/` から読む（`descriptor/sound_desc.cc`）。
- WAV は PCM 16bit・モノラル・22050Hz で、チャンクは `fmt `（16 バイト）と `data` だけにする。本体の Windows 版（`sound/win32_sound_xa.cc`）の読み方が簡単なため。`test_sounds.py` が形を検査する。
- ファイル名は `pak256_` で始め、英字の小文字と `_` にする。同じ名前の音は先に読んだ物が使われるので、アドオンと重ならない名前にする。数字で始まる名前は、makeobj が昔の音の番号と読む。

## dat のキー

| 物 | キー | 値 |
|---|---|---|
| 車両（`obj: vehicle`） | `sound` | `sound/` の WAV のファイル名 |
| 産業（`obj: factory`） | `sound` | 同上 |
| 産業 | `sound_interval` | 次に鳴るまで空ける時間（ミリ秒）。必ず書く（省くと本体の既定値の足し算があふれて、間隔が効かない。`simfab.cc`） |

pak を組むときに WAV は要らない（名前だけを持ち、ゲームが読み込むときに `sound/` を見る）。名前の誤りは makeobj の警告に出ないので、`test_sounds.py` が検査する。

## 鳴る条件（本体の動き）

- 車両: 停留所から発車するとき、編成の先頭の車両の音が鳴る（`simconvoi.cc`）。付随車には付けない。
- 産業: 生産したとき、`sound_interval` より間が空いていれば鳴る（`simfab.cc` の `smoke()`）。材料が無くて生産していない産業は鳴らない。
- どちらも、マウスのカーソルがある場所に近いほど大きく、縦と横のタイル数の和が 16 を超える遠さでは鳴らない（`karte_t::play_sound_area_clipped`）。車両の音は早送りの間は鳴らない。
- 本体は、起動の引数に `-sound` が無いと消音で始まる（`simmain.cc`）。鳴らすには `-sound` を付けて起動するか、音の設定の窓で消音を外す。`-mute` を付けると音を読み込まない。`tools/install_local.py` が作る `play.bat` は `-sound` を付ける。
- GDI 版の再生は `sound/win32_sound_xa.cc`（XAudio2）。

## 今の音

| ファイル | 使う物 | 中身 |
|---|---|---|
| `pak256_bus.wav` | `pak256_bus`・`pak256_sample_bus` | 空気ブレーキを抜く音とディーゼルの発車 |
| `pak256_truck.wav` | `pak256_mail_truck`・`pak256_coal_truck` | 低いディーゼルの発車 |
| `pak256_railcar.wav` | `pak256_railcar` | 短い汽笛と機関の音 |
| `pak256_tram.wav` | `pak256_tram` | 鐘を 2 回 |
| `pak256_monorail.wav` | `pak256_monorail` | 上がっていくモーターの唸り |
| `pak256_ship.wav` | `pak256_ferry`・`pak256_cargo_ship` | 低い汽笛 |
| `pak256_airplane.wav` | `pak256_airliner` | プロペラの回転が上がる音 |
| `pak256_coal_mine.wav` | `pak256_coal_mine` | 巻上げ機の唸りと炭車の金物の音 |
| `pak256_power_plant.wav` | `pak256_coal_kraftwerk` | タービンの唸りと蒸気 |

## 音を直す・足す

1. `tools/make_sounds.py` の音の関数を直すか足し、`python -X utf8 tools/make_sounds.py` で `sound/` を書き直す。乱数の種は固定なので、直していない音は変わらない（計算機が違うと、末尾の桁の丸めで数バイト違うことはある）。
2. 車両・産業の表は、その物を描くスクリプト（`draw_*.py`）の `sound` を直して流し直す。
3. `python -X utf8 -m unittest discover -s tools -p "test_*.py"` を流す。
4. ゲームで読めたかは、`-debug 3 -log` を付けて起動し、ログの `Successfully loaded sound` と `not found` を見る。起動の道具は `Game(sound="load", extra_args=("-log", "-debug", "3"))`（[game-check.md](game-check.md)）。耳で確かめるときは `--sound on`。

## 耳で確かめる

運び方と産業ごとの場面を 1 つ作って、閉じるまで待つ道具がある。pak を組んだ後（`python -X utf8 tools/build.py`）に流す。

```
python -X utf8 tools/vehicle_check/sound_run.py --env <検証環境> --port 47920 --scene bus
```

場面は `bus`・`coal`・`plant`・`rail`・`tram`・`monorail`・`air`・`ship`。停留所や産業の上にマウスのカーソルを置いて聞き、Enter で閉じる（端末で流す）。`plant` の発電所の音は、石炭が届いてから鳴る。
`--check` を付けると、鳴らさずに画面の中央の近くの停留所からの発車だけを読んで閉じる。

## sound.tab

`sound.tab` は、昔の番号で引く音と画面の操作の音（`sound[0]`〜`sound[15]`）の指定で、今はどれも指定していない。そのため、道具の音などは鳴らない。車両と産業の音は名前で読むので、`sound.tab` が無くても鳴る。`sound.tab` があると本体は環境の音（`beaches.wav`・`forest.wav`・気候の名前の WAV）も探し、無い分はログに `not found` の警告を出す。環境の音は入れていない。
