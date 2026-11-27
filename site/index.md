# pak256.LongScale

pak256.LongScale（略称 256LS）は、Simutrans の pak セットです。

- **256px のタイル**: 1 タイルの画素数を pak128 の 2 倍にした細かさで描きます。
- **実物の長さに合わせた線路の車両**: 縮尺は 1 単位 = 1.65m で、線路の車両の長さは実物に比例させます。道路の車両の長さと、車両の幅・高さは、見やすいように実物より大きく描きます。
- **pak128 に近い遊び方**: 貨物の分類は pak128 を元にし、`Post` は郵便です。

pak128 など、ほかの pak セットの保存データは持ち越せません。

## 今の版と状態

**α版**です（2026-11-27 の時点の最新は α0.5）。最新の版は [Releases](https://github.com/128-bit-net/pak256/releases/latest) を見てください。

- 動くことを確かめるための版で、**絵は仮**です。これから描き直します。
- 運賃と維持費のつり合いは未調整で、収支は赤字になります（α0.5 の時点）。
- 版ごとの変更点と既知の問題は、各版の Release の説明にあります。

遊び始めるには [導入方法](./install.md) を読んでください。アドオンを作る人は [作る人向けの仕様](./spec/index.md) を読んでください。

## 使用許諾

| 中身 | 許諾 |
|---|---|
| 絵・3D の元データ・dat・音・翻訳の文・説明書・初期マップ | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.ja) |
| 道具のコード（スクリプトなど） | MIT License |
| 同梱の AMI（道路・線路などのアドオン。作者 128na） | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ja) |

AMI の配布元は [128na/simutrans-addon-dev](https://github.com/128na/simutrans-addon-dev) です。正確な条件は [LICENSE.md](https://github.com/128-bit-net/pak256/blob/main/LICENSE.md)、作者の一覧は [CREDITS.md](https://github.com/128-bit-net/pak256/blob/main/CREDITS.md) を見てください。配布の zip にも同じ文書が入っています。
