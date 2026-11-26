"""道路の停留所と線路の駅の表の検査（docs/stations.md）。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import importlib.util
import os
import re
import unittest

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAYOUTS = 8


def stops():
    """objects/station/ の全部の表。停留所（type: stop）でない表があれば、検査で落とす。"""
    for p in sorted(glob.glob(os.path.join(ROOT, "objects", "station", "**", "*.yaml"), recursive=True)):
        with open(p, encoding="utf-8") as f:
            yield p, yaml.safe_load(f)


def names(o):
    out = []
    if isinstance(o, dict):
        for v in o.values():
            out += names(v)
    else:
        out.append(str(o))
    return out


def road_stop_script():
    """道路の停留所を描くスクリプト（白線の位置 LINE_FAR・LINE_NEAR の持ち主）。"""
    path = os.path.join(ROOT, "objects", "station", "road_stops", "draw_stops.py")
    spec = importlib.util.spec_from_file_location("road_draw_stops", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class StationTest(unittest.TestCase):
    def test_found(self):
        self.assertTrue(list(stops()), "停留所の表が見つからない")

    def test_shape(self):
        from PIL import Image
        for p, d in stops():
            self.assertEqual(d["type"], "stop", p)
            self.assertEqual(d["obj"], "building", p)
            self.assertIn(d["waytype"], ("road", "track"), p)
            self.assertEqual(d["waytype"] == "track", "rail_stops" in p.replace(os.sep, "/"), f"{p}: 置き場と waytype が合わない")
            self.assertEqual(str(d["dims"]), f"1,1,{LAYOUTS}", p)
            self.assertTrue(d.get("enables_pax") or d.get("enables_post") or d.get("enables_ware"), f"{p}: 何も扱わない")
            sheet = os.path.join(os.path.dirname(p), os.path.basename(p)[:-5] + ".png")
            with Image.open(sheet) as im:
                im = im.convert("RGB")
                self.assertEqual(im.size, (256 * LAYOUTS, 256 * 3), f"{sheet}: シートの大きさ")

                def has_art(row, col):
                    cell = im.crop((col * 256, row * 256, col * 256 + 256, row * 256 + 256))
                    return len(set(cell.getdata())) > 1  # 透明色だけでない

                # 道具の絵は、192px の四角を左上の角から隙間なく置く（隙間があると、本体が見える範囲だけを縮めて置き、枠がずれて灰色に見える。#71）
                icon = im.crop((0, 512, 256, 768))
                px = icon.load()
                for y in range(192):
                    for x in range(192):
                        corner = (x < 24 or x > 167) and (y < 24 or y > 167)  # 角丸の角は透明色でよい
                        self.assertTrue(corner or px[x, y] != (231, 255, 255), f"{sheet}: 道具の絵の四角に透明色 ({x}, {y})")
                self.assertEqual(icon.crop((192, 0, 256, 256)).getcolors(), [(64 * 256, (231, 255, 255))], f"{sheet}: 道具の絵が 192px の外にはみ出す")
                self.assertEqual(icon.crop((0, 192, 192, 256)).getcolors(), [(192 * 64, (231, 255, 255))], f"{sheet}: 道具の絵が 192px の外にはみ出す")
                # 後ろの絵は 0 行、前の絵は 1 行、道具の絵は 2 行 0 列
                for key, row in (("backimage", 0), ("frontimage", 1)):
                    self.assertEqual(sorted(d[key]), list(range(LAYOUTS)), f"{p}: {key} の向きが 8 通りにならない")
                    for i in range(LAYOUTS):
                        n = names(d[key][i])
                        self.assertEqual(n, [f"{os.path.basename(p)[:-5]}.{row}.{i}"], f"{p}: {key}[{i}] の絵")
                        self.assertTrue(has_art(row, i), f"{sheet}: {row} 行 {i} 列が空")
                self.assertEqual(str(d["icon"]).lstrip("> "), f"{os.path.basename(p)[:-5]}.2.0", f"{p}: icon")
                self.assertTrue(has_art(2, 0), f"{sheet}: 道具の絵が空")

    def test_road_stops_off_the_lane_lines(self):
        """道路の停留所の絵は、後ろ・前のどちらも、画面で白線より内側（道路の中央の側）に画素を置かない（#115）。

        白線の外側の端は draw_stops.py の LINE_FAR・LINE_NEAR（ami_road_local の値）。画素を地面（高さ 0）の座標に戻して調べるので、
        高い物が画面の上へ伸びて道路に掛かる場合も落ちる。
        """
        from PIL import Image
        ds = road_stop_script()
        for p, d in stops():
            if d["waytype"] != "road":
                continue
            sheet = os.path.join(os.path.dirname(p), os.path.basename(p)[:-5] + ".png")
            with Image.open(sheet) as im:
                px = im.convert("RGB").load()
            for row in (0, 1):
                for col in range(LAYOUTS):
                    bad = []
                    for y in range(256):
                        for x in range(256):
                            if px[col * 256 + x, row * 256 + y] == (231, 255, 255):
                                continue
                            a, b = (x + 0.5 - 128) / 128, (y + 0.5 - 128) / 64  # a = u - v, b = u + v
                            u, v = (b + a) / 2, (b - a) / 2
                            c = u if col % 2 == 0 else v  # 偶数の向きは NS の道路（c = u）、奇数は EW（c = v）
                            if ds.LINE_FAR < c < ds.LINE_NEAR:
                                bad.append((x, y, round(c, 3)))
                    self.assertEqual(bad[:5], [], f"{sheet}: {row} 行 {col} 列が道路に掛かる（{len(bad)} 画素）")

    def test_listed_in_docs(self):
        """docs/stations.md の駅の表に、全部の停留所が、扱う貨物とともに載っている。"""
        with open(os.path.join(ROOT, "docs", "stations.md"), encoding="utf-8") as f:
            doc = f.read()
        for p, d in stops():
            row = [ln for ln in doc.splitlines() if re.match(r"\|\s*`%s`\s*\|" % re.escape(d["name"]), ln)]
            self.assertEqual(len(row), 1, f"{p}: stations.md の表に無い")
            cells = [c.strip() for c in row[0].strip("|").split("|")]
            self.assertEqual(cells[1:4], [f"`{d['obj']}`", f"`{d['type']}`", f"`{d['waytype']}`"], p)
            for key in ("enables_pax", "enables_post", "enables_ware"):
                self.assertEqual(key in cells[4], bool(d.get(key)), f"{p}: 表の扱う貨物と {key} が合わない")


if __name__ == "__main__":
    unittest.main()
