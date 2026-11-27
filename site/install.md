# 導入方法

## 要る本体

確かめた本体は **OTRP v64 の Windows 版**です。本家の Simutrans（125.0.1 など）と、Windows 以外の環境では確かめていません。

OTRP は [配布元の Releases](https://github.com/teamhimeh/simutrans/releases/tag/v64) から入手します。本体の入れ方は [OTRP の wiki](https://github.com/teamhimeh/simutrans/wiki/OTRP-Home) など、配布元の案内を見てください。

## pak を置く

1. [Releases](https://github.com/128-bit-net/pak256/releases/latest) から `pak256-<版>.zip` をダウンロードします。`Source code` はゲームでは使いません。
2. zip を展開すると `pak256` というフォルダができます。これを、本体の実行ファイル（`sim-WinGDI64-OTRPv64.exe`）があるフォルダに置きます。

```
本体のフォルダ/
├─ sim-WinGDI64-OTRPv64.exe
├─ pak256/          ← zip から展開したフォルダ
│   ├─ *.pak
│   ├─ config/
│   └─ …
└─ …
```

## 起動する

pak を指定して起動します。効果音を鳴らすには `-sound` も付けます。

```
sim-WinGDI64-OTRPv64.exe -objects pak256/ -sound
```

- `-sound` を付けないと、本体は消音で始まります。ゲームの中の音の設定で消音を外すこともできます。
- 毎回入力しないように、この 1 行を書いたバッチファイル（`.bat`）を本体のフォルダに置くと便利です。
- 設定と保存データを本体のフォルダに置きたいときは、`-singleuser` も付けます。

## 版を上げる

古い `pak256` フォルダを消してから（または別の場所に移してから）、新しい zip の `pak256` を置きます。上書きすると、無くなった pak が残ります。

## 保存データの互換

α版の間は、版を上げると**前の版の保存データが読めなかったり、置いた物が消えたりすることがあります**。

- 版を上げる前に、保存データを別の場所に写しておいてください。
- どの版の保存データを引き継げるかは、各版の [Release の説明](https://github.com/128-bit-net/pak256/releases) に書きます。使っていた版より後の版の説明を順に確かめてください。
- 書いていない版の保存データは、確かめていません。
