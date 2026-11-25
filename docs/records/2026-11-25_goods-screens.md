# 貨物をゲームで確かめた記録（2026-11-25）

[#4](https://github.com/128-bit-net/pak256/issues/4) の貨物 4 つを、OTRP v64（`sim-WinGDI64-OTRPv64.exe`）で確かめた。決め事は [goods.md](../goods.md)。

## 手順

1. `python -X utf8 tools/build.py` で AMI（`ami_road.pak`）込みで組む。makeobj のログに `Warning`・`ERROR` は無い。
2. 検証環境（`addon_check`）の実行ファイル・`themes/`・`font/`・`text/`・`script/` を写した作業フォルダ（`-set_workdir`）に、自前の pak と AMI の道路の pak を置き、`config/*.tab` は `pak/config/`、`text/*.tab` は `pak/text/` に置いた。**`pak256poc` からは何も借りていない**（貨物が自前で足りるので、起動が止まらない）。`settings.xml` は `settings.xml.v64` から送信用の記録の中身だけ空にして写した。
3. 起動: `-objects pak/ -noaddons -load flat_512_left_v64 -freeplay -mute -mcp-port 47880 -screensize 1700x950`（`-lang ja` と `-lang en` で 2 回）。
4. `gui.open_dialog_tool(17)`（貨物の窓 `DIALOG_LIST_GOODS`）を開き、`capture_screen` で撮った。

## 画像

| 画像 | 見所 |
|---|---|
| `1_goods_ja.png` | 旅客・郵便・石炭が、色の線と名前、値、分類（専用貨物・ばら積み貨物）、重さつきで並ぶ |
| `2_goods_en.png` | 英語（Passengers・Mail・Coal・Bulk goods） |

起動のログの `ERROR` は `symbol.BigLogo.pak` の読み込み 1 件だけ（無くてもよい物。GUI の #6 から同じ）。

## 確かめていないこと

- 貨物を実際に産業・車両で運ぶこと（産業・車両が未着手）。
- 値の釣り合い。
