"""温帯の木の絵の検査（docs/trees.md）。高さ・幅が表の値の ±5% に収まり、特別な色が混じらないことを確かめる。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"

縮尺は docs/standards.md の 1 章（高さ 1m = 5.9px、地面の距離 1m = 6.9px）。育ち age 0〜4 は成木の 0.2〜1.0 倍。
Pillow が要る（tools/requirements.txt）。
"""
import os
import re
import unittest

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREES = os.path.join(ROOT, "objects", "scenery", "temperate_trees")
DOC = os.path.join(ROOT, "docs", "trees.md")
CELL = 256
AGES = 5
PX_H = 5.9
PX_W = 6.9
TOL = 0.05
CLEAR = (0xE7, 0xFF, 0xFF)  # 透明（0xE7FFFF）
# makeobj が特別な色として読む色（draw_trees.py の _SPECIAL と同じ。透明の 0xE7FFFF は別に扱う）
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF,
}


def doc_species():
    """docs/trees.md の「種類」の表から {ファイル名: (高さ m, 幅 m)} を読む。"""
    with open(DOC, encoding="utf-8") as f:
        text = f.read()
    found = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*`pak256_(\w+)`\s*\|[^|]*\|\s*(\d+)m\s*\|\s*約\s*(\d+)m\s*\|", line)
        if m:
            found[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return found


def cell_bbox(img, age):
    """age 番目のセルの、透明でない画素の外接枠 (x0, y0, x1, y1)（x1・y1 は含まない）。無ければ None。"""
    cell = img.crop((age * CELL, 0, (age + 1) * CELL, CELL)).convert("RGBA")
    px = cell.load()
    xs, ys = [], []
    for y in range(CELL):
        for x in range(CELL):
            r, g, b, a = px[x, y]
            if a != 0 and (r, g, b) != CLEAR:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def special_colors(img):
    """絵に混じった特別な色の一覧（16 進の文字列）。"""
    rgba = img.convert("RGBA")
    bad = set()
    for _, (r, g, b, a) in rgba.getcolors(maxcolors=CELL * CELL * AGES):
        if a != 0 and ((r << 16) | (g << 8) | b) in SPECIAL:
            bad.add(f"{r:02X}{g:02X}{b:02X}")
    return sorted(bad)


def size_problems(img, height_m, width_m):
    """各 age の高さと、成木の幅が表の値の ±5% に収まらない所を文字列の一覧で返す。"""
    problems = []
    if img.size != (CELL * AGES, CELL):
        return [f"シートの大きさが {img.size}（{CELL * AGES}x{CELL} のはず）"]
    for age in range(AGES):
        box = cell_bbox(img, age)
        if box is None:
            problems.append(f"age {age} が空")
            continue
        want_h = height_m * (age + 1) / AGES
        got_h = (box[3] - box[1]) / PX_H
        if abs(got_h - want_h) > want_h * TOL:
            problems.append(f"age {age} の高さ {got_h:.2f}m（表から {want_h:.2f}m の ±5% のはず）")
    box = cell_bbox(img, AGES - 1)
    if box is not None:
        got_w = (box[2] - box[0]) / PX_W
        if abs(got_w - width_m) > width_m * TOL:
            problems.append(f"成木の幅 {got_w:.2f}m（表の {width_m:g}m の ±5% のはず）")
    return problems


class TreeSheetTest(unittest.TestCase):
    def test_doc_table_has_three_species(self):
        self.assertEqual(sorted(doc_species()), ["birch", "cedar", "zelkova"])

    def test_sheets_match_doc(self):
        for name, (h, w) in doc_species().items():
            with self.subTest(name=name):
                img = Image.open(os.path.join(TREES, f"{name}.png"))
                self.assertEqual(size_problems(img, h, w), [])

    def test_no_special_colors(self):
        for name in doc_species():
            with self.subTest(name=name):
                img = Image.open(os.path.join(TREES, f"{name}.png"))
                self.assertEqual(special_colors(img), [])


class SpecialColorsTest(unittest.TestCase):
    def test_same_as_draw_script(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("draw_trees", os.path.join(TREES, "draw_trees.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(SPECIAL, set(mod._SPECIAL) - {0xE7FFFF})


class CheckerSelfTest(unittest.TestCase):
    """検査そのものが、誤った入力で失敗することの確かめ。"""

    @staticmethod
    def sheet(heights_px, width_px, color=(10, 120, 10)):
        img = Image.new("RGB", (CELL * AGES, CELL), CLEAR)
        for age, hp in enumerate(heights_px):
            for y in range(192 - hp, 192):
                for x in range(age * CELL + 128 - width_px // 2, age * CELL + 128 + width_px // 2):
                    img.putpixel((x, y), color)
        return img

    def good(self):
        # 高さ 10m の木・幅 5m。age ごとに 0.2〜1.0 倍
        return [round(10 * PX_H * (i + 1) / AGES) for i in range(AGES)], round(5 * PX_W)

    def test_good_passes(self):
        hs, w = self.good()
        self.assertEqual(size_problems(self.sheet(hs, w), 10, 5), [])

    def test_wrong_height_fails(self):
        hs, w = self.good()
        hs[4] = round(hs[4] * 1.1)
        self.assertTrue(size_problems(self.sheet(hs, w), 10, 5))

    def test_wrong_width_fails(self):
        hs, w = self.good()
        self.assertTrue(size_problems(self.sheet(hs, round(w * 1.2)), 10, 5))

    def test_empty_cell_fails(self):
        hs, w = self.good()
        hs[2] = 0
        self.assertTrue(size_problems(self.sheet(hs, w), 10, 5))

    def test_wrong_sheet_size_fails(self):
        self.assertTrue(size_problems(Image.new("RGB", (256, 256), CLEAR), 10, 5))

    def test_special_color_is_found(self):
        hs, w = self.good()
        self.assertEqual(special_colors(self.sheet(hs, w, color=(0x6B, 0x6B, 0x6B))), ["6B6B6B"])
        self.assertEqual(special_colors(self.sheet(hs, w)), [])


if __name__ == "__main__":
    unittest.main()
