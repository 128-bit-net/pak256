"""貨物の dat の検査（docs/goods.md）。本体が必ず求める貨物が表にあることを確かめる。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ("Passagiere", "Post", "None")  # 本体の bauer/goods_manager.cc の special_objects


def goods():
    found = {}
    for p in glob.glob(os.path.join(ROOT, "objects", "goods", "*.yaml")):
        with open(p, encoding="utf-8") as f:
            text = f.read()
        for block in re.split(r"^- ", text, flags=re.M):
            name = re.search(r"^\s*(?:- )?name:\s*(\S+)\s*$", block, re.M)
            catg = re.search(r"^\s*catg:\s*(\d+)\s*$", block, re.M)
            if name:
                found[name.group(1)] = int(catg.group(1)) if catg else None
    return found


class GoodsTest(unittest.TestCase):
    def test_required_goods(self):
        g = goods()
        for name in REQUIRED:
            self.assertIn(name, g, f"必須の貨物 {name} が objects/goods/ に無い（無いと本体が起動で止まる）")
            self.assertEqual(g[name], 0, f"{name} の catg は 0（専用貨物）")

    def test_catg_range(self):
        for name, catg in goods().items():
            self.assertIsNotNone(catg, f"{name} に catg が無い")
            self.assertTrue(0 <= catg <= 7, f"{name} の catg {catg} は 0〜7 の外（docs/goods.md）")


if __name__ == "__main__":
    unittest.main()
