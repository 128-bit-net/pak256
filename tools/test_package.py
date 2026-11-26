"""package.py と build.py の Warning 検出の検査。python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402
import package  # noqa: E402


def put(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


class PackageTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "root")
        self.build = os.path.join(self.root, "build")
        put(os.path.join(self.root, "LICENSE.md"), "CC BY-SA 4.0")
        put(os.path.join(self.root, "CREDITS.md"), "表")
        put(os.path.join(self.root, "LICENSES", "A.txt"))
        put(os.path.join(self.root, "config", ".gitkeep"), "")
        put(os.path.join(self.root, "config", "simuconf.tab"))
        put(os.path.join(self.root, "text", ".gitkeep"), "")
        put(os.path.join(self.build, "pak", "own.one.pak"))

    def tearDown(self):
        self.tmp.cleanup()

    def names(self):
        return sorted(a for a, _ in package.collect(self.root, self.build))

    def test_basic(self):
        self.assertEqual(self.names(), [
            "pak256/CREDITS.md", "pak256/LICENSE.md", "pak256/LICENSES/A.txt",
            "pak256/config/simuconf.tab", "pak256/own.one.pak"])

    def test_no_pak_stops(self):
        os.remove(os.path.join(self.build, "pak", "own.one.pak"))
        with self.assertRaises(SystemExit):
            self.names()

    def test_ami_license_included_when_texts_ready(self):
        put(os.path.join(self.build, "ami_license.txt"))
        put(os.path.join(self.root, "LICENSE.md"), "CC BY-SA 4.0 と CC BY 4.0")
        put(os.path.join(self.root, "CREDITS.md"), "AMI")
        self.assertIn("pak256/ami_license.txt", self.names())

    def test_ami_license_without_credits_stops(self):
        put(os.path.join(self.build, "ami_license.txt"))
        with self.assertRaises(SystemExit):
            self.names()


class WarningTest(unittest.TestCase):
    def test_bad_lines(self):
        out = "Makeobj version\nWarning: unknown key foo\n   Reading\nERROR: x\n"
        self.assertEqual(build.bad_lines(out), ["Warning: unknown key foo", "ERROR: x"])
        self.assertEqual(build.bad_lines("Makeobj\n  packing tree\n"), [])

    def run_makeobj(self, stdout, stderr):
        done = subprocess.CompletedProcess([], 0, stdout, stderr)  # makeobj は警告だけなら終了コード 0
        with mock.patch.object(build.subprocess, "run", return_value=done), \
                contextlib.redirect_stdout(io.StringIO()):
            build.makeobj("a", os.path.join(build.DAT_OUT, "a"))

    def test_warning_stops_build_with_exit_code_0(self):
        warning = 'Warning: pak256_bus:\tEntry "sped=60" ignored (check spelling)\n'
        for stdout in ("   packing vehicle.pak256_bus\n", "   packing vehicle.pak256_bus", ""):
            with self.assertRaises(SystemExit) as cm:
                self.run_makeobj(stdout, warning)
            self.assertTrue(cm.exception.code)  # 文言を渡した sys.exit は終了コード 1

    def test_clean_output_passes(self):
        self.run_makeobj("   packing vehicle.pak256_bus\n", "")


if __name__ == "__main__":
    unittest.main()
