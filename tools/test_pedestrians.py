"""歩行者の絵と表の検査（docs/pedestrians.md）。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(ROOT, "objects", "pedestrian", "walkers")
sys.path.insert(0, FOLDER)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import draw_pedestrians as D  # noqa: E402

SHOULDER = 0.156  # AMI の生活道路の路肩（道路の端から白線まで。タイルの単位。docs/stations.md）


class PedestrianTest(unittest.TestCase):
    def test_kinds(self):
        self.assertIn(len(D.WALKERS), (2, 3))
        names = [w["name"] for w in D.WALKERS]
        self.assertEqual(len(names), len(set(names)))

    def test_committed_files_match_script(self):
        from PIL import Image
        with open(os.path.join(FOLDER, "walkers.yaml"), encoding="utf-8") as f:
            self.assertEqual(f.read(), D.yaml_text(), "walkers.yaml がスクリプトの出力と違う（draw_pedestrians.py を流し直す）")
        with Image.open(os.path.join(FOLDER, "walkers.png")) as im:
            self.assertEqual(im.convert("RGBA").tobytes(), D.draw_sheet().tobytes(),
                             "walkers.png がスクリプトの出力と違う（draw_pedestrians.py を流し直す）")

    def test_every_direction_has_a_figure_of_the_decided_size(self):
        from PIL import Image
        with Image.open(os.path.join(FOLDER, "walkers.png")) as im:
            sheet = im.convert("RGBA")
        self.assertEqual(sheet.size, (256 * 8, 256 * len(D.WALKERS)))
        for row, spec in enumerate(D.WALKERS):
            tall = round(D.ADULT_PX * spec["height"])
            for col, direction in enumerate(D.V.DIRECTIONS):
                with self.subTest(spec["name"], direction=direction):
                    cell = sheet.crop((col * 256, row * 256, col * 256 + 256, row * 256 + 256))
                    box = cell.getchannel("A").getbbox()
                    self.assertIsNotNone(box, "絵が無い")
                    fx, fy = D.foot_point(direction, spec["offset"])
                    self.assertEqual(box[3] - 1, fy, "足元の高さが違う")
                    self.assertAlmostEqual((box[0] + box[2]) / 2, fx, delta=2, msg="足元の左右の位置が違う")
                    self.assertAlmostEqual(box[3] - box[1], tall, delta=1, msg="背丈が違う")

    def test_no_special_colors(self):
        from PIL import Image
        with Image.open(os.path.join(FOLDER, "walkers.png")) as im:
            colors = im.convert("RGBA").getcolors(1 << 16)
        for _, (r, g, b, a) in colors:
            self.assertIn(a, (0, 255))
            if a:
                self.assertNotIn(r << 16 | g << 8 | b, D.SPECIAL)

    def test_walks_on_the_shoulder(self):
        for spec in D.WALKERS:
            self.assertLess(spec["offset"] / 256, SHOULDER, spec["name"])

    def test_left_side_is_mirrored_by_the_game(self):
        """本体は左側を歩くとき、軸の向きで ((256−2×offset)/2, その半分) px ずらす。
        絵の足元がその半分だけ中心から外れていれば、両側とも道路の端から同じ距離になる。"""
        for spec in D.WALKERS:
            shift = (256 - 2 * spec["offset"]) / 2
            for direction in ("s", "w", "n", "e"):
                x, y = D.foot_offset_px(direction, spec["offset"])
                self.assertAlmostEqual(abs(x) * 2, shift, msg=f"{spec['name']} {direction}")
                self.assertAlmostEqual(abs(y) * 4, shift, msg=f"{spec['name']} {direction}")

    def test_documented(self):
        with open(os.path.join(ROOT, "docs", "pedestrians.md"), encoding="utf-8") as f:
            text = f.read()
        for spec in D.WALKERS:
            row = f"| `{spec['name']}` | {spec['title']} | {round(D.ADULT_PX * spec['height'])} | {spec['offset']} | {spec['weight']} |"
            self.assertIn(row, text)


if __name__ == "__main__":
    unittest.main()
