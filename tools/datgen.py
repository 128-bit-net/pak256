"""表（YAML）から dat を作る（docs/layout.md の「表から dat を作る」）。

YAML の 1 ファイルに、物を 1 つ（マッピング）か、いくつか（マッピングの並び）書く。
キーは dat のキーそのまま。値の入れ子は dat の添字になる。

    image:                     image[0][0]=zelkova.0.0
      0:                  →
        0: zelkova.0.0
    freight: [a, b]       →    freight[0]=a
                               freight[1]=b

`obj`・`name`・`copyright` の無い物は止める（CREDITS.md と dat の copyright= を必ず書くため。CONTRIBUTING.md）。

使い方（1 ファイルを dat にして標準出力へ）:
    python -X utf8 tools/datgen.py objects/scenery/temperate_trees/zelkova.yaml
"""
import sys

import yaml

REQUIRED = ("obj", "name", "copyright")


class DatError(Exception):
    pass


class _Loader(yaml.SafeLoader):
    """同じキーが 2 度あると止める（PyYAML の既定は後が勝つ）。"""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if isinstance(key, (list, dict)):
                raise DatError(f"キーに並びやマッピングは使えない（{key_node.start_mark}）")
            key = str(key)  # 0 と '0' は dat では同じキーになる
            if key in seen:
                raise DatError(f"キー {key!r} が 2 度ある（{key_node.start_mark}）")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def _check_key(k, where):
    if isinstance(k, bool) or not isinstance(k, (str, int)):
        raise DatError(f"{where}: キー {k!r} が文字でも数でもない（yes・no・on・off は引用符で囲む）")


def _flatten(key, value, out):
    if isinstance(value, dict):
        for k, v in value.items():
            _check_key(k, key)
            _flatten(f"{key}[{k}]", v, out)
    elif isinstance(value, list):
        if not value:
            raise DatError(f"{key} の並びが空")
        for i, v in enumerate(value):
            _flatten(f"{key}[{i}]", v, out)
    elif value is None:
        raise DatError(f"{key} の値が空")
    else:
        if isinstance(value, bool):
            value = 1 if value else 0
        text = str(value)
        if "\n" in text:
            raise DatError(f"{key} の値に改行がある")
        out.append(f"{key}={text}")


def object_to_dat(obj, where="?"):
    """物 1 つ（マッピング）を dat の文（末尾の `-` を含む）にする。"""
    if not isinstance(obj, dict):
        raise DatError(f"{where}: 物はマッピングで書く")
    missing = [k for k in REQUIRED if obj.get(k) is None or not str(obj.get(k)).strip()]
    if missing:
        raise DatError(f"{where}: {', '.join(missing)} が無いか空")
    lines = []
    for k, v in obj.items():
        _check_key(k, where)
        _flatten(str(k), v, lines)
    return "\n".join(lines) + "\n-\n"


def yaml_to_dat(path):
    """YAML のファイルを読み、dat の文にする。"""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.load(f, Loader=_Loader)  # noqa: S506（SafeLoader を元にした読み手）
    except yaml.YAMLError as e:
        raise DatError(f"{path}: YAML として読めない: {e}") from e
    if data is None:
        raise DatError(f"{path}: 中身が無い")
    objs = data if isinstance(data, list) else [data]
    return "".join(object_to_dat(o, f"{path} の {i + 1} 個目") for i, o in enumerate(objs))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    try:
        sys.stdout.write(yaml_to_dat(sys.argv[1]))
    except DatError as e:
        sys.exit(f"[datgen] {e}")


if __name__ == "__main__":
    main()
