"""MIT License。#176 の確かめに使う試験用の物（仮の箱の絵）を、指定した場所にだけ組む。pak256 の配布には入れない。

使い方: python -X utf8 build_test.py <出す先（git 管理外）>。makeobj は PATH か環境変数 MAKEOBJ。
出る物（<出す先>/pak/）:
- t8_factory_4x4・t8_factory_6x6: 品を扱わない産業（大きな足跡の確かめ）
- t8_stop_2x1: type=stop の 2×1 の駅、t8_ext_2x1・t8_ext_2x2: type=extension の駅舎
- t8_longbus: 1 枚の車体の長いバス（length 14。実物 18m の連節バスをバスと同じ比で描いた長さ）
- t8_ship_bow・t8_ship_mid: length 64 の船の形の箱（224.5m を 0.47 倍）。基準点が船首の先か、船の中ほどか
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "objects", "vehicle", "road"))
import draw_vehicles as D  # noqa: E402
import vehicles as V  # noqa: E402

OUT = os.path.abspath(sys.argv[1])
MAKEOBJ = os.environ.get("MAKEOBJ", "makeobj")
COLORS = [(200, 70, 60), (70, 140, 70), (70, 100, 190), (210, 170, 60), (150, 90, 170), (60, 170, 170)]


def tile_block(color, height, label):
    """1 タイル分の箱（256 のセル）。上の面に番号を書く。"""
    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top, right, bottom, left = (128, 132 - height), (248, 192 - height), (128, 252 - height), (8, 192 - height)
    d.polygon([left, bottom, (128, 252), (8, 192)], fill=color)
    d.polygon([bottom, right, (248, 192), (128, 252)], fill=D.shade(color, 0.7))
    d.polygon([top, right, bottom, left], fill=D.shade(color, 1.2))
    d.text((112, 184 - height), label, fill=(0, 0, 0))
    return img


def make(name, cell, dat, sheet):
    folder = os.path.join(OUT, "src", name)
    os.makedirs(folder, exist_ok=True)
    os.makedirs(os.path.join(OUT, "pak"), exist_ok=True)
    sheet.save(os.path.join(folder, name + ".png"))
    with open(os.path.join(folder, name + ".dat"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(dat) + "\n")
    pak = os.path.join(OUT, "pak", name + ".pak")
    r = subprocess.run([MAKEOBJ, f"pak{cell}", pak, folder.replace(os.sep, "/") + "/"], capture_output=True)
    log = (r.stdout + r.stderr).decode("utf-8", "replace")
    bad = [x for x in log.splitlines() if x.startswith(("Warning", "ERROR"))]
    print(name, "ok" if os.path.exists(pak) and not bad else bad or log)


def building(name, sx, sy, layouts, head, height, icon=False):
    """sx × sy の建物。layouts が 2 なら、2 つ目の向きは縦横を入れ替える。"""
    keys, cells = [], []
    for layout in range(layouts):
        w, h = (sx, sy) if layout % 2 == 0 else (sy, sx)
        for y in range(h):
            for x in range(w):
                keys.append((layout, y, x))
                cells.append(tile_block(COLORS[len(cells) % len(COLORS)], height, f"{layout}:{x},{y}"))
    sheet = Image.new("RGBA", (256 * len(cells), 256), (0, 0, 0, 0))
    for i, c in enumerate(cells):
        sheet.paste(c, (i * 256, 0))
    dat = head + [f"name={name}", "copyright=pak256 test", f"dims={sx},{sy},{layouts}", "intro_year=1900"]
    dat += [f"backimage[{lo}][{y}][{x}][0][0]={name}.0.{i}" for i, (lo, y, x) in enumerate(keys)]
    if icon:  # アイコンが無いと、駅の道具が作られない
        dat += [f"icon=> {name}.0.0", f"cursor={name}.0.0"]
    make(name, 256, dat, sheet)


class Box:
    """cell のセルに、基準点を ref に置いて箱を描く（draw_vehicles.Canvas と同じ 3 倍描き）。"""

    def __init__(self, cell, ref):
        self.cell, self.ref = cell, ref
        self.img = Image.new("RGBA", (cell * D.SS, cell * D.SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def scr(self, p, z):
        sx, sy = V.to_screen(p[0], p[1], z)
        return (sx - V.ORIGIN[0] + self.ref[0]) * D.SS, (sy - V.ORIGIN[1] + self.ref[1]) * D.SS

    def block(self, corners, z0, z1, color):
        cx = (corners[0][0] + corners[2][0]) / 2
        cy = (corners[0][1] + corners[2][1]) / 2
        for a, b, k, is_front in D.visible_faces(corners, cx, cy):
            col = D.shade(color, k) if not is_front else (235, 200, 40)  # 前の面は黄色
            self.d.polygon([self.scr(a, z0), self.scr(b, z0), self.scr(b, z1), self.scr(a, z1)], fill=col)
        self.d.polygon([self.scr(p, z1) for p in corners], fill=D.shade(color, 1.2))

    def finish(self):
        img = self.img.resize((self.cell, self.cell), Image.LANCZOS)
        alpha = img.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
        img.putalpha(alpha)
        return img


def vehicle(name, cell, ref, length, width_m, height_m, head, front_units=0, centered=False):
    sheet = Image.new("RGBA", (cell * 8, cell), (0, 0, 0, 0))
    for i, direction in enumerate(V.DIRECTIONS):
        box = Box(cell, ref)
        box.block(V.footprint(direction, length, width_m, front_units, centered), 0.5, height_m, (60, 90, 170))
        sheet.paste(box.finish(), (i * cell, 0))
    off = (ref[0] - V.ORIGIN[0], ref[1] - V.ORIGIN[1])
    pos = f",{-off[0]},{-off[1]}" if off != (0, 0) else ""
    dat = ["obj=vehicle", f"name={name}", "copyright=pak256 test", "intro_year=1900", f"length={length}"] + head
    dat += [f"EmptyImage[{d.upper()}]={name}.0.{i}{pos}" for i, d in enumerate(V.DIRECTIONS)]
    make(name, cell, dat, sheet)


for n, size in (("t8_factory_4x4", 4), ("t8_factory_6x6", 6)):
    building(n, size, size, 1, ["obj=factory", "location=Land", "mapcolor=176", "distributionweight=1", "productivity=80",
                                "range=0", "needs_ground=1"], 40)
building("t8_stop_2x1", 2, 1, 2, ["obj=building", "type=stop", "waytype=track", "enables_pax=1", "level=2", "noinfo=1"], 20, True)
building("t8_ext_2x1", 2, 1, 2, ["obj=building", "type=extension", "waytype=track", "enables_pax=1", "level=2"], 60, True)
building("t8_ext_2x2", 2, 2, 1, ["obj=building", "type=extension", "waytype=track", "enables_pax=1", "level=2"], 60, True)

# 長いバス: pak256 のバスと同じ倍率（幅 1.22・高さ 1.30）。512 のセルに、基準点を (256, 320) に置く
vehicle("t8_longbus", 512, (256, 320), 14, 2.5 * 1.22, 3.2 * 1.30,
        ["waytype=road", "freight=Passagiere", "payload=100", "engine_type=diesel", "power=250", "speed=60", "gear=80",
         "weight=15", "cost=1000000", "runningcost=50"])
# 大型船の形の箱: 幅 12m・高さ 10m は仮の値（手本の幅と高さの実物比は確かめていない）。1536 のセルに、基準点を真ん中に置く
SHIP = ["waytype=water", "freight=Passagiere", "payload=500", "engine_type=diesel", "power=2000", "speed=30", "gear=100",
        "weight=500", "cost=1000000", "runningcost=100"]
vehicle("t8_ship_bow", 1536, (768, 768), 64, 12.0, 10.0, SHIP, 0, True)
vehicle("t8_ship_mid", 1536, (768, 768), 64, 12.0, 10.0, SHIP, 32, True)
