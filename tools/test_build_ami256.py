"""build_ami256.py の検査（AMI のリポジトリ・Blender・gh は使わない）。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import json
import os
import subprocess
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

    def test_paks(self):
        self.assertEqual(len(B.PAKS), 9)
        self.assertIn("ami_maglev", B.PAKS)
        self.assertIn("ami_narrow", B.PAKS)
        self.assertNotIn("ami_rail_old", B.PAKS)

    def test_child_env_scrubs(self):
        names = ("BUILD_SKIP_MISSING", "CHECK_SKIP_MISSING", "CHECK_256_FULL", "SHEET_LAYOUT", "SHEET_ONLY",
                 "AMI_ROUND", "AMI_FAMILY", "AMI_SURFACE")
        with mock.patch.dict(os.environ, {**{n: "1" for n in names}, "SHEET_PAK_SIZE": "128", "KEEP_ME": "x"}):
            env = B.child_env("blender.exe")
        for n in names:
            self.assertNotIn(n, env)
        self.assertEqual(env["KEEP_ME"], "x")
        self.assertEqual(env["SHEET_PAK_SIZE"], "256")
        self.assertEqual(env["SHEET_BLENDER"], "blender.exe")


class WayEdgesStepTest(unittest.TestCase):
    def run_step(self, result, partial):
        with mock.patch.object(B.check_way_edges, "check", return_value=result) as check, mock.patch("builtins.print"):
            B.step_way_edges("ami", partial)
        check.assert_called_once_with(os.path.join("ami", "src256"), partial)

    def test_passes_and_fails(self):
        self.run_step((3, []), False)
        for result, partial in (((3, ["x"]), False), ((3, ["x"]), True), ((0, []), False)):
            with self.assertRaises(SystemExit, msg=(result, partial)):
                self.run_step(result, partial)

    def test_partial_without_ways(self):
        self.run_step((0, []), True)

    def test_step_check_runs_it(self):
        with mock.patch.object(B, "run"), mock.patch.object(B, "find_dat_linter", return_value="dat_linter"), \
                mock.patch.object(B, "step_way_edges") as edges, mock.patch("builtins.print"):
            B.step_check("ami", {}, False)
        edges.assert_called_once_with("ami", False)


class StepTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def icons(self, log_text, code=0):
        def fake_run(cmd, cwd, env, stdout, stderr, timeout):
            stdout.write(log_text)
            return mock.Mock(returncode=code)
        with mock.patch.object(B.subprocess, "run", side_effect=fake_run):
            B.step_icons(self.tmp.name, {}, "blender.exe")

    def test_icons_ok(self):
        self.icons("[icon] ok\nBlender quit\n")

    def test_icons_traceback_with_exit_0(self):
        with self.assertRaises(SystemExit):
            self.icons("Traceback (most recent call last):\nRuntimeError: x\nBlender quit\n")

    def test_icons_exit_code(self):
        with self.assertRaises(SystemExit):
            self.icons("", code=1)

    def test_resume_steps(self):
        self.assertEqual(B.resume_steps([], "dat"), [])
        self.assertEqual(B.resume_steps(["dat", "render", "icons", "check"], "icons"), ["dat", "render"])
        with self.assertRaises(SystemExit):
            B.resume_steps([], "icons")  # 控えが無いのに途中から
        with self.assertRaises(SystemExit):
            B.resume_steps(["dat"], "icons")

    def render_fake(self, results):
        calls = []

        def fake(ami, env, blender, stage):
            calls.append(list(stage))
            return results.pop(0)
        return calls, fake

    def test_render_stages_ok(self):
        calls, fake = self.render_fake([[], []])
        self.assertEqual(B.render_stages("ami", {}, "b", ["a", "x", "c"], ["x"], fake), [])
        self.assertEqual(calls, [["a", "c"], ["x"]])

    def test_render_stages_retry_keeps_stage_order(self):
        calls, fake = self.render_fake([["c"], ["x"], [], []])
        self.assertEqual(B.render_stages("ami", {}, "b", ["a", "x", "c"], ["x"], fake), ["c", "x"])
        self.assertEqual(calls, [["a", "c"], ["x"], ["c"], ["x"]])

    def test_render_stages_fails_twice(self):
        calls, fake = self.render_fake([["a"], [], ["a"]])
        with self.assertRaises(SystemExit):
            B.render_stages("ami", {}, "b", ["a", "x"], ["x"], fake)

    def test_tree_changes(self):
        repo = os.path.join(self.tmp.name, "repo")
        src = os.path.join(repo, "addons", "ami", "src256")
        os.makedirs(src)

        def git(*args):
            subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True)
        git("init", "-q")
        git("config", "core.autocrlf", "false")
        files = {"addons/ami/src256/a.dat": "x\n", "addons/ami/src256/a.png": "p", "addons/ami/src256/b.dat": "y\n",
                 "tools/t.py": "t\n"}
        for name, text in files.items():
            os.makedirs(os.path.dirname(os.path.join(repo, name)), exist_ok=True)
            with open(os.path.join(repo, name), "w", encoding="utf-8", newline="") as f:
                f.write(text)
        git("add", "-A")
        git("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", "x")
        self.assertEqual(B.tree_changes(repo), [])

        def write(name, text):
            with open(os.path.join(repo, name), "w", encoding="utf-8", newline="") as f:
                f.write(text)
        write("addons/ami/src256/a.png", "q")       # 描き直した絵: 数えない
        write("addons/ami/src256/b.dat", "y\r\n")   # 行末だけ: 数えない
        self.assertEqual(B.tree_changes(repo), [])
        write("addons/ami/src256/a.dat", "z\n")     # dat の中身: 数える
        write("addons/ami/src256/new.dat", "n\n")   # 新しい dat: 数える
        write("tools/t.py", "u\n")                  # 道具: 数える
        self.assertEqual(sorted(B.tree_changes(repo)),
                         ["addons/ami/src256/a.dat", "addons/ami/src256/new.dat", "tools/t.py"])

    def test_steps_roundtrip(self):
        wt = os.path.join(self.tmp.name, "wt")
        self.assertEqual(B.read_steps(wt), [])
        B.write_steps(wt, ["dat", "render"])
        self.assertEqual(B.read_steps(wt), ["dat", "render"])


class StagesTest(unittest.TestCase):
    def test_later_goes_second_in_order(self):
        targets = ["road", "ami_crossing_road", "canal", "monorail", "monorail_tunnel", "rail"]
        later = ["ami_crossing_road", "monorail_tunnel", "not_asked"]
        self.assertEqual(B.split_stages(targets, later),
                         [["road", "canal", "monorail", "rail"], ["ami_crossing_road", "monorail_tunnel"]])

    def test_parse_render_failed(self):
        self.assertEqual(B.parse_render_failed("[render] a: ok (1s)\n[render] done in 12s"), [])
        self.assertEqual(B.parse_render_failed("[render] done in 1358s, failed: a b\n"), ["a", "b"])
        self.assertIsNone(B.parse_render_failed("Traceback\n"))

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
        self.patches = [mock.patch.object(B, "DIST", self.dist), mock.patch.object(B.fetch_ami, "ENV_FILE", self.env_file)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def manifest(self, **over):
        m = {"version": "ami-256-alpha.9", "ami_commit": self.commit, "partial": False, "steps": list(B.STEPS),
             "tree_changes": [], "tools": {"blender": "Blender 4", "makeobj": "Makeobj version 60"},
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

    def test_refuses_skipped_steps(self):
        self.manifest(steps=["build", "release"])
        with self.assertRaises(SystemExit):
            self.upload()

    def test_refuses_old_manifest_without_steps(self):
        self.manifest(steps=None)
        with self.assertRaises(SystemExit):
            self.upload()

    def test_refuses_missing_tool_versions(self):
        self.manifest(tools={"blender": "", "makeobj": "Makeobj version 60"})
        with self.assertRaises(SystemExit):
            self.upload()

    def test_refuses_tree_changes(self):
        self.manifest(tree_changes=["tools/blender/sheetlib/core.py"])
        with self.assertRaises(SystemExit):
            self.upload()

    def test_refuses_changed_zip(self):
        self.manifest(zip_sha256="0" * 64)
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
