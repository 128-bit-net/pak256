"""install_local.py と game.install_pak の検査（ゲームは起動しない）。python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import game  # noqa: E402
import install_local  # noqa: E402
import package  # noqa: E402


def put(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


class InstallLocalTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        # LICENSE.md・CREDITS.md・LICENSES/ が無い root でも入れられる（配布用の検査から切り離してある）
        self.root = os.path.join(t, "root")
        self.build = os.path.join(self.root, "build")
        put(os.path.join(self.root, "config", "simuconf.tab"), "a = 1\n")
        put(os.path.join(self.root, "config", ".gitkeep"), "")
        put(os.path.join(self.root, "text", "ja.tab"))
        put(os.path.join(self.build, "pak", "own.one.pak"), "new")
        self.dest = os.path.join(t, "play")
        put(os.path.join(self.dest, game.EXE), "exe")
        put(os.path.join(self.dest, "settings.xml"), "設定")
        put(os.path.join(self.dest, "save", "a.sve"), "save")

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, **kw):
        return install_local.install_local(self.dest, root=self.root, build=self.build, **kw)

    def exists(self, *p):
        return os.path.exists(os.path.join(self.dest, *p))

    def read(self, *p):
        with open(os.path.join(self.dest, *p), encoding="utf-8", newline="") as f:
            return f.read()

    def make_zip(self, names, path=None):
        path = path or os.path.join(self.tmp.name, "r.zip")
        with zipfile.ZipFile(path, "w") as z:
            for n in names:
                z.writestr(n, "z:" + n)
        return path

    def test_installs_into_pak256_and_leaves_user_files(self):
        placed = self.install()
        self.assertEqual(sorted(placed), ["config/simuconf.tab", "own.one.pak", "text/ja.tab"])
        for rel in ("own.one.pak", "config/simuconf.tab", "text/ja.tab"):
            self.assertTrue(self.exists("pak256", *rel.split("/")), rel)
        self.assertFalse(self.exists("pak256", "config", ".gitkeep"))
        self.assertEqual(self.read("settings.xml"), "設定")
        self.assertEqual(self.read("save", "a.sve"), "save")

    def test_play_bat_created_once_and_not_overwritten(self):
        self.install()
        text = self.read("play.bat")
        self.assertIn("-singleuser -objects pak256/", text)
        self.assertIn(game.EXE, text)
        self.assertIn("\r\n", text)
        put(os.path.join(self.dest, "play.bat"), "mine")
        self.install()
        self.assertEqual(self.read("play.bat"), "mine")

    def test_no_play_bat(self):
        self.install(make_bat=False)
        self.assertFalse(self.exists("play.bat"))

    def test_reinstall_replaces_old_files_only(self):
        put(os.path.join(self.dest, "pak256", "old.pak"))
        put(os.path.join(self.dest, "pak256", "text", "old.tab"))
        put(os.path.join(self.dest, "pak256", "memo.txt"), "残す")
        self.install()
        self.assertFalse(self.exists("pak256", "old.pak"))
        self.assertFalse(self.exists("pak256", "text", "old.tab"))
        self.assertEqual(self.read("pak256", "memo.txt"), "残す")
        self.assertEqual(self.read("pak256", "own.one.pak"), "new")

    def test_failure_keeps_existing_install(self):
        put(os.path.join(self.dest, "pak256", "old.pak"))
        os.remove(os.path.join(self.build, "pak", "own.one.pak"))
        with self.assertRaises(SystemExit):
            self.install()
        self.assertTrue(self.exists("pak256", "old.pak"))

    def test_dest_must_be_game_folder(self):
        with self.assertRaises(RuntimeError):
            install_local.install_local(os.path.join(self.tmp.name, "none"), root=self.root, build=self.build)
        os.remove(os.path.join(self.dest, game.EXE))
        with self.assertRaises(RuntimeError):
            self.install()

    def test_dest_inside_repo_is_rejected(self):
        inside = os.path.join(self.root, "inside")
        put(os.path.join(inside, game.EXE))
        with self.assertRaises(RuntimeError):
            install_local.install_local(inside, root=self.root, build=self.build)

    def test_zip_with_top_folder(self):
        z = self.make_zip(["pak256/a.pak", "pak256/config/simuconf.tab", "pak256/text/ja.tab",
                           "pak256/LICENSE.md", "pak256/LICENSES/A.txt", "pak256/ami_license.txt", "pak256/sub/b.pak"])
        placed = self.install(zip_path=z)
        self.assertEqual(sorted(placed), ["a.pak", "config/simuconf.tab", "text/ja.tab"])
        self.assertEqual(self.read("pak256", "a.pak"), "z:pak256/a.pak")
        self.assertFalse(self.exists("pak256", "LICENSE.md"))
        self.assertFalse(self.exists("pak256", "own.one.pak"))  # 手元の build の物は入れない

    def test_zip_without_top_folder(self):
        z = self.make_zip(["a.pak", "config/simuconf.tab"])
        self.assertEqual(sorted(self.install(zip_path=z)), ["a.pak", "config/simuconf.tab"])

    def test_zip_without_pak_stops_and_keeps_install(self):
        put(os.path.join(self.dest, "pak256", "old.pak"))
        z = self.make_zip(["pak256/config/simuconf.tab"])
        with self.assertRaises(RuntimeError):
            self.install(zip_path=z)
        self.assertTrue(self.exists("pak256", "old.pak"))

    def test_zip_unsafe_names_stop(self):
        for bad in ("pak256/../evil.pak", "/abs.pak", "C:/x.pak"):
            z = self.make_zip(["pak256/a.pak", bad])
            with self.assertRaises(RuntimeError, msg=bad):
                self.install(zip_path=z)
        self.assertFalse(self.exists("evil.pak"))

    def test_package_zip_roundtrip(self):
        # package.py が作る zip の形（pak256/ 始まり）をそのまま入れられる
        put(os.path.join(self.root, "LICENSE.md"), "CC BY-SA 4.0")
        put(os.path.join(self.root, "CREDITS.md"), "表")
        put(os.path.join(self.root, "LICENSES", "A.txt"))
        names = [a for a, _ in package.collect(self.root, self.build)]
        self.assertIn("pak256/LICENSE.md", names)
        z = self.make_zip(names)
        self.assertEqual(sorted(self.install(zip_path=z)), ["config/simuconf.tab", "own.one.pak", "text/ja.tab"])

    def test_install_pak_extra_still_works(self):
        src = os.path.join(self.tmp.name, "b", "road.pak")
        put(src)
        out = os.path.join(self.tmp.name, "out")
        placed = game.install_pak(out, root=self.root, build=self.build, extra=[src])
        self.assertIn("road.pak", placed)


if __name__ == "__main__":
    unittest.main()
