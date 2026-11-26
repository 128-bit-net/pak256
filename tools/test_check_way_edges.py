"""check_way_edges.py の検査（#111）。AMI の絵は使わず、菱形を描いて確かめる。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import os
import sys
import tempfile
import unittest

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_way_edges as c  # noqa: E402


def diamond(unit):
    """幅 256・高さ 128 の菱形を 1 セルに描く。unit=1 は 256 で直接（段は 2×1）、unit=2 は 128 で描いて 2 倍（4×2）。"""
    size = c.CELL // unit
    small = Image.new("RGB", (size, size), c.TRANSPARENT)
    hw, hh, cx, cy = 128 // unit, 64 // unit, size // 2, 256 // unit
    for y in range(cy - hh, cy + hh):
        for x in range(cx - hw, cx + hw):
            if abs(x + 0.5 - cx) / hw + abs(y + 0.5 - cy) / hh < 1:
                small.putpixel((x, y), (60, 60, 60))
    return small.resize((c.CELL, c.CELL), Image.NEAREST)


DAT = """obj=way
name=x
system_type=0
icon=> x.0.0
image[-][0]=x.0.1,-128,-64
image[ns][0]=x.0.0,-128,-64
diagonal[sw][0]=> x.0.0,-128,-64
"""
KEYS_DAT = """obj=way
image[ns]=x.0.0
image[ns][1]=> x.1.2,-128,-64
diagonal[sw][0]=x.2.3,-128,-64
imageup[3][0]=x.3.0,-128,-64
"""


class WayCellsTest(unittest.TestCase):
    def test_keys(self):
        self.assertEqual(c.way_cells(DAT), [("image[ns][0]", "x", 0, 0), ("diagonal[sw][0]", "x", 0, 0)])

    def test_season_reference_and_slope(self):
        self.assertEqual(c.way_cells(KEYS_DAT),
                         [("image[ns]", "x", 0, 0), ("image[ns][1]", "x", 1, 2), ("diagonal[sw][0]", "x", 2, 3)])

    def test_skips_elevated_and_other_objects(self):
        self.assertEqual(c.way_cells(DAT.replace("system_type=0", "system_type=1")), [])
        self.assertEqual(c.way_cells(DAT.replace("obj=way", "obj=way-object")), [])

    def test_blocks(self):
        self.assertEqual(len(c.way_cells("obj=bridge\nimage[ns][0]=y.0.0\n---\n" + DAT)), 2)


class StaircaseTest(unittest.TestCase):
    def test_2x1_passes(self):
        for outline in c.outlines(diamond(1)):
            self.assertLess(c.staircase(outline)[0], c.MIN_STEPS)

    def test_4x2_fails(self):
        for outline in c.outlines(diamond(2)):
            self.assertGreaterEqual(c.staircase(outline)[0], c.MIN_STEPS)

    def test_gentle_slope_edge_is_not_counted(self):
        self.assertLess(c.staircase({x: 100 + x // 4 for x in range(64)})[0], c.MIN_STEPS)

    def test_zigzag_is_not_a_staircase(self):
        self.assertLess(c.staircase({x: 100 + 2 * ((x // 4) % 2) for x in range(64)})[0], c.MIN_STEPS)


class CheckTest(unittest.TestCase):
    def run_check(self, image, partial=False):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "x.dat"), "w", encoding="utf-8") as f:
                f.write(DAT)
            if image:
                image.save(os.path.join(d, "x.png"))
            return c.check(d, partial)

    def test_good(self):
        self.assertEqual(self.run_check(diamond(1)), (1, []))

    def test_bad(self):
        count, problems = self.run_check(diamond(2))
        self.assertEqual(count, 1)
        self.assertEqual(len(problems), 2)  # 上と下の縁

    def test_missing_sheet(self):
        self.assertEqual(len(self.run_check(None)[1]), 1)
        self.assertEqual(self.run_check(None, partial=True), (0, []))

    def test_nothing_checked_does_not_pass(self):
        self.assertFalse(c.report(0, []))


if __name__ == "__main__":
    unittest.main()
