"""炭鉱と石炭火力の発電所の絵と表を書き出す（docs/industry.md）。MIT License。絵は仮（箱を数式で描いた物）。

- 縮尺・タイルの座標は objects/city/town_buildings/draw_buildings.py と同じ（1 タイル = 26.4m、高さ 1m = 5.94px）。
- 産業は複数のタイルにまたがる（炭鉱 2x2、発電所 3x3）。物はメートルの座標 (x, y)（x は右下の向き、y は左下の向き）で
  並べ、タイルごとに、そのタイルの上に立つ部分だけを 256x256 のセルに描く。シートは (列 = x のタイル, 行 = y のタイル) の
  並びで、セルの名前は <名前>.<行>.<列>。
- 壁は、壁の端があるタイルにだけ描く。屋根は、タイルの範囲で切って描く。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/industry/coal_chain/draw_industry.py
"""
import importlib.util
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
_B = os.path.join(os.path.dirname(os.path.dirname(HERE)), "city", "town_buildings", "draw_buildings.py")
_spec = importlib.util.spec_from_file_location("draw_buildings", _B)
db = importlib.util.module_from_spec(_spec)
sys.modules["draw_buildings"] = db
_spec.loader.exec_module(db)

CELL = db.CELL
TILE_M = db.TILE_M


class Tile:
    """1 タイル分のセル。(tx, ty) は産業の中でのタイルの位置。物はメートルの座標で渡す。"""

    def __init__(self, tx, ty):
        self.tx, self.ty = tx, ty
        self.cv = db.Canvas()
        self.top = 10**9  # 描いた点の一番上（y の最小値）。セルをはみ出していないかの確かめ

    def _poly(self, pts, rgb):
        for _, y in pts:
            self.top = min(self.top, y)
        self.cv.poly(pts, rgb)

    def _clip(self, m0, m1, t):
        a = max(m0 / TILE_M, t) - t
        b = min(m1 / TILE_M, t + 1) - t
        return (a, b) if b > a + 1e-9 else None

    def box(self, x0, x1, y0, y1, z0, z1, wall, roof):
        """平らな屋根の箱。x が u の向き、y が v の向き（m）。"""
        cu, cv_ = self._clip(x0, x1, self.tx), self._clip(y0, y1, self.ty)
        if not (cu and cv_):
            return
        (u0, u1), (v0, v1) = cu, cv_
        # 壁は、壁の端が（右下は x1、左下は y1）このタイルの中にあるときだけ
        if self.ty < y1 / TILE_M <= self.ty + 1 + 1e-9:
            self._poly([db.P(u0, v1, z0), db.P(u1, v1, z0), db.P(u1, v1, z1), db.P(u0, v1, z1)],
                       db.shade(wall, db.LIT_SW))
        if self.tx < x1 / TILE_M <= self.tx + 1 + 1e-9:
            self._poly([db.P(u1, v0, z0), db.P(u1, v1, z0), db.P(u1, v1, z1), db.P(u1, v0, z1)],
                       db.shade(wall, db.LIT_SE))
        self._poly([db.P(u0, v0, z1), db.P(u1, v0, z1), db.P(u1, v1, z1), db.P(u0, v1, z1)],
                   db.shade(roof, db.LIT_ROOF))

    def pile(self, x0, x1, y0, y1, h, rgb):
        """石炭の山。段を重ねた箱で描く（上へ向けて小さくなる 3 段）。"""
        for i, k in enumerate((0.0, 0.18, 0.34)):
            z0, z1 = h * i / 3, h * (i + 1) / 3
            dx, dy = (x1 - x0) * k, (y1 - y0) * k
            self.box(x0 + dx, x1 - dx, y0 + dy, y1 - dy, z0, z1, db.shade(rgb, 1.0 + 0.12 * i), db.shade(rgb, 1.25 + 0.12 * i))

    def finish(self):
        return self.cv.finish()


def sheet(w, h, scene):
    """w x h タイルの産業のシート。scene(tile) が、そのタイルに立つ物を描く。"""
    out = Image.new("RGB", (CELL * w, CELL * h), db.CLEAR)
    tops = []
    for ty in range(h):
        for tx in range(w):
            t = Tile(tx, ty)
            scene(t)
            out.paste(t.finish(), (tx * CELL, ty * CELL))
            tops.append(((tx, ty), t.top))
    for pos, top in tops:
        assert top >= 0, f"タイル {pos} の絵がセルの上をはみ出す（y={top:.1f}）。高さを下げるか cell_size を使う"
    return out


# ---- 炭鉱（2x2 タイル = 52.8m 四方）。立坑の櫓・巻上げ小屋・積込み小屋・石炭の山 ----

STEEL = (96, 104, 112)
CONCRETE = (166, 164, 158)
COAL = (74, 70, 72)


def scene_mine(t):
    t.box(0, 52.8, 0, 52.8, 0, 0.2, CONCRETE, (150, 148, 142))  # 舗装
    t.box(22, 36, 8, 20, 0.2, 7.0, (150, 96, 76), (96, 92, 90))  # 巻上げ小屋（煉瓦）
    t.box(5, 31, 31, 47, 0.2, 6.0, (150, 160, 170), (112, 118, 124))  # 積込み小屋（トタン）
    t.box(12.5, 18.5, 11, 17, 0.2, 14.0, STEEL, (80, 86, 92))  # 櫓の脚
    t.box(11.5, 19.5, 10, 18, 14.0, 17.0, (84, 90, 98), (70, 74, 80))  # 櫓の上の覆い（巻上げ車の小屋）
    t.pile(34, 50, 30, 46, 6.5, COAL)  # 石炭の山


MINE = dict(
    key="coal_mine", name="pak256_coal_mine", w=2, h=2, scene=scene_mine,
    dat={
        "location": "Land", "mapcolor": 176, "distributionweight": 1,
        "outputgood": ["Kohle"], "outputcapacity": [300],
        "productivity": 80, "range": 50,
        "electricity_amount": 150, "electricity_boost": 800,
        "mail_demand": 0, "mail_boost": 0, "passenger_demand": 20, "passenger_boost": 500,
        "needs_ground": 1, "intro_year": 1700,
    },
    note="炭鉱。立坑の櫓（高さ 17m）・巻上げ小屋・積込み小屋・石炭の山。2x2 タイル。値は pak128 の shaft_coal_mine に合わせた",
)


# ---- 石炭火力の発電所（3x3 タイル = 79.2m 四方）。ボイラー棟・タービン棟・煙突・石炭置き場・開閉所 ----

def scene_plant(t):
    t.box(0, 79.2, 0, 79.2, 0, 0.2, CONCRETE, (150, 148, 142))  # 舗装
    t.box(8, 32, 8, 28, 0.2, 20.0, (176, 120, 96), (110, 106, 102))  # ボイラー棟（煉瓦）
    t.box(8, 52, 31, 51, 0.2, 14.0, (200, 196, 184), (120, 118, 112))  # タービン棟
    t.box(39, 45, 11, 17, 0.2, 4.0, (186, 180, 170), (120, 118, 112))  # 煙突の基部
    t.box(40, 44, 12, 16, 4.0, 28.0, (190, 74, 60), (110, 70, 64))  # 煙突
    t.box(56, 72, 8, 26, 0.2, 8.0, (110, 112, 118), (86, 88, 92))  # 石炭の搬入棟
    t.box(58, 72, 40, 50, 0.2, 3.0, (150, 154, 160), (130, 134, 140))  # 開閉所
    t.pile(56, 72, 54, 70, 7.0, COAL)  # 石炭置き場


PLANT = dict(
    key="coal_power_plant", name="pak256_coal_power_plant", w=3, h=3, scene=scene_plant,
    dat={
        "location": "Land", "mapcolor": 131, "distributionweight": 2,
        "productivity": 600, "range": 40,
        "electricity_amount": 800, "electricity_boost": 0,
        "mail_demand": 5, "mail_boost": 500, "passenger_demand": 20, "passenger_boost": 800,
        "inputgood": ["Kohle"], "inputcapacity": [8000], "inputsupplier": [0], "inputfactor": [50],
        "needs_ground": 1, "intro_year": 1890,
    },
    note="石炭火力の発電所。ボイラー棟（20m）・タービン棟・煙突（28m）・石炭置き場。3x3 タイル。値は pak128 の old_powerplant_kraftwerk に合わせた",
)

OBJECTS = [MINE, PLANT]


def fmt(v):
    if isinstance(v, list):
        return "[" + ", ".join(str(x) for x in v) + "]"
    return str(v)


def table(o):
    lines = [
        "# 産業（絵は仮）。この表と PNG は draw_industry.py が書き出す。直すときはスクリプトを直して流し直す。",
        "# 1 タイル = 26.4m の縮尺（docs/industry.md）。",
        "obj: factory",
        f"name: {o['name']}",
        "copyright: pak256.LongScale チーム",
        f"# {o['note']}",
    ]
    for k, v in o["dat"].items():
        lines.append(f"{k}: {fmt(v)}")
    lines += [
        f"dims: {o['w']},{o['h']}",
        "backimage:        # backimage[配置][y][x][高さ][コマ]。絵は draw_industry.py が描く",
        "  0:",
    ]
    for y in range(o["h"]):
        cells = ", ".join(f"{x}: {{0: {{0: {o['key']}.{y}.{x}}}}}" for x in range(o["w"]))
        lines.append(f"    {y}: {{{cells}}}")
    return "\n".join(lines) + "\n"


def main():
    for o in OBJECTS:
        sheet(o["w"], o["h"], o["scene"]).save(os.path.join(HERE, f"{o['key']}.png"))
        with open(os.path.join(HERE, f"{o['key']}.yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(table(o))


if __name__ == "__main__":
    main()
