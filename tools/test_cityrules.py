"""cityrules.tab の街の規則が、狙った盤面で当てはまる・当てはまらないことの検査。MIT License。

本体 simcity.cc の bewerte_loc を真似た照合（記号の意味と 90 度ずつの回転）を、小さな盤面で試す。
#8 で、役場が 1x1 だと街の道が 1 タイルだけになり、道を延ばす規則が当てはまらず街が育たなかった。
それを繰り返さないための検査。ゲームでの見え方は見ない。
python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 盤面の記号: n 空き地、s 道、h 家。盤面の外は None（本体は「規則を使えない」とする）
CELL = {
    "S": lambda c: c != "s",   # 道でない
    "s": lambda c: c == "s",
    "n": lambda c: c == "n",
    "H": lambda c: c != "h",   # 家でない
    "h": lambda c: c == "h",
    "T": lambda c: True,       # 停留所は盤面に置かない
    "t": lambda c: False,
    "U": lambda c: True,
    "u": lambda c: True,
    ".": lambda c: True,
}


def load_rules():
    rules = {}
    with open(os.path.join(ROOT, "config", "cityrules.tab"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^((?:house|road)_\d+)\s*=\s*(.+?)\s*$", line)
            if m:
                rules[m.group(1)] = m.group(2).split()
    return rules


def rotations(rows):
    """規則の (dx, dy, 記号) の並びを、0・90・180・270 度に回した 4 通りにして返す。"""
    n = len(rows)
    c = n // 2
    base = [(x - c, y - c, rows[y][x]) for y in range(n) for x in range(n)]
    out = []
    for k in range(4):
        cur = base
        for _ in range(k):
            cur = [(dy, -dx, f) for dx, dy, f in cur]
        out.append(cur)
    return out


def matches(rows, board, pos):
    """盤面（文字列の並び）の pos=(x, y) で、規則 rows がどれかの回転で当てはまるか。"""
    for rot in rotations(rows):
        ok = True
        for dx, dy, flag in rot:
            x, y = pos[0] + dx, pos[1] + dy
            if not (0 <= y < len(board) and 0 <= x < len(board[y])):
                ok = False
                break
            if not CELL[flag](board[y][x]):
                ok = False
                break
        if ok:
            return True
    return False


def board(text):
    return [list(r) for r in text.split()]


class CityRulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules()

    def matching(self, prefix, b, pos):
        return [k for k, rows in self.rules.items() if k.startswith(prefix) and matches(rows, b, pos)]

    def test_rules_exist(self):
        self.assertEqual(sorted(k for k in self.rules if k.startswith("road")), ["road_1", "road_2", "road_3", "road_4"])

    def test_single_road_tile_can_be_extended(self):
        # 役場の脇の道は 1 タイル。その 4 方向のどこでも、road_1 が当てはまる。
        b = board("""
            nnnnnnn
            nnnnnnn
            nnnnnnn
            nnnsnnn
            nnnnnnn
            nnnnnnn
            nnnnnnn
        """)
        for pos in [(2, 3), (4, 3), (3, 2), (3, 4)]:
            self.assertIn("road_1", self.matching("road", b, pos), pos)

    def test_single_road_tile_gets_no_house(self):
        # 道 1 タイルの周りに家が建って、道を延ばせなくならない。
        b = board("""
            nnnnnnn
            nnnnnnn
            nnnnnnn
            nnnsnnn
            nnnnnnn
            nnnnnnn
            nnnnnnn
        """)
        for pos in [(2, 3), (4, 3), (3, 2), (3, 4)]:
            self.assertEqual(self.matching("house", b, pos), [], pos)

    def test_road_end_gets_house_only_after_two_tiles(self):
        # 道が 2 タイル続く行き止まりなら、その先に house_3 の家が建つ。
        b = board("""
            nnnnnnn
            nnnnnnn
            nnnnnnn
            nnnnnnn
            nnnsnnn
            nnnsnnn
            nnnnnnn
        """)
        self.assertIn("house_3", self.matching("house", b, (3, 3)))

    def test_road_does_not_extend_next_to_parallel_road(self):
        # 隣に平行の道があるときは、道を延ばさない（道が並んで密にならない）。
        b = board("""
            nnnnnnn
            nnnnnnn
            nssnnnn
            nsnnnnn
            nnnnnnn
            nnnnnnn
            nnnnnnn
        """)
        self.assertNotIn("road_1", self.matching("road", b, (2, 3)))


if __name__ == "__main__":
    unittest.main()
