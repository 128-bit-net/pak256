"""game.py の検査（ゲームは起動しない）。python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import game  # noqa: E402


def put(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


class GameToolTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.root = os.path.join(t, "root")
        self.build = os.path.join(self.root, "build")
        put(os.path.join(self.root, "LICENSE.md"), "CC BY-SA 4.0")
        put(os.path.join(self.root, "CREDITS.md"), "表")
        put(os.path.join(self.root, "LICENSES", "A.txt"))
        put(os.path.join(self.root, "config", "simuconf.tab"), "a = 1\n")
        put(os.path.join(self.root, "text", "ja.tab"))
        put(os.path.join(self.build, "pak", "own.one.pak"))
        self.env = os.path.join(t, "env")
        put(os.path.join(self.env, game.EXE), "exe")
        put(os.path.join(self.env, "z.dll"))
        put(os.path.join(self.env, "settings.xml"), "送信用")
        put(os.path.join(self.env, "config", "simuconf.tab"), "base = 1")
        put(os.path.join(self.env, "themes", "t.tab"))
        put(os.path.join(self.env, "pak128", "big.pak"))
        put(os.path.join(self.env, "save", "map.sve"))
        put(os.path.join(self.env, "save", "other.sve"))
        self.work = os.path.join(t, "work")

    def tearDown(self):
        self.tmp.cleanup()

    def prepare(self, **kw):
        return game.prepare_workdir(self.env, self.work, "map", root=self.root, build=self.build, **kw)

    def read(self, *p):
        with open(os.path.join(self.work, *p), encoding="utf-8", newline="") as f:
            return f.read()

    def test_copies_only_what_is_needed(self):
        placed = self.prepare()
        self.assertEqual(sorted(placed), ["config/simuconf.tab", "own.one.pak", "text/ja.tab"])
        for rel in (game.EXE, "z.dll", "themes/t.tab", "save/map.sve", "pak/own.one.pak", "pak/text/ja.tab"):
            self.assertTrue(os.path.isfile(os.path.join(self.work, *rel.split("/"))), rel)
        for rel in ("settings.xml", "pak128", "save/other.sve", "pak/LICENSE.md"):
            self.assertFalse(os.path.exists(os.path.join(self.work, *rel.split("/"))), rel)

    def test_day_night_off_in_both_simuconf(self):
        self.prepare()
        self.assertEqual(self.read("config", "simuconf.tab"), "base = 1\n\nday_night_shift = 0\n")
        self.assertEqual(self.read("pak", "config", "simuconf.tab"), "a = 1\n\nday_night_shift = 0\n")

    def test_night_leaves_simuconf(self):
        self.prepare(night=True)
        self.assertEqual(self.read("config", "simuconf.tab"), "base = 1")
        self.assertEqual(self.read("pak", "config", "simuconf.tab"), "a = 1\n")

    def test_append_is_idempotent_and_keeps_crlf(self):
        p = os.path.join(self.tmp.name, "s.tab")
        put(p, "a = 1\r\n")
        game.append_day_night_off(p)
        game.append_day_night_off(p)
        with open(p, encoding="utf-8", newline="") as f:
            self.assertEqual(f.read(), "a = 1\r\n\r\nday_night_shift = 0\r\n")

    def test_append_creates_missing_file(self):
        p = os.path.join(self.tmp.name, "sub", "s.tab")
        game.append_day_night_off(p)
        with open(p, encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), "day_night_shift = 0")

    def test_rebuilds_existing_workdir(self):
        put(os.path.join(self.work, "old.txt"))
        self.prepare()
        self.assertFalse(os.path.exists(os.path.join(self.work, "old.txt")))

    def test_extra_pak_is_borrowed(self):
        src = os.path.join(self.tmp.name, "borrow", "road.depot.pak")
        put(src)
        self.assertIn("road.depot.pak", self.prepare(extra_paks=[src]))
        self.assertTrue(os.path.isfile(os.path.join(self.work, "pak", "road.depot.pak")))

    def test_missing_save_or_exe(self):
        with self.assertRaises(RuntimeError):
            game.prepare_workdir(self.env, self.work, "nothing", root=self.root, build=self.build)
        with self.assertRaises(RuntimeError):
            game.prepare_workdir(self.env, self.work, "map", exe="no.exe", root=self.root, build=self.build)

    def test_launch_command(self):
        cmd = game.launch_command("W", "map", 47880)
        for flag in ("-singleuser", "-set_workdir", "-lang", "-load", "-mcp-port", "-objects"):
            self.assertIn(flag, cmd)
        self.assertEqual(cmd[cmd.index("-lang") + 1], "ja")
        self.assertEqual(cmd[cmd.index("-objects") + 1], "pak/")
        self.assertEqual(cmd[cmd.index("-mcp-port") + 1], "47880")
        self.assertEqual(cmd[cmd.index("-set_workdir") + 1], "W")

    def test_port_range(self):
        game.check_port(47880)
        game.check_port(47899)
        for p in (47800, 47900):
            with self.assertRaises(RuntimeError):
                game.check_port(p)


if __name__ == "__main__":
    unittest.main()
