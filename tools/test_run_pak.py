"""--pak（入れる pak のフォルダ。#170）の検査。ゲームは起動しない。"""
import glob
import importlib.util
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import game  # noqa: E402
import tree_check  # noqa: E402
from test_game import Base, put  # noqa: E402

CHECK = os.path.join(HERE, "vehicle_check")
# ゲームを起動する道具。river_run.py は起動せず、game.py --interactive で開いたゲームへ流すだけ
LAUNCHERS = ("run", "rail_run", "rail_curve_run", "air_run", "monorail_run", "tram_run")
NO_LAUNCH = ("river_run",)
SCENES = ("sound_run",)  # --save・--out を受けず、--scene を受ける


class Stop(Exception):
    pass


def load(name):
    spec = importlib.util.spec_from_file_location(f"vehicle_check_{name}", os.path.join(CHECK, name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunScriptArgumentTest(Base):
    def game_kwargs(self, name, *extra):
        module = load(name)
        argv = [name + ".py", "--env", self.env, "--save", "map", "--port", "47900",
                "--out", os.path.join(self.work, "out"), *extra]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(module, "Game", side_effect=Stop) as made:
            with self.assertRaises(Stop):
                module.main()
        return made.call_args.kwargs

    def test_every_run_script_is_listed(self):
        names = {os.path.basename(p)[:-3] for p in glob.glob(os.path.join(CHECK, "*run.py"))}
        self.assertEqual(names, set(LAUNCHERS) | set(NO_LAUNCH) | set(SCENES))

    def test_default_is_none_and_given_folder_is_passed(self):
        for name in LAUNCHERS:
            with self.subTest(name):
                self.assertIsNone(self.game_kwargs(name)["pak_dir"])
                self.assertEqual(self.game_kwargs(name, "--pak", "some/pak256")["pak_dir"], "some/pak256")

    def test_sound_run_passes_pak_and_sound_mode(self):
        module = load("sound_run")
        for extra, sound in (((), "on"), (("--check",), "load")):
            argv = ["sound_run.py", "--env", self.env, "--port", "47900", "--scene", "bus", "--pak", "some/pak256", *extra]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(module, "Game", side_effect=Stop) as made:
                with self.assertRaises(Stop):
                    module.main()
            self.assertEqual((made.call_args.kwargs["pak_dir"], made.call_args.kwargs["sound"]), ("some/pak256", sound))


class TreeCheckArgumentTest(Base):
    def run_main(self, *extra):
        argv = ["tree_check.py", "--env", self.env, "--port", "47900", "--out", os.path.join(self.work, "out"), *extra]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(tree_check, "Game", side_effect=Stop) as made, \
                mock.patch.object(tree_check, "montage") as montaged:
            with self.assertRaises((Stop, SystemExit)) as caught:
                tree_check.main()
        self.assertFalse(montaged.called)
        return made, caught.exception

    def test_default_is_none_and_given_folder_is_passed(self):
        for extra, want in (((), None), (("--pak", "some/pak256"), "some/pak256")):
            made, _ = self.run_main(*extra)
            self.assertEqual(made.call_args.kwargs["pak_dir"], want)

    def test_rejects_pak_with_montage(self):
        made, error = self.run_main("--montage", os.path.join(self.work, "montage"), "--pak", "some/pak256")
        self.assertIsInstance(error, SystemExit)
        self.assertIn("--pak", str(error))
        self.assertFalse(made.called)


class GameCommandTest(unittest.TestCase):
    def run_main(self, *argv):
        with mock.patch.object(sys, "argv", ["game.py", "--port", "47900", *argv]), \
                mock.patch.object(game, "Game", side_effect=Stop) as made, \
                mock.patch.object(game.subprocess, "run") as built, \
                mock.patch.object(game, "send_command") as sent:
            with self.assertRaises((Stop, SystemExit)) as caught:
                game.main()
        self.assertFalse(built.called)
        self.assertFalse(sent.called)
        return made, caught.exception

    def test_passes_pak(self):
        for extra, want in (((), None), (("--pak", "some/pak256"), "some/pak256")):
            made, _ = self.run_main("--env", "e", "--save", "map", *extra)
            self.assertEqual(made.call_args.kwargs["pak_dir"], want)

    def test_rejects_pak_with_build_or_send(self):
        for argv in (("--env", "e", "--save", "map", "--build", "--pak", "p"),
                     ("--send", "return 1", "--pak", "p")):
            made, error = self.run_main(*argv)
            self.assertIsInstance(error, SystemExit)
            self.assertIn("--pak", str(error))
            self.assertFalse(made.called)


class PakDirTest(Base):
    """pak_dir を指定して作業フォルダを用意する。"""

    def setUp(self):
        super().setUp()
        self.dist = os.path.join(os.path.dirname(self.root), "dist-pak256")
        put(os.path.join(self.dist, "dist.pak"), "dist")

    def copied(self):
        base = os.path.join(self.work, game.PAK_DIR)
        return {os.path.relpath(os.path.join(d, n), base).replace(os.sep, "/")
                for d, _, names in os.walk(base) for n in names}

    def prepare_dist(self, **kw):
        return game.prepare_workdir(self.env, self.work, "map", root=self.root, build=self.build,
                                    pak_dir=self.dist, **kw)

    def test_extracted_zip_does_not_mix_repository_files(self):
        put(os.path.join(self.dist, "config", "simuconf.tab"), "# dist\n")
        put(os.path.join(self.dist, "text", "dist.tab"))
        put(os.path.join(self.dist, "demo.sve"), "demo")
        put(os.path.join(self.dist, "LICENSE.md"))
        put(os.path.join(self.root, "text", "repo.tab"))
        self.prepare_dist()
        self.assertEqual(self.copied(), {"dist.pak", "config/simuconf.tab", "text/dist.tab", "demo.sve"})
        self.assertIn("# dist", self.read(self.work, game.PAK_DIR, "config", "simuconf.tab"))

    def test_folder_without_config_uses_repository_files(self):
        put(os.path.join(self.root, "config", "simuconf.tab"), "# repo\n")
        put(os.path.join(self.root, "text", "repo.tab"))
        put(os.path.join(self.root, "demo", "demo.sve"), "demo")
        self.prepare_dist()
        self.assertEqual(self.copied(), {"dist.pak", "config/simuconf.tab", "text/ja.tab", "text/repo.tab", "demo.sve"})
        self.assertIn("# repo", self.read(self.work, game.PAK_DIR, "config", "simuconf.tab"))

    def test_bad_folder_stops_before_touching_workdir(self):
        self.prepare()
        kept = os.path.join(self.work, "keep.txt")
        put(kept)
        empty = os.path.join(os.path.dirname(self.root), "empty")
        os.makedirs(empty)
        no_conf = os.path.join(os.path.dirname(self.root), "no-conf")
        put(os.path.join(no_conf, "a.pak"))
        os.makedirs(os.path.join(no_conf, "config"))
        inside = os.path.join(self.work, game.PAK_DIR)
        for folder in ("", empty, no_conf, os.path.join(empty, "nothing"), inside):
            with self.subTest(folder):
                with self.assertRaises(RuntimeError):
                    game.prepare_workdir(self.env, self.work, "map", root=self.root, build=self.build, pak_dir=folder)
                self.assertTrue(os.path.isfile(kept))

    def test_game_keeps_absolute_path_and_passes_it(self):
        g = game.Game(self.env, "map", 47900, work=self.work, client=__file__, root=self.root, pak_dir="some/pak256")
        self.assertEqual(g.pak_dir, os.path.abspath("some/pak256"))
        with mock.patch.object(game, "port_in_use", return_value=False), \
                mock.patch.object(g, "alive_mcp", return_value=False), \
                mock.patch.object(game, "prepare_workdir", side_effect=Stop) as prepare:
            with self.assertRaises(Stop):
                g.start()
        self.assertEqual(prepare.call_args.kwargs["pak_dir"], os.path.abspath("some/pak256"))


if __name__ == "__main__":
    unittest.main()
