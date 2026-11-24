"""lint_config.py の検査。わざと誤りを入れた設定で失敗し、今の config/ で通ることを確かめる。MIT License。
python -X utf8 -m unittest discover -s tools -p "test_*.py" """
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lint_config  # noqa: E402

CONFIG = os.path.join(lint_config.ROOT, "config")


class LintConfigTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.join(self.tmp.name, "config")
        shutil.copytree(CONFIG, self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def edit(self, name, fn):
        path = os.path.join(self.dir, name)
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
        new = fn(text)
        self.assertNotEqual(text, new, "テストの書き換えが効いていない")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)

    def assertFails(self, needle):
        errors = lint_config.lint(self.dir)
        self.assertTrue(any(needle in e for e in errors), f"{needle!r} が無い: {errors}")

    def test_current_config_passes(self):
        self.assertEqual(lint_config.lint(CONFIG), [])

    def test_space_around_equal_in_toolbar(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=general_tool[0]", "toolbar[0][2] = general_tool[0]"))
        self.assertFails("`=` の前後に空白")

    def test_toolbar_position_gap(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=", "toolbar[0][3]=", 1))
        self.assertFails("toolbar[0] の位置が")

    def test_toolbar_position_duplicate(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=general_tool[0]", "toolbar[0][1]=general_tool[0]"))
        self.assertFails("重なり")

    def test_toolbar_number_skipped(self):
        # toolbar[2] を toolbar[9] に書き換えると、出てくる順の連番でなくなる
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[2][", "toolbar[9]["))
        self.assertFails("出てくる順の 0, 1, 2")

    def test_undefined_tool(self):
        self.edit("menuconf.tab", lambda t: t.replace("dialog_tool[2] = 2,m\n", ""))
        self.assertFails("dialog_tool[2] を使っているが")

    def test_unused_toolbar(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][3]=toolbar[2],0", "toolbar[0][3]=general_tool[2],0"))
        self.assertFails("どこからも使われていない")

    def test_not_key_value(self):
        self.edit("simuconf.tab", lambda t: t + "\nこれは設定ではない\n")
        self.assertFails("の形でない行")

    def test_rule_not_square(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1 = ... .n. sss", "house_1 = ... .n. ss"))
        self.assertFails("正方形でない")

    def test_rule_bad_size(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1 = ... .n. sss", "house_1 = .n. sss"))
        self.assertFails("3・5・7 のどれでもない")

    def test_rule_bad_char(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1 = ... .n. sss", "house_1 = ... .n. ssx"))
        self.assertFails("使えない記号")

    def test_rule_center_not_n(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1 = ... .n. sss", "house_1 = ... .s. sss"))
        self.assertFails("中央が n")

    def test_rule_missing_chance(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_5.chance = -2\n", ""))
        self.assertFails("house_5.chance が無い")

    def test_rule_number_gap(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_5", "house_7"))
        self.assertFails("連番")

    def test_missing_cityrules(self):
        os.remove(os.path.join(self.dir, "cityrules.tab"))
        self.assertFails("cityrules.tab: ファイルが無い")


if __name__ == "__main__":
    unittest.main()
