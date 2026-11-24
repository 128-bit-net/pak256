"""表（YAML）から dat を作る（docs/layout.md の「表から dat を作る」）。

YAML の 1 ファイルに、物を 1 つ（マッピング）か、いくつか（マッピングの並び）書く。
キーは dat のキーそのまま。値の入れ子は dat の添字になる。

    image:                     image[0][0]=sample_marker.0.0
      0:                  →
        0: sample_marker.0.0
    freight: [a, b]       →    freight[0]=a
                               freight[1]=b

`obj`・`name`・`copyright` の無い物は止める（CREDITS.md と dat の copyright= を必ず書くため。CONTRIBUTING.md）。

使い方（1 ファイルを dat にして標準出力へ）:
    python -X utf8 tools/datgen.py objects/scenery/sample_marker/sample_marker.yaml
"""
import sys

import yaml

REQUIRED = ("obj", "name", "copyright")


class DatError(Exception):
    pass


def _flatten(key, value, out):
    if isinstance(value, dict):
        for k, v in value.items():
            _flatten(f"{key}[{k}]", v, out)
    elif isinstance(value, list):
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
    missing = [k for k in REQUIRED if k not in obj]
    if missing:
        raise DatError(f"{where}: {', '.join(missing)} が無い")
    lines = []
    for k, v in obj.items():
        _flatten(str(k), v, lines)
    return "\n".join(lines) + "\n-\n"


def yaml_to_dat(path):
    """YAML のファイルを読み、dat の文にする。"""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
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
