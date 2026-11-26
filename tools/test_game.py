"""game.py の検査（ゲームは起動しない）。python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import os
import sys
import subprocess
import tempfile
import threading
import time
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

    def test_simuconf_extra_goes_before_existing_lines_in_both_files(self):
        # 本体は同じキーを先に書いた行から取るので、足した行はファイルの先頭に来る
        put(os.path.join(self.env, "config", "simuconf.tab"), "show_names = 3\r\n")
        self.prepare(simuconf_extra=["show_names = 0", "tile_height = 8"])
        self.assertEqual(self.read("config", "simuconf.tab"),
                         "show_names = 0\r\ntile_height = 8\r\nshow_names = 3\r\n\r\nday_night_shift = 0\r\n")
        self.assertEqual(self.read("pak", "config", "simuconf.tab"),
                         "show_names = 0\ntile_height = 8\na = 1\n\nday_night_shift = 0\n")

    def test_simuconf_extra_applies_at_night(self):
        self.prepare(night=True, simuconf_extra=("show_names = 0",))
        self.assertEqual(self.read("config", "simuconf.tab"), "show_names = 0\nbase = 1")
        self.assertEqual(self.read("pak", "config", "simuconf.tab"), "show_names = 0\na = 1\n")

    def test_rebuilt_workdir_starts_from_fresh_simuconf(self):
        self.prepare(night=True, simuconf_extra=["show_names = 0"])
        self.prepare(night=True, simuconf_extra=["show_names = 0"])
        self.assertEqual(self.read("pak", "config", "simuconf.tab"), "show_names = 0\na = 1\n")

    def test_prepend_creates_missing_file(self):
        p = os.path.join(self.tmp.name, "sub", "s.tab")
        game.prepend_lines(p, ["show_names = 0"])
        with open(p, encoding="utf-8") as f:
            self.assertEqual(f.read(), "show_names = 0\n")

    def test_simuconf_extra_rejects_bad_lines_before_touching_workdir(self):
        put(os.path.join(self.work, "old.txt"))
        for bad in ("show_names = 0", ["show_names"], ["a = 1\nb = 2"], ["# a = 1"], ["= 1"], ["-"], [1]):
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.prepare(simuconf_extra=bad)
            with self.assertRaises(ValueError, msg=repr(bad)):
                game.Game("e", "m", 47880, work="w", client=__file__, simuconf_extra=bad)
        self.assertTrue(os.path.isfile(os.path.join(self.work, "old.txt")))

    def test_game_passes_simuconf_extra_to_prepare(self):
        g = game.Game(self.env, "map", 47880, work=self.work, client=__file__, root=self.root, build=self.build,
                      simuconf_extra=["show_names = 0"])
        with mock.patch.object(game, "port_in_use", lambda p: False), \
                mock.patch.object(game.Game, "alive_mcp", lambda self_: False), \
                mock.patch.object(game.subprocess, "Popen", side_effect=OSError("起動しない")):
            with self.assertRaises(OSError):
                g.start()
        self.assertTrue(self.read("pak", "config", "simuconf.tab").startswith("show_names = 0\n"))
        g.stop()

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
        with mock.patch.dict(os.environ):
            os.environ.pop(game.PORT_RANGE_ENV, None)
            game.check_port(47880)
            game.check_port(47999)
            game.check_port(47800)
            self.assertEqual((game.PORT_MIN, game.PORT_MAX), (47800, 47999))
            for p in (47799, 48000, 47200):
                with self.assertRaises(RuntimeError):
                    game.check_port(p)

    def test_port_range_from_argument(self):
        with mock.patch.dict(os.environ, {game.PORT_RANGE_ENV: "47500-47599"}):  # 引数が環境変数より先
            for port_range in ("47200-47299", (47200, 47299)):
                game.check_port(47200, port_range)
                game.check_port(47299, port_range)
                for p in (47199, 47300, 47500):
                    with self.assertRaises(RuntimeError):
                        game.check_port(p, port_range)
            game.Game("e", "m", 47200, work="w", client=__file__, port_range="47200-47299")

    def test_port_range_from_environment(self):
        with mock.patch.dict(os.environ, {game.PORT_RANGE_ENV: "47200-47299"}):
            game.Game("e", "m", 47250, work="w", client=__file__)  # port_range を渡さない道具からも効く
            with self.assertRaises(RuntimeError):
                game.check_port(47880)

    def test_port_range_follows_patched_defaults(self):
        # スクリプトで PORT_MIN・PORT_MAX を差し替えて使っている物（#128 より前の書き方）も効く
        with mock.patch.dict(os.environ, {game.PORT_RANGE_ENV: ""}), \
                mock.patch.object(game, "PORT_MIN", 47200), mock.patch.object(game, "PORT_MAX", 47299):
            game.check_port(47200)

    def test_bad_port_range(self):
        for bad in ("47200", "47200-", "a-b", "47299-47200", "0-10", "47200-70000", "1-2-3", (47200,), 47200):
            with self.assertRaises(RuntimeError, msg=repr(bad)):
                game.check_port(47200, bad)
        with mock.patch.dict(os.environ, {game.PORT_RANGE_ENV: "oops"}):
            with self.assertRaisesRegex(RuntimeError, game.PORT_RANGE_ENV):
                game.check_port(47880)


SLEEPER = [sys.executable, "-c", "import time; time.sleep(60)"]


class WorkDirTest(Base):
    """リポジトリの直下に work/ が無い状態（作ったばかりの worktree）。#119。"""

    def default_work(self):
        self.assertFalse(os.path.exists(os.path.join(self.root, "work")))
        return game.default_work(47880, self.root)

    def test_creates_missing_work_parents(self):
        work = self.default_work()
        game.prepare_workdir(self.env, work, "map", root=self.root, build=self.build)
        self.assertTrue(os.path.isfile(os.path.join(work, game.MARK)))

    def test_fails_when_work_cannot_be_made(self):
        work = self.default_work()
        put(os.path.join(self.root, "work"), "フォルダでなくファイル")
        g = game.Game(self.env, "map", 47880, work=work, client=__file__, root=self.root, build=self.build)
        with mock.patch.object(game, "port_in_use", lambda p: False), \
                mock.patch.object(game.Game, "alive_mcp", lambda self_: False), \
                mock.patch.object(game.subprocess, "Popen") as popen:
            with self.assertRaises(OSError):  # コマンドからは例外のまま終わる（終了コードは 0 でない）
                with g:
                    pass
        popen.assert_not_called()


@unittest.skipUnless(os.name == "nt", "taskkill・tasklist が要る（Windows だけ。CI は Linux なので飛ばす）")
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

    @unittest.skipUnless(os.name == "nt", "Job Object は Windows だけ")
    def test_game_process_is_in_job_and_job_closed_on_stop(self):
        g = self.run_with(lambda self_, code, timeout=30: "1")
        assigned = []
        orig = game.JobObject.assign

        def spy(job, proc):
            ok = orig(job, proc)
            assigned.append((proc.pid, ok))
            return ok
        with mock.patch.object(game.JobObject, "assign", spy):
            with g:
                self.assertIsNotNone(g.job.handle)
                self.assertEqual(assigned, [(g.proc.pid, True)])  # 起動したゲームのプロセスが Job に入った
        self.assertIsNone(g.job)

    def test_job_failure_does_not_stop_the_game(self):
        g = self.run_with(lambda self_, code, timeout=30: "1")
        with mock.patch.object(game, "JobObject", side_effect=OSError("no job")):
            with g:
                self.assertIsNone(g.job)
                self.assertTrue(game.alive(g.proc.pid))
        self.assertFalse(os.path.exists(self.work))

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


class FatalLogTest(Base):
    """game.log の FATAL ERROR を見つける（#132）。ゲームは起動しない。"""

    def game(self):
        g = game.Game("e", "m", 47880, work=self.work, client=__file__)
        g.proc = object()  # 起動したことにする（fatal() は中身を使わない）
        patch = mock.patch.object(game, "FATAL_FLUSH", 0)
        patch.start()
        self.addCleanup(patch.stop)
        return g

    def log(self, text, mode="a"):
        os.makedirs(self.work, exist_ok=True)
        with open(os.path.join(self.work, "game.log"), mode, encoding="utf-8", newline="") as f:
            f.write(text)

    def test_no_log_or_no_fatal(self):
        g = self.game()
        self.assertIsNone(g.fatal())
        self.log("Warning: something\nERROR: not fatal\n")
        self.assertIsNone(g.fatal())
        g.check_fatal()

    def test_finds_fatal_appended_later_even_split(self):
        g = self.game()
        self.log("x" * 100 + "\nFATAL ER")
        self.assertIsNone(g.fatal())
        self.log("ROR: karte_t::load() - No road found at all!\nAborting program execution ...\n")
        message = g.fatal()
        self.assertTrue(message.startswith("FATAL ERROR: karte_t::load() - No road found at all!"), message)
        with self.assertRaises(game.GameFatalError) as cm:
            g.check_fatal()
        self.assertIn("No road found at all!", str(cm.exception))

    def test_loadsave_form(self):
        g = self.game()
        self.log('FATAL ERROR during reading of "a.sve"\n')
        self.assertIsNotNone(g.fatal())

    def test_old_log_is_ignored_before_start(self):
        g = self.game()
        g.proc = None  # 起動の前（--keep で残った前の回の game.log）
        self.log("FATAL ERROR: old\n")
        self.assertIsNone(g.fatal())

    def test_remembered_after_close_and_sends_nothing(self):
        g = self.game()
        self.log("FATAL ERROR: x - y\n")
        self.assertIsNotNone(g.fatal())
        with mock.patch.object(game.subprocess, "Popen", side_effect=AssertionError("送ってはいけない")):
            with self.assertRaises(game.GameFatalError):
                g.sq("return 1")

    def test_client_wait_is_cut_by_fatal(self):
        # 答えないクライアントを待つ間に FATAL が出たら、timeout を待たずに失敗する
        client = os.path.join(self.tmp.name, "slow.py")
        put(client, "import time\ntime.sleep(60)\n")
        g = self.game()
        g.client = client
        self.log("")
        timer = threading.Timer(1, self.log, args=("FATAL ERROR: x - y\n",))
        timer.start()
        self.addCleanup(timer.cancel)
        start = time.monotonic()
        with self.assertRaises(game.GameFatalError):
            g.sq("return 1", timeout=40)
        self.assertLess(time.monotonic() - start, 15)


class FatalMainTest(unittest.TestCase):
    """コマンドとしての main() が、エラーの文を出して 0 以外で終わる（#132）。ゲームは偽物（CI でも回る）。"""

    class Fake:
        left_over = False
        work = "w"

        def __init__(self, *a, **k):
            self.closed = False
            FatalMainTest.last = self

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.closed = True

        def check_fatal(self):
            raise game.GameFatalError("FATAL ERROR: x - at the end")

    def run_main(self, cls):
        argv = ["game.py", "--env", "e", "--save", "m", "--port", "47880"]
        with mock.patch.object(game, "Game", cls), mock.patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit) as cm:
                game.main()
        return cm.exception.code  # 文字列の code は、stderr に出して終了コード 1

    def test_fatal_while_starting(self):
        class FailsToStart(self.Fake):
            def __enter__(self):
                raise game.GameFatalError("FATAL ERROR: x - at start")
        self.assertIn("FATAL ERROR: x - at start", self.run_main(FailsToStart))

    def test_fatal_after_last_command_is_not_success(self):
        self.assertIn("FATAL ERROR: x - at the end", self.run_main(self.Fake))
        self.assertTrue(self.last.closed)


@unittest.skipUnless(os.name == "nt", "taskkill・tasklist が要る（Windows だけ。CI は Linux なので飛ばす）")
class FatalStartTest(Base):
    """FATAL ERROR を出して眠る偽のゲームを起動して、待たずに閉じることを見る（#132）。"""

    def test_start_fails_fast_closes_and_cleans(self):
        fake = [sys.executable, "-c",
                "import sys, time; print('FATAL ERROR: x - No road found at all!', file=sys.stderr, flush=True); time.sleep(60)"]
        g = game.Game(self.env, "map", 47880, work=self.work, client=__file__, root=self.root, build=self.build)
        pids = []
        orig = game.subprocess.Popen

        def spy(*a, **k):
            p = orig(*a, **k)
            if a and a[0] == fake:
                pids.append(p.pid)
            return p
        start = time.monotonic()
        with mock.patch.object(game, "launch_command", lambda *a, **k: fake), \
                mock.patch.object(game, "port_in_use", lambda p: False), \
                mock.patch.object(game.Game, "alive_mcp", lambda self_: False), \
                mock.patch.object(game.subprocess, "Popen", spy):
            with self.assertRaises(game.GameFatalError) as cm:
                with g:
                    pass
        self.assertLess(time.monotonic() - start, 30)
        self.assertIn("No road found at all!", str(cm.exception))
        self.assertEqual(len(pids), 1)
        self.assertFalse(game.alive(pids[0]))
        self.assertFalse(os.path.exists(self.work))


class SquirrelCheckTest(unittest.TestCase):
    """run_squirrel に渡す文字列の検査（#59）。"""

    def test_newline_in_string_literal_is_rejected(self):
        with self.assertRaises(ValueError):
            game.check_squirrel('return "a\nb"')  # Python の "\n" は本物の改行になる
        with self.assertRaises(ValueError):
            game.check_squirrel('return "a\r\nb"')

    def test_error_names_the_line(self):
        with self.assertRaises(ValueError) as cm:
            game.check_squirrel('local a = 1;\nlocal b = "x\ny";')
        self.assertIn("2 行目", str(cm.exception))

    def test_multiline_code_and_escapes_are_fine(self):
        game.check_squirrel("local a = 1;\nlocal b = 2;\nreturn a + b")
        game.check_squirrel(r'return "a\nb"')  # 書いた通りの \n（Squirrel の改行の記号）は通る
        game.check_squirrel(r'return "a\"" + "b"')  # 引用符のエスケープ
        game.check_squirrel('// "コメントの引用符\nreturn 1')
        game.check_squirrel('/* " \n " */ return 1')
        game.check_squirrel('return @"a\nb"')  # 逐語の文字列は改行を許す
        game.check_squirrel('local q = \'"\';\nlocal s = "x";')  # 文字リテラル '"'
        game.check_squirrel("local q = '\\'';\nlocal s = \"x\";")  # エスケープした文字リテラル
        game.check_squirrel('# "注釈の引用符\nreturn 1')
        with self.assertRaises(ValueError):  # 文字リテラルの後でも、文字列の改行は弾く
            game.check_squirrel('local q = \'"\';\nreturn "a\nb"')

    def test_sq_stops_before_sending(self):
        g = game.Game("e", "m", 47880, work="w", client=__file__)
        with mock.patch.object(game.Game, "_client", side_effect=AssertionError("送ってはいけない")):
            with self.assertRaises(ValueError):
                g.sq('return "a\nb"')

    def test_sq_file_is_checked_too(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, "a.nut")
            put(p, 'return "x\ny"')
            g = game.Game("e", "m", 47880, work="w", client=__file__)
            with self.assertRaises(ValueError):
                g.sq_file(p)


class DialogSettleTest(unittest.TestCase):
    def game(self):
        g = game.Game("e", "m", 47880, work="w", client=__file__)
        g.sent = []
        patch = mock.patch.object(game.Game, "sq", lambda self_, code, timeout=30: g.sent.append(code) or "1")
        patch.start()
        self.addCleanup(patch.stop)
        return g

    def test_dialog_by_name_and_number(self):
        g = self.game()
        g.dialog("finances")
        g.dialog(15)
        g.dialog("list_factory")
        self.assertEqual(g.sent, ["return gui.open_dialog_tool(5)", "return gui.open_dialog_tool(15)",
                                  "return gui.open_dialog_tool(18)"])

    def test_dialog_numbers_match_docs(self):
        # 収入・編成一覧・産業一覧・貨物の窓（#41・#42・#59 で使った番号）
        self.assertEqual((game.DIALOGS["finances"], game.DIALOGS["list_convoi"], game.DIALOGS["list_goods"],
                          game.DIALOGS["list_factory"]), (5, 15, 17, 18))
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "game-check.md"), encoding="utf-8") as f:
            text = f.read()
        for name, nr in game.DIALOGS.items():
            self.assertIn(f"| {nr} | `{name}` |", text, name)

    def test_dialog_rejects_unknown(self):
        g = self.game()
        for bad in ("nothing", -1, None, True, 1.5):
            with self.assertRaises(ValueError, msg=repr(bad)):
                g.dialog(bad)
        self.assertEqual(g.sent, [])

    def test_settle_speeds_up_then_restores(self):
        g = self.game()
        with mock.patch.object(game.time, "sleep") as sl:
            g.settle(7)
        sl.assert_called_once_with(7)
        self.assertEqual(g.sent, ["debug.set_game_speed(64); return 1", "debug.set_game_speed(1); return 1"])

    def test_settle_restores_speed_when_interrupted(self):
        g = self.game()
        with mock.patch.object(game.time, "sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                g.settle(7)
        self.assertEqual(g.sent[-1], "debug.set_game_speed(1); return 1")


PARENT = """
import os, subprocess, sys, time
sys.path.insert(0, {tools!r})
import game
job = game.JobObject()
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
print(child.pid, job.assign(child), flush=True)
time.sleep(120)
"""


@unittest.skipUnless(os.name == "nt", "Job Object は Windows だけ")
class JobObjectTest(unittest.TestCase):
    def test_child_dies_when_parent_is_force_killed(self):
        tools = os.path.dirname(os.path.abspath(__file__))
        parent = subprocess.Popen([sys.executable, "-X", "utf8", "-c", PARENT.format(tools=tools)], stdout=subprocess.PIPE, text=True)
        try:
            pid, assigned = parent.stdout.readline().split()
            pid = int(pid)
            self.assertEqual(assigned, "True")
            self.assertTrue(game.alive(pid))
            parent.kill()  # TaskStop と同じ強制終了（with も finally も走らない）
            parent.wait(timeout=10)
            for _ in range(50):
                if not game.alive(pid):
                    break
                time.sleep(0.1)
            self.assertFalse(game.alive(pid), "親の強制終了の後も子が残った")
        finally:
            parent.kill()
            parent.stdout.close()
            if "pid" in locals() and game.alive(pid):
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)


class ClimateMonthTest(unittest.TestCase):
    """気候を塗る手と、月を進める手（#109）。ゲームは偽物。"""

    def game(self, months=()):
        g = game.Game("e", "m", 47880, work="w", client=__file__)
        g.sent = []
        rest = list(months)

        def sq(self_, code, timeout=30):
            g.sent.append(code)
            if code == "return world.get_time().month":
                return str(rest.pop(0) if len(rest) > 1 else rest[0])
            return "1"
        patch = mock.patch.object(game.Game, "sq", sq)
        patch.start()
        self.addCleanup(patch.stop)
        return g

    def speeds(self, g):
        return [c for c in g.sent if c.startswith("debug.set_game_speed")]

    def test_climate_paints_rectangle(self):
        g = self.game()
        g.climate(1, 2, 3, 4, "desert")
        g.climate(1, 2, 3, 4, 7, z=14)
        self.assertEqual(g.sent, [
            'return command_x(tool_set_climate).work(player_x(0), coord3d(1,2,0), coord3d(3,4,0), "1")',
            'return command_x(tool_set_climate).work(player_x(0), coord3d(1,2,14), coord3d(3,4,14), "7")'])
        for c in g.sent:
            game.check_squirrel(c)

    def test_climate_rejects_water_and_unknown(self):
        g = self.game()
        for bad in (0, 8, -1, "water", "snow", None, True, 1.0):
            with self.assertRaises(ValueError, msg=repr(bad)):
                g.climate(1, 1, 2, 2, bad)
        self.assertEqual(g.sent, [])

    def test_season_table(self):
        # 本体の month_to_season（1〜3 月 冬・4〜5 月 春・6〜9 月 夏・10〜11 月 秋・12 月 冬）
        self.assertEqual(game.MONTH_TO_SEASON, (2,) * 3 + (3,) * 2 + (0,) * 4 + (1,) * 2 + (2,))
        # 撮る月が、その季節（0 夏・1 秋・2 冬・3 春）に当たる
        for name, nr in (("summer", 0), ("autumn", 1), ("winter", 2), ("spring", 3)):
            self.assertEqual(game.MONTH_TO_SEASON[game.SEASON_MONTHS[name]], nr, name)

    def test_wait_month_advances_then_restores_speed(self):
        g = self.game([3, 4, 5, 6])
        with mock.patch.object(game.time, "sleep"):
            g.wait_month(6)
        self.assertEqual(self.speeds(g), ["debug.set_game_speed(64); return 1", "debug.set_game_speed(1); return 1"])
        self.assertEqual(g.sent[-1], "debug.set_game_speed(1); return 1")

    def test_wait_month_does_nothing_when_already_there(self):
        g = self.game([6])
        g.wait_month(6)
        self.assertEqual(self.speeds(g), [])

    def test_wait_month_restores_speed_on_timeout_and_interrupt(self):
        g = self.game([1])
        with mock.patch.object(game.time, "sleep"), mock.patch.object(game.time, "monotonic", side_effect=[0, 0, 999]):
            with self.assertRaises(RuntimeError):
                g.wait_month(6, timeout=10)
        self.assertEqual(g.sent[-1], "debug.set_game_speed(1); return 1")
        g.sent.clear()
        with mock.patch.object(game.time, "sleep", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                g.wait_month(6)
        self.assertEqual(g.sent[-1], "debug.set_game_speed(1); return 1")

    def test_wait_month_rejects_bad_month(self):
        g = self.game([1])
        for bad in (-1, 12, "6", None, True):
            with self.assertRaises(ValueError, msg=repr(bad)):
                g.wait_month(bad)
        self.assertEqual(g.sent, [])


class InboxTest(unittest.TestCase):
    """開いたままのゲームへ命令を流す入口（#85）。ゲームは偽物。"""

    class Fake:
        proc = None

        def __init__(self):
            self.calls = []

        def sq(self, code, timeout=30):
            self.calls.append(("sq", code))
            if code == "boom":
                raise RuntimeError("bad")
            return "r:" + code

        def capture(self, path):
            self.calls.append(("capture", path))

        def dialog(self, which):
            self.calls.append(("dialog", which))
            return "d"

        def settle(self, sec):
            self.calls.append(("settle", sec))

        def wait_month(self, month):
            self.calls.append(("month", month))

        fatal_message = None

        def fatal(self):
            return self.fatal_message

        def check_fatal(self):
            if self.fatal_message is not None:
                raise game.GameFatalError(self.fatal_message)

    def test_serve_stops_when_fatal_while_idle(self):
        g = self.Fake()
        g.fatal_message = "FATAL ERROR: x - idle"
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(game.GameFatalError):
                game.serve_inbox(g, os.path.join(t, "inbox"), 30, 0.01, lambda *_: None)

    def test_serve_writes_out_then_stops_when_command_hits_fatal(self):
        class Dies(self.Fake):
            def sq(self, code, timeout=30):
                self.fatal_message = "FATAL ERROR: x - during command"
                self.check_fatal()

        with tempfile.TemporaryDirectory() as t:
            inbox = os.path.join(t, "inbox")
            put(os.path.join(inbox, "1.cmd"), "return 1")
            put(os.path.join(inbox, "2.cmd"), "return 2")
            with mock.patch.object(game, "FATAL_SEND_WAIT", 0), self.assertRaises(game.GameFatalError):
                game.serve_inbox(Dies(), inbox, 30, 0.01, lambda *_: None)
            with open(os.path.join(inbox, "1.out"), encoding="utf-8") as f:
                out = f.read()
            self.assertTrue(out.startswith("error\n"))
            self.assertIn("during command", out)
            self.assertTrue(os.path.isfile(os.path.join(inbox, "2.cmd")))  # 次の命令は流さない

    def test_run_command(self):
        g = self.Fake()
        self.assertEqual(game.run_command(g, "return 1"), "r:return 1")
        game.run_command(g, "@capture a.png")
        game.run_command(g, "@dialog 5")
        game.run_command(g, "@dialog finances")
        game.run_command(g, "@settle")
        game.run_command(g, "@settle 3")
        self.assertEqual(g.calls[1:], [("capture", "a.png"), ("dialog", 5), ("dialog", "finances"),
                                       ("settle", 15), ("settle", 3)])
        with self.assertRaises(ValueError):
            game.run_command(g, "@nothing")
        with self.assertRaises(ValueError):
            game.run_command(g, "@capture")
        game.run_command(g, "@month 0")
        self.assertEqual(g.calls[-1], ("month", 0))
        with self.assertRaises(ValueError):
            game.run_command(g, "@month winter")

    def test_serve_and_send_round_trip(self):
        import threading
        with tempfile.TemporaryDirectory() as t:
            inbox = os.path.join(t, "inbox")
            g = self.Fake()
            th = threading.Thread(target=game.serve_inbox, args=(g, inbox, 30, 0.02, lambda *_: None))
            th.start()
            while not os.path.isdir(inbox):
                time.sleep(0.01)
            self.assertEqual(game.send_command(inbox, "return 1", 5), (True, "r:return 1"))
            ok, body = game.send_command(inbox, "boom", 5)
            self.assertFalse(ok)
            self.assertIn("RuntimeError: bad", body)
            self.assertEqual(game.send_command(inbox, "return 2", 5), (True, "r:return 2"))  # 失敗の後も続く
            self.assertEqual(game.send_command(inbox, "@quit", 5), (True, "bye"))
            th.join(5)
            self.assertFalse(th.is_alive())

    def test_idle_limit_stops(self):
        with tempfile.TemporaryDirectory() as t:
            game.serve_inbox(self.Fake(), os.path.join(t, "inbox"), 0.1, 0.02, lambda *_: None)

    def test_send_fails_fast_when_inbox_disappears(self):
        import shutil
        import threading
        with tempfile.TemporaryDirectory() as t:
            inbox = os.path.join(t, "inbox")
            os.makedirs(inbox)
            threading.Timer(0.3, shutil.rmtree, args=(inbox,)).start()
            start = time.monotonic()
            with self.assertRaises(RuntimeError):
                game.send_command(inbox, "return 1", 30)
            self.assertLess(time.monotonic() - start, 10)

    def test_withdrawn_command_does_not_crash_server(self):
        real_open = open
        calls = []

        def flaky(path, *a, **k):
            if str(path).endswith(".cmd") and not calls:
                calls.append(1)
                raise FileNotFoundError(path)
            return real_open(path, *a, **k)

        with tempfile.TemporaryDirectory() as t:
            inbox = os.path.join(t, "inbox")
            os.makedirs(inbox)
            put(os.path.join(inbox, "1.cmd"), "@quit")
            with mock.patch("builtins.open", flaky):
                game.serve_inbox(self.Fake(), inbox, 30, 0.01, lambda *_: None)
            self.assertTrue(os.path.isfile(os.path.join(inbox, "1.out")))

    def test_send_without_game_fails(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(RuntimeError):
                game.send_command(os.path.join(t, "inbox"), "return 1", 1)


if __name__ == "__main__":
    unittest.main()
