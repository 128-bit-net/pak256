"""check_demo.py の検査（ゲームも makeobj も使わない）。python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import bz2
import contextlib
import gzip
import io
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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
        # 地図は作り直すので、置いてある物の名前は決め打ちしない
        self.assertTrue(check_demo.save_names(check_demo.read_save(check_demo.DEMO)))

    def run_main(self, in_pak):
        used = {"pak256_bus", "ami_road_local"}
        with mock.patch.object(check_demo, "read_save"), \
                mock.patch.object(check_demo, "save_names", return_value=used), \
                mock.patch.object(check_demo, "pak_names", return_value=in_pak), \
                contextlib.redirect_stdout(io.StringIO()):
            check_demo.main()

    def test_main_fails_on_missing_name_only(self):
        self.run_main({"pak256_bus", "ami_road_local", "pak256_other"})
        with self.assertRaises(SystemExit) as cm:
            self.run_main({"ami_road_local"})
        self.assertIn("pak256_bus", cm.exception.code)

    def test_pak_names_stops_when_makeobj_cannot_list(self):
        head = "type  name  nodes  size\n----  ----  -----  ----\n"
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):  # pak が無い
                check_demo.pak_names(t)
            open(os.path.join(t, "a.pak"), "wb").close()
            for done in (subprocess.CompletedProcess([], 1, head, ""), subprocess.CompletedProcess([], 0, "", "ERROR")):
                with mock.patch.object(check_demo.subprocess, "run", return_value=done), self.assertRaises(ValueError):
                    check_demo.pak_names(t)
            done = subprocess.CompletedProcess([], 0, "x\n" + head + "vehicle  pak256_bus  6  50302\n", "")
            with mock.patch.object(check_demo.subprocess, "run", return_value=done):
                self.assertEqual(check_demo.pak_names(t), {"pak256_bus"})


if __name__ == "__main__":
    unittest.main()
