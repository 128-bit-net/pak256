# 使用許諾

pak256.LongScale（256LS）は、中身の種類ごとに次の許諾で配布します。

| 中身 | 許諾 | 本文 |
|---|---|---|
| 素材: 絵（`.png` など）、3D の元データ（`.blend` など）、dat、音、翻訳の文、説明書、初期マップの保存データ（`demo.sve`） | CC BY-SA 4.0（クリエイティブ・コモンズ 表示-継承 4.0 国際） | [LICENSES/CC-BY-SA-4.0.txt](LICENSES/CC-BY-SA-4.0.txt) |
| コード: dat や絵を作るスクリプト、ビルドの道具、ゲームの中で動くスクリプト（`.py`・`.nut`・`.sh`・Makefile など） | MIT License | [LICENSES/MIT.txt](LICENSES/MIT.txt) |

- 個別に別の許諾を書いたファイル・フォルダは、その許諾に従います。
- 例外: 同梱する AMI（`vendor/ami` から取る `ami_*.pak` とその絵、AMI の物の名前の訳 `vendor/ami/text`。配布物では `text/` の `*.ami.tab`）は、CC BY-SA 4.0 ではなく CC BY 4.0（クリエイティブ・コモンズ 表示 4.0 国際）です。作者（128na）と配布元（https://github.com/128na/simutrans-addon-dev）を表示してください。許諾の文は配布物の `ami_license.txt` にあります。
- 著作権は各作者が持っています。作者の一覧は [CREDITS.md](CREDITS.md) にあります。
- 素材を使う・直して配るときは、作者の名前、CC BY-SA 4.0 であること、直したかどうかを示し、直した版も CC BY-SA 4.0 で配ってください。
- 配布物（`.pak`）にも同じ許諾が及びます（AMI の pak は上の例外のとおり CC BY 4.0）。配布物にはこのファイルと `CREDITS.md` を同梱します。

## English summary

- Assets (graphics, 3D source files, dat files, sounds, translations, documentation, the demo map save `demo.sve`): CC BY-SA 4.0.
- Code (generators, build tools, in-game scripts): MIT License.
- Copyright remains with each author listed in `CREDITS.md`.
- Exception: the bundled AMI add-on (`ami_*.pak` and its images fetched from `vendor/ami`, and its object name translations in `vendor/ami/text`, shipped as `text/*.ami.tab`) is licensed under CC BY 4.0, not CC BY-SA. Attribution: 128na, https://github.com/128na/simutrans-addon-dev.
