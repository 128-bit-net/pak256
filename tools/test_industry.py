"""産業の表の検査（docs/industry.md）。

本体は、名前が「kraftwerk」か「Power Plant」で終わる産業を発電所と見なす（descriptor/reader/factory_reader.cc）。
dat のキーでは示せないので、名前の約束をここで確かめる。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import os
import unittest

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def factories():
    for p in sorted(glob.glob(os.path.join(ROOT, "objects", "industry", "**", "*.yaml"), recursive=True)):
        with open(p, encoding="utf-8") as f:
            docs = yaml.safe_load(f)
        for d in docs if isinstance(docs, list) else [docs]:
            if d.get("obj") == "factory":
                yield p, d


class IndustryTest(unittest.TestCase):
    def test_found(self):
        self.assertTrue(list(factories()), "産業の表が見つからない")

    def test_power_plant_name(self):
        """石炭などを受けて電気を作る産業（入力があり、出力が無い）は、名前が kraftwerk か Power Plant で終わる。"""
        for p, d in factories():
            if d.get("inputgood") and not d.get("outputgood"):
                self.assertTrue(str(d["name"]).endswith(("kraftwerk", "Power Plant")),
                                f"{p}: 発電所の名前が kraftwerk / Power Plant で終わらない（本体が発電所と見なさない）")

    def test_images_exist(self):
        """表が引く絵（<名前>.<行>.<列>）の PNG があり、シートの大きさに収まる。"""
        from PIL import Image
        for p, d in factories():
            w, h = (int(v) for v in str(d["dims"]).split(",")[:2])
            names = set()

            def walk(o):
                if isinstance(o, dict):
                    for v in o.values():
                        walk(v)
                else:
                    names.add(str(o))
            walk(d["backimage"])
            self.assertEqual(len(names), w * h, f"{p}: 絵の数が dims と合わない")
            for n in names:
                base, row, col = n.rsplit(".", 2)
                png = os.path.join(os.path.dirname(p), base + ".png")
                self.assertTrue(os.path.exists(png), png)
                sz = Image.open(png).size
                self.assertEqual(sz, (256 * w, 256 * h), f"{png}: シートの大きさが dims と合わない")
                self.assertTrue(int(row) < h and int(col) < w)


if __name__ == "__main__":
    unittest.main()
