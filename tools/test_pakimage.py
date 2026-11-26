"""pakimage.py の検査。MIT License。makeobj で組む往復の検査は、makeobj と Pillow があるときに走る。"""
import contextlib
import io
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PIL import Image

    import pakimage
except ImportError:  # Pillow が無い
    pakimage = None

MAKEOBJ = shutil.which(os.environ.get("MAKEOBJ", "makeobj"))


def node(kind, body=b"", *children):
    head = kind.encode().ljust(4, b"\0")
    if len(body) < 0xFFFF:
        head += struct.pack("<HH", len(children), len(body))
    else:
        head += struct.pack("<HHI", len(children), 0xFFFF, len(body))
    return head + body + b"".join(children)


def pak(*objects, version=1003):
    return b"Simutrans object file\n\x1a" + struct.pack("<I", version) + node("ROOT", b"", *objects)


def img(x, y, w, h, words, version=3):
    if version == 3:
        head = struct.pack("<hhhBhB", x, y, w, 3, h, 1)
    else:
        head = struct.pack("<hhBBBHB", x, y, w, h, version, len(words), 1)
    return node("IMG", head + struct.pack(f"<{len(words)}H", *words))


def text(s):
    return node("TEXT", s.encode() + b"\0")


@unittest.skipIf(pakimage is None, "Pillow が無い")
class TestFormat(unittest.TestCase):
    def test_pixels_and_runs(self):
        # 1 行目: 透明 2、不透明 1、区切り（0x8000 は 0 画素の透明）、半透明 1。2 行目: 透明だけ
        words = [2, 1, 0x7C00, 0x8000, 0x8001, 0x8020, 0, 3, 0, 0]
        root = pakimage.parse_pak(pak(node("MISC", b"", text("a"), img(2, 5, 2, 2, words))))
        p = pakimage.Picture(root.children[0].children[1].body)
        self.assertEqual(p.pixels, {(4, 5): 0x7C00, (5, 5): 0x8020})

    def test_old_image_version(self):
        words = [0, 1, 0x001F, 0]
        p = pakimage.Picture(pakimage.parse_pak(pak(img(1, 2, 1, 1, words, version=2))).children[0].body)
        self.assertEqual(p.pixels, {(1, 2): 0x001F})
        with self.assertRaises(pakimage.PakError):
            pakimage.Picture(pakimage.parse_pak(pak(img(1, 2, 1, 1, words, version=1))).children[0].body)

    def test_colors(self):
        self.assertEqual(pakimage.rgba(0x7C00), (255, 0, 0, 255))
        self.assertEqual(pakimage.rgba(0x8000), (0x24, 0x4B, 0x67, 255))  # プレーヤー色 1
        self.assertEqual(pakimage.rgba(0x8020 + 31 * 18 + 15), (0xFF, 0xFF, 0x53, 128))  # 半透明の特別な色
        self.assertEqual(pakimage.rgba(0x8020 + 31 * 31 + 31 * 0x380 + 30), (224, 0, 0, 247))  # 半透明の 3-4-3

    def test_large_node_and_factory_name(self):
        big = node("IMG1", b"\0" * 70000)
        fact = node("FACT", b"", node("BUIL", b"", text("mine"), text("who")))
        root = pakimage.parse_pak(pak(big, fact))
        self.assertEqual([len(c.body) for c in root.children][0], 70000)
        self.assertEqual(pakimage.object_name(root.children[1]), "mine")

    def test_errors(self):
        with self.assertRaises(pakimage.PakError):
            pakimage.parse_pak(b"not a pak")
        with self.assertRaises(pakimage.PakError):
            pakimage.parse_pak(pak(version=2000))
        with self.assertRaises(pakimage.PakError):
            pakimage.parse_pak(pak(text("a"))[:-1])
        with self.assertRaises(pakimage.PakError):
            pakimage.Picture(struct.pack("<hhhBhB", 0, 0, 1, 3, 1, 1) + struct.pack("<H", 0))

    def test_spec(self):
        self.assertEqual(pakimage.parse_spec("road"), ("road", ()))
        self.assertEqual(pakimage.parse_spec("road:6/8"), ("road", (6, 8)))
        self.assertEqual(pakimage.parse_spec("road:*.0"), ("road", (None, 0)))
        self.assertEqual(pakimage.parse_spec("a:b"), ("a:b", ()))
        self.assertTrue(pakimage.matches((6, 8), (6,)))
        self.assertFalse(pakimage.matches((6, 8), (6, 8, 0)))
        self.assertFalse(pakimage.matches((7, 8), (6,)))

    def test_canvas_grows_by_cell(self):
        p = pakimage.Picture(img(-3, 300, 1, 1, [0, 1, 0, 0])[8:])
        self.assertEqual(pakimage.canvas_box([p], 256), (-256, 0, 256, 512))

    def test_duplicate_and_missing_name(self):
        found = [("a.pak", o) for o in pakimage.parse_pak(pak(
            node("WAY", b"", text("x")), node("SYMB", b"", text("x")))).children]
        with self.assertRaises(pakimage.PakError):
            pakimage.find_object(found, "x", None)
        self.assertEqual(pakimage.find_object(found, "x", "way")[1].kind, "WAY")
        with self.assertRaises(pakimage.PakError):
            pakimage.find_object(found, "y", None)


RED, TRANSPARENT, PLAYER = (248, 0, 0, 255), (231, 255, 255, 255), (0x24, 0x4B, 0x67, 255)
HALF = (64, 128, 192, 128)  # 半透明の普通の色


@unittest.skipIf(pakimage is None or MAKEOBJ is None, "Pillow か makeobj が無い")
class TestRoundTrip(unittest.TestCase):
    """小さな PNG を makeobj で組み、取り出した画素が元と合うかを見る。"""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        d = cls.tmp.name
        sheet = Image.new("RGBA", (512, 256), TRANSPARENT)
        # 1 枚目: 不透明・特別な色・半透明が同じ行で混ざる
        cls.row = [RED, RED, HALF, HALF, PLAYER, TRANSPARENT, HALF, RED]
        for i, c in enumerate(cls.row):
            sheet.putpixel((100 + i, 200), c)
        sheet.putpixel((100, 201), RED)
        sheet.putpixel((256 + 10, 20), RED)
        sheet.save(os.path.join(d, "a.png"))
        with open(os.path.join(d, "a.dat"), "w", encoding="ascii") as f:
            f.write("obj=misc\nname=t_obj\ncopyright=t\nimage[0]=a.0.0\nimage[1]=-\nimage[2]=a.0.1,-30,5\n-\n")
        r = subprocess.run([MAKEOBJ, "pak256", "t.pak", "a.dat"], cwd=d, capture_output=True, text=True, errors="replace")
        assert r.returncode == 0 and os.path.exists(os.path.join(d, "t.pak")), r.stdout + r.stderr
        cls.pak = os.path.join(d, "t.pak")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def chosen(self):
        return pakimage.select([self.pak], ["t_obj"], None)

    def test_pixels(self):
        first, empty, offset = [p for _, _, p in self.chosen()]
        im = pakimage.render(first, (0, 0, 256, 256))
        for i, c in enumerate(self.row):
            got = im.getpixel((100 + i, 200))
            if c == TRANSPARENT:
                self.assertEqual(got, (0, 0, 0, 0))
            elif c == HALF:
                self.assertEqual(got[:3], (64, 128, 192))
                self.assertAlmostEqual(got[3], 128, delta=10)
            elif c == RED:
                self.assertEqual(got, (255, 0, 0, 255))
            else:
                self.assertEqual(got, c)
        self.assertEqual(im.getpixel((100, 201)), (255, 0, 0, 255))
        self.assertEqual(len(first.pixels), 8)  # 7（上の行の透明でない所）+ 1
        self.assertTrue(empty.empty)
        self.assertEqual(list(offset.pixels), [(10 - 30, 20 + 5)])

    def test_commands(self):
        out = os.path.join(self.tmp.name, "out")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pakimage.main(["list", "--pak", self.pak])
            pakimage.main(["tree", "t_obj", "--pak", self.pak])
            pakimage.main(["export", "t_obj:2/0", "--pak", self.pak, "-o", out])
            pakimage.main(["sheet", "t_obj", "--pak", self.pak, "-o", os.path.join(out, "s.png"),
                           "--scale", "2", "--cols", "3", "--crop", "96,196,112,204"])
        self.assertIn("t_obj  画像 3", buf.getvalue())
        self.assertIn("2/1 IMG 空", buf.getvalue())
        with Image.open(os.path.join(out, "t_obj_2-0.png")) as im:
            self.assertEqual((im.mode, im.size), ("RGBA", (256, 256)))
        with Image.open(os.path.join(out, "s.png")) as im:
            # 切り抜きの (100, 200) は 2 倍の大きさの (8, 8)
            self.assertEqual(im.getpixel((8, 8)), (255, 0, 0))
            self.assertEqual(im.getpixel((0, 0)), (96, 128, 96))

    def test_documented_paths(self):
        """docs/game-check.md の道筋の表（WAY・VHCL・BUIL）が、makeobj の書く順と合うこと。"""
        d = self.tmp.name
        sheet = Image.new("RGBA", (2048, 256), TRANSPARENT)
        for col in range(8):
            sheet.putpixel((col * 256 + col, 100), RED)  # 列 col の画素は x = col
        sheet.save(os.path.join(d, "n.png"))
        way = "obj=way\nname=t_way\ncopyright=t\nwaytype=road\n"
        for season in (0, 1):
            way += f"image[-][{season}]=n.0.{season}\nimageup[3][{season}]=n.0.{2 + season}\n"
            way += f"frontimage[-][{season}]=n.0.{4 + season}\n"
        car = "obj=vehicle\nname=t_car\ncopyright=t\nwaytype=road\n"
        car += "emptyimage[s]=n.0.0\nemptyimage[w]=n.0.1\n"
        car += "freight=Passagiere\nfreightimage[s]=n.0.2\nfreightimage[w]=n.0.3\n"
        house = "obj=building\nname=t_house\ncopyright=t\ntype=res\ndims=1,1,1\n"
        for season in (0, 1):
            house += f"backimage[0][0][0][0][0][{season}]=n.0.{season}\n"
            house += f"frontimage[0][0][0][0][0][{season}]=n.0.{2 + season}\n"
        with open(os.path.join(d, "n.dat"), "w", encoding="ascii") as f:
            f.write("-\n".join((way, car, house)) + "-\n")
        r = subprocess.run([MAKEOBJ, "pak256", "n.pak", "n.dat"], cwd=d, capture_output=True, text=True, errors="replace")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        found = {pakimage.object_name(o): o for _, o in pakimage.objects([os.path.join(d, "n.pak")])}

        def columns(name):
            out = {}
            for where, n in pakimage.images(found[name]):
                p = pakimage.Picture(n.body)
                if not p.empty:
                    out[pakimage.path_text(where)] = min(p.pixels)[0]
            return out

        # 平ら（番号 0）・坂（3）: 夏 2・3、雪 6・7、手前の夏 9、手前の雪 12
        self.assertEqual(columns("t_way"), {"2/0": 0, "3/0": 2, "6/0": 1, "7/0": 3, "9/0": 4, "12/0": 5})
        self.assertEqual(columns("t_car"), {"4/0": 0, "4/1": 1, "5/0": 2, "5/1": 3})
        # 2×季節+(0 奥・1 手前)
        self.assertEqual(columns("t_house"), {"2/0/0/0": 0, "2/1/0/0": 2, "2/2/0/0": 1, "2/3/0/0": 3})

    def test_unknown_image(self):
        with self.assertRaises(SystemExit):
            pakimage.main(["export", "t_obj:9", "--pak", self.pak, "-o", self.tmp.name])


if __name__ == "__main__":
    unittest.main()
