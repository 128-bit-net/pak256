"""check_demo.py の検査（ゲームも makeobj も使わない）。python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import bz2
import gzip
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_demo  # noqa: E402


def s(name):
    raw = name.encode("utf-8")
    return struct.pack("<H", len(raw)) + raw


class CheckDemoTest(unittest.TestCase):
    def test_names_use_length_prefix(self):
        # 名前の直後の読める字（次の値）は名前に含めない。長さのバイトが読める字でもよい
        long_name = "ami_" + "x" * 40
        data = b"Simutrans 0.122\n" + s("pak256_bus") + b"abc" + s(long_name) + s("ami_road_local") + b"\x00"
        self.assertEqual(check_demo.save_names(data), {"pak256_bus", long_name, "ami_road_local"})

    def test_prefix_inside_name_is_not_split(self):
        self.assertEqual(check_demo.save_names(s("pak256_ami_x")), {"pak256_ami_x"})

    def test_unreadable_shape_stops(self):
        with self.assertRaises(ValueError):
            check_demo.save_names(b"\x00\x00pak256_bus")

    def test_read_save_forms(self):
        body = b"Simutrans 0.122\n" + s("pak256_bus")
        with tempfile.TemporaryDirectory() as t:
            for data in (body, gzip.compress(body), bz2.compress(body)):
                path = os.path.join(t, "a.sve")
                with open(path, "wb") as f:
                    f.write(data)
                self.assertEqual(check_demo.read_save(path), body)
            with open(path, "wb") as f:
                f.write(b"\x28\xb5\x2f\xfd")  # zstd
            with self.assertRaises(ValueError):
                check_demo.read_save(path)

    def test_list_names(self):
        out = ("Makeobj version 60.12\n\nContents of file a.pak (pak version 1003):\n"
               "type              name                            nodes  size\n"
               "----------------  ------------------------------  -----  ----------\n"
               "vehicle           pak256_bus                          6       50302\n"
               "way               ami_road_expressway_elev_front_long     15    40024\n")
        self.assertEqual(check_demo.list_names(out), {"pak256_bus", "ami_road_expressway_elev_front_long"})

    def test_committed_demo_is_readable(self):
        names = check_demo.save_names(check_demo.read_save(check_demo.DEMO))
        self.assertIn("pak256_bus_stop", names)


if __name__ == "__main__":
    unittest.main()
