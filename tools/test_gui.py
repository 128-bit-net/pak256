"""GUI の絵（objects/gui/）の検査。MIT License。

- 本体（simskin.cc）が必ず求める cursor・symbol・misc の物と、駅・車庫の窓が NULL を確かめずに使う記号が、dat にあること。
- menuconf.tab が使うアイコンの番号が、各一覧の Image の数に収まること（本体は範囲外の番号に警告を出して 0 番にする）。

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

REQUIRED = {
    "cursor": ["Builder", "GeneralTools", "Marked"],
    "symbol": ["Seasons", "MessageOptions", "ColorOptions", "Logo", "NewYear", "NewWorld", "Flags", "Message",
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


if __name__ == "__main__":
    unittest.main()
