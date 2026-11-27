# pak256.LongScale

256px のタイルの Simutrans 用 pak セット（略称 256LS）。線路の車両の長さは実物の長さに比例させます（ほかの乗り物を含む規格は [docs/standards.md](docs/standards.md)）。
開発中の α 版で、絵は仮の物です。

## リンク

- [ドキュメントサイト](https://128-bit-net.github.io/pak256/)
- [配布（Releases）](https://github.com/128-bit-net/pak256/releases)（タグが `vendor-` で始まる物は組むための素材で、配布物ではありません）
- [参加のしかた](CONTRIBUTING.md)
- [使用許諾](LICENSE.md)・[作者の一覧](CREDITS.md)
- 文書の入口:
  - [構想](docs/concept.md)
  - [道筋](docs/roadmap.md)
  - [アドオン作者向けの仕様](https://128-bit-net.github.io/pak256/spec/)
  - [大きさの規格](docs/standards.md)
  - [リポジトリの形](docs/layout.md)
  - [ゲームでの確認](docs/game-check.md)

## 開発

コマンドはリポジトリの直下で実行します。Python 3 と makeobj（`PATH` に置くか、環境変数 `MAKEOBJ` で指定）が要ります。

### ビルド

```
pip install -r tools/requirements.txt
python -X utf8 tools/build.py
```

pak は `build/pak/` にできます。同梱する AMI は `gh` で取るので、先に `gh auth login` をしておきます（AMI 抜きなら `--no-ami`）。詳しくは [docs/layout.md](docs/layout.md) の「組み方」。

### 確かめ

```
python -X utf8 tools/lint_config.py
python -X utf8 -m unittest discover -s tools -p "test_*.py"
```

文書の検査（docs-lint）の流し方は [CONTRIBUTING.md](CONTRIBUTING.md) の「文書の検査」。

### AMI の 256 版の取り込み

同梱する AMI の版を上げるときだけ、`tools/build_ami256.py` で 256 版を組んで取り込みます（ふだんのビルドでは使いません）。手順と要る物は [docs/layout.md](docs/layout.md) の「AMI の 256 版を組む」。
