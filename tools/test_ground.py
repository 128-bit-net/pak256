"""地面の模様の検査（docs/ground.md）。

ClimateTexture（256x256 の模様 8 枚）は、斜め格子の周期（(128,64) と (128,-64)）でずらしても同じ絵にならないと、
隣のタイルと継ぎ目が出る。コミットしてある PNG を見る（描き直しはしない）。透明な画素が無いことも見る。
Water は菱形で、ずらした先が隣のタイルに当たって重ならないので、ここでは見ない（docs/ground.md）。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import os
import unittest

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PNG = os.path.join(ROOT, "objects", "ground", "temperate", "texture-climate.png")
CELL = 256
CLIMATES = 8
SHIFTS = ((128, 64), (128, -64))  # 隣のタイルへの並びの 2 つのずれ（draw_ground.py の lattice の周期）


def period_problems(cell):
    """256x256 の模様 cell が、斜め格子の周期でつながらない所・透明な所を、文字列の一覧で返す。"""
    problems = []
    if cell.size != (CELL, CELL):
        return [f"大きさが {cell.size}（{CELL}x{CELL} のはず）"]
    rgba = cell.convert("RGBA")
    if rgba.getchannel("A").getextrema()[0] != 255:
        problems.append("透明な画素がある")
    px = list(rgba.getdata())
    for dx, dy in SHIFTS:
        bad = sum(1 for y in range(CELL) for x in range(CELL)
                  if px[y * CELL + x] != px[((y + dy) % CELL) * CELL + (x + dx) % CELL])
        if bad:
            problems.append(f"({dx},{dy}) ずらすと {bad} 画素が違う")
    return problems


class ClimateTextureTest(unittest.TestCase):
    def test_every_climate_tiles_on_the_diagonal_lattice(self):
        with Image.open(PNG) as f:
            sheet = f.convert("RGBA")
        self.assertEqual(sheet.size, (CELL * CLIMATES, CELL))
        for i in range(CLIMATES):
            with self.subTest(climate=i):
                self.assertEqual(period_problems(sheet.crop((i * CELL, 0, (i + 1) * CELL, CELL))), [])


class CheckerSelfTest(unittest.TestCase):
    """検査そのものが、誤った入力で失敗することの確かめ。"""

    @staticmethod
    def periodic():
        img = Image.new("RGBA", (CELL, CELL))
        img.putdata([(((x + 2 * y) % 256), ((x - 2 * y) % 256), 40, 255) for y in range(CELL) for x in range(CELL)])
        return img

    def test_periodic_passes(self):
        self.assertEqual(period_problems(self.periodic()), [])

    def test_non_periodic_fails(self):
        img = self.periodic()
        img.putpixel((3, 5), (0, 0, 0, 255))
        self.assertTrue(period_problems(img))
        grad = Image.new("RGBA", (CELL, CELL))
        grad.putdata([(x, y, 0, 255) for y in range(CELL) for x in range(CELL)])
        self.assertTrue(period_problems(grad))

    def test_transparent_pixel_fails(self):
        img = self.periodic()
        img.putpixel((0, 0), (0, 0, 40, 0))
        self.assertIn("透明な画素がある", period_problems(img))

    def test_wrong_size_fails(self):
        self.assertTrue(period_problems(Image.new("RGBA", (128, 128))))


if __name__ == "__main__":
    unittest.main()
