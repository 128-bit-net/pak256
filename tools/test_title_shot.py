"""title_shot.py の検査（ゲームは起動しない。窓も読まない）。python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import contextlib
import io
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import game  # noqa: E402
import title_shot  # noqa: E402


def put(path, text="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


class Proc:
    pid = 123

    def __init__(self, code=None):
        self.returncode = code

    def poll(self):
        return self.returncode


class TitleShotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.env, self.root, self.work = (os.path.join(t, n) for n in ("env", "root", "work"))
        for rel in (game.EXE, "z.dll", "themes/t.tab", "config/simuconf.tab", "save/a.sve", "settings.xml"):
            put(os.path.join(self.env, rel))
        put(os.path.join(self.root, "demo", "demo.sve"), "demo")
        put(os.path.join(self.root, "build", "pak", "own.one.pak"))
        self.log = os.path.join(t, "game.log")
        put(self.log, "Message: Show banner")

    def tearDown(self):
        self.tmp.cleanup()

    def test_prepare_has_no_save_and_no_settings(self):
        title_shot.prepare(self.env, self.work, root=self.root)
        for rel in (game.EXE, "z.dll", "themes/t.tab", "config/simuconf.tab", "pak256/own.one.pak", "pak256/demo.sve"):
            self.assertTrue(os.path.isfile(os.path.join(self.work, rel)), rel)
        for rel in ("save", "settings.xml"):
            self.assertFalse(os.path.exists(os.path.join(self.work, rel)), rel)

    def test_prepare_refuses_other_folder(self):
        put(os.path.join(self.work, "mine.txt"))
        with self.assertRaises(RuntimeError):
            title_shot.prepare(self.env, self.work, root=self.root)
        self.assertTrue(os.path.isfile(os.path.join(self.work, "mine.txt")))

    def test_command_takes_the_no_save_path(self):
        cmd = title_shot.command(self.work)
        self.assertNotIn("-load", cmd)
        self.assertNotIn("-mcp-port", cmd)
        self.assertIn("pak256/", cmd)
        self.assertIn("-singleuser", cmd)

    def shoot(self, proc, results):
        calls = []

        def capture(pid, out):
            calls.append(pid)
            return results[len(calls) - 1]

        with contextlib.redirect_stdout(io.StringIO()):
            title_shot.shoot(proc, capture, self.log, "o.png", retries=len(results), sleep=lambda s: None)
        return len(calls)

    def test_retries_until_not_black(self):
        self.assertEqual(self.shoot(Proc(), [False, False, True]), 3)
        with self.assertRaises(RuntimeError):
            self.shoot(Proc(), [False, False])

    def test_stops_when_game_ended_or_fatal(self):
        with self.assertRaises(RuntimeError):
            self.shoot(Proc(1), [True])
        put(self.log, "x\nFATAL ERROR: boom\n")
        with self.assertRaises(game.GameFatalError):
            self.shoot(Proc(), [True])

    def test_output_inside_work_is_refused(self):
        with self.assertRaises(RuntimeError):
            title_shot.title_shot(self.env, os.path.join(self.work, "a.png"), self.work, root=self.root)

    def test_closes_game_and_removes_work_on_failure(self):
        proc = mock.Mock(pid=123)
        proc.poll.return_value = None
        with mock.patch.object(title_shot.subprocess, "Popen", return_value=proc), \
                mock.patch.object(title_shot.game, "JobObject"), \
                mock.patch.object(title_shot.game, "alive", return_value=False), \
                mock.patch.object(title_shot, "shoot", side_effect=RuntimeError("黒いまま")), \
                contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(RuntimeError):
                title_shot.title_shot(self.env, os.path.join(self.tmp.name, "a.png"), self.work, root=self.root)
        proc.kill.assert_called_once()
        self.assertFalse(os.path.exists(self.work))


if __name__ == "__main__":
    unittest.main()
