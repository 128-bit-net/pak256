"""GUI の絵（objects/gui/）の検査。MIT License。

- 本体（simskin.cc）が必ず求める cursor・symbol・misc の物と、駅・車庫の窓が NULL を確かめずに使う記号が、dat にあること。
- menuconf.tab が使うアイコンの番号が、各一覧の Image の数に収まること（本体は範囲外の番号に警告を出して 0 番にする）。
- 使うアイコンがすべて専用の絵を持ち、同じ種類の中で絵が重ならず、半透明・特別な色が無いこと（#66）。

使い方: python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUI = os.path.join(ROOT, "objects", "gui")
sys.path.insert(0, GUI)
import draw_gui  # noqa: E402
import gui_icons  # noqa: E402

REQUIRED = {
    "cursor": ["Builder", "GeneralTools", "Marked"],
    "symbol": ["Seasons", "MessageOptions", "ColorOptions", "Logo", "BigLogo", "NewYear", "NewWorld", "Flags", "Message",
               "Electricity", "InTown", "Passagiere", "Post", "Waren",
               # 本体は無くても起動するが、窓を開くと落ちる（halt_info.cc・depotlist_frame.cc）
               "TrainStop", "CarStop", "ShipStop", "BusStop", "AirStop", "MonorailStop", "MaglevStop",
               "NarrowgaugeStop", "TramStop"],
    "misc": ["Construction", "Sidewalk", "TunnelTexture", "RibiArrow", "PowerSource", "PowerDest"],
    "menu": ["GeneralTools", "SimpleTools", "DialogeTools", "BarTools"],
}


def read_dats():
    found = {}
    for path in glob.glob(os.path.join(GUI, "*.dat")):
        obj = name = None
        images = 0
        with open(path, encoding="utf-8") as f:
            for ln in f:
                m = re.match(r"(Obj|Name)=(.*)", ln.strip(), re.I)
                if m and m.group(1).lower() == "obj":
                    obj = m.group(2).strip()
                elif m:
                    name = m.group(2).strip()
                elif re.match(r"Image\[\d+\]", ln):
                    images += 1
        found[(obj, name)] = images
    return found


class GuiTest(unittest.TestCase):
    def test_required_objects(self):
        found = read_dats()
        missing = [f"{o}.{n}" for o, names in REQUIRED.items() for n in names if (o, n) not in found]
        self.assertEqual(missing, [])

    def test_menuconf_icons_fit(self):
        found = read_dats()
        for kind, nums in draw_gui.used_icons().items():
            if nums:
                self.assertGreater(found[("menu", draw_gui.MENU_NAME[kind])], max(nums), kind)

    def test_cursors_of_tools_without_own_cursor(self):
        """本体が道具の cursor を menuconf.tab の 2 つめの番号でしか決めない道具に、番号がある（#77・#84）。

        12・13 はダイヤの編集の「駅を追加」「駅を挿入」、39 は気候の塗り替え、22・25・27・44 は窓から選ぶ道具（街の建物・産業・本部・地面の物）。無いとカーソルが出ない。
        """
        found = read_dats()
        count = found[("cursor", "GeneralTools")]
        with open(os.path.join(draw_gui.ROOT, "config", "menuconf.tab"), encoding="utf-8") as f:
            text = f.read()
        for n in (12, 13, 39, 22, 25, 27, 44):
            m = re.search(r"^general_tool\[%d\]\s*=[^,\n]*,\s*(\d+)" % n, text, re.M)
            self.assertIsNotNone(m, f"general_tool[{n}] にカーソルの番号が無い")
            self.assertLess(int(m.group(1)), count, f"general_tool[{n}] のカーソルが GeneralTools の枚数に収まらない")

    def test_every_used_icon_has_a_picture(self):
        """使っているアイコンがすべて、番号でなく専用の絵を持つ（#66）。"""
        used = {(kind, n) for kind, nums in draw_gui.used_icons().items() for n in nums}
        self.assertEqual(sorted(used - set(gui_icons.ICONS)), [], "絵が無い番号")
        self.assertEqual(sorted(set(gui_icons.ICONS) - used), [], "使われない絵（menuconf.tab に無い番号）")

    def test_icons_are_distinguishable(self):
        """同じ種類の中で、同じ絵のアイコンが無い。"""
        for kind, nums in draw_gui.used_icons().items():
            seen = {}
            for n in sorted(nums):
                key = draw_gui.tool_icon(kind, n).tobytes()
                self.assertNotIn(key, seen, f"{kind} {n} は {seen.get(key)} と同じ絵")
                seen[key] = n

    def test_icon_pixels(self):
        """128px の絵で、半透明が無く、特別な色を使わない。"""
        special = {(v >> 16, (v >> 8) & 255, v & 255) for v in draw_gui.dg._SPECIAL}
        for kind, nums in draw_gui.used_icons().items():
            for n in nums:
                im = draw_gui.tool_icon(kind, n)
                self.assertEqual(im.size, (128, 128))
                raw = im.tobytes()
                for i in range(0, len(raw), 4):
                    r, g, b, a = raw[i:i + 4]
                    self.assertIn(a, (0, 255))
                    if a:
                        self.assertNotIn((r, g, b), special)

    def test_logo(self):
        """BigLogo は 4 枚の同じ大きさの正方形で全面不透明（makeobj が縁を切っても継ぎ目がずれない）。Logo も不透明で特別な色なし。"""
        special = {(v >> 16, (v >> 8) & 255, v & 255) for v in draw_gui.dg._SPECIAL}
        cells = draw_gui.logo_art.big_cells()
        self.assertEqual(len(cells), 4)
        small = draw_gui.logo_art.small()
        for im in cells + [small]:
            self.assertEqual(im.size[0], im.size[1])
            self.assertEqual({a for _, a in im.getchannel("A").getcolors()}, {255})
            self.assertFalse({c[1][:3] for c in im.getcolors(1 << 20)} & special)
        self.assertEqual({im.size for im in cells}, {(draw_gui.logo_art.BIG // 2,) * 2})
        # ロゴの気動車は、ゲームの気動車と同じ長さの比（length ÷ 16 タイル）
        with open(os.path.join(ROOT, "objects", "vehicle", "rail", "railcar", "railcar.yaml"), encoding="utf-8") as f:
            length = int(re.search(r"^length:\s*(\d+)", f.read(), re.M).group(1))
        self.assertEqual(length, draw_gui.logo_art.RAILCAR_LENGTH)
        with open(os.path.join(GUI, "sym_biglogo.dat"), encoding="utf-8") as f:
            self.assertIn(f"cell_size={draw_gui.logo_art.BIG // 2}", f.read())


if __name__ == "__main__":
    unittest.main()
