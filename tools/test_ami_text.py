"""AMI の物の名前の訳（vendor/ami/text/）の検査（docs/layout.md の「AMI の物の名前の訳」）。取得は差し替えるので、外のネットには出ない。

    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import json
import os
import re
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_ami256 as B  # noqa: E402
import fetch_ami  # noqa: E402
import game  # noqa: E402
import package  # noqa: E402


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def put(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def tabs():
    return sorted(glob.glob(os.path.join(B.TEXT_DIR, "*.tab")))


class VendorTextTest(unittest.TestCase):
    def test_same_commit_as_the_pak(self):
        # AMI を上げたら訳も写し直す（build_ami256.py text）
        self.assertEqual(fetch_ami.read_env(B.TEXT_ENV)["AMI_TEXT_COMMIT"], fetch_ami.read_env()["AMI_COMMIT"],
                         "訳の元のコミットが ami.env と違う（python -X utf8 tools/build_ami256.py text を流す）")

    def test_copies_are_unchanged(self):
        recorded = {k: v for k, v in fetch_ami.read_env(B.TEXT_ENV).items() if k.endswith(".tab")}
        self.assertTrue(recorded)
        for name, sha in recorded.items():
            self.assertEqual(B.blob_sha(read_bytes(os.path.join(B.TEXT_DIR, name))), sha, name)

    def test_names_and_shape(self):
        for path in tabs():
            name = os.path.basename(path)
            # 本家 125.0.1 は「ja.xxx.tab」の形を読む（ja_ami.tab の形は読まない）
            self.assertRegex(name, r"^(ja|en)\.[a-z0-9\-]+\.tab$")
            lines = read_bytes(path).decode("utf-8").split("\n")
            self.assertTrue(lines[0].startswith("§"), f"{name}: 先頭が § でない")
            self.assertFalse(any("\r" in ln for ln in lines), f"{name}: 改行は LF だけ")
            lines[0] = lines[0][1:]
            while lines and lines[0].startswith("#"):
                lines.pop(0)
            if lines and lines[-1] == "":
                lines.pop()
            self.assertEqual(len(lines) % 2, 0, f"{name}: 名前と訳の行が交互にならない")
            names = lines[0::2]
            self.assertEqual(len(names), len(set(names)), f"{name}: 名前が重複している")
            self.assertTrue(all(n.startswith("ami_") for n in names), f"{name}: AMI でない名前がある")
            self.assertTrue(all(t.strip() and t != n for n, t in zip(names, lines[1::2])), f"{name}: 空か名前と同じ訳がある")


class PackagingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = os.path.join(self.tmp.name, "root")
        self.build = os.path.join(self.root, "build")
        put(os.path.join(self.root, "config", "simuconf.tab"))
        put(os.path.join(self.root, "text", "ja.tab"))
        put(os.path.join(self.root, "vendor", "ami", "text", "ja.ami.tab"))
        put(os.path.join(self.build, "pak", "own.one.pak"))

    def runtime(self):
        return [a for a, _ in package.collect_runtime(self.root, self.build)]

    def test_only_with_ami_paks(self):
        self.assertNotIn("pak256/text/ja.ami.tab", self.runtime())  # --no-ami で組んだ形
        put(os.path.join(self.build, "pak", "ami_road.pak"))
        self.assertIn("pak256/text/ja.ami.tab", self.runtime())

    def test_pak_dir_without_config(self):
        pak_dir = os.path.join(self.build, "pak")
        put(os.path.join(pak_dir, "ami_road.pak"))
        placed = [rel for rel, _ in game.pak_dir_sources(pak_dir, self.root)]
        self.assertIn("text/ja.ami.tab", placed)

    def test_unpacked_pak_dir_uses_its_own_text(self):
        pak_dir = os.path.join(self.tmp.name, "pak256")
        put(os.path.join(pak_dir, "ami_road.pak"))
        put(os.path.join(pak_dir, "config", "simuconf.tab"))
        placed = [rel for rel, _ in game.pak_dir_sources(pak_dir, self.root)]
        self.assertNotIn("text/ja.ami.tab", placed)


class TextCommandTest(unittest.TestCase):
    COMMIT = "1" * 40

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.text_dir = os.path.join(self.tmp.name, "text")
        self.text_env = os.path.join(self.tmp.name, "text.env")
        env = os.path.join(self.tmp.name, "ami.env")
        put(env, f"AMI_COMMIT={self.COMMIT}\n")
        for target, name, value in ((B, "TEXT_DIR", self.text_dir), (B, "TEXT_ENV", self.text_env),
                                    (B.fetch_ami, "ENV_FILE", env)):
            p = mock.patch.object(target, name, value)
            p.start()
            self.addCleanup(p.stop)

    def run_text(self, files, sha=None):
        def contents(path, ref, raw=False):
            self.assertEqual(ref, self.COMMIT)
            if raw:
                return files[path.rsplit("/", 1)[1]]
            return [{"name": n, "path": f"{B.AMI_TEXT_PATH}/{n}", "sha": sha or B.blob_sha(d)} for n, d in files.items()]
        with mock.patch.object(B, "gh_contents", side_effect=contents):
            B.main(["text"])

    def test_copies_renames_and_records(self):
        self.run_text({"ja_ami.tab": b"a\n", "en_ami.tab": b"b\n"})
        self.assertEqual(sorted(os.listdir(self.text_dir)), ["en.ami.tab", "ja.ami.tab"])
        env = fetch_ami.read_env(self.text_env)
        self.assertEqual(env["AMI_TEXT_COMMIT"], self.COMMIT)
        self.assertEqual(env["ja.ami.tab"], B.blob_sha(b"a\n"))
        # AMI から無くなった訳は消し、pak256 の側で置いた物は残す
        put(os.path.join(self.text_dir, "ja.own.tab"))
        self.run_text({"ja_ami.tab": b"c\n"})
        self.assertEqual(sorted(os.listdir(self.text_dir)), ["ja.ami.tab", "ja.own.tab"])

    def test_unknown_name_stops(self):
        with self.assertRaises(SystemExit):
            self.run_text({"readme.txt": b"a"})
        self.assertFalse(os.path.exists(self.text_env))

    def test_broken_content_stops(self):
        with self.assertRaises(SystemExit):
            self.run_text({"ja_ami.tab": b"a\n"}, sha="0" * 40)
        self.assertFalse(os.path.exists(self.text_env))

    def test_blob_sha_is_git_hash_object(self):
        self.assertEqual(B.blob_sha(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")

    def test_gh_contents_reads_json(self):
        done = mock.Mock(returncode=0, stdout=json.dumps([{"name": "x"}]).encode(), stderr=b"")
        with mock.patch.object(B.subprocess, "run", return_value=done) as run:
            self.assertEqual(B.gh_contents("p", self.COMMIT), [{"name": "x"}])
        self.assertTrue(re.search(r"contents/p\?ref=1{40}$", run.call_args[0][0][2]))


if __name__ == "__main__":
    unittest.main()
