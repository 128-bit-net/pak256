"""仮の道路の車庫の表の検査（docs/stations.md の「仮の道路の車庫」）。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import os
import re
import unittest

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUTS = 4


def depots():
    for p in sorted(glob.glob(os.path.join(ROOT, "objects", "depot", "**", "*.yaml"), recursive=True)):
        with open(p, encoding="utf-8") as f:
            yield p, yaml.safe_load(f)


def names(o):
    out = []
    if isinstance(o, dict):
        for v in o.values():
            out += names(v)
    else:
        out.append(str(o))
    return out


def tab_has(path, name):
    with open(os.path.join(ROOT, "text", path), encoding="utf-8") as f:
        lines = f.read().splitlines()
    return name in lines[:-1] and bool(lines[lines.index(name) + 1].strip())


class DepotTest(unittest.TestCase):
    def test_found(self):
        self.assertTrue(list(depots()), "車庫の表が見つからない")

    def test_shape(self):
        from PIL import Image
        for p, d in depots():
            self.assertEqual((d["obj"], d["type"], d["waytype"]), ("building", "depot", "road"), p)
            self.assertEqual(str(d["dims"]), f"1,1,{LAYOUTS}", p)
            key = os.path.basename(p)[:-5]
            with Image.open(os.path.join(os.path.dirname(p), key + ".png")) as im:
                im = im.convert("RGB")
                self.assertEqual(im.size, (256 * LAYOUTS, 256 * 3))

                def has_art(row, col):
                    return len(set(im.crop((col * 256, row * 256, col * 256 + 256, row * 256 + 256)).getdata())) > 1

                for k, row in (("backimage", 0), ("frontimage", 1)):
                    self.assertEqual(sorted(d[k]), list(range(LAYOUTS)), f"{p}: {k} の向き")
                    for i in range(LAYOUTS):
                        self.assertEqual(names(d[k][i]), [f"{key}.{row}.{i}"], f"{p}: {k}[{i}]")
                        self.assertTrue(has_art(row, i), f"{p}: {row} 行 {i} 列が空")
                self.assertEqual(str(d["icon"]).lstrip("> "), f"{key}.2.0")
                self.assertTrue(has_art(2, 0), "道具の絵が空")

    def test_listed_and_translated(self):
        with open(os.path.join(ROOT, "docs", "stations.md"), encoding="utf-8") as f:
            doc = f.read()
        for p, d in depots():
            row = [ln for ln in doc.splitlines() if re.match(r"\|\s*`%s`\s*\|" % re.escape(d["name"]), ln)]
            self.assertEqual(len(row), 1, f"{p}: stations.md の控えに無い")
            cells = [c.strip() for c in row[0].strip("|").split("|")]
            self.assertEqual(cells[1:4], [f"`{d['obj']}`", f"`{d['type']}`", f"`{d['waytype']}`"], p)
            for t in ("ja.tab", "en.tab"):
                self.assertTrue(tab_has(t, d["name"]), f"{t} に {d['name']} の訳が無い")


if __name__ == "__main__":
    unittest.main()
