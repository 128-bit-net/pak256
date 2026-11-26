"""街の建物の季節の絵の添字の検査（docs/buildings.md の「季節の絵」）。

本体は、絵が 4 枚のとき backimage の末尾の添字 0〜3 を夏・秋・冬・春として選ぶ（2 枚だと月の冬には使われない）。
pak256 の街の建物の絵は 2 枚並び（左 = 夏、右 = 冬）で、夏・秋・春は左、冬だけ右を指す。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import os
import unittest

import yaml
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDINGS = os.path.join(ROOT, "objects", "city")
CELL = 256
SUMMER, AUTUMN, WINTER, SPRING = 0, 1, 2, 3


def buildings():
    for p in sorted(glob.glob(os.path.join(BUILDINGS, "**", "*.yaml"), recursive=True)):
        with open(p, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        if d.get("obj") == "building":
            yield p, d


def season_dicts(node):
    """backimage の入れ子の一番内側（値が絵の参照の dict）を全部返す。"""
    if all(isinstance(v, str) for v in node.values()):
        yield node
        return
    for v in node.values():
        yield from season_dicts(v)


def season_problems(stem, backimage):
    """季節の添字の崩れを文字列の一覧で返す。stem は絵のファイル名（拡張子なし）。"""
    problems = []
    for seasons in season_dicts(backimage):
        if sorted(seasons) != [SUMMER, AUTUMN, WINTER, SPRING]:
            problems.append(f"季節の添字が 0〜3 の 4 枚でない: {sorted(seasons)}")
            continue
        for nr, name in seasons.items():
            want = f"{stem}.0.{1 if nr == WINTER else 0}"
            if name != want:
                problems.append(f"季節 {nr} が {name}（{want} のはず）")
    return problems


def sheet_problems(img):
    """2 枚並びの絵の大きさと、冬の絵が夏と違うことを見る。"""
    if img.size != (CELL * 2, CELL):
        return [f"シートの大きさが {img.size}（{CELL * 2}x{CELL} のはず）"]
    rgb = img.convert("RGB")
    if rgb.crop((0, 0, CELL, CELL)).tobytes() == rgb.crop((CELL, 0, CELL * 2, CELL)).tobytes():
        return ["冬の絵（右）が夏の絵（左）と同じ"]
    return []


class TownBuildingSeasonTest(unittest.TestCase):
    def test_found(self):
        self.assertTrue(list(buildings()), "街の建物の表が見つからない")

    def test_season_indices_and_sheets(self):
        for p, d in buildings():
            stem = os.path.splitext(os.path.basename(p))[0]
            with self.subTest(name=stem):
                self.assertEqual(season_problems(stem, d["backimage"]), [])
                with Image.open(os.path.join(os.path.dirname(p), stem + ".png")) as img:
                    self.assertEqual(sheet_problems(img), [])


class CheckerSelfTest(unittest.TestCase):
    """検査そのものが、誤った入力で失敗することの確かめ。"""

    @staticmethod
    def table(seasons):
        return {0: {0: {0: {0: {0: seasons}}}}}

    def test_good_passes(self):
        good = {0: "a.0.0", 1: "a.0.0", 2: "a.0.1", 3: "a.0.0"}
        self.assertEqual(season_problems("a", self.table(good)), [])

    def test_two_images_fail(self):
        self.assertTrue(season_problems("a", self.table({0: "a.0.0", 1: "a.0.1"})))

    def test_wrong_winter_index_fails(self):
        for bad in ({0: "a.0.0", 1: "a.0.1", 2: "a.0.0", 3: "a.0.0"},
                    {0: "a.0.0", 1: "a.0.0", 2: "a.0.1", 3: "a.0.1"},
                    {0: "a.0.0", 1: "a.0.0", 2: "b.0.1", 3: "a.0.0"}):
            self.assertTrue(season_problems("a", self.table(bad)), bad)

    def test_same_winter_picture_fails(self):
        self.assertTrue(sheet_problems(Image.new("RGB", (CELL * 2, CELL))))

    def test_wrong_sheet_size_fails(self):
        self.assertTrue(sheet_problems(Image.new("RGB", (CELL, CELL))))


if __name__ == "__main__":
    unittest.main()
