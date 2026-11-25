"""地面一式（温帯）の絵と dat を書き出す。MIT License。

使い方（このフォルダで）:
    python -X utf8 draw_ground.py [出力先]     出力先の既定はこのフォルダ。Outside は出力先の隣の Outside/ に出る

pak256.LongScale の地面は、タイルが 256px（菱形は幅 256・高さ 128）、高さ 1 段が 32px
（simuconf.tab の tile_height = 8）。絵はすべてこのスクリプトが数式から描く（他の pak の絵は使わない）。
どの絵も、タイルの並び方（斜め格子）の周期に合わせてあるので、隣のタイルと継ぎ目なく並ぶ。
決め事は docs/ground.md にまとめてある。

書き出すもの（dat の Name ＝ 本体が探す名前。drawn する PNG は 256 マスのシート）:
    Outside / ClimateTexture / LightTexture / ShoreTrans / SlopeTrans / Water /
    Slopes / Basement / Fence / Marker / Borders
Shore は pak128 にも無く、本体も無くて動くので作らない（docs/ground.md）。
"""
import math
import os
import sys

from PIL import Image, ImageDraw

CELL = 256          # 1 マス = 1 タイルの幅
STEP = 32           # 高さ 1 段の画素（tile_height = 8 → 256/8）
COPYRIGHT = "pak256.LongScale チーム"

# makeobj が特別な色として読む色（描いた色がこれに当たると別の意味になるので、避ける）
_SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}


def rgba(r, g, b, a=255):
    """色を 0..255 に丸め、特別な色に当たるときは青を 1 ずらす。"""
    r = max(0, min(255, int(round(r))))
    g = max(0, min(255, int(round(g))))
    b = max(0, min(255, int(round(b))))
    if (r << 16 | g << 8 | b) in _SPECIAL:
        b = b + 1 if b < 255 else b - 1
    return (r, g, b, a)


# ---------------------------------------------------------------- 雑音（斜め格子の周期つき）

def _hash(i, j, seed):
    h = (i * 374761393 + j * 668265263 + seed * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFF) / 65535.0


def _smooth(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def vnoise(u, v, nu, nv, seed):
    """周期 (nu, nv) 個の格子の値の雑音。u, v は 0..1 を 1 周期とする座標。0..1 を返す。"""
    fu, fv = u * nu, v * nv
    i, j = math.floor(fu), math.floor(fv)
    tu, tv = _smooth(fu - i), _smooth(fv - j)
    i0, i1 = i % nu, (i + 1) % nu
    j0, j1 = j % nv, (j + 1) % nv
    a = _hash(i0, j0, seed)
    b = _hash(i1, j0, seed)
    c = _hash(i0, j1, seed)
    d = _hash(i1, j1, seed)
    return (a + (b - a) * tu) * (1 - tv) + (c + (d - c) * tu) * tv


def lattice(x, y):
    """マス内の画素 (x, y) を、斜め格子の周期（(128,64) と (128,-64) で一周）の座標 (a, b)（0..1）にする。"""
    return ((x + 2 * y) % 256) / 256.0, ((x - 2 * y) % 256) / 256.0


def warp(a, b, seed):
    """座標を周期つきの雑音でゆがめる（格子の向きが絵に出ないようにする）。"""
    return (a + 0.07 * (vnoise(a, b, 3, 3, seed + 50) - 0.5), b + 0.07 * (vnoise(a, b, 3, 3, seed + 51) - 0.5))


# ---------------------------------------------------------------- タイルの形

def corner_ys(sw, se, ne, nw):
    return 192 - STEP * sw, 256 - STEP * se, 192 - STEP * ne, 128 - STEP * nw


def column_span(sw, se, ne, nw):
    """列 x ごとに、地面が覆う行の範囲 [上, 下) を返す（上は含み、下は含まない。隣のタイルと隙間も重なりも出ない）。"""
    sy, ey, ny, wy = corner_ys(sw, se, ne, nw)
    spans = []
    for x in range(CELL):
        xc = x + 0.5
        if xc < 128:
            t = sy + (wy - sy) * xc / 128
            b = sy + (ey - sy) * xc / 128
        else:
            t = wy + (ny - wy) * (xc - 128) / 128
            b = ey + (ny - ey) * (xc - 128) / 128
        spans.append((t, b))
    return spans


def covered(spans, x, y):
    t, b = spans[x]
    return t <= y < b


def new_cell():
    return Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))


def from_pixels(pix):
    im = new_cell()
    im.putdata(pix)
    return im


# ---------------------------------------------------------------- 光の絵（LightTexture）

def solve_uv(x, y, hfunc):
    """画素 (x, y) の地面の点 (u, v)（u は北西→北東、v は北西→南西、0..1）を求める。"""
    d = (x + 0.5 - 128) / 128.0
    s = (y - 128) / 64.0
    u = v = 0.5
    for _ in range(14):
        u = min(1.0, max(0.0, (s + d) / 2))
        v = min(1.0, max(0.0, (s - d) / 2))
        s = ((y - 128) + STEP * hfunc(u, v)) / 64.0
    return u, v


def lightmap(sw, se, ne, nw):
    if min(sw, se, ne, nw) >= 1:        # 全部が上がった形は使われない（平らと同じにする）
        sw = se = ne = nw = 0
    spans = column_span(sw, se, ne, nw)

    def h(u, v):
        return nw * (1 - u) * (1 - v) + ne * u * (1 - v) + sw * (1 - u) * v + se * u * v

    pix = [(0, 0, 0, 0)] * (CELL * CELL)
    for y in range(40, CELL):
        for x in range(CELL):
            if not covered(spans, x, y):
                continue
            if sw == se == ne == nw:
                b = 134.0
            else:
                u, v = solve_uv(x, y, h)
                # 面は 2 枚の三角形（南西-北東の線で分ける）。三角形ごとに平らな陰にする（5bit の縞が出ないように）
                if u + v < 1:
                    gu, gv = ne - nw, sw - nw
                else:
                    gu, gv = se - sw, se - ne
                b = 134.0 + 26.0 * (gu - gv)
            b = max(90, min(205, b))
            pix[y * CELL + x] = rgba(b, b, b)
    return from_pixels(pix)


def flat_diamond(color_fn):
    """平らなタイルの形に color_fn(x, y) の色を塗る。"""
    spans = column_span(0, 0, 0, 0)
    pix = [(0, 0, 0, 0)] * (CELL * CELL)
    for y in range(128, CELL):
        for x in range(CELL):
            if covered(spans, x, y):
                pix[y * CELL + x] = color_fn(x, y)
    return from_pixels(pix)


# ---------------------------------------------------------------- 気候の絵（ClimateTexture）

CLIMATES = [
    # 名前, 暗い色, 明るい色（本体の気候の番号の順。温帯が 4）
    ("water", (60, 110, 160), (76, 128, 176)),
    ("desert", (196, 172, 112), (222, 200, 140)),
    ("tropic", (66, 132, 52), (104, 164, 70)),
    ("mediterran", (104, 138, 62), (148, 166, 84)),
    ("temperate", (72, 120, 52), (118, 160, 76)),
    ("tundra", (104, 120, 92), (138, 150, 118)),
    ("rocky", (112, 106, 98), (152, 146, 134)),
    ("arctic", (222, 228, 238), (246, 248, 252)),
]


def fbm(a, b, seed, octaves=((4, 0.45), (8, 0.30), (16, 0.17), (32, 0.08))):
    """周期つきの雑音を重ねる（0..1）。"""
    return sum(w * vnoise(a, b, n, n, seed + i) for i, (n, w) in enumerate(octaves))


def worley(a, b, n, seed):
    """周期 n の細胞雑音。(最も近い点までの距離, 2 番目までの距離, 最も近い細胞の乱数) を返す（細胞の大きさが 1）。"""
    fa, fb = (a % 1.0) * n, (b % 1.0) * n
    ia, ib = math.floor(fa), math.floor(fb)
    best = [9.0, 9.0, 0.0]
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ci, cj = ia + di, ib + dj
            hi, hj = ci % n, cj % n
            px = ci + 0.15 + 0.7 * _hash(hi, hj, seed)
            py = cj + 0.15 + 0.7 * _hash(hi, hj, seed + 1)
            d = math.hypot(fa - px, fb - py)
            if d < best[0]:
                best[1] = best[0]
                best[0], best[2] = d, _hash(hi, hj, seed + 2)
            elif d < best[1]:
                best[1] = d
    return best[0], best[1], best[2]


def mix(c0, c1, t):
    t = min(1.0, max(0.0, t))
    return tuple(c0[i] + (c1[i] - c0[i]) * t for i in range(3))


def grain(x, y, seed, amp=0.07):
    """細かい粒（周期は斜め格子と同じ）。明るさの倍率を返す。"""
    f = _hash((x + 2 * y) % 256, (x - 2 * y) % 256, seed + 9)
    return 1.0 - amp + 2 * amp * f


def tex_temperate(x, y, seed):
    dark, light = (72, 120, 52), (118, 160, 76)
    a, b = warp(*lattice(x, y), seed)
    n = fbm(a, b, seed)
    n = min(1.0, max(0.0, (n - 0.5) * 1.5 + 0.5))
    return [c * grain(x, y, seed, 0.07) for c in mix(dark, light, n)]


def tex_desert(x, y, seed):
    """砂丘のさざ波（うねる縞）と、ところどころの小石。"""
    a, b = warp(*lattice(x, y), seed)
    w = fbm(a, b, seed, ((2, 0.6), (4, 0.4)))
    ripple = 0.5 + 0.5 * math.sin(2 * math.pi * (5 * (a + b) + 9 * w))
    big = fbm(a, b, seed + 20, ((3, 0.4), (6, 0.3), (12, 0.2), (24, 0.1)))
    sand = mix((206, 178, 114), (232, 208, 148), 0.25 * ripple + 0.75 * big)
    d1, d2, r = worley(*lattice(x, y), 14, seed + 40)
    if d1 < 0.2 and r > 0.78:
        sand = mix(sand, (150, 124, 90), 0.8 - d1 * 3)
    return [c * grain(x, y, seed, 0.06) for c in sand]


def tex_tropic(x, y, seed):
    """濃い緑の下草。暗い茂みの塊と、明るい若葉の点。"""
    a, b = warp(*lattice(x, y), seed)
    n = fbm(a, b, seed, ((4, 0.35), (8, 0.3), (16, 0.2), (32, 0.15)))
    col = mix((34, 98, 40), (86, 160, 58), (n - 0.35) * 2.2)
    d1, d2, r = worley(*lattice(x, y), 20, seed + 30)
    if d1 < 0.28:
        col = mix(col, (116, 188, 66) if r > 0.5 else (22, 74, 34), 0.45 * (1 - d1 / 0.28))
    return [c * grain(x, y, seed, 0.08) for c in col]


def tex_mediterran(x, y, seed):
    """乾いたオリーブ色の草地に、赤茶の土と石のまだら。"""
    a, b = warp(*lattice(x, y), seed)
    n = fbm(a, b, seed)
    grass = mix((112, 134, 64), (170, 168, 88), (n - 0.3) * 2.0)
    soil_m = fbm(a, b, seed + 20, ((6, 0.45), (12, 0.35), (24, 0.2)))
    col = mix(grass, (176, 124, 84), (soil_m - 0.6) * 3.5)
    d1, d2, r = worley(*lattice(x, y), 16, seed + 40)
    if d1 < 0.18 and r > 0.7:
        col = mix(col, (196, 188, 170), 0.7)
    return [c * grain(x, y, seed, 0.07) for c in col]


def tex_tundra(x, y, seed):
    """灰緑のこけ・地衣類と、茶色の湿った土、残った雪の斑点。"""
    a, b = warp(*lattice(x, y), seed)
    n = fbm(a, b, seed)
    moss = mix((92, 108, 78), (146, 152, 112), (n - 0.3) * 2.0)
    m2 = fbm(a, b, seed + 20, ((6, 0.45), (12, 0.35), (24, 0.2)))
    col = mix(moss, (96, 80, 62), (m2 - 0.6) * 3.5)
    d1, d2, r = worley(*lattice(x, y), 18, seed + 40)
    if d1 < 0.2:
        col = mix(col, (176, 176, 140) if r > 0.55 else (70, 80, 66), 0.5 * (1 - d1 / 0.2))
    sn = fbm(a, b, seed + 60, ((5, 0.5), (10, 0.3), (20, 0.2)))
    if sn > 0.74:
        col = mix(col, (226, 230, 236), (sn - 0.74) * 4)
    return [c * grain(x, y, seed, 0.07) for c in col]


def tex_rocky(x, y, seed):
    """割れ目のある岩盤。板状の石が並び、板ごとに色が違う。"""
    a, b = warp(*lattice(x, y), seed)
    d1, d2, r = worley(a, b, 6, seed)
    edge = d2 - d1
    base = mix((104, 98, 92), (158, 150, 138), 0.2 + 0.7 * r)
    base = mix(base, (130, 118, 104), 0.4 * vnoise(a, b, 8, 8, seed + 5))
    fine = fbm(a, b, seed + 10, ((12, 0.5), (24, 0.3), (48, 0.2)))
    col = mix(base, (74, 70, 66), (fine - 0.5) * 1.2 + 0.2)
    if edge < 0.09:
        col = mix(col, (50, 46, 44), 1.0 - edge / 0.09)
    return [c * grain(x, y, seed, 0.08) for c in col]


def tex_arctic(x, y, seed):
    """雪原。ゆるい吹きだまりの青い影と、きらめく粒。"""
    a, b = warp(*lattice(x, y), seed)
    n = fbm(a, b, seed, ((2, 0.5), (4, 0.3), (8, 0.2)))
    # 明るさに余裕を残す（坂の明るい面は光の絵で明るくなるので、白く飛ばない上限にする）
    col = mix((190, 204, 226), (228, 236, 248), (n - 0.25) * 1.9)
    r = 0.5 + 0.5 * math.sin(2 * math.pi * (3 * (a - b) + 3 * n))
    col = mix(col, (172, 190, 218), 0.25 * r)
    f = _hash((x + 2 * y) % 256, (x - 2 * y) % 256, seed + 9)
    if f > 0.985:
        return (240, 244, 252)
    return [c * (0.97 + 0.06 * f) for c in col]


def tex_water_base(x, y, seed):
    """気候番号 0（水）の下絵。本体は水に Water を使うので見えない。"""
    a, b = warp(*lattice(x, y), seed)
    n = fbm(a, b, seed)
    return [c * grain(x, y, seed, 0.07) for c in mix((60, 110, 160), (76, 128, 176), n)]


CLIMATE_FUNCS = [tex_water_base, tex_desert, tex_tropic, tex_mediterran, tex_temperate,
                 tex_tundra, tex_rocky, tex_arctic]


def climate_texture(index):
    seed = 11 + index * 7
    fn = CLIMATE_FUNCS[index]
    im = Image.new("RGBA", (CELL, CELL))
    im.putdata([rgba(*fn(x, y, seed)) for y in range(CELL) for x in range(CELL)])
    return im


# ---------------------------------------------------------------- つなぎ目の絵（SlopeTrans・ShoreTrans）

# 本体は、坂の形ごとにこの絵を回して使う。回す前の絵（回転 0）で、四隅の高さ (sw, se, ne, nw)。
# 絵の座標は、左上が南西、右上が北西、左下が南東、右下が北東（ground_desc.cc の create_alpha_tile）。
SLOPE_TRANS_CORNERS = [
    (0, 0, 1, 1),   # 0: 南（北西+北東）
    (0, 1, 1, 1),   # 1: 北西+北東+南東
    (0, 0, 1, 0),   # 2: 北東
    (0, 1, 0, 1),   # 3: 南東+北西
    (0, 0, 2, 2),   # 4: 南 x2
    (0, 2, 2, 2),   # 5
    (0, 0, 2, 0),   # 6
    (0, 2, 0, 2),   # 7
    (0, 0, 1, 2),   # 8: 北西 x2 + 北東
    (2, 0, 1, 0),   # 9: 南西 x2 + 北東
    (0, 1, 1, 2),   # 10
    (2, 1, 2, 0),   # 11
    (2, 2, 1, 0),   # 12
    (0, 1, 2, 1),   # 13
    (2, 2, 2, 2),   # 14: 全部 x2
]


def _field(corners, size=256, wiggle=0.16, seed=3, radial=None):
    """四隅の高さから、絵の各画素の値（0〜2 ほど）の表を作る。縁では乱れを 0 にして、隣のタイルとつなぐ。
    radial = (R, 混ぜる割合) のとき、角からの距離で広がる項を混ぜる（海岸で、角のまわりに陸が丸く残る）。"""
    sw, se, ne, nw = corners
    pts = ((0, 0, sw), (1, 0, nw), (0, 1, se), (1, 1, ne))
    out = []
    for y in range(size):
        fy = (y + 0.5) / size
        for x in range(size):
            fx = (x + 0.5) / size
            h = sw * (1 - fx) * (1 - fy) + nw * fx * (1 - fy) + se * (1 - fx) * fy + ne * fx * fy
            if radial:
                rad = 0.0
                for px, py, v in pts:
                    if v > 0:
                        rad = max(rad, v * (1 - math.hypot(fx - px, fy - py) / radial[0]))
                h = h * (1 - radial[1]) + max(h, rad) * radial[1]
            win = 16 * fx * (1 - fx) * fy * (1 - fy)
            n = vnoise(fx, fy, 5, 5, seed) * 2 - 1
            out.append(h + wiggle * n * win)
    return out


def _step(h, edge, width):
    t = min(1.0, max(0.0, (h - (edge - width)) / (2 * width)))
    return _smooth(t)


def _disc(size, radius, seed, wiggle=0.03):
    """中央の円。円の内側が 0、外側が 1 の表（円のふちは少し乱す）。"""
    out = []
    for y in range(size):
        fy = (y + 0.5) / size
        for x in range(size):
            fx = (x + 0.5) / size
            d = math.hypot(fx - 0.5, fy - 0.5) + wiggle * (vnoise(fx, fy, 6, 6, seed) * 2 - 1)
            out.append(_step(d, radius, 0.03))
    return out


def slope_trans(index):
    corners = SLOPE_TRANS_CORNERS[index]
    pix = []
    if index == 14:                      # 四隅とも重ねるとき: 中央だけ元の気候を残す
        for v in _disc(CELL, 0.2, 31):
            pix.append(rgba(0, v * 248, 0))
        im = Image.new("RGBA", (CELL, CELL))
        im.putdata(pix)
        return im
    for h in _field(corners):
        g = _step(h, 0.5, 0.08)
        b = _step(h, 1.5, 0.08)
        pix.append(rgba(0, g * 248, b * 248))
    im = Image.new("RGBA", (CELL, CELL))
    im.putdata(pix)
    return im


# 浜（海岸）。四隅は陸の側を 1 とする（本体が水の隅を引いて渡す）。赤い所に水が出る。
SHORE_TRANS_CORNERS = [
    (0, 0, 1, 1),
    (0, 1, 1, 1),
    (0, 0, 1, 0),
    (0, 1, 0, 1),
    (0, 0, 1, 1), (0, 1, 1, 1), (0, 0, 1, 0), (0, 1, 0, 1),   # 4〜7: 2 段の坂用（0〜3 と同じ）
    (0, 0, 1, 1), (0, 1, 1, 1), (0, 0, 1, 0),                 # 8〜10
]


def shore_trans(index):
    if index == 11:                      # 四隅とも水の斜面: 四隅に水、中央に陸が丸く残る
        pix = [rgba(v * 255, 0, 0) for v in _disc(CELL, 0.4, 41)]
    else:
        pix = []
        for h in _field(SHORE_TRANS_CORNERS[index], wiggle=0.22, seed=17 + index, radial=(1.6, 0.5)):
            w = 1.0 - _step(h, 0.3, 0.06)
            pix.append(rgba(w * 255, 0, 0))
    im = Image.new("RGBA", (CELL, CELL))
    im.putdata(pix)
    return im


# ---------------------------------------------------------------- 水（Water）

WATER_FRAMES = 8
WATER_DEPTHS = 6
WATER_COLORS = [(72, 128, 174), (60, 112, 164), (50, 96, 152), (42, 82, 140), (34, 66, 124), (28, 54, 108)]


def water_cell(depth, frame):
    base = WATER_COLORS[depth]
    waves = [(1, 0, 1, 0.5), (0, 2, 1, 0.3), (2, 1, 2, 0.25), (1, 3, 3, 0.2), (3, -2, 2, 0.15)]

    def color(x, y):
        a, b = lattice(x, y)
        s = 0.0
        for m, n, w, amp in waves:
            s += amp * math.sin(2 * math.pi * (m * a + n * b + w * frame / WATER_FRAMES))
        k = 1.0 + 0.045 * s
        r, g, bl = base[0] * k, base[1] * k, base[2] * k
        if depth == 0 and s > 0.85:         # 波の頭を少し明るく
            t = min(1.0, (s - 0.85) * 1.5)
            r, g, bl = r + 38 * t, g + 40 * t, bl + 34 * t
        return rgba(r, g, bl)

    return flat_diamond(color)


# ---------------------------------------------------------------- 壁（Slopes・Basement）

def rock(q, p, artificial):
    """壁の色。q は壁に沿った位置、p は壁の面の縦の位置（周期は 128 と 64。隣・上下に継ぎ目なく並ぶ）。"""
    a, b = (q % 128) / 128.0, (p % 64) / 64.0
    if artificial:
        base = 150.0
        line = 0.0
        if (q % 32) < 2 or (p % 32) < 2:
            line = -26.0
        n = vnoise(a, b, 8, 4, 5) * 12
        v = base + n + line
        return rgba(v, v * 0.98, v * 0.94)
    n = 0.5 * vnoise(a, b, 4, 4, 21) + 0.3 * vnoise(a, b, 8, 8, 22) + 0.2 * vnoise(a, b, 16, 8, 23)
    strata = math.sin(2 * math.pi * (b * 4 + 0.8 * vnoise(a, b, 4, 2, 24)))
    v = 0.52 + 0.34 * n + 0.07 * strata
    return rgba(138 * v, 124 * v, 106 * v)


def wall(kind, h1, h2, artificial):
    """壁 1 枚。kind: 0 = 左（南西→北西）、1 = 奥（北西→北東）。h1・h2 は始めと終わりの高さ（段。負は下がる）。"""
    if kind == 0:
        x0, base0, x1, base1 = 0, 192, 128, 128
    else:
        x0, base0, x1, base1 = 128, 128, 256, 192
    top0 = base0 - STEP * h1
    top1 = base1 - STEP * h2
    pix = [(0, 0, 0, 0)] * (CELL * CELL)
    shade = 1.0 if kind == 0 else 0.82
    for x in range(x0, x1):
        f = (x + 0.5 - x0) / (x1 - x0)
        base = base0 + (base1 - base0) * f
        top = top0 + (top1 - top0) * f
        for y in range(max(0, int(top) - 1), min(CELL, int(base) + 1)):
            if top <= y < base:
                q = x
                p = x + 2 * y if kind == 0 else x - 2 * y
                r, g, b, _ = rock(q, p, artificial)
                pix[y * CELL + x] = rgba(r * shade, g * shade, b * shade)
    return from_pixels(pix)


# 壁の絵の並び: 番号 = h1 + h2*3（h1・h2 は 0〜2）、9・10 は片方が下がる形（本体の grund.cc の get_back_image_from_diff）
WALL_SHAPES = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2), (-1, 1), (1, -1)]


# ---------------------------------------------------------------- 柵（Fence）

def fence(kind, artificial):
    """kind: 0 = 左だけ、1 = 奥だけ、2 = 両方。"""
    im = new_cell()
    d = ImageDraw.Draw(im)
    wood = rgba(122, 88, 52) if not artificial else rgba(120, 124, 130)
    dark = rgba(86, 60, 36) if not artificial else rgba(84, 88, 94)

    def edge(x0, y0, x1, y1):
        n = 4
        for i in range(n):
            f = (i + 0.5) / n
            px = x0 + (x1 - x0) * f
            py = y0 + (y1 - y0) * f
            d.rectangle([px - 2, py - 26, px + 1, py], fill=wood)
        for hgt in (9, 19):
            d.line([(x0 + 2, y0 - hgt), (x1 - 2, y1 - hgt)], fill=dark, width=3)

    if kind in (0, 2):
        edge(0, 192, 128, 128)
    if kind in (1, 2):
        edge(128, 128, 255, 192)
    return im


# ---------------------------------------------------------------- 印・境界（Marker・Borders）

def polyline(points, color, width):
    im = new_cell()
    d = ImageDraw.Draw(im)
    d.line(points, fill=color, width=width, joint="curve")
    return im


def front_line(sw, se, ne):
    return [(1, 192 - STEP * sw), (128, 256 - STEP * se - 1), (254, 192 - STEP * ne)]


def back_line(sw, ne, nw):
    return [(1, 192 - STEP * sw), (128, 128 - STEP * nw), (254, 192 - STEP * ne)]


# ---------------------------------------------------------------- シートと dat

class Sheet:
    def __init__(self, name, cols, rows):
        self.name = name
        self.cols = cols
        self.rows = rows
        self.im = Image.new("RGBA", (cols * CELL, rows * CELL), (0, 0, 0, 0))

    def put(self, row, col, cell):
        self.im.paste(cell, (col * CELL, row * CELL))

    def ref(self, row, col):
        return f"{self.name}.{row}.{col}"

    def save(self, outdir):
        self.im.save(os.path.join(outdir, self.name + ".png"))


def write_dat(outdir, filename, obj_name, lines, comment=""):
    text = ["# " + comment] if comment else []
    text += ["Obj=ground", f"Name={obj_name}", f"copyright={COPYRIGHT}"] + lines
    with open(os.path.join(outdir, filename), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(text) + "\n")


def build_all(outdir):
    os.makedirs(outdir, exist_ok=True)

    # Outside（地図の外。この絵の幅が、本体のタイルの幅を決める）
    # 本体は pak のフォルダの ground.Outside.pak を先に読むので、この 1 枚だけ別のフォルダ（Outside）に置く
    outside_dir = os.path.join(os.path.dirname(os.path.abspath(outdir)), "Outside")
    os.makedirs(outside_dir, exist_ok=True)
    sheet = Sheet("outside", 1, 1)
    sheet.put(0, 0, flat_diamond(lambda x, y: rgba(28, 32, 44)))
    sheet.save(outside_dir)
    write_dat(outside_dir, "outside.dat", "Outside", [f"Image[0][0]={sheet.ref(0, 0)}"],
              "地図の外のタイル。この絵の幅（256）が本体のタイルの幅になる")

    # ClimateTexture（8 気候。温帯が 4。温帯以外は仮の色）
    sheet = Sheet("texture-climate", 8, 1)
    lines = []
    for i in range(8):
        sheet.put(0, i, climate_texture(i))
        lines.append(f"# {CLIMATES[i][0]}")
        lines.append(f"Image[{i}][0]={sheet.ref(0, i)}")
    sheet.save(outdir)
    write_dat(outdir, "texture-climate.dat", "ClimateTexture", lines)

    # LightTexture（坂 81 通り。番号 = sw + 3*se + 9*ne + 27*nw、各隅 0〜2）
    sheet = Sheet("texture-lightmap", 9, 9)
    lines = []
    cache = {}
    for i in range(81):
        sw, se, ne, nw = i % 3, (i // 3) % 3, (i // 9) % 3, i // 27
        key = (0, 0, 0, 0) if min(sw, se, ne, nw) >= 1 else (sw, se, ne, nw)
        if key not in cache:
            cache[key] = lightmap(*key)
        sheet.put(i // 9, i % 9, cache[key])
        lines.append(f"# sw{sw} se{se} ne{ne} nw{nw}")
        lines.append(f"Image[{i}][0]={sheet.ref(i // 9, i % 9)}")
    sheet.save(outdir)
    write_dat(outdir, "texture-lightmap.dat", "LightTexture", lines,
              "番号 = sw + 3*se + 9*ne + 27*nw（各隅の高さ 0〜2）")

    # ShoreTrans（海岸のつなぎ目 12 枚）
    sheet = Sheet("texture-shore", 4, 3)
    lines = []
    for i in range(12):
        sheet.put(i // 4, i % 4, shore_trans(i))
        lines.append(f"Image[{i}][0]={sheet.ref(i // 4, i % 4)}")
    sheet.save(outdir)
    write_dat(outdir, "texture-shore.dat", "ShoreTrans", lines)

    # SlopeTrans（気候・雪線のつなぎ目 15 枚）
    sheet = Sheet("texture-slope", 4, 4)
    lines = []
    for i in range(len(SLOPE_TRANS_CORNERS)):
        sheet.put(i // 4, i % 4, slope_trans(i))
        lines.append(f"Image[{i}][0]={sheet.ref(i // 4, i % 4)}")
    sheet.save(outdir)
    write_dat(outdir, "texture-slope.dat", "SlopeTrans", lines)

    # Water（深さ 6 段、どの深さも 8 コマで動く）
    sheet = Sheet("water", WATER_FRAMES, WATER_DEPTHS)
    lines = []
    for depth in range(WATER_DEPTHS):
        # 本体は深さごとに「その深さの絵の、今のコマ」を引く（grund.cc）ので、どの深さも全コマ要る
        for f in range(WATER_FRAMES):
            sheet.put(depth, f, water_cell(depth, f))
            lines.append(f"Image[{depth}][{f}]={sheet.ref(depth, f)}")
    sheet.save(outdir)
    write_dat(outdir, "water.dat", "Water", lines, "深さ 0 が浅い水、1〜5 が深い水。どれも 8 コマで動く")

    # Slopes（自然の壁）・Basement（人工の壁）。左 11 枚 + 奥 11 枚
    for fname, objname, artificial, note in (
        ("slope", "Slopes", False, "自然の壁。番号 0〜10 が左（南西→北西）、11〜21 が奥（北西→北東）"),
        ("basement", "Basement", True, "人工の壁（建物の基礎）。並びは Slopes と同じ"),
    ):
        sheet = Sheet(fname, 11, 2)
        lines = []
        for kind in (0, 1):
            for n, (h1, h2) in enumerate(WALL_SHAPES):
                idx = kind * 11 + n
                if n == 0:
                    lines.append(f"Image[{idx}][0]=-")
                    continue
                sheet.put(kind, n, wall(kind, h1, h2, artificial))
                lines.append(f"# h1={h1} h2={h2}")
                lines.append(f"Image[{idx}][0]={sheet.ref(kind, n)}")
        sheet.save(outdir)
        write_dat(outdir, fname + ".dat", objname, lines, note)

    # Fence（自然の柵 3 枚 + 建物の柵 3 枚。左だけ・奥だけ・両方）
    sheet = Sheet("fences", 3, 2)
    lines = []
    for art in (0, 1):
        for kind in range(3):
            sheet.put(art, kind, fence(kind, bool(art)))
            lines.append(f"Image[{art * 3 + kind}][0]={sheet.ref(art, kind)}")
    sheet.save(outdir)
    write_dat(outdir, "fences.dat", "Fence", lines, "0〜2 が自然の柵（左・奥・両方）、3〜5 が建物の柵")

    # Marker（地面の印。前 27 枚 = sw + 3*se + 9*ne、奥 27 枚 = 27 + sw + 3*ne + 9*nw）
    sheet = Sheet("marker", 9, 6)
    lines = []
    orange = rgba(255, 128, 0)
    for i in range(27):
        sw, se, ne = i % 3, (i // 3) % 3, i // 9
        sheet.put(i // 9, i % 9, polyline(front_line(sw, se, ne), orange, 3))
        lines.append(f"Image[{i}][0]={sheet.ref(i // 9, i % 9)}")
    for j in range(27):
        sw, ne, nw = j % 3, (j // 3) % 3, j // 9
        k = 27 + j
        sheet.put(k // 9, k % 9, polyline(back_line(sw, ne, nw), orange, 3))
        lines.append(f"Image[{k}][0]={sheet.ref(k // 9, k % 9)}")
    sheet.save(outdir)
    write_dat(outdir, "marker.dat", "Marker", lines,
              "前（番号 0〜26）は南西→南東→北東の線、奥（27〜53）は南西→北西→北東の線")

    # Borders（格子の線。奥の線 27 枚。番号 = 南西 + 3*北東 + 9*北西。本体の get_border_image）
    sheet = Sheet("borders", 9, 3)
    lines = []
    for i in range(27):
        sw, ne, nw = i % 3, (i // 3) % 3, i // 9
        sheet.put(i // 9, i % 9, polyline(back_line(sw, ne, nw), rgba(36, 36, 40), 2))
        lines.append(f"Image[{i}][0]={sheet.ref(i // 9, i % 9)}")
    sheet.save(outdir)
    write_dat(outdir, "borders.dat", "Borders", lines,
              "番号 = 南西 + 3*北東 + 9*北西。南西→北西→北東の線（Marker の奥と同じ形）")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    build_all(out)
    print("done:", out)
