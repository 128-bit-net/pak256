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

    def way_cell(self, key, ribi):
        with Image.open(os.path.join(OBJ, "airport", key, key + ".png")) as im:
            x, y = (ribi % 4) * 256, (ribi // 4) * 256
            return im.convert("RGB").crop((x, y, x + 256, y + 256))

    def test_way_art_is_what_the_script_draws(self):
        """コミットした道の絵（向き 16 通り）が、今のスクリプトの絵と画素まで同じ。"""
        for key in airport.WAYS:
            for ribi in range(16):
                want = airport.ground_cell(lambda u, v: airport.way_colour(key, ribi, u, v))
                self.assertEqual(self.way_cell(key, ribi).tobytes(), want.tobytes(), (key, ribi))

    def test_way_art_stays_in_the_tile(self):
        """道の絵は地面の菱形の中の画素だけ（隣の升へはみ出さない・重ならない）。"""
        for key in airport.WAYS:
            for ribi in range(16):
                px = self.way_cell(key, ribi).load()
                for y in range(256):
                    for x in range(256):
                        if px[x, y] == airport.CLEAR:
                            continue
                        a, b = (x + 0.5 - 128) / 128, (y + 0.5 - 128) / 64
                        self.assertTrue(0 <= (b + a) / 2 < 1 and 0 <= (b - a) / 2 < 1, (key, ribi, x, y))

    def test_way_reaches_connected_sides_only(self):
        """絵は、つながる辺（番号の北 1・東 2・南 4・西 8）まで届く。滑走路の端だけは、反対の辺の手前まで延びる。"""
        edges = {1: (0.5, 0.01), 2: (0.99, 0.5), 4: (0.5, 0.99), 8: (0.01, 0.5)}  # 辺の中ほどの (u, v)
        for key in airport.WAYS:
            for ribi in range(16):
                px = self.way_cell(key, ribi).load()
                for bit, (u, v) in edges.items():
                    painted = px[round(128 + (u - v) * 128), round(128 + (u + v) * 64)] != airport.CLEAR
                    self.assertEqual(painted, bool(ribi & bit), (key, ribi, bit))

    def test_stop_line_is_at_the_far_end(self):
        """駅の絵の向き 0〜3（南・東・北・西につながる）で、停止線はつながる辺から STOP_AT の所にある。"""
        with Image.open(os.path.join(OBJ, "airport", "air_stop", "air_stop.png")) as im:
            px = im.convert("RGB").load()
        for layout, side in enumerate(airport.SIDES):
            found = []
            for across in (0.38, 0.62):
                u, v = airport.from_open(side, airport.STOP_AT, across)
                found.append(px[layout * 256 + round(128 + (u - v) * 128), round(128 + (u + v) * 64)])
            self.assertIn(airport.YELLOW, found, side)  # 片側はターミナルに隠れてもよい

    def test_buildings(self):
        for key, kind in (("air_stop", "stop"), ("air_depot", "depot")):
            t = table(key, key)
            self.assertEqual((t["obj"], t["type"], t["waytype"], str(t["dims"])), ("building", kind, "air", "1,1,4"))
            self.assertEqual(list(t["backimage"]), [0, 1, 2, 3])
            # 格納庫は、口が奥を向く向き（北・西につながる = 2・3）だけ、飛行機の上の絵がある
            self.assertEqual(list(t.get("frontimage", {})), [2, 3] if kind == "depot" else [])
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
        # 飛行機は実物比例（standards.md「船・飛行機」）: length = 実物の長さ ÷ 1.65
        self.assertEqual(self.table["length"], V.length_units(self.spec["real_length_m"]))

    def test_listed_in_docs(self):
        cells = doc_rows()[self.spec["name"]]
        keys = ("payload", "speed", "power", "gear", "weight", "cost", "runningcost", "intro_year", "length")
        self.assertEqual(cells[2:11], [str(self.table[k]) for k in keys])

    def test_screen_size(self):
        """横向き（sw）の胴の長さと、正面向き（se）の翼の幅が、実物の大きさ（length × 1.65m と翼の幅）の ±8% に入る。"""
        def width(direction):
            i = V.DIRECTIONS.index(direction)
            box = self.img.crop((i * 512, 0, (i + 1) * 512, 512)).getbbox()
            return box[2] - box[0]

        px_per_m = V.PX_PER_UNIT_SIDE / V.M_PER_UNIT  # 画面で横向きの 1m
        length = self.table["length"] * V.M_PER_UNIT * px_per_m
        span = self.spec["real_span_m"] * px_per_m
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
        # 段の番号は、ほかの乗り物の段が入るとずれるので、AIRTOOLS の行から読む
        m = re.search(r"toolbar\[0\]\[\d+\]=toolbar\[(\d+)\],52,,AIRTOOLS,airtools\.txt", menu)
        self.assertTrue(m, "AIRTOOLS の入口が無い")
        lines = re.findall(r"(?m)^toolbar\[%s\]\[\d+\]=(\S+)" % m.group(1), menu)
        self.assertEqual(lines, ["ways(16,0)", "ways(16,1)", "general_tool[17],53,,16", "buildings(33,16)", "buildings(34,16)"])


if __name__ == "__main__":
    unittest.main()
