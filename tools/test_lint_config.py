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

    def test_mismatched_tool_id_definition(self):
        self.edit("menuconf.tab", lambda t: t + "simple_tool[40] = 40,\n")
        self.assertFails("番号が違う道具")

    def test_tool_id_limits_boundary(self):
        # 各種類で、上限の 1 つ手前は通り、上限は失敗する（本家 125.0.1 と OTRP で番号が同じ最後の番号）
        for kind, limit in (("general_tool", 48), ("simple_tool", 36), ("dialog_tool", 36)):
            with self.subTest(kind=kind):
                self.assertEqual(lint_config.TOOL_ID_LIMITS[kind], limit)
                ok = lint_config.check_menuconf([(1, f"{kind}[{limit - 1}] = 1,"), (2, "toolbar[0][0]=-")])
                self.assertEqual([e for e in ok if "番号が違う" in e], [])
                ng = lint_config.check_menuconf([(1, f"{kind}[{limit}] = 1,"), (2, "toolbar[0][0]=-")])
                self.assertTrue(any("番号が違う" in e for e in ng), ng)

    def test_mismatched_tool_id_in_toolbar(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=general_tool[0]", "toolbar[0][2]=general_tool[48],1"))
        self.assertFails("general_tool[48] は本家")

    def test_space_around_equal_in_toolbar(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=general_tool[0]", "toolbar[0][2] = general_tool[0]"))
        self.assertFails("`=` の前後に空白")

    def test_space_after_equal_in_toolbar(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=general_tool[0]", "toolbar[0][2]= general_tool[0]"))
        self.assertFails("`=` の前後に空白")

    def test_toolbar_position_gap(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=", "toolbar[0][3]=", 1))
        self.assertFails("抜け [2]")

    def test_toolbar_position_duplicate(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=general_tool[0]", "toolbar[0][1]=general_tool[0]"))
        self.assertFails("重なり")

    def test_toolbar_number_skipped(self):
        # toolbar[2] を toolbar[9] に書き換えると、出てくる順の連番でなくなる
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[2][", "toolbar[9]["))
        self.assertFails("その段の行が無い")

    def test_toolbar_reference_order_swapped(self):
        # toolbar[0] で toolbar[3] を toolbar[2] より先に参照すると、本体は toolbar[3] を捨てる
        def swap(t):
            t = t.replace("toolbar[0][3]=toolbar[2],0", "toolbar[0][3]=toolbar[X],0")
            t = t.replace("toolbar[0][4]=toolbar[3],4", "toolbar[0][3]=toolbar[2],0".replace("[3]=", "[4]=").replace("toolbar[2]", "toolbar[2]"))
            return t.replace("toolbar[X]", "toolbar[3]")
        self.edit("menuconf.tab", swap)
        self.assertFails("参照が、読む順の")

    def test_toolbar_double_reference(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][1]=dialog_tool[2]", "toolbar[0][1]=toolbar[1],29,,X,x.txt"))
        self.assertFails("参照が、読む順の")

    def test_toolbar_missing_menuconf(self):
        os.remove(os.path.join(self.dir, "menuconf.tab"))
        self.assertFails("menuconf.tab: ファイルが無い")

    def test_leading_space_line(self):
        self.edit("cityrules.tab", lambda t: t + " house_6 = ... .n. sss\n")
        self.assertFails("行頭が空白の行")

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

    def test_rule_row_separator(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1 = ... .n. sss", "house_1 = ...  .n.  sss"))
        self.assertFails("空白 1 個で区切る")

    def test_rule_four_rows(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1 = ... .n. sss", "house_1 = .... .n.. .... ...."))
        self.assertFails("3・5・7 のどれでもない")

    def test_rule_slope_chars_ok(self):
        self.edit("cityrules.tab", lambda t: t.replace("road_4 = .S. sns .S.", "road_4 = .u. sns .U."))
        self.assertEqual(lint_config.lint(self.dir), [])

    def test_road_rule_checked(self):
        self.edit("cityrules.tab", lambda t: t.replace("road_4 = .S. sns .S.", "road_4 = .S. sns .S"))
        self.assertFails("road_4 は正方形でない")

    def test_rule_duplicate(self):
        self.edit("cityrules.tab", lambda t: t + "house_1 = ... .n. sss\n")
        self.assertFails("house_1 が重なっている")

    def test_chance_without_rule(self):
        self.edit("cityrules.tab", lambda t: t + "house_9.chance = -2\n")
        self.assertFails("house_9.chance があるが")

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
