"""game.py の検査（ゲームは起動しない）。python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import game  # noqa: E402


def put(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


class Base(unittest.TestCase):
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



class GameToolTest(Base):
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
        self.assertEqual(cmd[cmd.index("-load") + 1], "map")
        for flag in ("-freeplay", "-mute", "-screensize"):
            self.assertIn(flag, cmd)

    def test_port_range(self):
        game.check_port(47880)
        game.check_port(47899)
        for p in (47800, 47900):
            with self.assertRaises(RuntimeError):
                game.check_port(p)


SLEEPER = [sys.executable, "-c", "import time; time.sleep(60)"]


class LifecycleTest(Base):
    """ゲームの代わりに眠るだけのプロセスを起動して、閉じ方と片付けを見る（本物のゲームは起動しない）。"""

    def make(self, **kw):
        g = game.Game(self.env, "map", 47880, work=self.work, client=__file__, root=self.root, build=self.build, **kw)
        return g

    def patches(self, sq):
        return (mock.patch.object(game, "launch_command", lambda *a, **k: SLEEPER),
                mock.patch.object(game, "port_in_use", lambda p: False),
                mock.patch.object(game.Game, "sq", sq),
                mock.patch.object(game.Game, "alive_mcp", lambda self_: False),
                mock.patch.object(game.time, "sleep", lambda s: None))

    def run_with(self, sq, **kw):
        g = self.make(**kw)
        ps = self.patches(sq)
        for p in ps:
            p.start()
        self.addCleanup(lambda: [p.stop() for p in ps])
        return g

    def test_normal_close_kills_pid_and_removes_workdir(self):
        g = self.run_with(lambda self_, code, timeout=30: "1")
        with g:
            pid = g.proc.pid
            self.assertTrue(game.alive(pid))
            self.assertTrue(os.path.isdir(self.work))
        self.assertFalse(game.alive(pid))
        self.assertFalse(os.path.exists(self.work))
        self.assertFalse(g.left_over)

    def test_keep_leaves_workdir(self):
        g = self.run_with(lambda self_, code, timeout=30: "1", keep=True)
        with g:
            pass
        self.assertTrue(os.path.isdir(self.work))

    def test_failed_start_still_closes_game(self):
        def never(self_, code, timeout=30):
            raise RuntimeError("no answer")
        g = self.run_with(never)
        pids = []
        orig = game.subprocess.Popen

        def spy(*a, **k):
            p = orig(*a, **k)
            if a and a[0] == SLEEPER:
                pids.append(p.pid)
            return p
        with mock.patch.object(game.subprocess, "Popen", spy), mock.patch.object(game.time, "monotonic", mock.Mock(side_effect=[0, 0, 1, 999])):
            with self.assertRaises(RuntimeError):
                with g:
                    pass
        self.assertEqual(len(pids), 1)
        self.assertFalse(game.alive(pids[0]))
        self.assertFalse(os.path.exists(self.work))

    def test_busy_port_does_not_touch_foreign_workdir(self):
        put(os.path.join(self.work, "theirs.txt"))
        g = self.make()
        with mock.patch.object(game, "port_in_use", lambda p: True):
            with self.assertRaises(RuntimeError):
                with g:
                    pass
        self.assertTrue(os.path.isfile(os.path.join(self.work, "theirs.txt")))

    def test_failed_start_message_has_log_tail(self):
        g = self.make()
        with mock.patch.object(game, "launch_command", lambda *a, **k: [sys.executable, "-c", "print('boom')"]),                 mock.patch.object(game, "port_in_use", lambda p: False),                 mock.patch.object(game.Game, "alive_mcp", lambda self_: False),                 mock.patch.object(game.Game, "sq", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x"))):
            with self.assertRaises(RuntimeError) as cm:
                with g:
                    pass
        self.assertIn("boom", str(cm.exception))

    def test_left_over_pid_is_reported_and_workdir_kept(self):
        g = self.run_with(lambda self_, code, timeout=30: "1")
        with mock.patch.object(game, "alive", lambda pid: True):
            with g:
                pass
        self.assertTrue(g.left_over)
        self.assertTrue(os.path.isdir(self.work))
        g.proc = None
        # 後始末（テストのゲームの代わりのプロセスは stop で閉じてある）

    def test_port_in_use_sees_listener(self):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.bind(("127.0.0.1", 0))
            srv.listen(1)
            self.assertTrue(game.port_in_use(srv.getsockname()[1]))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.bind(("127.0.0.1", 0))
            free = srv.getsockname()[1]
        self.assertFalse(game.port_in_use(free))

    def test_foreign_workdir_untouched_when_port_free(self):
        put(os.path.join(self.work, "theirs.txt"))
        g = self.run_with(lambda self_, code, timeout=30: "1")
        with self.assertRaises(RuntimeError):
            with g:
                pass
        self.assertTrue(os.path.isfile(os.path.join(self.work, "theirs.txt")))

    def test_keep_then_reuse(self):
        g = self.run_with(lambda self_, code, timeout=30: "1", keep=True)
        with g:
            pass
        g2 = self.make()
        with g2:
            pass  # 目印のある作業フォルダは作り直せる（例外にならない）

    def test_check_work_rejects_repo(self):
        with self.assertRaises(RuntimeError):
            game.check_work(self.root, self.env, self.root)
        with self.assertRaises(RuntimeError):
            game.check_work(os.path.dirname(self.root), self.env, self.root)

    def test_check_work_rejects_overlap_and_foreign(self):
        with self.assertRaises(RuntimeError):
            game.check_work(self.env, self.env, self.root)
        with self.assertRaises(RuntimeError):
            game.check_work(os.path.dirname(self.env), self.env, self.root)
        with self.assertRaises(RuntimeError):
            game.check_work(os.path.join(self.env, "sub"), self.env, self.root)
        put(os.path.join(self.work, "x.txt"))
        with self.assertRaises(RuntimeError):
            game.check_work(self.work, self.env, self.root)
        game.check_work(os.path.join(self.tmp.name, "fresh"), self.env, self.root)


if __name__ == "__main__":
    unittest.main()
