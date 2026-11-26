"""旅客機の絵と表を書き出す（docs/airport.md・#155）。MIT License。
絵は仮（多角形を組んだ 3 発の単葉機）で、見た目は後から描き直す。他の pak の絵は使わない。

- 画面の大きさは pak128 の同じ時代の旅客機（Junkers Ju 52）の手本の 2 倍（docs/standards.md の 4 章の道路の車両と同じ考え方）:
  胴の長さ 152px・翼の幅 260px。`length` はその長さから決める（`vehicles.length_from_px`）。
- 描画位置は、機首を基準点に置き、胴を後ろへ伸ばす。飛行機は車線のずれが無いので、道の中心に描く。
- 翼の幅が 1 タイルを超えるので、512 のセルに描く（cell_size と位置合わせ -128,-128）。
- 影は描かない。飛んでいる間の影は、本体が同じ絵を黒の半透明で地面に描く。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/vehicle/air/draw_aircraft.py
"""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import vehicles as V  # noqa: E402

CELL = 512
PAD = (CELL - V.CELL) // 2
SS = 3

SKIN = (196, 202, 210)
WING = (178, 186, 196)
TAIL = (60, 96, 140)
ENGINE = (88, 90, 98)
PROP = (52, 52, 56)
GLASS = (58, 72, 88)
WHEEL = (38, 38, 42)

# 値は pak128 の Junkers Ju 52 の機能上の数値（docs/airport.md の表）。登場年だけ pak256 の開始年
SPEC = dict(
    name="pak256_airliner", dir="airliner", stem="airliner",
    payload=18, speed=211, power=1599, weight=7, gear=50, cost=2110146, runningcost=65, intro_year=1930,
    target_px=(152, 260),  # 胴の長さ・翼の幅（画面の横向きの px）
)

# makeobj の特別な色を避ける
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}


def length_of(spec=SPEC):
    return V.length_from_px(spec["target_px"][0])


def span_m(spec=SPEC):
    """翼の幅（m）。画面の横向きの px から。"""
    return spec["target_px"][1] / V.PX_PER_UNIT_SIDE * V.M_PER_UNIT


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


class Plane:
    """機首を原点に、後ろ向きの距離 a（m）・右向きの距離 s（m）・高さ z（m）で描く。"""

    def __init__(self, direction):
        self.img = Image.new("RGBA", (CELL * SS, CELL * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.hx, self.hy = V.HEADING[direction]
        self.rx, self.ry = -self.hy, self.hx

    def ground(self, a, s):
        x = (-self.hx * a + self.rx * s) / V.M_PER_TILE
        y = (-self.hy * a + self.ry * s) / V.M_PER_TILE
        return x, y

    def scr(self, a, s, z):
        x, y = self.ground(a, s)
        sx, sy = V.to_screen(x, y, z)
        return (sx + PAD) * SS, (sy + PAD) * SS

    def poly(self, pts, colour):
        self.d.polygon([self.scr(*p) for p in pts], fill=colour)

    def depth(self, a, s):
        """画面の手前ほど大きい。"""
        x, y = self.ground(a, s)
        return x + y

    def tube(self, a0, a1, w0, w1, z0, z1, colour, at=0.0):
        """前後で太さが変わる筒（a0 が前、w は幅の半分、at は中心の左右の位置）。見える側面・端の面と上の面を描く。"""
        cx, cy = self.ground((a0 + a1) / 2, at)
        ring = [(a0, at + w0), (a0, at - w0), (a1, at - w1), (a1, at + w1)]  # 前の右・前の左・後の左・後の右
        for i, k in zip(range(4), (1.0, 0.86, 0.72, 0.86)):
            (pa, ps), (qa, qs) = ring[i], ring[(i + 1) % 4]
            p, q = self.ground(pa, ps), self.ground(qa, qs)
            nx, ny = q[1] - p[1], -(q[0] - p[0])
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            if nx * (mx - cx) + ny * (my - cy) < 0:
                nx, ny = -nx, -ny
            if nx + ny <= 1e-9:
                continue
            self.poly([(pa, ps, z0), (qa, qs, z0), (qa, qs, z1), (pa, ps, z1)], shade(colour, k))
        self.poly([(a, s, z1) for a, s in ring], shade(colour, 1.08))

    def finish(self):
        img = self.img.resize((CELL, CELL), Image.LANCZOS)
        px = img.load()
        for y in range(CELL):
            for x in range(CELL):
                r, g, b, a = px[x, y]
                if a < 128:
                    px[x, y] = (0, 0, 0, 0)
                    continue
                if (r << 16 | g << 8 | b) in SPECIAL:
                    r = r + 1 if r < 255 else r - 1
                px[x, y] = (r, g, b, 255)
        return img


def draw_cell(direction):
    """1 方向のセル（512x512、RGBA）。"""
    p = Plane(direction)
    length = length_of() * V.M_PER_UNIT  # 胴の長さ（m）
    half = span_m() / 2
    wing_z = 1.6

    # 車輪（主脚 2 つと尾輪）
    for a, s in ((length * 0.30, 3.2), (length * 0.30, -3.2), (length * 0.92, 0.0)):
        p.tube(a - 0.6, a + 0.6, 0.35, 0.35, 0.0, 1.2, WHEEL, at=s)

    # 主翼（低翼）。左右を奥から
    for sign in sorted((1, -1), key=lambda s: p.depth(length * 0.36, s * half / 2)):
        p.poly([(length * 0.24, 0.0, wing_z), (length * 0.36, sign * half, wing_z),
                (length * 0.46, sign * half, wing_z), (length * 0.50, 0.0, wing_z)], shade(WING, 1.0 if sign > 0 else 0.94))
        # 翼のエンジンとプロペラ
        s = sign * half * 0.30
        p.tube(length * 0.20, length * 0.38, 0.85, 0.7, wing_z - 0.4, wing_z + 0.9, ENGINE, at=s)
        p.poly([(length * 0.19, s - 1.8, wing_z + 0.1), (length * 0.19, s + 1.8, wing_z + 0.1),
                (length * 0.19, s + 1.8, wing_z + 0.5), (length * 0.19, s - 1.8, wing_z + 0.5)], PROP)

    # 胴（機首から尾まで 3 つ）。奥の部分から描く
    parts = [
        (0.0, length * 0.14, 0.9, 1.5, 1.2, 3.4),
        (length * 0.14, length * 0.66, 1.5, 1.5, 1.2, 3.9),
        (length * 0.66, length, 1.5, 0.35, 1.8, 3.5),
    ]
    for a0, a1, w0, w1, z0, z1 in sorted(parts, key=lambda q: p.depth((q[0] + q[1]) / 2, 0.0)):
        p.tube(a0, a1, w0, w1, z0, z1, SKIN)
    # 窓（見える側の列）と操縦席
    side = 1 if p.depth(length * 0.4, 1.5) > p.depth(length * 0.4, -1.5) else -1
    for i in range(6):
        a = length * (0.24 + i * 0.07)
        p.poly([(a, side * 1.52, 2.7), (a + length * 0.035, side * 1.52, 2.7),
                (a + length * 0.035, side * 1.52, 3.3), (a, side * 1.52, 3.3)], GLASS)
    p.poly([(length * 0.10, 1.2, 3.55), (length * 0.10, -1.2, 3.55), (length * 0.16, -1.3, 3.95), (length * 0.16, 1.3, 3.95)], GLASS)
    # 機首のエンジンとプロペラ
    p.tube(-0.2, length * 0.06, 0.85, 0.9, 1.7, 3.1, ENGINE)
    p.poly([(-0.3, -1.8, 2.3), (-0.3, 1.8, 2.3), (-0.3, 1.8, 2.6), (-0.3, -1.8, 2.6)], PROP)

    # 水平尾翼と垂直尾翼
    for sign in sorted((1, -1), key=lambda s: p.depth(length * 0.9, s * half * 0.2)):
        p.poly([(length * 0.82, 0.0, 3.0), (length * 0.90, sign * half * 0.34, 3.0),
                (length * 0.98, sign * half * 0.34, 3.0), (length * 0.99, 0.0, 3.0)], shade(WING, 0.96))
    p.poly([(length * 0.80, 0.0, 3.3), (length * 0.92, 0.0, 6.4), (length * 0.99, 0.0, 6.4), (length, 0.0, 3.3)], TAIL)
    return p.finish()


def yaml_text(spec=SPEC):
    length = length_of(spec)
    stem = spec["stem"]
    lines = [
        "# 旅客機（絵は仮）。この表と PNG は ../draw_aircraft.py が書き出す。直すときはスクリプトを直して流し直す。",
        "# 値は pak128 の Junkers Ju 52 の機能上の数値（docs/airport.md）。",
        "obj: vehicle",
        f"name: {spec['name']}",
        "copyright: pak256.LongScale チーム",
        "waytype: air",
        "cell_size: 512",
        "freight: Passagiere",
        f"payload: {spec['payload']}",
        "engine_type: diesel",
        f"power: {spec['power']}",
        f"speed: {spec['speed']}",
        f"gear: {spec['gear']}",
        f"intro_year: {spec['intro_year']}",
        f"cost: {spec['cost']}",
        f"runningcost: {spec['runningcost']}",
        f"weight: {spec['weight']}",
        f"length: {length}",
        "constraint:       # 1 機で飛ぶ（前にも後ろにもつながない）",
        "  prev: {0: none}",
        "  next: {0: none}",
        "emptyimage:       # 向きごとの絵（画像名,x の位置合わせ,y の位置合わせ）",
    ]
    for i, direction in enumerate(V.DIRECTIONS):
        lines.append(f"  {direction}: \"{stem}.0.{i},{-PAD},{-PAD}\"")
    return "\n".join(lines) + "\n"


def draw_sheet():
    sheet = Image.new("RGBA", (CELL * len(V.DIRECTIONS), CELL), (0, 0, 0, 0))
    for i, direction in enumerate(V.DIRECTIONS):
        sheet.paste(draw_cell(direction), (i * CELL, 0))
    return sheet


def main():
    out = os.path.join(HERE, SPEC["dir"])
    os.makedirs(out, exist_ok=True)
    draw_sheet().save(os.path.join(out, SPEC["stem"] + ".png"))
    with open(os.path.join(out, SPEC["stem"] + ".yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(yaml_text())
    print("wrote", os.path.join(out, SPEC["stem"] + ".png"))


if __name__ == "__main__":
    main()
