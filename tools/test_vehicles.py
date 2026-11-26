"""車両の長さと描画位置の決まり（docs/standards.md の 4 章）の検査。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"

- tools/vehicles.py の換算と横の位置が、docs/standards.md の数と合うこと。
- 車両の画面の大きさが、手本の 2 倍の目標（docs/standards.md の 4 章「大きさ」）に合うこと。
- 見本のバス（objects/vehicle/road/sample_bus/）の表の length が決まりどおりで、絵の 8 方向が決まりの位置に描かれていること
  （車体の外接枠が、決まりから計算した枠と ±2px で合う）。特別な色が混じらないこと。
- 石炭のトラック（objects/vehicle/road/coal_truck/）の表（length・貨物・freightimage）と、空・積んだ 2 行の絵が決まりの位置に描かれていること。
Pillow と PyYAML が要る（tools/requirements.txt）。
"""
import importlib.util
import os
import sys
import unittest

import yaml
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import vehicles as V  # noqa: E402

BUS_DIR = os.path.join(ROOT, "objects", "vehicle", "road", "sample_bus")
TRUCK_DIR = os.path.join(ROOT, "objects", "vehicle", "road", "coal_truck")
TOL = 2
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}


def load_draw_bus():
    spec = importlib.util.spec_from_file_location("draw_bus", os.path.join(BUS_DIR, "draw_bus.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestRules(unittest.TestCase):
    def test_length_units(self):
        # 四捨五入。pak128.Japan と同じ 20m → 12、25m → 15。短くても 1
        self.assertEqual(V.length_units(12.0), 7)   # 7.27
        self.assertEqual(V.length_units(20.0), 12)  # 12.12
        self.assertEqual(V.length_units(25.0), 15)  # 15.15
        self.assertEqual(V.length_units(4.95), 3)   # 3.0
        self.assertEqual(V.length_units(5.0), 3)    # 3.03
        self.assertEqual(V.length_units(5.8), 4)    # 3.52
        self.assertEqual(V.length_units(0.5), 1)
        # 0.5 ちょうどは切り上げ（Python の round の偶数丸めではない）
        self.assertEqual(V.length_units(4.125), 3)  # 2.5

    def test_fixed_numbers(self):
        # docs/standards.md に書いた数。変えるときは文書と一緒に直す
        self.assertEqual(V.FRONT_UNITS, 0)
        self.assertEqual(V.ORIGIN, (128, 192))
        self.assertEqual(V.CELL, 256)
        self.assertEqual(V.UNITS_PER_TILE, 16)
        self.assertAlmostEqual(V.M_PER_UNIT, 1.65)
        self.assertAlmostEqual(V.PX_PER_M_Z, 5.94, places=2)
        self.assertAlmostEqual(V.PX_PER_UNIT_SIDE, 11.31, places=2)
        self.assertEqual((V.RAIL_WIDTH_SCALE, V.RAIL_HEIGHT_SCALE), (1.40, 1.20))

    def test_length_from_px(self):
        # 道路の車両の length は、手本の 2 倍の横向きの長さから（バス・郵便・石炭）
        self.assertEqual([V.length_from_px(px) for px in (100, 68, 86)], [9, 6, 8])
        self.assertEqual(V.length_from_px(1), 1)

    def test_lane_offset_is_half_of_driveleft(self):
        # 右側の車線は、本体の左側通行のずれ（×4）のちょうど半分を反対に置く。軸の向きで 24,12、斜めで 24,0 か 0,12
        expect = {"n": (24, 12), "s": (-24, -12), "e": (-24, 12), "w": (24, -12),
                  "ne": (0, 12), "sw": (0, -12), "se": (-24, 0), "nw": (24, 0)}
        for d, xy in expect.items():
            self.assertEqual(V.lane_offset_px(d), xy, d)
            # 左側通行で足すずれを足すと、道路の中心に対して反対の側の同じ距離に来る
            lx, ly = V.DRIVELEFT_64[d]
            self.assertEqual((xy[0] + lx * 4, xy[1] + ly * 4), (-xy[0], -xy[1]), d)

    def test_lane_is_on_the_right(self):
        # 右側の車線の点は、進む向きの右にある（外積の向き）
        for d in V.DIRECTIONS:
            hx, hy = V.HEADING[d]
            px, py = V.lane_point(d)
            self.assertGreater(hx * py - hy * px, 0, d)

    def test_footprint_length(self):
        # 車体の長さは length × 1.65m（実物の長さではない）。前の端は基準点から FRONT_UNITS 前
        for d in V.DIRECTIONS:
            fr, fl, bl, br = V.footprint(d, 7, 2.5, V.FRONT_UNITS)
            along = ((fr[0] - br[0]) ** 2 + (fr[1] - br[1]) ** 2) ** 0.5
            self.assertAlmostEqual(along * V.M_PER_TILE, 7 * V.M_PER_UNIT, places=6)
            px, py = V.lane_point(d)
            hx, hy = V.HEADING[d]
            mid_front = ((fr[0] + fl[0]) / 2 - px, (fr[1] + fl[1]) / 2 - py)
            self.assertAlmostEqual(mid_front[0] * hx + mid_front[1] * hy, V.FRONT_UNITS / V.UNITS_PER_TILE, places=6)


class TestSampleBus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bus = load_draw_bus()
        with open(os.path.join(BUS_DIR, "sample_bus.yaml"), encoding="utf-8") as f:
            cls.table = yaml.safe_load(f)
        cls.img = Image.open(os.path.join(BUS_DIR, "sample_bus.png")).convert("RGBA")

    def test_table(self):
        self.assertEqual(self.table["length"], self.bus.LENGTH)
        self.assertEqual(self.table["name"], self.bus.NAME)
        self.assertEqual(list(self.table["emptyimage"]), list(V.DIRECTIONS))

    def test_sheet_size(self):
        self.assertEqual(self.img.size, (V.CELL * len(V.DIRECTIONS), V.CELL))

    def test_cells_at_rule_position(self):
        for i, d in enumerate(V.DIRECTIONS):
            corners = V.footprint(d, self.bus.LENGTH, self.bus.WIDTH_M * self.bus.SCALE[0], V.FRONT_UNITS)
            pts = [V.to_screen(x, y, z) for (x, y) in corners for z in (0.0, self.bus.HEIGHT_M * self.bus.SCALE[1])]
            ex = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
            cell = self.img.crop((i * V.CELL, 0, (i + 1) * V.CELL, V.CELL))
            box = cell.getchannel("A").getbbox()
            self.assertIsNotNone(box, d)
            got = (box[0], box[1], box[2], box[3])
            for g, e, name in zip(got, ex, ("left", "top", "right", "bottom")):
                self.assertLessEqual(abs(g - e), TOL, f"{d} {name}: 絵 {got} 決まり {tuple(round(v, 1) for v in ex)}")

    def test_no_special_colors(self):
        found = set()
        px = self.img.load()
        for y in range(self.img.height):
            for x in range(self.img.width):
                r, g, b, a = px[x, y]
                if a and (r << 16 | g << 8 | b) in SPECIAL:
                    found.add(f"{r:02X}{g:02X}{b:02X}")
        self.assertFalse(found, f"特別な色: {sorted(found)}")

    def test_alpha_is_binary(self):
        hist = self.img.getchannel("A").histogram()
        self.assertEqual(sum(hist[1:255]), 0)


def docs_row(text, name):
    """docs/vehicles.md の表の、name の行を、その表の見出し（直前の `name` で始まる行）の列名で引いた辞書にする。"""
    lines = text.splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith(f"| `{name}` |"))
    j = max(n for n in range(i) if lines[n].startswith("| `name` |"))
    keys = [c.strip().strip("`") for c in lines[j].strip("|").split("|")]
    vals = [c.strip() for c in lines[i].strip("|").split("|")]
    return dict(zip(keys, vals))


ROAD_DIR = os.path.join(ROOT, "objects", "vehicle", "road")


def load_draw_vehicles():
    spec = importlib.util.spec_from_file_location("draw_vehicles", os.path.join(ROAD_DIR, "draw_vehicles.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCoalTruck(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.truck = load_draw_vehicles()
        cls.spec = next(v for v in cls.truck.VEHICLES if v["name"] == "pak256_coal_truck")
        with open(os.path.join(TRUCK_DIR, "coal_truck.yaml"), encoding="utf-8") as f:
            cls.table = yaml.safe_load(f)
        cls.img = Image.open(os.path.join(TRUCK_DIR, "coal_truck.png")).convert("RGBA")

    def test_table(self):
        t = self.table
        self.assertEqual(t["length"], self.spec["length"])
        self.assertEqual(t["length"], V.length_from_px(self.spec["target_px"][0]))
        self.assertEqual(t["name"], self.spec["name"])
        self.assertEqual(t["waytype"], "road")
        self.assertEqual(t["freight"], "Kohle")  # 炭鉱が出し、発電所が受ける貨物（objects/goods）
        self.assertEqual(list(t["emptyimage"]), list(V.DIRECTIONS))
        self.assertEqual(list(t["freightimage"]), list(V.DIRECTIONS))
        for i, d in enumerate(V.DIRECTIONS):  # 0 行 = 空、1 行 = 積んだ。列は向きの順
            self.assertEqual(t["emptyimage"][d], f"coal_truck.0.{i}")
            self.assertEqual(t["freightimage"][d], f"coal_truck.1.{i}")

    def test_yaml_is_what_the_script_writes(self):
        # 表は draw_vehicles.py が書き出す物。スクリプトだけ直して流し直さないと落ちる
        with open(os.path.join(TRUCK_DIR, "coal_truck.yaml"), encoding="utf-8", newline="") as f:
            self.assertEqual(f.read(), self.truck.yaml_lines(self.spec))

    def test_values_match_docs_table(self):
        # docs/vehicles.md の「道路の車両」の表の値と、表（yaml）の値が同じ
        with open(os.path.join(ROOT, "docs", "vehicles.md"), encoding="utf-8") as f:
            text = f.read()
        doc = docs_row(text, self.spec["name"])
        for k in ("payload", "speed", "power", "gear", "weight", "cost", "runningcost", "intro_year"):
            self.assertEqual(str(self.table[k]), doc[k], k)
        self.assertEqual(doc["name"].strip("`"), self.table["name"])

    def test_body_length_matches_length(self):
        # 絵の車体の長さは length × 1.65m（運転席と荷台で全長）。前の端は基準点（0）
        length_m = self.table["length"] * V.M_PER_UNIT
        self.assertAlmostEqual(self.truck.CAB[0], 0.0)
        self.assertAlmostEqual(self.truck.BED[1], -length_m, places=6)
        self.assertAlmostEqual(self.truck.CAB[1], self.truck.BED[0])  # 運転席と荷台の間にすき間も重なりも無い

    def test_sheet_size(self):
        self.assertEqual(self.img.size, (V.CELL * len(V.DIRECTIONS), V.CELL * 2))

    def test_cells_at_rule_position(self):
        for row, parts in enumerate((self.truck.PARTS_EMPTY, self.truck.PARTS_LOADED)):
            for i, d in enumerate(V.DIRECTIONS):
                pts = []
                for part in parts:
                    z0, z1 = part[3] * self.spec["scale"][1], part[4] * self.spec["scale"][1]
                    pts += [V.to_screen(x, y, z) for (x, y) in self.truck.corners(d, part) for z in (z0, z1)]
                ex = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
                cell = self.img.crop((i * V.CELL, row * V.CELL, (i + 1) * V.CELL, (row + 1) * V.CELL))
                box = cell.getchannel("A").getbbox()
                self.assertIsNotNone(box, (row, d))
                for g, e, name in zip(box, ex, ("left", "top", "right", "bottom")):
                    self.assertLessEqual(abs(g - e), TOL, f"行{row} {d} {name}: 絵 {box} 決まり {tuple(round(v, 1) for v in ex)}")

    def test_loaded_differs_from_empty(self):
        # 積んだ絵は空の絵と違う（石炭の山が見える向きがある）
        diff = 0
        for i in range(len(V.DIRECTIONS)):
            a = self.img.crop((i * V.CELL, 0, (i + 1) * V.CELL, V.CELL)).tobytes()
            b = self.img.crop((i * V.CELL, V.CELL, (i + 1) * V.CELL, 2 * V.CELL)).tobytes()
            diff += a != b
        self.assertGreaterEqual(diff, 6)

    def test_no_special_colors(self):
        px = self.img.load()
        found = {f"{r:02X}{g:02X}{b:02X}" for y in range(self.img.height) for x in range(self.img.width)
                 for (r, g, b, a) in [px[x, y]] if a and (r << 16 | g << 8 | b) in SPECIAL}
        self.assertFalse(found, f"特別な色: {sorted(found)}")

    def test_alpha_is_binary(self):
        hist = self.img.getchannel("A").histogram()
        self.assertEqual(sum(hist[1:255]), 0)


class TestRoadVehicles(unittest.TestCase):
    """バス・郵便のトラック（#41）。表の length・貨物・絵の位置（部分ごとの高さを含む）・特別な色。"""

    @classmethod
    def setUpClass(cls):
        cls.mod = load_draw_vehicles()

    def each(self):
        for spec in self.mod.VEHICLES:
            if spec["style"] != "panel":
                continue
            d = os.path.join(ROAD_DIR, spec["dir"])
            with open(os.path.join(d, spec["stem"] + ".yaml"), encoding="utf-8") as f:
                table = yaml.safe_load(f)
            img = Image.open(os.path.join(d, spec["stem"] + ".png")).convert("RGBA")
            yield spec, table, img

    def test_tables(self):
        names = set()
        for spec, table, _ in self.each():
            names.add(table["name"])
            self.assertEqual(table["length"], spec["length"], spec["name"])
            self.assertEqual(spec["length"], V.length_from_px(spec["target_px"][0]), spec["name"])
            self.assertEqual(table["name"], spec["name"])
            self.assertEqual(table["freight"], spec["freight"])
            self.assertEqual(table["waytype"], "road")
            self.assertEqual(list(table["emptyimage"]), list(V.DIRECTIONS))
            for key in ("payload", "speed", "power", "gear", "weight", "cost", "runningcost", "intro_year"):
                self.assertEqual(table[key], spec[key], f"{spec['name']} {key}")
        self.assertEqual(names, {"pak256_bus", "pak256_mail_truck"})  # panel の 2 種（石炭のトラックは TestCoalTruck）
        # docs/vehicles.md の表の length
        self.assertEqual({s["name"]: s["length"] for s in self.mod.VEHICLES},
                         {"pak256_bus": 9, "pak256_mail_truck": 6, "pak256_coal_truck": 8})

    def test_all_vehicles_are_in_one_table(self):
        # 道路の車両は 1 つの表・1 本の道具（#59）。表の name の行が全部あり、yaml は道具が書く物と同じ
        with open(os.path.join(ROOT, "docs", "vehicles.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertEqual({s["name"] for s in self.mod.VEHICLES}, {"pak256_bus", "pak256_mail_truck", "pak256_coal_truck"})
        for spec in self.mod.VEHICLES:
            docs_row(text, spec["name"])
            with open(os.path.join(ROAD_DIR, spec["dir"], spec["stem"] + ".yaml"), encoding="utf-8", newline="") as f:
                self.assertEqual(f.read(), self.mod.yaml_lines(spec), spec["name"])

    def test_cells_at_rule_position(self):
        for spec, table, img in self.each():
            self.assertEqual(img.size, (V.CELL * len(V.DIRECTIONS), V.CELL))
            kw, kh = spec["scale"]
            for i, d in enumerate(V.DIRECTIONS):
                whole = V.footprint(d, spec["length"], spec["width_m"] * kw, V.FRONT_UNITS)
                pts = []
                for t0, t1, height, *_ in spec["parts"]:
                    for (x, y) in self.mod.part_corners(whole, t0, t1):
                        pts += [V.to_screen(x, y, 0.0), V.to_screen(x, y, height * kh)]
                ex = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
                box = img.crop((i * V.CELL, 0, (i + 1) * V.CELL, V.CELL)).getchannel("A").getbbox()
                self.assertIsNotNone(box, d)
                for g, e, name in zip(box, ex, ("left", "top", "right", "bottom")):
                    self.assertLessEqual(abs(g - e), TOL, f"{spec['name']} {d} {name}: 絵 {box} 決まり {tuple(round(v, 1) for v in ex)}")

    def test_no_special_colors_and_binary_alpha(self):
        for spec, _, img in self.each():
            found = set()
            px = img.load()
            for y in range(img.height):
                for x in range(img.width):
                    r, g, b, a = px[x, y]
                    if a and (r << 16 | g << 8 | b) in SPECIAL:
                        found.add(f"{r:02X}{g:02X}{b:02X}")
            self.assertFalse(found, f"{spec['name']} 特別な色: {sorted(found)}")
            self.assertEqual(sum(img.getchannel("A").histogram()[1:255]), 0, spec["name"])

    def test_values_match_docs_table(self):
        # docs/vehicles.md の「道路の車両」の表の値と、VEHICLES の値が同じ
        with open(os.path.join(ROOT, "docs", "vehicles.md"), encoding="utf-8") as f:
            text = f.read()
        for spec in self.mod.VEHICLES:
            doc = docs_row(text, spec["name"])
            self.assertEqual(int(doc["length"]), spec["length"], spec["name"])
            self.assertEqual(doc["freight"].strip("`"), spec["freight"], spec["name"])
            for k in ("payload", "speed", "power", "gear", "weight", "cost", "runningcost", "intro_year"):
                self.assertEqual(doc[k], str(spec[k]), f"{spec['name']} {k}")

    def test_screen_size_is_twice_the_reference(self):
        # 画面の大きさが、pak128 の手本の 2 倍の目標に合う（長さは length の丸めで ±6px、幅・高さは ±2px）
        for spec in self.mod.VEHICLES:
            img = Image.open(os.path.join(ROAD_DIR, spec["dir"], spec["stem"] + ".png")).convert("RGBA")
            for got, want, tol, key in zip(screen_size(img, V.CELL), spec["target_px"], (6, TOL, TOL), ("長さ", "幅", "高さ")):
                self.assertLessEqual(abs(got - want), tol, f"{spec['name']} {key}: {got} 目標 {want}")

    def test_translations(self):
        for lang in ("ja", "en"):
            with open(os.path.join(ROOT, "text", lang + ".tab"), encoding="utf-8") as f:
                lines = [ln.rstrip("\r\n") for ln in f]
            for spec in self.mod.VEHICLES:
                self.assertIn(spec["name"], lines, f"{lang}: {spec['name']}")


def screen_size(img, cell):
    """シートの横向き（sw）の横 = 長さ、正面向き（se）の横 = 幅、横向きの縦 − 幅の半分 = 高さ。"""
    def box(direction):
        i = V.DIRECTIONS.index(direction)
        return img.crop((i * cell, 0, (i + 1) * cell, cell)).getchannel("A").getbbox()
    sw, se = box("sw"), box("se")
    width = se[2] - se[0]
    return sw[2] - sw[0], width, sw[3] - sw[1] - width / 2


RAIL_DIR = os.path.join(ROOT, "objects", "vehicle", "rail")


class TestRailVehicles(unittest.TestCase):
    """線路の車両（気動車・付随車。#46）。表・512 のセル・線路の中心に描く位置・特別な色・docs の表。"""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("draw_trains", os.path.join(RAIL_DIR, "draw_trains.py"))
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def each(self):
        for spec in self.mod.VEHICLES:
            d = os.path.join(RAIL_DIR, spec["dir"])
            with open(os.path.join(d, spec["stem"] + ".yaml"), encoding="utf-8", newline="") as f:
                raw = f.read()
            img = Image.open(os.path.join(d, spec["stem"] + ".png")).convert("RGBA")
            yield spec, raw, yaml.safe_load(raw), img

    def test_centered_footprint_has_no_lane_offset(self):
        # 線路の車両は車線のずれを付けない（本体は左側通行のずれを道路の車両にしか足さない）
        for d in V.DIRECTIONS:
            pts = V.footprint(d, 12, 2.8, 0, centered=True)
            mx = sum(p[0] for p in pts) / 4
            my = sum(p[1] for p in pts) / 4
            hx, hy = V.HEADING[d]
            # 中心は基準点から後ろへ length / 2 の所（横のずれが無い）
            self.assertAlmostEqual(mx, -hx * 6 / V.UNITS_PER_TILE, 6, d)
            self.assertAlmostEqual(my, -hy * 6 / V.UNITS_PER_TILE, 6, d)

    def test_tables(self):
        self.assertEqual({s["name"] for s in self.mod.VEHICLES}, {"pak256_railcar", "pak256_railcar_trailer"})
        for spec, raw, table, _ in self.each():
            self.assertEqual(raw, self.mod.yaml_lines(spec), spec["name"])  # yaml は道具が書く物と同じ
            self.assertEqual(table["length"], V.length_units(spec["real_length_m"]))
            self.assertEqual(table["length"], 12)  # 20m
            self.assertEqual(table["waytype"], "track")
            self.assertEqual(table["freight"], "Passagiere")
            self.assertEqual(table["cell_size"], 512)
            self.assertEqual(list(table["emptyimage"]), list(V.DIRECTIONS))
            for i, d in enumerate(V.DIRECTIONS):
                self.assertEqual(table["emptyimage"][d], f"{spec['stem']}.0.{i},-128,-128")
            self.assertEqual(table.get("engine_type") == "diesel", spec["powered"])
            self.assertEqual(table["power"] > 0, spec["powered"])

    def test_cells_at_rule_position(self):
        for spec, _, _, img in self.each():
            self.assertEqual(img.size, (512 * len(V.DIRECTIONS), 512))
            length = V.length_units(spec["real_length_m"])
            for i, d in enumerate(V.DIRECTIONS):
                kw, kh = V.RAIL_WIDTH_SCALE, V.RAIL_HEIGHT_SCALE
                whole = V.footprint(d, length, self.mod.WIDTH_M * kw, V.FRONT_UNITS, centered=True)
                bogie = V.footprint(d, length - 3, self.mod.BOGIE_WIDTH_M * kw, V.FRONT_UNITS - 1.5, centered=True)
                pts = []
                # 車体（床 〜 屋根）と、その下の台車（地面 〜 床。車体より狭い）
                for corners, zs in ((whole, (self.mod.FLOOR_M, self.mod.HEIGHT_M)), (bogie, (0.0,))):
                    for (x, y) in corners:
                        for z in zs:
                            sx, sy = V.to_screen(x, y, z * kh)
                            pts.append((sx + self.mod.PAD, sy + self.mod.PAD + V.RAIL_WHEEL_DROP_PX))
                ex = (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))
                box = img.crop((i * 512, 0, (i + 1) * 512, 512)).getchannel("A").getbbox()
                self.assertIsNotNone(box, d)
                for g, e, name in zip(box, ex, ("left", "top", "right", "bottom")):
                    self.assertLessEqual(abs(g - e), TOL, f"{spec['name']} {d} {name}: 絵 {box} 決まり {tuple(round(v, 1) for v in ex)}")

    def test_no_special_colors_and_binary_alpha(self):
        for spec, _, _, img in self.each():
            found = set()
            px = img.load()
            for y in range(img.height):
                for x in range(img.width):
                    r, g, b, a = px[x, y]
                    if a and (r << 16 | g << 8 | b) in SPECIAL:
                        found.add(f"{r:02X}{g:02X}{b:02X}")
            self.assertFalse(found, f"{spec['name']} 特別な色: {sorted(found)}")
            self.assertEqual(sum(img.getchannel("A").histogram()[1:255]), 0, spec["name"])

    def test_screen_size_is_twice_the_reference(self):
        # pak128.Japan の手本の 2 倍（長さは実物の換算のままで ±5px、幅・高さは ±2px）
        for spec, _, _, img in self.each():
            for got, want, tol, key in zip(screen_size(img, 512), self.mod.TARGET_PX, (5, TOL, TOL), ("長さ", "幅", "高さ")):
                self.assertLessEqual(abs(got - want), tol, f"{spec['name']} {key}: {got} 目標 {want}")

    def test_values_match_docs_table_and_translations(self):
        with open(os.path.join(ROOT, "docs", "vehicles.md"), encoding="utf-8") as f:
            text = f.read()
        for spec in self.mod.VEHICLES:
            doc = docs_row(text, spec["name"])
            self.assertEqual(int(doc["length"]), V.length_units(spec["real_length_m"]), spec["name"])
            for k in ("payload", "speed", "power", "gear", "weight", "cost", "runningcost", "intro_year"):
                self.assertEqual(doc[k], str(spec[k]), f"{spec['name']} {k}")
        for lang in ("ja", "en"):
            with open(os.path.join(ROOT, "text", lang + ".tab"), encoding="utf-8") as f:
                lines = [ln.rstrip("\r\n") for ln in f]
            for spec in self.mod.VEHICLES:
                self.assertIn(spec["name"], lines, f"{lang}: {spec['name']}")


if __name__ == "__main__":
    unittest.main()
