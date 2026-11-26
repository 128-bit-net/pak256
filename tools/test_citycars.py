"""街の車（objects/citycar/citycars/。docs/vehicles.md の「街の車」）の検査。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"

- 表（yaml）と絵（PNG）が draw_citycars.py の出力と同じで、citycar のキーと 8 方向の絵があること。
- 画面の大きさが手本の 2 倍（docs/standards.md の 4 章）で、8 方向が決まりの位置（右側の車線・前の端が基準点）に描かれていること（±2px）。
- makeobj の特別な色が混じらず、透明は α = 0 であること。docs/vehicles.md の表と、訳（ja・en）があること。
Pillow と PyYAML が要る（tools/requirements.txt）。
"""
import importlib.util
import os
import sys
import unittest

import yaml
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vehicles as V  # noqa: E402

CAR_DIR = os.path.join(ROOT, "objects", "citycar", "citycars")
TOL = 2

_spec = importlib.util.spec_from_file_location("draw_citycars", os.path.join(CAR_DIR, "draw_citycars.py"))
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def sheet(spec):
    return Image.open(os.path.join(CAR_DIR, spec["stem"] + ".png")).convert("RGBA")


def bbox(img):
    return img.getchannel("A").point(lambda a: 255 if a else 0).getbbox()


def cell(img, i):
    return img.crop((i * V.CELL, 0, (i + 1) * V.CELL, V.CELL))


class TestCityCars(unittest.TestCase):
    def test_there_are_three(self):
        self.assertEqual(len(D.CARS), 3)
        self.assertEqual(len({s["name"] for s in D.CARS}), 3)

    def test_tables_are_what_the_script_writes(self):
        for spec in D.CARS:
            text = read(os.path.join(CAR_DIR, spec["stem"] + ".yaml"))
            self.assertEqual(text, D.yaml_lines(spec), spec["name"])
            t = yaml.safe_load(text)
            self.assertEqual(t["obj"], "citycar")
            self.assertEqual(set(t["image"]), set(V.DIRECTIONS))
            self.assertNotIn("retire_year", t)

    def test_sheet_is_what_the_script_draws(self):
        for spec in D.CARS:
            self.assertEqual(sheet(spec).tobytes(), D.draw_sheet(spec).tobytes(), spec["name"])

    def test_screen_size_is_twice_the_reference(self):
        for spec in D.CARS:
            length, width, height = spec["ref_px"]
            for got, ref in zip(spec["target_px"], (length, width, height)):
                self.assertLessEqual(abs(got - ref * 2), 1, spec["name"])
            img = sheet(spec)
            sw = bbox(cell(img, V.DIRECTIONS.index("sw")))
            se = bbox(cell(img, V.DIRECTIONS.index("se")))
            L, W = sw[2] - sw[0], se[2] - se[0]
            H = (sw[3] - sw[1]) - W / 2
            for got, want in zip((L, W, H), spec["target_px"]):
                self.assertLessEqual(abs(got - want), TOL + 1, f"{spec['name']} {(L, W, H)}")

    def test_cells_at_rule_position(self):
        for spec in D.CARS:
            img = sheet(spec)
            _, _, height = D.size_m(spec)
            for i, direction in enumerate(V.DIRECTIONS):
                pts = [V.to_screen(x, y, z) for x, y in D.footprint(spec, direction) for z in (0.0, height)]
                want = (min(p[0] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
                box = bbox(cell(img, i))
                got = (box[0], box[2], box[3])
                for g, w in zip(got, want):
                    self.assertLessEqual(abs(g - w), TOL, f"{spec['name']} {direction}: {got} != {want}")

    def test_no_special_colors_and_binary_alpha(self):
        for spec in D.CARS:
            data = sheet(spec).tobytes()
            for i in range(0, len(data), 4):
                r, g, b, a = data[i:i + 4]
                self.assertIn(a, (0, 255))
                if a:
                    self.assertNotIn(r << 16 | g << 8 | b, D.R.SPECIAL)

    def test_values_match_docs_table_and_translations(self):
        doc = read(os.path.join(ROOT, "docs", "vehicles.md"))
        ja = read(os.path.join(ROOT, "text", "ja.tab")).splitlines()
        en = read(os.path.join(ROOT, "text", "en.tab")).splitlines()
        for spec in D.CARS:
            name = spec["name"]
            row = next(ln for ln in doc.splitlines() if ln.startswith(f"| `{name}` |"))
            cols = [c.strip() for c in row.strip("|").split("|")]
            ja_name, en_name = (s.strip() for s in cols[1].split(" / "))
            self.assertEqual(cols[2], f"`{spec['reference']}`")
            self.assertEqual(cols[3:], [str(spec["distributionweight"]), str(spec["speed"]), str(spec["intro_year"])])
            self.assertEqual(ja[ja.index(name) + 1], ja_name)
            self.assertEqual(en[en.index(name) + 1], en_name)


if __name__ == "__main__":
    unittest.main()
