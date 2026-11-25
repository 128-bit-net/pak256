"""線路の信号の表の検査（docs/signals.md）。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import os
import re
import unittest

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATES = 2
DIRS = 4  # n・s・w・e


def signals():
    for p in sorted(glob.glob(os.path.join(ROOT, "objects", "signal", "**", "*.yaml"), recursive=True)):
        with open(p, encoding="utf-8") as f:
            yield p, yaml.safe_load(f)


class SignalTest(unittest.TestCase):
    def test_found(self):
        self.assertTrue(list(signals()), "信号の表が見つからない")

    def test_shape(self):
        from PIL import Image
        for p, d in signals():
            key = os.path.basename(p)[:-5]
            self.assertEqual(d["obj"], "roadsign", p)
            self.assertEqual(d["waytype"], "track", p)
            self.assertEqual(int(d["is_signal"]), 1, p)
            self.assertEqual(sorted(d["image"]), list(range(STATES * DIRS)), f"{p}: 絵が 状態 × 向き の数にならない")
            sheet = os.path.join(os.path.dirname(p), key + ".png")
            with Image.open(sheet) as im:
                im = im.convert("RGB")
                self.assertEqual(im.size, (256 * STATES * DIRS, 256 * 2), f"{sheet}: シートの大きさ")

                def has_art(row, col):
                    cell = im.crop((col * 256, row * 256, col * 256 + 256, row * 256 + 256))
                    return len(set(cell.getdata())) > 1

                for i in range(STATES * DIRS):
                    self.assertEqual(str(d["image"][i]), f"{key}.0.{i}", f"{p}: image[{i}]")
                    self.assertTrue(has_art(0, i), f"{sheet}: 0 行 {i} 列が空")
                self.assertEqual(str(d["icon"]).lstrip("> "), f"{key}.1.0", f"{p}: icon")
                self.assertEqual(str(d["cursor"]), f"{key}.1.1", f"{p}: cursor")
                self.assertTrue(has_art(1, 0), f"{sheet}: 道具の絵が空")
                self.assertTrue(has_art(1, 1), f"{sheet}: カーソルの絵が空")
                # 道具の絵は、192px の四角を左上の角から隙間なく置く（駅と同じ。#71）
                px = im.crop((0, 256, 256, 512)).load()
                for y in range(192):
                    for x in range(192):
                        corner = (x < 24 or x > 167) and (y < 24 or y > 167)
                        self.assertTrue(corner or px[x, y] != (231, 255, 255), f"{sheet}: 道具の絵の四角に透明色 ({x}, {y})")

    def test_red_and_green_differ(self):
        """赤と青の絵が、同じ向きで違う絵になっている（状態の取り違えを防ぐ）。"""
        from PIL import Image
        for p, d in signals():
            key = os.path.basename(p)[:-5]
            with Image.open(os.path.join(os.path.dirname(p), key + ".png")) as im:
                im = im.convert("RGB")
                for i in range(DIRS):
                    red = im.crop((i * 256, 0, i * 256 + 256, 256)).tobytes()
                    green = im.crop(((DIRS + i) * 256, 0, (DIRS + i) * 256 + 256, 256)).tobytes()
                    self.assertNotEqual(red, green, f"{key}: 向き {i} の赤と青が同じ絵")

    def test_menuconf_removal_tool(self):
        """信号の撤去（general_tool[46]）の定義と、線路のツールバーの並びがある。"""
        with open(os.path.join(ROOT, "config", "menuconf.tab"), encoding="utf-8") as f:
            text = f.read()
        self.assertRegex(text, r"(?m)^general_tool\[46\]\s*=")
        self.assertRegex(text, r"(?m)^toolbar\[3\]\[\d+\]=general_tool\[46\],\d+,,2\s*$")
        self.assertRegex(text, r"(?m)^toolbar\[3\]\[\d+\]=signs\(2\)\s*$")

    def test_listed_in_docs_and_text(self):
        with open(os.path.join(ROOT, "docs", "signals.md"), encoding="utf-8") as f:
            doc = f.read()
        for p, d in signals():
            row = [ln for ln in doc.splitlines() if re.match(r"\|\s*`%s`\s*\|" % re.escape(d["name"]), ln)]
            self.assertEqual(len(row), 1, f"{p}: signals.md の表に無い")
            cells = [c.strip() for c in row[0].strip("|").split("|")]
            self.assertEqual(cells[1:3], [f"`{d['obj']}`", f"`{d['waytype']}`"], p)
            for lang in ("ja", "en"):
                with open(os.path.join(ROOT, "text", f"{lang}.tab"), encoding="utf-8") as f:
                    lines = f.read().splitlines()
                self.assertIn(d["name"], lines, f"text/{lang}.tab に {d['name']} が無い")


if __name__ == "__main__":
    unittest.main()
