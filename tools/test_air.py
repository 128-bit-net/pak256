"""飛行機と空港の表・絵・ツールバーの検査（docs/airport.md・#155）。
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
OBJ = os.path.join(ROOT, "objects")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import vehicles as V  # noqa: E402


def load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(OBJ, *path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


airport = load("draw_airport", "airport", "draw_airport.py")
aircraft = load("draw_aircraft", "vehicle", "air", "draw_aircraft.py")


def read(*path):
    with open(os.path.join(*path), encoding="utf-8") as f:
        return f.read()


def table(folder, key):
    return yaml.safe_load(read(OBJ, "airport", folder, key + ".yaml"))


def doc_rows():
    """docs/airport.md の表の行を {name: 欄の並び} にする。"""
    out = {}
    for line in read(ROOT, "docs", "airport.md").splitlines():
        m = re.match(r"\|\s*`(pak256_\w+)`\s*\|", line)
        if m:
            out[m.group(1)] = [c.strip() for c in line.strip("|").split("|")]
    return out


class AirportTest(unittest.TestCase):
    def test_yaml_is_what_the_script_writes(self):
        for key in airport.WAYS:
            self.assertEqual(read(OBJ, "airport", key, key + ".yaml"), airport.way_table(key), key)
        for key in airport.BUILDINGS:
            self.assertEqual(read(OBJ, "airport", key, key + ".yaml"), airport.building_table(key), key)

    def test_ways(self):
        for key, styp in (("runway", 1), ("taxiway", 0)):
            t = table(key, key)
            self.assertEqual((t["obj"], t["waytype"], t["system_type"]), ("way", "air", styp))
            self.assertEqual(list(t["image"]), airport.RIBI)
            self.assertTrue(set(("icon", "cursor")) <= set(t))

    def test_way_art_stays_in_the_tile(self):
        """道の絵は地面の菱形の画素だけ（隣の升へはみ出さない・重ならない）。"""
        for key in airport.WAYS:
            for ribi in range(16):
                cell = airport.ground_cell(lambda u, v: airport.way_colour(key, ribi, u, v))
                self.assertIsNotNone(airport.rail._mask(cell).getbbox(), (key, ribi))
                self.assertGreaterEqual(airport.rail._mask(cell).getbbox()[1], 128, (key, ribi))

    def test_buildings(self):
        for key, kind in (("air_stop", "stop"), ("air_depot", "depot")):
            t = table(key, key)
            self.assertEqual((t["obj"], t["type"], t["waytype"], str(t["dims"])), ("building", kind, "air", "1,1,4"))
            self.assertEqual(list(t["backimage"]), [0, 1, 2, 3])
            with Image.open(os.path.join(OBJ, "airport", key, key + ".png")) as im:
                self.assertEqual(im.size, (256 * 4, 256 * 3))

    def test_listed_in_docs(self):
        rows = doc_rows()
        for key, o in airport.WAYS.items():
            cells = rows[o["name"]]
            want = [str(o["dat"][k]) for k in ("cost", "maintenance", "topspeed", "max_weight", "intro_year")]
            self.assertEqual(cells[4:9], want, key)
        for o in airport.BUILDINGS.values():
            self.assertIn(o["name"], rows)


class AirlinerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = aircraft.SPEC
        cls.table = yaml.safe_load(read(OBJ, "vehicle", "air", "airliner", "airliner.yaml"))
        cls.img = Image.open(os.path.join(OBJ, "vehicle", "air", "airliner", "airliner.png")).convert("RGBA")

    def test_table(self):
        self.assertEqual(read(OBJ, "vehicle", "air", "airliner", "airliner.yaml"), aircraft.yaml_text())
        self.assertEqual((self.table["waytype"], self.table["cell_size"]), ("air", 512))
        self.assertEqual(list(self.table["emptyimage"]), list(V.DIRECTIONS))
        self.assertEqual(self.table["length"], V.length_from_px(self.spec["target_px"][0]))

    def test_listed_in_docs(self):
        cells = doc_rows()[self.spec["name"]]
        keys = ("payload", "speed", "power", "gear", "weight", "cost", "runningcost", "intro_year", "length")
        self.assertEqual(cells[2:11], [str(self.table[k]) for k in keys])

    def test_screen_size(self):
        """横向き（sw）の胴の長さと、正面向き（se）の翼の幅が、目標の ±8% に入る。"""
        def width(direction):
            i = V.DIRECTIONS.index(direction)
            box = self.img.crop((i * 512, 0, (i + 1) * 512, 512)).getbbox()
            return box[2] - box[0]

        length, span = self.spec["target_px"]
        self.assertAlmostEqual(width("sw"), length, delta=length * 0.08)
        self.assertAlmostEqual(width("se"), span, delta=span * 0.08)

    def test_no_special_colors_and_binary_alpha(self):
        for r, g, b, a in self.img.getdata():
            self.assertIn(a, (0, 255))
            if a:
                self.assertNotIn(r << 16 | g << 8 | b, aircraft.SPECIAL)


class ToolbarTest(unittest.TestCase):
    def test_air_toolbar(self):
        menu = read(ROOT, "config", "menuconf.tab")
        for line in ("toolbar[5][0]=ways(16,0)", "toolbar[5][1]=ways(16,1)", "toolbar[5][2]=general_tool[17],49,,16",
                     "toolbar[5][3]=buildings(33,16)", "toolbar[5][4]=buildings(34,16)"):
            self.assertIn(line, menu)
        self.assertRegex(menu, r"toolbar\[0\]\[\d+\]=toolbar\[5\],48,,AIRTOOLS,airtools\.txt")


if __name__ == "__main__":
    unittest.main()
