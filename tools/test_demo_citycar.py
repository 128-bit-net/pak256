"""demo_citycar.py の検査（ゲームも makeobj も使わない）。python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import bz2
import gzip
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demo_citycar  # noqa: E402


def road(name):
    raw = name.encode("utf-8")
    return struct.pack("<H", 1) + struct.pack("<H", len(raw)) + raw + struct.pack("<HH", 0, 0)


def save(level, life):
    """版の行・初めの 8 つの整数・寿命・numbered_stations・道路の 2 つの一覧だけの保存データ。"""
    head = struct.pack("<8i", 256, 33, 4, 330, 16, 1600, 16, level)
    return (b"Simutrans 0.122.0.64-pak256\n" + head + b"\xff" * 16 + struct.pack("<i", life) + b"0"
            + road("ami_road_local") + road("ami_road_local") + b"\xff" * 16)


class DemoCitycarTest(unittest.TestCase):
    def test_patch_changes_only_the_two_values(self):
        values = {"citycar_level": 8, "default_citycar_life": 36}
        self.assertEqual(demo_citycar.read_values(save(5, 120)), {"citycar_level": 5, "default_citycar_life": 120})
        self.assertEqual(demo_citycar.patch(save(5, 120), values), save(8, 36))

    def test_unknown_shape_stops(self):
        with self.assertRaises(ValueError):
            demo_citycar.offsets(save(5, 120).replace(b"0.122.", b"0.124."))
        with self.assertRaises(ValueError):
            demo_citycar.offsets(save(99, 120))  # 交通量の位置の値が範囲の外

    def test_wanted_values_take_first_line(self):
        with tempfile.TemporaryDirectory() as t:
            path = os.path.join(t, "simuconf.tab")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# citycar_level = 1\ncitycar_level = 8\ncitycar_level = 5\ndefault_citycar_life=36\n")
            self.assertEqual(demo_citycar.wanted_values(path), {"citycar_level": 8, "default_citycar_life": 36})
            with open(path, "w", encoding="utf-8") as f:
                f.write("citycar_level = 20\ndefault_citycar_life = 36\n")
            with self.assertRaises(ValueError):
                demo_citycar.wanted_values(path)

    def test_write_save_keeps_compression(self):
        with tempfile.TemporaryDirectory() as t:
            path = os.path.join(t, "a.sve")
            for pack in (gzip.compress, bz2.compress, bytes):
                with open(path, "wb") as f:
                    f.write(pack(save(5, 120)))
                demo_citycar.write_save(path, save(8, 36))
                with open(path, "rb") as f:
                    self.assertEqual(f.read()[:3], pack(save(8, 36))[:3])
                self.assertEqual(demo_citycar.check_demo.read_save(path), save(8, 36))

    def test_committed_demo_is_readable(self):
        data = demo_citycar.check_demo.read_save(demo_citycar.DEMO)
        self.assertEqual(set(demo_citycar.read_values(data)), set(demo_citycar.KEYS))


if __name__ == "__main__":
    unittest.main()
