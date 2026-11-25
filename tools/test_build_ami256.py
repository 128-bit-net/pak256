"""build_ami256.py の検査（AMI のリポジトリ・Blender・gh は使わない）。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import json
import os
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ami256 as B  # noqa: E402


class SettingsTest(unittest.TestCase):
    def test_build_env_commit(self):
        self.assertRegex(B.build_commit(), r"^[0-9a-f]{40}$")

    def test_build_env_bad_commit(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "build.env")
            with open(p, "w", encoding="utf-8") as f:
                f.write("AMI_COMMIT=8801a1e\n")
            with self.assertRaises(SystemExit):
                B.build_commit(p)

    def test_version(self):
        self.assertEqual(B.check_version("alpha.4"), "alpha.4")
        for bad in ("Alpha.4", "alpha 4", "../x", "", "-x"):
            with self.assertRaises(SystemExit, msg=bad):
                B.check_version(bad)

    def test_paks_are_seven(self):
        self.assertEqual(len(B.PAKS), 7)
        self.assertNotIn("ami_rail_old", B.PAKS)

    def test_child_env_scrubs(self):
        with mock.patch.dict(os.environ, {"BUILD_SKIP_MISSING": "1", "CHECK_SKIP_MISSING": "1", "SHEET_PAK_SIZE": "128"}):
            env = B.child_env("blender.exe")
        self.assertNotIn("BUILD_SKIP_MISSING", env)
        self.assertNotIn("CHECK_SKIP_MISSING", env)
        self.assertEqual(env["SHEET_PAK_SIZE"], "256")
        self.assertEqual(env["SHEET_BLENDER"], "blender.exe")


class StagesTest(unittest.TestCase):
    def test_later_goes_second_in_order(self):
        targets = ["road", "ami_crossing_road", "canal", "monorail", "monorail_tunnel", "rail"]
        later = ["ami_crossing_road", "monorail_tunnel", "not_asked"]
        self.assertEqual(B.split_stages(targets, later),
                         [["road", "canal", "monorail", "rail"], ["ami_crossing_road", "monorail_tunnel"]])

    def test_no_empty_stage(self):
        self.assertEqual(B.split_stages(["road"], ["x"]), [["road"]])


class RewriteEnvTest(unittest.TestCase):
    TEXT = ("# AMI_VERSION: AMI の版（例 ami-256-alpha.2）\n"
            "AMI_VERSION=ami-256-alpha.2\n"
            "AMI_ZIP_URL=https://x/old.zip\n"
            "AMI_ZIP_SHA256=aaa\n")

    def test_replace_and_append(self):
        out = B.rewrite_env(self.TEXT, {"AMI_VERSION": "ami-256-alpha.4", "AMI_ZIP_SHA256": "bbb", "AMI_COMMIT": "c" * 40})
        self.assertEqual(out.splitlines(), [
            "# AMI_VERSION: AMI の版（例 ami-256-alpha.2）",
            "AMI_VERSION=ami-256-alpha.4",
            "AMI_ZIP_URL=https://x/old.zip",
            "AMI_ZIP_SHA256=bbb",
            "AMI_COMMIT=" + "c" * 40,
        ])
        self.assertTrue(out.endswith("\n") and "\r\n" not in out)

    def test_keeps_crlf(self):
        out = B.rewrite_env(self.TEXT.replace("\n", "\r\n"), {"AMI_VERSION": "v"})
        self.assertIn("AMI_VERSION=v\r\n", out)
        self.assertNotIn("\n", out.replace("\r\n", ""))

    def test_url(self):
        self.assertEqual(B.release_url("vendor-ami-256-alpha.4", "ami-256-alpha.4.zip"),
                         "https://github.com/128-bit-net/pak256/releases/download/vendor-ami-256-alpha.4/ami-256-alpha.4.zip")


class CompareTest(unittest.TestCase):
    def test_same_names(self):
        ok, lines = B.compare({"a.pak": 10, "b.pak": 5}, {"a.pak": 12, "b.pak": 5},
                              {"a.pak": {("way", "x")}, "b.pak": set()}, {"a.pak": {("way", "x"), ("way", "y")}, "b.pak": set()})
        self.assertTrue(ok)
        self.assertIn("a.pak: A 10 B / B 12 B（差 -2）", lines)
        self.assertIn("    B だけ: way y", lines)

    def test_missing_pak(self):
        ok, lines = B.compare({"a.pak": 1}, {"a.pak": 1, "b.pak": 2}, None, None)
        self.assertFalse(ok)
        self.assertTrue(any(line.startswith("b.pak: 片方だけ") for line in lines))


class UploadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = self.tmp.name
        self.dist = os.path.join(d, "dist")
        os.makedirs(self.dist)
        self.env_file = os.path.join(d, "ami.env")
        with open(self.env_file, "w", encoding="utf-8") as f:
            f.write("AMI_VERSION=ami-256-alpha.3\nAMI_ZIP_URL=u\nAMI_ZIP_SHA256=s\n")
        self.zip = os.path.join(self.dist, "ami-256-alpha.9.zip")
        with zipfile.ZipFile(self.zip, "w") as z:
            for p in B.PAKS:
                z.writestr(p + ".pak", b"x")
        self.commit = B.build_commit()
        self.patches = [mock.patch.object(B, "DIST", self.dist), mock.patch.object(B, "PATCHES", os.path.join(d, "patches")),
                        mock.patch.object(B.fetch_ami, "ENV_FILE", self.env_file)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def manifest(self, **over):
        m = {"version": "ami-256-alpha.9", "ami_commit": self.commit, "patches": [], "partial": False,
             "zip_sha256": B.sha256_file(self.zip), "paks": {}}
        m.update(over)
        with open(os.path.join(self.dist, "ami-256-alpha.9.json"), "w", encoding="utf-8") as f:
            json.dump(m, f)

    def upload(self, *extra):
        with mock.patch.object(B, "run") as run, mock.patch.object(B, "tag_exists", return_value=False) as te:
            B.main(["upload", "--version", "alpha.9", *extra])
        return run, te

    def env_text(self):
        with open(self.env_file, encoding="utf-8") as f:
            return f.read()

    def test_uploads_and_rewrites(self):
        self.manifest()
        run, _ = self.upload()
        cmd = run.call_args[0][0]
        self.assertEqual(cmd[:4], ["gh", "release", "create", "vendor-ami-256-alpha.9"])
        self.assertIn("--prerelease", cmd)
        self.assertIn("--latest=false", cmd)
        env = self.env_text()
        self.assertIn("AMI_VERSION=ami-256-alpha.9\n", env)
        self.assertIn("releases/download/vendor-ami-256-alpha.9/ami-256-alpha.9.zip\n", env)
        self.assertIn("AMI_ZIP_SHA256=" + B.sha256_file(self.zip), env)
        self.assertIn("AMI_COMMIT=" + self.commit, env)

    def test_dry_run_changes_nothing(self):
        self.manifest()
        before = self.env_text()
        run, _ = self.upload("--dry-run")
        run.assert_not_called()
        self.assertEqual(self.env_text(), before)

    def test_refuses_partial(self):
        self.manifest(partial=True)
        with self.assertRaises(SystemExit):
            self.upload()

    def test_refuses_other_commit(self):
        self.manifest(ami_commit="0" * 40)
        with self.assertRaises(SystemExit):
            self.upload()

    def test_refuses_changed_zip(self):
        self.manifest(zip_sha256="0" * 64)
        with self.assertRaises(SystemExit):
            self.upload()

    def test_refuses_new_patch(self):
        self.manifest()
        os.makedirs(B.PATCHES)
        with open(os.path.join(B.PATCHES, "0001-x.patch"), "w", encoding="utf-8") as f:
            f.write("x")
        with self.assertRaises(SystemExit):
            self.upload()

    def test_refuses_existing_tag(self):
        self.manifest()
        with mock.patch.object(B, "run") as run, mock.patch.object(B, "tag_exists", return_value=True):
            with self.assertRaises(SystemExit):
                B.main(["upload", "--version", "alpha.9"])
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
