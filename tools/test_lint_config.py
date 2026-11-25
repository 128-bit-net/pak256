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

    # ---- #21: 大文字・小文字、範囲の書き方、.chance の値 ----

    def test_normalize_keeps_current_config_lines(self):
        # 今の config/ は範囲の書き方も大文字も使わないので、直しても行は変わらない
        for name in ("menuconf.tab", "cityrules.tab"):
            lines = lint_config.read_lines(os.path.join(CONFIG, name))
            norm, errs = lint_config.normalize(lines)
            self.assertEqual(errs, [])
            self.assertEqual(norm, lines)

    def test_key_case_is_ignored_like_engine(self):
        # 本体はキーを小文字にして読むので、大文字のキーの menuconf も同じ検査を受け、通る
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=general_tool[0]", "Toolbar[0][2]=general_tool[0]"))
        self.assertEqual(lint_config.lint(self.dir), [])

    def test_key_uppercase_still_checked(self):
        # 大文字のキーでも、位置の重なりは見つかる（小文字にする前は検査をすり抜けた）
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=general_tool[0]", "TOOLBAR[0][1]=general_tool[0]"))
        self.assertFails("重なり")

    def test_uppercase_house_key_counted(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_5 = ", "House_5 = ").replace("house_5.chance", "House_5.chance"))
        self.assertEqual(lint_config.lint(self.dir), [])
        self.edit("cityrules.tab", lambda t: t.replace("House_5.chance = -2\n", ""))
        self.assertFails("house_5.chance が無い")

    def test_tool_name_value_must_be_lowercase(self):
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[0][2]=general_tool[0]", "toolbar[0][2]=General_Tool[0]"))
        self.assertFails("道具の名前は小文字")

    def test_range_expansion_position(self):
        # toolbar[2] には位置 9・10 が既にある。範囲 [9-10] は両方に重なる（終端の 10 も展開される）
        self.edit("menuconf.tab", lambda t: t + "toolbar[2][9-10]=general_tool[2]" + chr(10))
        self.assertFails("重なり [9, 10]")

    def test_range_expansion_fills_positions(self):
        # 範囲で書いた位置が、連番を埋める（展開しないと「抜け」になる）
        def fn(t):
            t = t.replace("toolbar[2][0]=general_tool[2]\n", "toolbar[2][0-1]=general_tool[2]\n")
            return t.replace("toolbar[2][1]=general_tool[3]\n", "")
        self.edit("menuconf.tab", fn)
        self.assertEqual(lint_config.lint(self.dir), [])

    def test_range_expansion_overlap(self):
        # 範囲が既にある位置と重なると、展開した後で重なりが見つかる
        self.edit("menuconf.tab", lambda t: t.replace("toolbar[2][0]=general_tool[2]", "toolbar[2][0-1]=general_tool[2]"))
        self.assertFails("重なり [1]")

    def test_range_expansion_list_and_unit(self):
        keys, err = lint_config.expand_key("Toolbar[6][10-11]")
        self.assertEqual((keys, err), (["toolbar[6][10]", "toolbar[6][11]"], None))
        self.assertEqual(lint_config.expand_key("a[1,3]")[0], ["a[1]", "a[3]"])
        self.assertEqual(lint_config.expand_key("a[2-4,7]")[0], ["a[2]", "a[3]", "a[4]", "a[7]"])
        self.assertEqual(sorted(lint_config.expand_key("a[0-1][0,1]")[0]), ["a[0][0]", "a[0][1]", "a[1][0]", "a[1][1]"])
        self.assertEqual(lint_config.expand_key("a[ 3 - 4 ]")[0], ["a[3]", "a[4]"])
        self.assertEqual(lint_config.expand_key("a[5]")[0], ["a[5]"])

    def test_range_limit_boundary(self):
        # 本体は 1 つの範囲で値が 256 個以上になると止まる（255 個までは通る）
        self.assertEqual(lint_config.expand_key("a[0-254]")[1], None)
        self.assertIn("256", lint_config.expand_key("a[0-255]")[1])

    def test_ribi_names_not_expanded(self):
        self.assertEqual(lint_config.expand_key("a[n,s]")[0], ["a[n,s]"])

    def test_chance_sint16_bounds(self):
        for v, ok in (("-32768", True), ("32767", True), ("-32769", False), ("32768", False)):
            with self.subTest(v=v):
                errors = lint_config.check_cityrules([(1, "house_1 = ... .n. sss"), (2, "house_1.chance = " + v)])
                self.assertEqual(not any("chance の値" in e for e in errors), ok)

    def test_range_too_large(self):
        self.edit("menuconf.tab", lambda t: t + "toolbar[2][0-300]=general_tool[2]\n")
        self.assertFails("256 個以上になる")

    def test_chance_not_integer(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1.chance = -2", "house_1.chance = abc"))
        self.assertFails("house_1.chance の値が")

    def test_chance_decimal_point(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1.chance = -2", "house_1.chance = 1.5"))
        self.assertFails("house_1.chance の値が")

    def test_chance_empty(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1.chance = -2", "house_1.chance ="))
        self.assertFails("house_1.chance の値が")

    def test_chance_octal_like(self):
        self.edit("cityrules.tab", lambda t: t.replace("house_1.chance = -2", "house_1.chance = 08"))
        self.assertFails("house_1.chance の値が")

    def test_chance_out_of_sint16(self):
        self.edit("cityrules.tab", lambda t: t.replace("road_1.chance = -4", "road_1.chance = 40000"))
        self.assertFails("road_1.chance の値が")

    def test_chance_hex_and_positive_ok(self):
        self.edit("cityrules.tab", lambda t: t.replace("road_1.chance = -4", "road_1.chance = 0x10").replace("house_1.chance = -2", "house_1.chance = +3"))
        self.assertEqual(lint_config.lint(self.dir), [])

    def test_missing_cityrules(self):
        os.remove(os.path.join(self.dir, "cityrules.tab"))
        self.assertFails("cityrules.tab: ファイルが無い")


if __name__ == "__main__":
    unittest.main()
