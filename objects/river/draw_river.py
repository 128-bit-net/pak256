"""川（水の道。system_type=255）の絵と表を書き出す（docs/config.md の「川」・#158）。MIT License。
絵は仮（数式で描いた水面と土の岸）で、見た目は後から描き直す。他の pak の絵は使わない。

- 地面の形と画素の置き方は objects/ground/temperate/draw_ground.py と同じ（column_span・solve_uv）。
  u は右下（東）、v は左下（南）。北の辺は v = 0（右上）、西の辺は u = 0（左上）。
- 川の中心線は、まっすぐ・行き止まりは直線、角（隣り合う 2 辺）はタイルの角を中心にした半径 0.5 の円弧。
  岸の細かい凸凹は、タイルの辺では 0 にして、隣のタイルと幅がそろうようにする。
- 夏の絵は季節 0、雪の絵は季節 1（岸が雪）。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/river/draw_river.py
"""
import importlib.util
import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OBJECTS = os.path.dirname(HERE)


def _load(name, *path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(OBJECTS, *path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gr = _load("draw_ground", "ground", "temperate", "draw_ground.py")

CELL = gr.CELL
COPYRIGHT = gr.COPYRIGHT

# 太い順（simuconf.tab の river_type[0]〜 と同じ順）。half は水面の半分の幅（タイル）。
# topspeed が 0 より大きい川だけを船が通れる（本体の water_vehicle_t::check_next_tile）。どの段も通れる。
TIERS = [
    dict(name="pak256_river_30", half=0.34, topspeed=30),
    dict(name="pak256_river_20", half=0.27, topspeed=20),
    dict(name="pak256_river_10", half=0.20, topspeed=10),
]

RIBI = ["-", "n", "e", "ne", "s", "ns", "se", "nse", "w", "nw", "ew", "new", "sw", "nsw", "sew", "nsew"]
N, E, S, W = 1, 2, 4, 8
MID = {N: (0.5, 0.0), E: (1.0, 0.5), S: (0.5, 1.0), W: (0.0, 0.5)}
CORNER = {N | E: (1.0, 0.0), S | E: (1.0, 1.0), S | W: (0.0, 1.0), N | W: (0.0, 0.0)}

# 坂の絵の番号（imageup の添字）と、四隅の高さ (sw, se, ne, nw)。本体の slope_t の north・west・east・south の順
SLOPES = {3: (1, 1, 0, 0), 6: (0, 1, 1, 0), 9: (1, 0, 0, 1), 12: (0, 0, 1, 1)}
# 坂を流れる向き（坂の上の辺と下の辺をつなぐ ribi）
SLOPE_RIBI = {3: N | S, 6: E | W, 9: E | W, 12: N | S}

BANK = 0.045  # 土の岸の幅（タイル）


def _segment(u, v, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    t = max(0.0, min(1.0, ((u - ax) * dx + (v - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(u - ax - t * dx, v - ay - t * dy)


def distance(ribi, u, v):
    """(u, v) から川の中心線までの距離（タイル）。"""
    sides = [b for b in (N, E, S, W) if ribi & b]
    if not sides:
        return math.hypot(u - 0.5, v - 0.5)
    if len(sides) == 1:
        return _segment(u, v, MID[sides[0]], (0.5, 0.5))
    if len(sides) == 2:
        if ribi in CORNER:
            cx, cy = CORNER[ribi]
            return abs(math.hypot(u - cx, v - cy) - 0.5)
        return _segment(u, v, MID[sides[0]], MID[sides[1]])
    # 3・4 方向: 中央への直線と、隣り合う 2 辺の円弧（合流の内側を丸くする）
    best = min(_segment(u, v, MID[s], (0.5, 0.5)) for s in sides)
    for pair, (cx, cy) in CORNER.items():
        if ribi & pair == pair:
            best = min(best, abs(math.hypot(u - cx, v - cy) - 0.5))
    return best


def _bank_noise(u, v):
    """岸の凸凹。タイルの辺では 0。"""
    window = min(1.0, 6 * min(u, 1 - u, v, 1 - v))
    return window * (gr.vnoise(u, v, 7, 7, 91) - 0.5) * 0.05


def colour(ribi, half, snow, x, y, u, v, slope):
    """画素 (x, y)（地面の点 (u, v)）の色。川でなければ None。"""
    d = distance(ribi, u, v) + _bank_noise(u, v)
    if d >= half + BANK:
        return None
    a, b = gr.lattice(x, y)
    g = gr.grain(x, y, 57, 0.10)
    if d >= half:  # 岸: 水ぎわは濃い土、外側は明るい土（雪の絵は雪）
        k = (d - half) / BANK
        near, far = ((176, 192, 208), (232, 236, 244)) if snow else ((100, 86, 60), (146, 128, 90))
        return gr.rgba(*[c * g for c in gr.mix(near, far, k)])
    depth = min(1.0, (half - d) / (half * 0.6))  # 中ほどほど濃い
    shallow, deep = ((86, 126, 156), (50, 90, 130)) if snow else ((92, 142, 168), (60, 112, 160))
    r, gg, bl = gr.mix(shallow, deep, depth)
    wave = 0.6 * math.sin(2 * math.pi * (a + 2 * b)) + 0.4 * math.sin(2 * math.pi * (3 * a - 2 * b))
    k = 1.0 + 0.045 * wave
    r, gg, bl = r * k, gg * k, bl * k
    if slope:  # 坂は流れの方向に沿った白い筋
        along = v if ribi == (N | S) else u
        across = u if ribi == (N | S) else v
        streak = gr.vnoise(along, across, 3, 23, 63 + slope)
        if streak > 0.62:
            t = min(1.0, (streak - 0.62) * 3)
            r, gg, bl = gr.mix((r, gg, bl), (214, 228, 236), t * (0.9 if slope > 1 else 0.6))
    return gr.rgba(r, gg, bl)


def cell(ribi, half, snow, corners=(0, 0, 0, 0)):
    """地面の形（corners の坂）に川を塗った 1 マス。"""
    sw, se, ne, nw = corners
    steps = max(corners)

    def height(u, v):
        return nw * (1 - u) * (1 - v) + ne * u * (1 - v) + sw * (1 - u) * v + se * u * v

    spans = gr.column_span(sw, se, ne, nw)
    pix = [(0, 0, 0, 0)] * (CELL * CELL)
    for y in range(40, CELL):
        for x in range(CELL):
            if not gr.covered(spans, x, y):
                continue
            if steps:
                u, v = gr.solve_uv(x, y, height)
            else:
                a, b = (x + 0.5 - 128) / 128, (y + 0.5 - 128) / 64 - 1
                u, v = (b + 1 + a) / 2, (b + 1 - a) / 2
                if not (0 <= u <= 1 and 0 <= v <= 1):
                    u, v = min(1.0, max(0.0, u)), min(1.0, max(0.0, v))
            c = colour(ribi, half, snow, x, y, u, v, steps)
            if c is not None:
                pix[y * CELL + x] = c
    return gr.from_pixels(pix)


COLS = 8


def sheet(tier):
    """8 列。行 0・1 は ribi の番号順（16 枚）、行 2 は坂 4 枚と 2 段の坂 4 枚。行 3〜5 は同じ並びの雪。"""
    out = Image.new("RGBA", (CELL * COLS, CELL * 6), (0, 0, 0, 0))
    for snow in (0, 1):
        row = snow * 3
        for ribi in range(16):
            out.paste(cell(ribi, tier["half"], snow), ((ribi % COLS) * CELL, (row + ribi // COLS) * CELL))
        for i, (key, corners) in enumerate(SLOPES.items()):
            for step in (1, 2):
                col = i + (step - 1) * 4
                out.paste(cell(SLOPE_RIBI[key], tier["half"], snow, tuple(c * step for c in corners)),
                          (col * CELL, (row + 2) * CELL))
    return out


def table(tier):
    n = tier["name"]
    lines = [
        "- obj: way",
        f"  name: {n}",
        f"  copyright: {COPYRIGHT}",
        "  waytype: water",
        "  system_type: 255",
        "  cost: 0",
        "  maintenance: 0",
        f"  topspeed: {tier['topspeed']}",
        "  max_weight: 999",
        "  intro_year: 1",
        "  draw_as_ding: 1",
        "  image:            # つながる向き（n 北・e 東・s 南・w 西）ごとの絵。[0] 夏・[1] 雪",
    ]
    for i, r in enumerate(RIBI):
        lines.append(f"    \"{r}\": {{0: {n}.{i // COLS}.{i % COLS}, 1: {n}.{3 + i // COLS}.{i % COLS}}}")
    for key_name, col0, comment in (("imageup", 0, "1 段の坂"), ("imageup2", 4, "2 段の坂")):
        lines.append(f"  {key_name}:          # {comment}。3 北・6 西・9 東・12 南の坂")
        for i, key in enumerate(SLOPES):
            lines.append(f"    {key}: {{0: {n}.2.{col0 + i}, 1: {n}.5.{col0 + i}}}")
    return "\n".join(lines) + "\n"


def main():
    head = ("# 川（絵は仮）。この表と PNG は draw_river.py が書き出す（docs/config.md の「川」）。\n"
            "# 太い順。simuconf.tab の river_type[0]〜 に同じ順で並べる。どの段も船が通れる。\n")
    for tier in TIERS:
        sheet(tier).save(os.path.join(HERE, tier["name"] + ".png"))
    with open(os.path.join(HERE, "river.yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(head + "".join(table(t) for t in TIERS))


if __name__ == "__main__":
    main()
