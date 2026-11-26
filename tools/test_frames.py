"""地面の印・格子の線・タイルのカーソルの枠の検査（#112。docs/ground.md の「枠の線」）。MIT License。

コミットしてある PNG を見る（描き直しはしない）。
- 枠の外側の画素が、列ごとに、地面の絵（texture-lightmap.png の同じ坂）の縁の画素と一致する。
- 両端の高さが同じ辺は、横 2px・縦 1px の階段になる（両端の高さが違う辺は、坂の傾きの階段になるので 2:1 にならない）。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import os
import unittest

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GROUND = os.path.join(ROOT, "objects", "ground", "temperate")
GUI = os.path.join(ROOT, "objects", "gui")
CELL = 256
HALF = CELL // 2
ORANGE = (255, 128, 0, 255)
GRID = (36, 36, 40, 255)
NUMBER_COLUMNS = (96, 160)  # GeneralTools の番号の文字が入る列


def cell(path, index, cols):
    with Image.open(path) as f:
        x, y = (index % cols) * CELL, (index // cols) * CELL
        return f.convert("RGBA").crop((x, y, x + CELL, y + CELL))


def column_rows(img, color):
    """列ごとに、color（None なら透明でない画素）の行の一覧。"""
    px = img.load()
    return [[y for y in range(CELL) if (px[x, y] == color if color else px[x, y][3])] for x in range(CELL)]


def ground_edges(sw, se, ne, nw):
    """地面の絵（LightTexture）の、列ごとの上の端と下の端の行。地面の画素が無い列（急な坂の尖った角）は None。"""
    img = cell(os.path.join(GROUND, "texture-lightmap.png"), sw + 3 * se + 9 * ne + 27 * nw, 9)
    rows = column_rows(img, None)
    return [r[0] if r else None for r in rows], [r[-1] if r else None for r in rows]


def stair_problems(edge, start):
    """列 start から 128 列の端の行が、横 2px・縦 1px の階段（2 列ずつ同じ行で、1 行ずつ同じ向きに進む）か。"""
    rows = edge[start:start + HALF]
    steps = [rows[i + 2] - rows[i] for i in range(0, HALF - 2, 2)]
    if any(rows[i] != rows[i + 1] for i in range(0, HALF, 2)):
        return [f"列 {start}〜: 2 列ずつ同じ行になっていない"]
    if not (all(s == 1 for s in steps) or all(s == -1 for s in steps)):
        return [f"列 {start}〜: 2 列で 1 行ずつ進んでいない"]
    return []


def line_problems(img, color, top, bottom, front, width):
    """列ごとの枠の色の行が、地面の端（front は下の端）から内側へちょうど width 行（地面がそれより薄い列は地面の全部）か。"""
    problems = []
    for x, rows in enumerate(column_rows(img, color)):
        if top[x] is None:
            want = []
        elif front:
            want = list(range(max(top[x], bottom[x] - width + 1), bottom[x] + 1))
        else:
            want = list(range(top[x], min(bottom[x], top[x] + width - 1) + 1))
        if rows != want:
            problems.append(f"列 {x}: 線の行が {rows}（{want} のはず）")
    return problems


class GroundFrameTest(unittest.TestCase):
    def check(self, img, color, corners, front, width):
        top, bottom = ground_edges(*corners)
        self.assertEqual(line_problems(img, color, top, bottom, front, width), [])
        self.assertEqual({c for _, c in img.getcolors() if c[3]}, {color})
        sw, se, ne, nw = corners
        mid = se if front else nw
        for start, end in ((0, sw), (HALF, ne)):
            if end == mid:
                got = [r[-1 if front else 0] if r else None for r in column_rows(img, color)]
                self.assertEqual(stair_problems(got, start), [])

    def test_marker(self):
        path = os.path.join(GROUND, "marker.png")
        for i in range(27):
            with self.subTest(front=i):
                self.check(cell(path, i, 9), ORANGE, (i % 3, i // 3 % 3, i // 9, 0), True, 3)
            with self.subTest(back=i):
                self.check(cell(path, 27 + i, 9), ORANGE, (i % 3, 0, i // 3 % 3, i // 9), False, 3)

    def test_borders(self):
        path = os.path.join(GROUND, "borders.png")
        for i in range(27):
            with self.subTest(index=i):
                self.check(cell(path, i, 9), GRID, (i % 3, 0, i // 3 % 3, i // 9), False, 2)


class CursorFrameTest(unittest.TestCase):
    """カーソルは平らなタイルの菱形。GeneralTools は本体が 16px 下げて描くので、16px 上に描いてある。"""

    def check(self, img, color, width, dy):
        top, bottom = ground_edges(0, 0, 0, 0)
        rows = column_rows(img, color)
        for edge, front in ((top, False), (bottom, True)):
            got = [r[-1 if front else 0] if r else None for r in rows]
            self.assertEqual(got, [y + dy for y in edge])
            for start in (0, HALF):
                self.assertEqual(stair_problems(got, start), [])
        # 枠の色は上下の端から width 行ずつだけ（角の細い列は菱形の高さまで）。中央の列は番号の文字があるので、埋まっていることだけ見る
        for x in range(CELL):
            n = min(width, bottom[x] - top[x] + 1)
            want = set(range(top[x] + dy, top[x] + dy + n)) | set(range(bottom[x] + dy - n + 1, bottom[x] + dy + 1))
            if NUMBER_COLUMNS[0] <= x < NUMBER_COLUMNS[1]:
                self.assertLessEqual(want, set(rows[x]), x)
            else:
                self.assertEqual(set(rows[x]), want, x)

    def test_general_tools(self):
        with open(os.path.join(GUI, "cursor_general.dat"), encoding="utf-8") as f:
            count = sum(1 for line in f if line.startswith("Image["))
        self.assertGreater(count, 0)
        for i in range(count):
            with self.subTest(index=i):
                self.check(cell(os.path.join(GUI, "cursor_general.png"), i, 8), (255, 230, 0, 255), 6, -16)

    def test_builder_and_marked(self):
        for name, color in (("cursor_builder", (255, 160, 0, 255)), ("cursor_marked", (230, 40, 40, 255))):
            with self.subTest(name=name):
                self.check(cell(os.path.join(GUI, name + ".png"), 0, 10), color, 8, 0)


class CheckerSelfTest(unittest.TestCase):
    """検査そのものが、直す前の描き方（端の点を結ぶ線）で失敗することの確かめ。"""

    def test_polyline_fails(self):
        img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
        ImageDraw.Draw(img).line([(1, 192), (128, 255), (254, 192)], fill=ORANGE, width=3, joint="curve")
        top, bottom = ground_edges(0, 0, 0, 0)
        self.assertTrue(line_problems(img, ORANGE, top, bottom, True, 3))
        self.assertTrue(stair_problems([r[-1] if r else 0 for r in column_rows(img, ORANGE)], 0))

    def test_ground_edge_is_a_stair(self):
        top, bottom = ground_edges(0, 0, 0, 0)
        for edge in (top, bottom):
            for start in (0, HALF):
                self.assertEqual(stair_problems(edge, start), [])


if __name__ == "__main__":
    unittest.main()
