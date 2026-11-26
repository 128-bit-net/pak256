"""vendor/ami/ami.env の値の形と、fetch_ami.py の検査（SHA-256 の照合と展開）。取得は差し替えるので、外のネットには出ない。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import hashlib
import io
import os
import re
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_ami  # noqa: E402

URL_RE = re.compile(r"^https://github\.com/128-bit-net/pak256/releases/download/([^/\s]+)/[^/\s]+\.zip$")


def make_zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


class AmiEnvTest(unittest.TestCase):
    def test_values_shape(self):
        env = fetch_ami.read_env()
        keys = ("AMI_VERSION", "AMI_ZIP_URL", "AMI_ZIP_SHA256")
        if not any(env.get(k) for k in keys):
            self.skipTest("ami.env が空（AMI 抜きで組む）")
        for k in keys:
            self.assertTrue(env.get(k), f"ami.env に {k} が無い")
        m = URL_RE.match(env["AMI_ZIP_URL"])
        self.assertTrue(m, f"AMI_ZIP_URL の形が違う: {env['AMI_ZIP_URL']}")
        self.assertEqual(m.group(1), "vendor-" + env["AMI_VERSION"], "URL のタグが vendor-<AMI_VERSION> でない")
        self.assertRegex(env["AMI_ZIP_SHA256"], r"^[0-9a-f]{64}$")

    def test_license_file_exists(self):
        self.assertTrue(os.path.isfile(fetch_ami.LICENSE_FILE))

    def test_read_env_parses(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.env")
            with open(p, "w", encoding="utf-8") as f:
                f.write("# コメント\n\nA=1\n B = http://x/y=z \n")
            self.assertEqual(fetch_ami.read_env(p), {"A": "1", "B": "http://x/y=z"})


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.vendor = os.path.join(self.tmp.name, "vendor")
        os.makedirs(self.vendor)
        self.license = os.path.join(self.vendor, "ami_license.txt")
        with open(self.license, "w", encoding="utf-8") as f:
            f.write("CC BY 4.0")
        self.cache = os.path.join(self.tmp.name, "cache")
        self.out = os.path.join(self.tmp.name, "build", "ami")
        self.env_file = os.path.join(self.vendor, "ami.env")
        self.zip = make_zip({"ami/a.pak": b"AAA", "ami/sub/b.PAK": b"BBB", "ami/readme.txt": b"x"})
        self.sha = hashlib.sha256(self.zip).hexdigest()
        self.write_env(sha=self.sha)
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("AMI_DIST", None)
        for name, value in (("ENV_FILE", self.env_file), ("LICENSE_FILE", self.license), ("CACHE", self.cache)):
            p = mock.patch.object(fetch_ami, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.urlopen_calls = []

    def write_env(self, sha=None, url="https://example.invalid/ami.zip"):
        lines = ["AMI_VERSION=test.1"]
        if url:
            lines.append(f"AMI_ZIP_URL={url}")
        if sha:
            lines.append(f"AMI_ZIP_SHA256={sha}")
        with open(self.env_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    def fake_urlopen(self, data):
        def opener(url, timeout=None):
            assert timeout, "urlopen に timeout を渡す"
            self.urlopen_calls.append(url)
            return io.BytesIO(data)
        return mock.patch.object(fetch_ami.urllib.request, "urlopen", opener)

    def test_download_extracts_paks_and_license(self):
        with self.fake_urlopen(self.zip):
            paks = fetch_ami.fetch(self.out)
        self.assertEqual(sorted(os.path.basename(p) for p in paks), ["a.pak", "b.PAK"])
        with open(os.path.join(self.out, "a.pak"), "rb") as f:
            self.assertEqual(f.read(), b"AAA")
        self.assertFalse(os.path.exists(os.path.join(self.out, "readme.txt")))
        self.assertTrue(os.path.isfile(os.path.join(os.path.dirname(self.out), "ami_license.txt")))
        self.assertEqual(self.urlopen_calls, ["https://example.invalid/ami.zip"])

    def test_sha_mismatch_exits_and_leaves_no_cache(self):
        with self.fake_urlopen(self.zip + b"tampered"):
            with self.assertRaises(SystemExit) as cm:
                fetch_ami.fetch(self.out)
        self.assertIn("SHA-256 が合わない", str(cm.exception))
        self.assertEqual(os.listdir(self.cache) if os.path.isdir(self.cache) else [], [])
        self.assertEqual(os.listdir(self.out), [])

    def test_sha_is_case_insensitive(self):
        self.write_env(sha=self.sha.upper())
        with self.fake_urlopen(self.zip):
            self.assertEqual(len(fetch_ami.fetch(self.out)), 2)

    def test_cache_is_used_and_bad_cache_is_dropped(self):
        with self.fake_urlopen(self.zip):
            fetch_ami.fetch(self.out)
        self.assertEqual(len(self.urlopen_calls), 1)
        with self.fake_urlopen(b"must not be read"):
            fetch_ami.fetch(self.out)  # キャッシュから
        self.assertEqual(len(self.urlopen_calls), 1)
        cached = os.path.join(self.cache, "test.1.zip")
        with open(cached, "wb") as f:
            f.write(b"broken")
        with self.fake_urlopen(self.zip):
            with self.assertRaises(SystemExit):
                fetch_ami.fetch(self.out)  # 合わないキャッシュは失敗にして、捨てる
            self.assertFalse(os.path.exists(cached))
            fetch_ami.fetch(self.out)  # 次は取り直す
        self.assertEqual(len(self.urlopen_calls), 2)

    def fake_gh(self, data, returncode=0, stderr=b""):
        def run(cmd, capture_output=None, timeout=None):
            assert timeout, "gh に timeout を渡す"
            self.gh_calls.append(cmd)
            if returncode == 0:
                with open(os.path.join(cmd[cmd.index("-D") + 1], cmd[cmd.index("-p") + 1]), "wb") as f:
                    f.write(data)
            return mock.Mock(returncode=returncode, stderr=stderr)
        return mock.patch.object(fetch_ami.subprocess, "run", run)

    def test_release_url_uses_gh(self):
        url = "https://github.com/128-bit-net/pak256/releases/download/vendor-test.1/test.1.zip"
        self.write_env(sha=self.sha, url=url)
        self.gh_calls = []
        with self.fake_gh(self.zip), self.fake_urlopen(b"must not be read"):
            paks = fetch_ami.fetch(self.out)
        self.assertEqual(len(paks), 2)
        self.assertEqual(self.urlopen_calls, [])
        self.assertEqual(len(self.gh_calls), 1)
        cmd = self.gh_calls[0]
        self.assertEqual(cmd[:3], ["gh", "release", "download"])
        self.assertEqual(cmd[3], "vendor-test.1")
        self.assertEqual(cmd[cmd.index("-R") + 1], "128-bit-net/pak256")
        self.assertEqual(cmd[cmd.index("-p") + 1], "test.1.zip")

    def test_gh_failure_exits(self):
        url = "https://github.com/128-bit-net/pak256/releases/download/vendor-test.1/test.1.zip"
        self.write_env(sha=self.sha, url=url)
        self.gh_calls = []
        with self.fake_gh(b"", returncode=1, stderr=b"release not found"):
            with self.assertRaises(SystemExit) as cm:
                fetch_ami.fetch(self.out)
        self.assertIn("release not found", str(cm.exception))

    def test_gh_missing_exits(self):
        url = "https://github.com/128-bit-net/pak256/releases/download/vendor-test.1/test.1.zip"
        self.write_env(sha=self.sha, url=url)
        with mock.patch.object(fetch_ami.subprocess, "run", side_effect=FileNotFoundError):
            with self.assertRaises(SystemExit) as cm:
                fetch_ami.fetch(self.out)
        self.assertIn("gh が無い", str(cm.exception))

    def test_gh_sha_mismatch_exits(self):
        url = "https://github.com/128-bit-net/pak256/releases/download/vendor-test.1/test.1.zip"
        self.write_env(sha=self.sha, url=url)
        self.gh_calls = []
        with self.fake_gh(self.zip + b"tampered"):
            with self.assertRaises(SystemExit) as cm:
                fetch_ami.fetch(self.out)
        self.assertIn("SHA-256 が合わない", str(cm.exception))

    def test_non_release_url_uses_urllib(self):
        self.gh_calls = []
        with self.fake_gh(b"unused"), self.fake_urlopen(self.zip):
            fetch_ami.fetch(self.out)
        self.assertEqual(self.gh_calls, [])
        self.assertEqual(len(self.urlopen_calls), 1)

    def test_missing_sha_exits(self):
        self.write_env(sha=None)
        with self.assertRaises(SystemExit) as cm:
            fetch_ami.fetch(self.out)
        self.assertIn("AMI_ZIP_SHA256", str(cm.exception))

    def test_no_url_does_nothing(self):
        self.write_env(url=None, sha=None)
        self.assertEqual(fetch_ami.fetch(self.out), [])
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(self.out), "ami_license.txt")))

    def test_zip_without_pak_exits(self):
        data = make_zip({"readme.txt": b"x"})
        self.write_env(sha=hashlib.sha256(data).hexdigest())
        with self.fake_urlopen(data):
            with self.assertRaises(SystemExit) as cm:
                fetch_ami.fetch(self.out)
        self.assertIn("pak が無い", str(cm.exception))

    def test_missing_license_message_survives_other_drive(self):
        os.remove(self.license)

        def other_drive(path, start=None):
            raise ValueError("path is on mount 'D:', start on mount 'C:'")
        with mock.patch.object(fetch_ami.os.path, "relpath", other_drive), self.fake_urlopen(self.zip):
            with self.assertRaises(SystemExit) as cm:
                fetch_ami.fetch(self.out)
        self.assertIn("許諾の文", str(cm.exception))
        self.assertIn(self.license, str(cm.exception))

    def test_rel_falls_back_to_path(self):
        self.assertEqual(fetch_ami._rel(os.path.join(fetch_ami.ROOT, "a", "b")), os.path.join("a", "b"))
        with mock.patch.object(fetch_ami.os.path, "relpath", side_effect=ValueError):
            self.assertEqual(fetch_ami._rel("X:/y"), "X:/y")

    def test_missing_license_exits(self):
        os.remove(self.license)
        with self.fake_urlopen(self.zip):
            with self.assertRaises(SystemExit) as cm:
                fetch_ami.fetch(self.out)
        self.assertIn("許諾の文", str(cm.exception))

    def test_ami_dist_dir_has_priority_over_env(self):
        src = os.path.join(self.tmp.name, "dist")
        os.makedirs(src)
        for n, d in (("x.pak", b"X"), ("note.txt", b"n")):
            with open(os.path.join(src, n), "wb") as f:
                f.write(d)
        os.environ["AMI_DIST"] = src
        with self.fake_urlopen(b"unused"):
            paks = fetch_ami.fetch(self.out)
        self.assertEqual([os.path.basename(p) for p in paks], ["x.pak"])
        self.assertEqual(self.urlopen_calls, [])

    def test_ami_dist_zip(self):
        p = os.path.join(self.tmp.name, "local.zip")
        with open(p, "wb") as f:
            f.write(make_zip({"only.pak": b"L"}))  # ami.env 側の zip と中身を変える
        os.environ["AMI_DIST"] = p
        with self.fake_urlopen(b"unused"):
            paks = fetch_ami.fetch(self.out)
        self.assertEqual(len(paks), 1)
        self.assertEqual(self.urlopen_calls, [])

    def test_ami_dist_invalid_exits(self):
        os.environ["AMI_DIST"] = os.path.join(self.tmp.name, "nothing")
        with self.assertRaises(SystemExit):
            fetch_ami.fetch(self.out)


class ArgsTest(unittest.TestCase):
    def test_help_does_not_fetch(self):
        for arg in ("-h", "--help"):
            with mock.patch.object(fetch_ami, "fetch") as f, mock.patch("builtins.print"):
                fetch_ami.main([arg])
                f.assert_not_called()

    def test_unknown_option_does_not_fetch(self):
        for argv in ([], ["--dry-run"], ["a", "b"]):
            with mock.patch.object(fetch_ami, "fetch") as f, self.assertRaises(SystemExit):
                fetch_ami.main(argv)
            f.assert_not_called()


if __name__ == "__main__":
    unittest.main()
