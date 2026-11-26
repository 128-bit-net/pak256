"""川の表・絵・simuconf.tab の検査（docs/config.md の「川」・#158）。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import importlib.util
import os
import re
import sys
import unittest

import yaml
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJ = os.path.join(ROOT, "objects", "river")


def load():
    spec = importlib.util.spec_from_file_location("draw_river", os.path.join(OBJ, "draw_river.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["draw_river"] = mod
    spec.loader.exec_module(mod)
    return mod


river = load()


def read(*path):
    with open(os.path.join(*path), encoding="utf-8") as f:
        return f.read()


class RiverTest(unittest.TestCase):
    def setUp(self):
        self.tables = {t["name"]: t for t in yaml.safe_load(read(OBJ, "river.yaml"))}

    def test_yaml_is_what_the_script_writes(self):
        text = read(OBJ, "river.yaml")
        for tier in river.TIERS:
            self.assertIn(river.table(tier), text)

    def test_simuconf_names_are_rivers(self):
        """river_type[n] は 0 から連番で、全部が pak の川（本体は合流で太らせるときに名前を確かめない）。"""
        conf = read(ROOT, "config", "simuconf.tab")
        found = re.findall(r"^river_type\[(\d+)\]\s*=\s*(\S+)\s*$", conf, re.M)
        self.assertEqual([int(i) for i, _ in found], list(range(len(found))))
        self.assertEqual([n for _, n in found], [t["name"] for t in river.TIERS])
        for _, name in found:
            t = self.tables[name]
            self.assertEqual((t["obj"], t["waytype"], t["system_type"]), ("way", "water", 255), name)

    def test_wide_to_narrow_and_navigable(self):
        halves = [t["half"] for t in river.TIERS]
        self.assertEqual(halves, sorted(halves, reverse=True))
        for t in river.TIERS:
            self.assertGreater(self.tables[t["name"]]["topspeed"], 0, t["name"])  # 0 だと船が通れない

    def test_images_exist(self):
        for name, t in self.tables.items():
            self.assertEqual(list(t["image"]), river.RIBI, name)
            with Image.open(os.path.join(OBJ, name + ".png")) as im:
                rows, cols = im.size[1] // 256, im.size[0] // 256
            for key in ("image", "imageup", "imageup2"):
                for seasons in t[key].values():
                    self.assertEqual(sorted(seasons), [0, 1], (name, key))
                    for ref in seasons.values():
                        sheet, row, col = ref.rsplit(".", 2)
                        self.assertEqual(sheet, name)
                        self.assertTrue(int(row) < rows and int(col) < cols, ref)

    def test_art_is_what_the_script_draws(self):
        """代表の絵（直線・角・合流・坂）が、今のスクリプトの絵と画素まで同じ。"""
        tier = river.TIERS[0]
        with Image.open(os.path.join(OBJ, tier["name"] + ".png")) as im:
            sheet = im.convert("RGBA")
        for ribi in (5, 3, 7):
            col, row = ribi % river.COLS, ribi // river.COLS
            got = sheet.crop((col * 256, row * 256, (col + 1) * 256, (row + 1) * 256))
            self.assertEqual(got.tobytes(), river.cell(ribi, tier["half"], 0).tobytes(), ribi)
        got = sheet.crop((0, 2 * 256, 256, 3 * 256))
        self.assertEqual(got.tobytes(), river.cell(river.SLOPE_RIBI[3], tier["half"], 0, river.SLOPES[3]).tobytes())

    def test_every_tier_has_its_own_snow_and_double_slope_art(self):
        """どの段も、雪の直線（行 3）と、2 段の坂（行 2 の列 4）の絵が、その段の幅で今のスクリプトと同じ。"""
        for tier in river.TIERS:
            with Image.open(os.path.join(OBJ, tier["name"] + ".png")) as im:
                sheet = im.convert("RGBA")
            got = sheet.crop((5 * 256, 3 * 256, 6 * 256, 4 * 256))
            self.assertEqual(got.tobytes(), river.cell(5, tier["half"], 1).tobytes(), tier["name"])
            got = sheet.crop((4 * 256, 2 * 256, 5 * 256, 3 * 256))
            double = tuple(c * 2 for c in river.SLOPES[3])
            self.assertEqual(got.tobytes(), river.cell(river.SLOPE_RIBI[3], tier["half"], 0, double).tobytes(), tier["name"])

    def test_edges_have_the_same_width(self):
        """どの段も、つながる辺の中ほどは水で、つながらない辺の中ほどは何も無い（隣の升と幅がそろう）。"""
        edges = {1: (0.5, 0.001), 2: (0.999, 0.5), 4: (0.5, 0.999), 8: (0.001, 0.5)}
        for tier in river.TIERS:
            for ribi in range(1, 16):
                for bit, (u, v) in edges.items():
                    d = river.distance(ribi, u, v) + river._bank_noise(u, v)
                    if ribi & bit:
                        self.assertLess(d, 0.01, (tier["name"], ribi, bit))
                    else:
                        self.assertGreater(d, tier["half"] + river.BANK, (tier["name"], ribi, bit))


if __name__ == "__main__":
    unittest.main()
