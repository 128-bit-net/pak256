"""道の上でない建物に needs_ground があることの検査（docs/buildings.md の「下の地面」。#126）。MIT License。

本体は、needs_ground の無い建物が基礎の升（fundament_t）にあると、地面を描かない（gebaeude_t::calc_image が地面の絵を空にする）。
絵に地面の無い建物でこれを忘れると、その升に何も描かれず、スクロールすると前の画面が残る。
道の上に建てる停留所・車庫は、今ある道の升に載るだけで基礎の升にならない。
港（type が dock・habour）も、今ある升に載せるだけで基礎の升にならない。
検査は、type が stop・depot で waytype のある建物と港を除き、ほかの建物と産業のすべてに needs_ground を求める。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import os
import re
import unittest

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJECTS = os.path.join(ROOT, "objects")
BUILDING_OBJS = ("building", "factory")
ON_WAY_TYPES = ("stop", "depot")  # waytype があれば道の上に建てる物
HARBOUR_TYPES = ("dock", "habour", "harbour")  # 港。今ある升に載せる


def tables():
    """objects/ の表（.yaml）の物を (パス, 表) で返す。"""
    for p in sorted(glob.glob(os.path.join(OBJECTS, "**", "*.yaml"), recursive=True)):
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        for d in data if isinstance(data, list) else [data]:
            yield p, d


def problem(d):
    """表 1 つの問題を文字列で返す。問題が無ければ None。"""
    if d.get("obj") not in BUILDING_OBJS:
        return None
    if d.get("obj") == "building" and d.get("type") in ON_WAY_TYPES and d.get("waytype"):
        return None
    if d.get("obj") == "building" and d.get("type") in HARBOUR_TYPES:
        return None
    if int(d.get("needs_ground", 0)) <= 0:  # makeobj は 0 より大きければ有効
        return "needs_ground: 1 が無い（本体が下の地面を描かない）"
    return None


class NeedsGroundTest(unittest.TestCase):
    def test_found(self):
        kinds = {d.get("obj") for _, d in tables()}
        self.assertTrue(set(BUILDING_OBJS) <= kinds, f"建物か産業の表が見つからない: {kinds}")

    def test_off_way_buildings_have_ground(self):
        for p, d in tables():
            with self.subTest(name=d.get("name")):
                self.assertIsNone(problem(d), os.path.relpath(p, ROOT))

    def test_no_hand_written_building_dat(self):
        """建物は表から作る。手書きの dat を足すと、上の検査に掛からない。"""
        for p in glob.glob(os.path.join(OBJECTS, "**", "*.dat"), recursive=True):
            with open(p, encoding="utf-8") as f:
                self.assertIsNone(re.search(r"(?im)^\s*obj\s*=\s*(building|factory)\b", f.read()), os.path.relpath(p, ROOT))


class CheckerSelfTest(unittest.TestCase):
    """検査そのものが、誤った入力で失敗することの確かめ。"""

    def test_missing_fails(self):
        for d in ({"obj": "building", "type": "res"}, {"obj": "building", "type": "res", "needs_ground": 0},
                  {"obj": "factory"}, {"obj": "building", "type": "stop"}, {"obj": "building", "type": "extension", "waytype": "road"}):
            self.assertIsNotNone(problem(d), d)

    def test_good_passes(self):
        for d in ({"obj": "building", "type": "res", "needs_ground": 1}, {"obj": "factory", "needs_ground": 1},
                  {"obj": "building", "type": "stop", "waytype": "road"}, {"obj": "tree"},
                  {"obj": "building", "type": "dock"}, {"obj": "building", "type": "habour"}):
            self.assertIsNone(problem(d), d)


if __name__ == "__main__":
    unittest.main()
