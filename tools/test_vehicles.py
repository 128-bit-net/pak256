"""車両の長さと描画位置の決まり（docs/vehicles.md）の検査。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"

- tools/vehicles.py の換算と横の位置が、docs/vehicles.md の数と合うこと。
- 見本のバス（objects/vehicle/road/sample_bus/）の表の length が換算どおりで、絵の 8 方向が決まりの位置に描かれていること
  （車体の外接枠が、決まりから計算した枠と ±2px で合う）。特別な色が混じらないこと。
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

BUS_DIR = os.path.join(ROOT, "objects", "vehicle", "road", "sample_bus")
TOL = 2
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}


def load_draw_bus():
    spec = importlib.util.spec_from_file_location("draw_bus", os.path.join(BUS_DIR, "draw_bus.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestRules(unittest.TestCase):
    def test_length_units(self):
        # 四捨五入。pak128.Japan と同じ 20m → 12、25m → 15。短くても 1
        self.assertEqual(V.length_units(12.0), 7)   # 7.27
        self.assertEqual(V.length_units(20.0), 12)  # 12.12
        self.assertEqual(V.length_units(25.0), 15)  # 15.15
        self.assertEqual(V.length_units(4.95), 3)   # 3.0
        self.assertEqual(V.length_units(5.0), 3)    # 3.03
        self.assertEqual(V.length_units(5.8), 4)    # 3.52
        self.assertEqual(V.length_units(0.5), 1)
        # 0.5 ちょうどは切り上げ（Python の round の偶数丸めではない）
        self.assertEqual(V.length_units(4.125), 3)  # 2.5

    def test_fixed_numbers(self):
        # docs/vehicles.md に書いた数。変えるときは文書と一緒に直す
        self.assertEqual(V.FRONT_UNITS, 0)
        self.assertEqual(V.ORIGIN, (128, 192))
        self.assertEqual(V.CELL, 256)
        self.assertEqual(V.UNITS_PER_TILE, 16)
        self.assertAlmostEqual(V.M_PER_UNIT, 1.65)
        self.assertAlmostEqual(V.PX_PER_M_Z, 5.94, places=2)

    def test_lane_offset_is_half_of_driveleft(self):
        # 右側の車線は、本体の左側通行のずれ（×4）のちょうど半分を反対に置く。軸の向きで 24,12、斜めで 24,0 か 0,12
        expect = {"n": (24, 12), "s": (-24, -12), "e": (-24, 12), "w": (24, -12),
                  "ne": (0, 12), "sw": (0, -12), "se": (-24, 0), "nw": (24, 0)}
        for d, xy in expect.items():
            self.assertEqual(V.lane_offset_px(d), xy, d)
            # 左側通行で足すずれを足すと、道路の中心に対して反対の側の同じ距離に来る
            lx, ly = V.DRIVELEFT_64[d]
            self.assertEqual((xy[0] + lx * 4, xy[1] + ly * 4), (-xy[0], -xy[1]), d)

    def test_lane_is_on_the_right(self):
        # 右側の車線の点は、進む向きの右にある（外積の向き）
        for d in V.DIRECTIONS:
            hx, hy = V.HEADING[d]
            px, py = V.lane_point(d)
            self.assertGreater(hx * py - hy * px, 0, d)

    def test_footprint_length(self):
        # 車体の長さは length × 1.65m（実物の長さではない）。前の端は基準点から FRONT_UNITS 前
        for d in V.DIRECTIONS:
            fr, fl, bl, br = V.footprint(d, 7, 2.5, V.FRONT_UNITS)
            along = ((fr[0] - br[0]) ** 2 + (fr[1] - br[1]) ** 2) ** 0.5
            self.assertAlmostEqual(along * V.M_PER_TILE, 7 * V.M_PER_UNIT, places=6)
            px, py = V.lane_point(d)
            hx, hy = V.HEADING[d]
            mid_front = ((fr[0] + fl[0]) / 2 - px, (fr[1] + fl[1]) / 2 - py)
            self.assertAlmostEqual(mid_front[0] * hx + mid_front[1] * hy, V.FRONT_UNITS / V.UNITS_PER_TILE, places=6)


class TestSampleBus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bus = load_draw_bus()
        with open(os.path.join(BUS_DIR, "sample_bus.yaml"), encoding="utf-8") as f:
            cls.table = yaml.safe_load(f)
        cls.img = Image.open(os.path.join(BUS_DIR, "sample_bus.png")).convert("RGBA")

    def test_table(self):
        self.assertEqual(self.table["length"], V.length_units(self.bus.REAL_LENGTH_M))
        self.assertEqual(self.table["name"], self.bus.NAME)
        self.assertEqual(list(self.table["emptyimage"]), list(V.DIRECTIONS))

    def test_sheet_size(self):
        self.assertEqual(self.img.size, (V.CELL * len(V.DIRECTIONS), V.CELL))

    def test_cells_at_rule_position(self):
        length = V.length_units(self.bus.REAL_LENGTH_M)
        for i, d in enumerate(V.DIRECTIONS):
            corners = V.footprint(d, length, self.bus.WIDTH_M, V.FRONT_UNITS)
            pts = [V.to_screen(x, y, z) for (x, y) in corners for z in (0.0, self.bus.HEIGHT_M)]
            ex = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
            cell = self.img.crop((i * V.CELL, 0, (i + 1) * V.CELL, V.CELL))
            box = cell.getchannel("A").getbbox()
            self.assertIsNotNone(box, d)
            got = (box[0], box[1], box[2], box[3])
            for g, e, name in zip(got, ex, ("left", "top", "right", "bottom")):
                self.assertLessEqual(abs(g - e), TOL, f"{d} {name}: 絵 {got} 決まり {tuple(round(v, 1) for v in ex)}")

    def test_no_special_colors(self):
        found = set()
        px = self.img.load()
        for y in range(self.img.height):
            for x in range(self.img.width):
                r, g, b, a = px[x, y]
                if a and (r << 16 | g << 8 | b) in SPECIAL:
                    found.add(f"{r:02X}{g:02X}{b:02X}")
        self.assertFalse(found, f"特別な色: {sorted(found)}")

    def test_alpha_is_binary(self):
        hist = self.img.getchannel("A").histogram()
        self.assertEqual(sum(hist[1:255]), 0)


if __name__ == "__main__":
    unittest.main()
