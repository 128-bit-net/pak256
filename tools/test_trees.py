"""木の絵・表・設定の検査（docs/trees.md）。
- 絵: 見た目（季節）の行ごとに、高さ・幅が表の値の ±5% に収まり、特別な色が混じらない。
- 表（.yaml）: 気候・季節の数・画像の参照が docs/trees.md の表と合う。温帯の 3 種は 5 季節（冬・雪の絵がある）。
- 設定: 水・岩を除く各気候に木が 1 種以上ある。config/simuconf.tab の tree_climates・no_tree_climates が木と食い違わない。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"

縮尺は docs/standards.md の 1 章（高さ 1m = 5.9px、地面の距離 1m = 6.9px）。育ち age 0〜4 は成木の 0.2〜1.0 倍。
Pillow・PyYAML が要る（tools/requirements.txt）。
"""
import os
import re
import unittest

import yaml
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TREES = os.path.join(ROOT, "objects", "scenery", "trees")
DOC = os.path.join(ROOT, "docs", "trees.md")
SIMUCONF = os.path.join(ROOT, "config", "simuconf.tab")
# 本体の気候のビット（config/simuconf.tab の tree_climates の説明と同じ）
CLIMATE_BIT = {"water": 1, "desert": 2, "tropic": 4, "mediterran": 8, "temperate": 16, "tundra": 32, "rocky": 64, "arctic": 128}
NO_TREE_OK = {"water", "rocky"}  # 木を置かない気候（理由は docs/trees.md の「気候ごとの木」）
TEMPERATE_TRIO = {"zelkova", "cedar", "birch"}
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


def doc_table():
    """docs/trees.md の「種類」の表から {ファイル名: (高さ m, 幅 m, 気候の集合)} を読む。
    列: 名前 | 見た目 | 成木の高さ | 樹冠の幅 | 気候 | 重み"""
    with open(DOC, encoding="utf-8") as f:
        text = f.read()
    found = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*`pak256_(\w+)`\s*\|[^|]*\|\s*(\d+)m\s*\|\s*約\s*(\d+)m\s*\|\s*`([\w,]+)`\s*\|", line)
        if m:
            found[m.group(1)] = (float(m.group(2)), float(m.group(3)), set(m.group(4).split(",")))
    return found


def doc_species():
    """{ファイル名: (高さ m, 幅 m)}。"""
    return {k: (h, w) for k, (h, w, _) in doc_table().items()}


def doc_weights():
    """docs/trees.md の「種類」の表の「重み」の列。{ファイル名: 重み}"""
    with open(DOC, encoding="utf-8") as f:
        text = f.read()
    found = {}
    for line in text.splitlines():
        m = re.match(r"\|\s*`pak256_(\w+)`\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*(\d+)\s*\|\s*$", line)
        if m:
            found[m.group(1)] = int(m.group(2))
    return found


def read_yaml(name):
    with open(os.path.join(TREES, f"{name}.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def simuconf_int(key):
    with open(SIMUCONF, encoding="utf-8") as f:
        for line in f:
            m = re.match(rf"\s*{key}\s*=\s*(\d+)", line)
            if m:
                return int(m.group(1))
    raise KeyError(key)


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
    """シートの各行（見た目）の、各 age の高さと成木の幅が表の値の ±5% に収まらない所を文字列の一覧で返す。"""
    if img.width != CELL * AGES or img.height % CELL or img.height < CELL:
        return [f"シートの大きさが {img.size}（幅 {CELL * AGES}、高さは {CELL} の倍数のはず）"]
    problems = []
    for row in range(img.height // CELL):
        band = img.crop((0, row * CELL, img.width, (row + 1) * CELL))
        for age in range(AGES):
            box = cell_bbox(band, age)
            if box is None:
                problems.append(f"行 {row} の age {age} が空")
                continue
            want_h = height_m * (age + 1) / AGES
            got_h = (box[3] - box[1]) / PX_H
            if abs(got_h - want_h) > want_h * TOL:
                problems.append(f"行 {row} の age {age} の高さ {got_h:.2f}m（表から {want_h:.2f}m の ±5% のはず）")
        box = cell_bbox(band, AGES - 1)
        if box is not None:
            got_w = (box[2] - box[0]) / PX_W
            if abs(got_w - width_m) > width_m * TOL:
                problems.append(f"行 {row} の成木の幅 {got_w:.2f}m（表の {width_m:g}m の ±5% のはず）")
    return problems


class TreeSheetTest(unittest.TestCase):
    def test_doc_table_matches_files(self):
        on_disk = sorted(f[:-5] for f in os.listdir(TREES) if f.endswith(".yaml"))
        self.assertEqual(sorted(doc_species()), on_disk)
        self.assertTrue(TEMPERATE_TRIO <= set(on_disk))

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


def season_rows(name, t):
    """表（.yaml）の image から {season: 行} を返す。年齢ごとに行が違う・形が合わないときは AssertionError。"""
    n = t["seasons"]
    rows = {}
    for age in range(AGES):
        assert sorted(t["image"][age]) == list(range(n)), f"{name}: age {age} の season が 0〜{n - 1} でない"
        for season in range(n):
            m = re.fullmatch(rf"{name}\.(\d+)\.(\d+)", str(t["image"][age][season]))
            assert m, f"{name}: image[{age}][{season}] = {t['image'][age][season]!r}"
            assert int(m.group(2)) == age, f"{name}: image[{age}][{season}] の列が age と違う"
            row = int(m.group(1))
            assert rows.setdefault(season, row) == row, f"{name}: season {season} の行が年齢で変わる"
    return rows


def cell_pixels(img, row, age):
    return list(img.convert("RGB").crop((age * CELL, row * CELL, (age + 1) * CELL, (row + 1) * CELL)).getdata())


def differing_pixels(img, row_a, row_b, age):
    return sum(1 for p, q in zip(cell_pixels(img, row_a, age), cell_pixels(img, row_b, age)) if p != q)


def climate_problems(covered, tree_bits, no_tree_bits):
    """各気候に木があること（水・岩を除く）と、simuconf.tab の 2 つの値が木と食い違わないことを、文字列の一覧で返す。"""
    problems = []
    for cl in sorted(set(CLIMATE_BIT) - covered - NO_TREE_OK):
        problems.append(f"{cl} に木が無い")
    for cl, bit in CLIMATE_BIT.items():
        if cl in covered and no_tree_bits & bit:
            problems.append(f"{cl} は木があるのに no_tree_climates に入っている")
        if cl not in covered and not no_tree_bits & bit:
            problems.append(f"{cl} は木が無いのに no_tree_climates に入っていない")
        if tree_bits & bit and cl not in covered:
            problems.append(f"{cl} は木が無いのに tree_climates に入っている")
    if tree_bits & no_tree_bits:
        problems.append("tree_climates と no_tree_climates が重なる")
    return problems


class TreeTableTest(unittest.TestCase):
    """表（.yaml）の気候・季節・画像の参照・名前・重み・訳。"""

    def test_climates_match_doc(self):
        for name, (_, _, climates) in doc_table().items():
            with self.subTest(name=name):
                got = set(read_yaml(name)["climates"].replace(" ", "").split(","))
                self.assertEqual(got, climates)
                self.assertTrue(got <= set(CLIMATE_BIT))

    def test_name_weight_and_translations(self):
        """dat の name は pak256_<ファイル名>、重みは docs/trees.md の表と同じ、日本語・英語の訳がある。"""
        weights = doc_weights()
        for lang in ("ja", "en"):
            with open(os.path.join(ROOT, "text", f"{lang}.tab"), encoding="utf-8") as f:
                lines = [ln.strip() for ln in f if ln.strip() and not ln.startswith(("#", "§"))]
            keys = set(lines[0::2])
            for name in doc_species():
                with self.subTest(name=name, lang=lang):
                    self.assertIn(f"pak256_{name}", keys)
        for name in doc_species():
            with self.subTest(name=name):
                t = read_yaml(name)
                self.assertEqual(t["name"], f"pak256_{name}")
                self.assertEqual(t["distributionweight"], weights[name])

    def test_seasons_and_images(self):
        """seasons は 5（夏・秋・冬・春・雪）か 2（夏・雪）。画像の参照が、年齢によらず season ごとに 1 つの行を指し、
        その行がシートに収まる。温帯の 3 種は 5 で、冬（season 2）と雪（season 4）が夏と別の行。"""
        for name in doc_species():
            with self.subTest(name=name):
                t = read_yaml(name)
                img = Image.open(os.path.join(TREES, f"{name}.png"))
                rows = season_rows(name, t)
                n = t["seasons"]
                self.assertIn(n, (2, 5))
                self.assertLess(max(rows.values()), img.height // CELL)
                self.assertEqual(sorted(rows), list(range(n)))
                self.assertNotEqual(rows[n - 1], rows[0], "雪は夏と別の行")
                if name in TEMPERATE_TRIO:
                    self.assertEqual(n, 5)
                    self.assertNotEqual(rows[2], rows[0], "冬は夏と別の行")

    def test_distinct_rows_look_different(self):
        """別の行を指す season の絵が、実際に違う（夏のコピーを置いただけでない）。全年齢で見る。
        落葉樹の冬・雪は葉が無いので夏とかなり違い、針葉樹・常緑樹の雪も夏と違う。"""
        for name in doc_species():
            with self.subTest(name=name):
                t = read_yaml(name)
                img = Image.open(os.path.join(TREES, f"{name}.png"))
                rows = season_rows(name, t)
                for season, row in rows.items():
                    if row == rows[0]:
                        continue
                    for age in range(AGES):
                        self.assertGreater(differing_pixels(img, rows[0], row, age), 20,
                                           f"season {season} の絵が夏と同じ（age {age}）")
                # 落葉樹: 冬・雪は、夏よりずっと画素が少ない（葉が無い）
                if name in ("zelkova", "birch"):
                    for season in (2, 4):
                        a = sum(1 for p in cell_pixels(img, rows[season], AGES - 1) if p != CLEAR)
                        b = sum(1 for p in cell_pixels(img, rows[0], AGES - 1) if p != CLEAR)
                        self.assertLess(a, b * 0.5, f"{name} season {season} が葉を落としていない")
                    for season in (1, 3):  # 秋・春は葉があって、夏と色が違う
                        self.assertGreater(differing_pixels(img, rows[0], rows[season], AGES - 1), 500)


class ClimateCoverageTest(unittest.TestCase):
    """各気候に木があり、config/simuconf.tab と食い違わない。"""

    @staticmethod
    def covered():
        out = set()
        for name, (_, _, climates) in doc_table().items():
            out |= climates
        return out

    def test_every_climate_has_a_tree_except_water_and_rock(self):
        self.assertEqual(set(CLIMATE_BIT) - self.covered(), NO_TREE_OK)

    def test_simuconf_matches_trees(self):
        self.assertEqual(
            climate_problems(self.covered(), simuconf_int("tree_climates"), simuconf_int("no_tree_climates")), [])

    def test_checker_finds_mistakes(self):
        """検査そのものが、誤った入力で落ちることの確かめ。"""
        covered = set(CLIMATE_BIT) - NO_TREE_OK
        good_no = CLIMATE_BIT["water"] | CLIMATE_BIT["rocky"]
        tropic = CLIMATE_BIT["tropic"]
        self.assertEqual(climate_problems(covered, tropic, good_no), [])
        self.assertTrue(climate_problems(covered - {"desert"}, tropic, good_no))  # 砂漠の木が無い
        self.assertTrue(climate_problems(covered, tropic, good_no | CLIMATE_BIT["desert"]))  # 木のある砂漠が no_tree
        self.assertTrue(climate_problems(covered, tropic, CLIMATE_BIT["water"]))  # 木の無い岩が no_tree に無い
        self.assertTrue(climate_problems(covered, tropic | CLIMATE_BIT["rocky"], good_no))  # 木の無い岩が tree_climates


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
