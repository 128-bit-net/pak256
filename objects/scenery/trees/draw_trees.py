"""木の絵と表を書き出す（docs/trees.md）。MIT License。絵は仮（数式で描いた物）で、見た目は後から描き直す。

- 種類: 温帯（ケヤキ・スギ・シラカバ）、地中海（カサマツ）、熱帯（ヤシ・パンヤ）、砂漠（アカシア）、
  ツンドラ・極地（トウヒ）。
- 縮尺（docs/concept.md の 3 章 C）: 1 タイル = 16 単位 × 1.65m = 26.4m。256px のタイルの菱形から、
  地面の距離は 1m = 約 6.9px、高さは 1m = 約 5.9px（2:1 の斜め上からの見え方で、高さは 0.866 倍）。
- 木の育ち age 0〜4 は、高さを 0.2・0.4・0.6・0.8・1.0 倍にする。
- シートは、256px のセルを横に age の 5 つ、縦に「見た目（looks）」の数だけ並べる。
  根元はセルの (128, 192)（地面の菱形の中心。docs/ground.md）。
- 季節: 本体の season は 0 夏・1 秋・2 冬・3 春・4 雪（雪線の上・極地）。seasons=5 の木は season ごとに
  見た目を持ち、seasons=2 の木は 0 夏（ふだん）と 1 雪だけを持つ（本体は雪のときだけ 1 を使う）。
  どの season がどの見た目の行を引くかは、種類ごとの SEASON_MAP に書いてある。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/scenery/trees/draw_trees.py
"""
import math
import os
import random

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = 256
AGES = 5
SS = 3  # 描くときの拡大（縁をなめらかにしてから、半透明を切る）
PX_H = 5.9  # 高さ 1m の px
PX_W = 6.9  # 地面の距離 1m の px
BASE = (128, 192)  # 根元（タイルの中心）
CLEAR = (231, 255, 255)  # makeobj の透明色
WHITE = (246, 248, 252)

# makeobj が特別な色として読む色（描いた色がこれに当たると別の意味になるので、避ける）
_SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}

# 見た目（looks）: 行の名前。season 0 夏・1 秋・2 冬・3 春・4 雪 のどれを描くか（palette の名前と、雪の量）
LOOK_DEFS = {
    "summer": dict(leaf="summer", snow=0.0),
    "autumn": dict(leaf="autumn", snow=0.0),
    "spring": dict(leaf="spring", snow=0.0),
    "winter": dict(leaf="summer", snow=0.55),  # 落葉樹は leaf を落とす（bare）
    "snow": dict(leaf="summer", snow=1.0),
}

# 種類ごとの決め事。
#   name・height（m）・weight（distributionweight）・climates（dat に書く気候）
#   looks: シートの行の見た目の並び。season_map: season 0〜4（seasons=2 は 0・1）が引く行
#   deciduous: 冬・雪で葉を落とす
SPECIES = {
    "zelkova": dict(name="pak256_zelkova", height=18.0, weight=2, climates="temperate", deciduous=True,
                    looks=["summer", "autumn", "winter", "spring", "snow"], season_map=[0, 1, 2, 3, 4]),
    "cedar": dict(name="pak256_cedar", height=24.0, weight=2, climates="temperate", deciduous=False,
                  looks=["summer", "winter", "snow"], season_map=[0, 0, 1, 0, 2]),
    "birch": dict(name="pak256_birch", height=14.0, weight=1, climates="temperate", deciduous=True,
                  looks=["summer", "autumn", "winter", "spring", "snow"], season_map=[0, 1, 2, 3, 4]),
    "pine": dict(name="pak256_pine", height=16.0, weight=2, climates="mediterran", deciduous=False,
                 looks=["summer", "snow"], season_map=[0, 1]),
    "palm": dict(name="pak256_palm", height=14.0, weight=2, climates="tropic", deciduous=False,
                 looks=["summer", "snow"], season_map=[0, 1]),
    "kapok": dict(name="pak256_kapok", height=22.0, weight=2, climates="tropic", deciduous=False,
                  looks=["summer", "snow"], season_map=[0, 1]),
    "acacia": dict(name="pak256_acacia", height=8.0, weight=1, climates="desert", deciduous=False,
                   looks=["summer", "snow"], season_map=[0, 1]),
    "spruce": dict(name="pak256_spruce", height=12.0, weight=2, climates="tundra,arctic", deciduous=False,
                   looks=["summer", "winter", "snow"], season_map=[0, 0, 1, 0, 2]),
}

# 葉・針の色。dark/light は球の暗い側と明るい側。spk は葉の粒。tier は針葉樹の（暗・明・中）
PAL = {
    "zelkova": {
        "summer": dict(dark=(38, 82, 36), light=(112, 160, 62), spk=[(34, 76, 34), (96, 146, 54), (132, 176, 74)]),
        "autumn": dict(dark=(120, 48, 20), light=(214, 128, 36), spk=[(110, 40, 24), (200, 110, 30), (230, 160, 50)]),
        "spring": dict(dark=(60, 110, 48), light=(150, 200, 96), spk=[(52, 100, 44), (140, 190, 86), (190, 225, 130)]),
    },
    "birch": {
        "summer": dict(dark=(64, 120, 52), light=(156, 202, 84), spk=[(58, 112, 48), (150, 196, 78), (186, 220, 108)]),
        "autumn": dict(dark=(150, 110, 20), light=(240, 200, 60), spk=[(140, 100, 20), (230, 190, 50), (250, 225, 100)]),
        "spring": dict(dark=(86, 140, 60), light=(176, 220, 110), spk=[(80, 130, 56), (170, 215, 100), (210, 238, 140)]),
    },
    "cedar": {"summer": dict(tier=((24, 66, 40), (46, 100, 56), (34, 84, 48)), spk=[(20, 56, 34), (60, 118, 70)])},
    "spruce": {"summer": dict(tier=((20, 56, 44), (40, 92, 70), (30, 76, 58)), spk=[(16, 48, 38), (50, 100, 80)])},
    "pine": {"summer": dict(dark=(34, 78, 44), light=(96, 146, 66), spk=[(30, 70, 40), (110, 160, 76), (70, 120, 54)])},
    "kapok": {"summer": dict(dark=(22, 70, 34), light=(70, 130, 52), spk=[(18, 60, 30), (56, 116, 44), (90, 150, 64)])},
    "acacia": {"summer": dict(dark=(70, 100, 40), light=(150, 160, 70), spk=[(64, 92, 36), (150, 150, 66), (176, 176, 90)])},
    "palm": {"summer": dict(dark=(30, 100, 40), light=(110, 176, 64), spk=[])},
}

BARK = {  # 幹（暗・明）、枝の色
    "zelkova": ((84, 58, 38), (122, 88, 58)),
    "cedar": ((80, 56, 40), (118, 86, 58)),
    "birch": ((176, 172, 160), (232, 230, 218)),
    "pine": ((92, 62, 44), (136, 96, 66)),
    "palm": ((120, 96, 68), (170, 140, 100)),
    "kapok": ((92, 76, 60), (136, 116, 92)),
    "acacia": ((96, 76, 52), (140, 112, 76)),
    "spruce": ((70, 52, 40), (104, 80, 58)),
}


_fit = [1.0]  # 描いた高さを表の値に合わせる補正（render_cell が測って決める）


def hpx(species, k):
    """育ち k（0.2〜1.0）の、木の高さ（px）。"""
    return SPECIES[species]["height"] * k * PX_H * _fit[0]


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def safe(rgb):
    r, g, b = (max(0, min(255, int(round(v)))) for v in rgb)
    if (r << 16 | g << 8 | b) in _SPECIAL:
        b = b + 1 if b < 255 else b - 1
    return (r, g, b)


def snow_palette(pal, a):
    """葉の色を、雪の量 a だけ白へ寄せる。"""
    if a <= 0:
        return pal
    out = dict(pal)
    for key in ("dark", "light"):
        if key in pal:
            out[key] = lerp(pal[key], WHITE, a * (0.5 if key == "dark" else 0.7))
    if "spk" in pal:
        out["spk"] = [lerp(c, WHITE, a * 0.55) for c in pal["spk"]]
    if "tier" in pal:
        dark, light, mid = pal["tier"]
        out["tier"] = (lerp(dark, WHITE, a * 0.35), lerp(light, WHITE, a * 0.9), lerp(mid, WHITE, a * 0.75))
    return out


class Canvas:
    """SS 倍に拡大した 1 セル分の透明な画。座標は等倍の px で受ける。"""

    def __init__(self):
        self.im = Image.new("RGBA", (CELL * SS, CELL * SS), (0, 0, 0, 0))
        self.dr = ImageDraw.Draw(self.im)

    def ellipse(self, cx, cy, rx, ry, rgb):
        self.dr.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=safe(rgb) + (255,))

    def poly(self, pts, rgb):
        self.dr.polygon([(x * SS, y * SS) for x, y in pts], fill=safe(rgb) + (255,))

    def line(self, p, q, width, rgb):
        self.dr.line([(p[0] * SS, p[1] * SS), (q[0] * SS, q[1] * SS)], fill=safe(rgb) + (255,), width=max(1, int(round(width * SS))))
        r = width * SS / 2  # 端を丸める
        for x, y in (p, q):
            self.dr.ellipse([x * SS - r, y * SS - r, x * SS + r, y * SS + r], fill=safe(rgb) + (255,))

    def ball(self, cx, cy, rx, ry, dark, light):
        """左上から光が当たる球。同心の楕円を、暗い色から明るい色へ、左上へずらして重ねる。"""
        steps = max(6, int(max(rx, ry) / 2))
        for i in range(steps + 1):
            t = i / steps
            self.ellipse(cx - rx * 0.30 * t, cy - ry * 0.35 * t, rx * (1 - 0.6 * t), ry * (1 - 0.6 * t), lerp(dark, light, t))

    def finish(self):
        """縮めて、半透明を切り（α ≥ 128 を不透明）、透明色で埋めた RGB にする。"""
        small = self.im.resize((CELL, CELL), Image.LANCZOS)
        out = Image.new("RGB", (CELL, CELL), CLEAR)
        px, src = out.load(), small.load()
        for y in range(CELL):
            for x in range(CELL):
                r, g, b, a = src[x, y]
                if a >= 128:
                    px[x, y] = safe((r, g, b))
        return out


def bbox(img):
    """透明でない画素の外接枠 (x0, y0, x1, y1)。"""
    px = img.load()
    xs, ys = [], []
    for y in range(CELL):
        for x in range(CELL):
            if px[x, y] != CLEAR:
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def snowify(img, amount, rng):
    """上を向いた縁（上が透明な画素）を白くする。細い枝や葉の上に雪が積もった見た目。"""
    if amount <= 0:
        return img
    src, out = img.load(), img.copy()
    po = out.load()
    for y in range(CELL):
        for x in range(CELL):
            if src[x, y] == CLEAR:
                continue
            d = 0
            while d < 8 and y - 1 - d >= 0 and src[x, y - 1 - d] != CLEAR:
                d += 1
            w = amount * max(0.0, 1 - d / 5.0)
            if w > 0 and rng.random() < min(1.0, w * 1.3):
                po[x, y] = safe(lerp(WHITE, (214, 224, 238), rng.random() * 0.35))
    return out


def trunk(cv, h_px, w_px, dark, light, taper=0.6):
    """根元から高さ h_px までの幹。左半分を明るく、右半分を暗くする。"""
    x, y = BASE
    top_w = w_px * taper
    cv.poly([(x - w_px / 2, y), (x + w_px / 2, y), (x + top_w / 2, y - h_px), (x - top_w / 2, y - h_px)], dark)
    cv.poly([(x - w_px / 2, y), (x, y), (x, y - h_px), (x - top_w / 2, y - h_px)], light)


def speckle(cv, rng, cx, cy, rx, ry, n, size, colors):
    """葉の粒。球の中に小さな点を散らして、のっぺりを避ける。"""
    if not colors:
        return
    for _ in range(n):
        a = rng.random() * math.tau
        d = math.sqrt(rng.random()) * 0.9
        x, y = cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d
        s = size * (0.6 + rng.random() * 0.8)
        cv.ellipse(x, y, s, s * 0.8, colors[rng.randrange(len(colors))])


def bare_crown(cv, rng, origins, box, color, k):
    """葉を落とした樹冠。幹の先（origins）から、夏の樹冠の外接枠 box の中へ枝を広げる。
    外接枠の上・左・右の端に必ず枝の先を置き、夏と同じ高さ・幅に収める。"""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
    w = max(1.0, 1.6 * k + 0.4)
    h = w / 2 + 1.6 # 線の端の丸みの分だけ内側に置く
    tips = [(cx, y0 + w / 2 - 0.3), (x0 + h, cy + ry * 0.1), (x1 - h, cy + ry * 0.1)]
    for _ in range(int(7 + 6 * k)):
        a = rng.uniform(0, math.pi)
        d = math.sqrt(rng.uniform(0.35, 1.0))
        tips.append((min(max(cx - math.cos(a) * rx * d, x0 + h), x1 - h), max(cy - math.sin(a) * ry * d * 0.95 + ry * 0.05, y0 + h)))
    for tx, ty in tips:
        ox, oy = origins[rng.randrange(len(origins))]
        cv.line((ox, oy), (tx, ty), w, color)
        for _ in range(3):  # 小枝
            ang = rng.uniform(0, math.tau)
            ln = rng.uniform(0.10, 0.2) * max(rx, ry)
            mx, my = (ox + tx) / 2 + (tx - ox) * rng.uniform(0, 0.45), (oy + ty) / 2 + (ty - oy) * rng.uniform(0, 0.45)
            ex = min(max(mx + math.cos(ang) * ln, x0 + h), x1 - h)
            ey = min(max(my + math.sin(ang) * ln, y0 + h), y1 - h)
            cv.line((mx, my), (ex, ey), max(1.0, w * 0.6), color)


def draw_zelkova(cv, k, rng, pal, box=None):
    """広葉樹。幹の上に、大きな樹冠（球をいくつか重ねる）。樹冠の幅は 13m ほど。pal が None なら葉を落とした冬。"""
    H = hpx("zelkova", k)
    dark, light = BARK["zelkova"]
    trunk(cv, H * 0.42, max(3, 1.0 * PX_W * k * 1.1), dark, light)
    x, y = BASE
    if pal is None:
        bare_crown(cv, rng, [(x, y - H * 0.42), (x - 1, y - H * 0.38), (x + 1, y - H * 0.4)], box, dark, k)
        return
    cr = 5.6 * k * PX_W  # 樹冠の半径（横。球の端まで入れた幅が 13m ほどになる）
    cz = 0.69 * H  # 樹冠の中心の高さ
    ry = cr * 0.80
    blobs = [(0.0, 0.0, 1.0), (-0.55, 0.1, 0.62), (0.55, 0.1, 0.62), (-0.25, -0.35, 0.6), (0.3, -0.38, 0.56), (0.0, 0.3, 0.55)]
    blobs.sort(key=lambda b: b[1] * -1)
    for bx, by, br in blobs:
        cv.ball(x + bx * cr, y - cz + by * ry, cr * br, ry * br, pal["dark"], pal["light"])
    speckle(cv, rng, x, y - cz, cr * 0.95, ry * 0.95, int(60 * k + 10), 2.4 * max(0.5, k), pal["spk"])


def draw_birch(cv, k, rng, pal, box=None):
    """シラカバ。白い細い幹に、細長い明るい樹冠。樹冠の幅は高さの 0.35 倍ほど。"""
    H = hpx("birch", k)
    x, y = BASE
    dark, light = BARK["birch"]
    trunk(cv, H * 0.72, max(2.5, 0.35 * PX_W * k * 1.2), dark, light, taper=0.5)
    for _ in range(int(6 * k) + 2):  # 幹の黒い筋
        sy = y - rng.random() * H * 0.6
        cv.ellipse(x + rng.uniform(-1.5, 1.5), sy, 1.6, 0.9, (56, 52, 48))
    if pal is None:
        bare_crown(cv, rng, [(x, y - H * 0.72), (x, y - H * 0.55), (x, y - H * 0.4)], box, (84, 76, 66), k)
        return
    cr = 2.6 * k * PX_W
    cz = 0.66 * H
    ry = H * 0.30
    blobs = [(0.0, 0.1, 1.0), (-0.3, 0.45, 0.7), (0.3, 0.4, 0.72), (0.0, -0.4, 0.75)]
    blobs.sort(key=lambda b: -b[1])
    for bx, by, br in blobs:
        cv.ball(x + bx * cr, y - cz + by * ry, cr * br, ry * br * 0.8, pal["dark"], pal["light"])
    speckle(cv, rng, x, y - cz, cr * 0.9, ry * 0.9, int(40 * k + 8), 2.0 * max(0.5, k), pal["spk"])


def conifer(cv, k, rng, pal, species, cr_m, tiers, z_lo, z_span, h0, shrink, trunk_frac, trunk_w):
    """針葉樹。細い幹に、段になった円錐の枝（下の段ほど広い）。一番上の段の頂点が高さ H に届く。"""
    H = hpx(species, k)
    dark_b, light_b = BARK[species]
    trunk(cv, H * trunk_frac, max(3, trunk_w * PX_W * k * 1.2), dark_b, light_b)
    x, y = BASE
    cr = cr_m * k * PX_W
    d_c, l_c, m_c = pal["tier"]
    for i in range(tiers):  # 下の段から描き、上の段を後で重ねる
        t = i / (tiers - 1)
        z0 = H * (z_lo + z_span * t)  # 段の下の縁の高さ
        w = cr * (1.0 - 0.78 * t)
        top = z0 + H * h0 * (1.0 - shrink * t)
        base_y = y - z0
        apex = (x, y - top - (0.8 if i == tiers - 1 else 0))  # 先の細い所は縮小で欠けるので少し伸ばす
        ry = w * 0.45
        cv.poly([apex, (x - w, base_y), (x + w, base_y)], d_c)
        cv.ellipse(x, base_y, w, ry, d_c)
        cv.poly([apex, (x - w, base_y), (x - w * 0.1, base_y + ry * 0.9)], l_c)
        cv.poly([apex, (x - w * 0.1, base_y + ry * 0.9), (x + w * 0.5, base_y + ry * 0.7)], m_c)
    speckle(cv, rng, x, y - H * 0.5, cr * 0.5, H * 0.32, int(30 * k + 6), 1.8 * max(0.5, k), pal["spk"])


def draw_cedar(cv, k, rng, pal, box=None):
    """スギ風の針葉樹。樹冠の幅は 7m ほど。"""
    conifer(cv, k, rng, pal, "cedar", 3.6, 6, 0.16, 0.60, 0.275, 0.127, 0.30, 0.7)


def draw_spruce(cv, k, rng, pal, box=None):
    """トウヒ風の針葉樹。スギより低く、段が細かい。"""
    conifer(cv, k, rng, pal, "spruce", 2.4, 5, 0.14, 0.55, 0.344, 0.10, 0.22, 0.6)


def umbrella(cv, k, rng, pal, species, crown_m, crown_h, trunk_frac, trunk_w, lean):
    """傘の形の樹冠（カサマツ・アカシア）。幅 crown_m、高さ（厚み）crown_h の平たい球を横に並べる。"""
    H = hpx(species, k)
    x, y = BASE
    dark_b, light_b = BARK[species]
    cr = crown_m / 2 * k * PX_W
    ry = crown_h / 2 * k * PX_H
    cz = H - ry  # 樹冠の上の端が高さ H
    tx = x + lean * k * PX_W
    # 幹: 根元から樹冠の下まで、少し傾ける（折れ線）
    pts = [(x, y), (x + (tx - x) * 0.4, y - (H - 2 * ry) * 0.5), (tx, y - (H - 2 * ry) * 0.95)]
    bw = max(3, trunk_w * PX_W * k * 1.2)
    for p, q, f in ((pts[0], pts[1], 1.0), (pts[1], pts[2], 0.7)):
        cv.line(p, q, bw * f, dark_b)
        cv.line((p[0] - bw * 0.15 * f, p[1]), (q[0] - bw * 0.15 * f, q[1]), bw * f * 0.5, light_b)
    blobs = [(-0.55, 0.15, 0.55), (0.55, 0.15, 0.55), (0.0, 0.0, 0.62), (-0.3, -0.15, 0.5), (0.3, -0.12, 0.5)]
    blobs.sort(key=lambda b: -b[1])
    for bx, by, br in blobs:
        cv.ball(tx + bx * cr * 0.55, y - cz + by * ry, cr * br * 1.0, ry * (0.55 + 0.45 * br), pal["dark"], pal["light"])
    speckle(cv, rng, tx, y - cz, cr * 0.9, ry * 0.8, int(30 * k + 6), 2.2 * max(0.5, k), pal["spk"])


def draw_pine(cv, k, rng, pal, box=None):
    """カサマツ。長い幹の上に、平たい傘の樹冠。幅 10m。"""
    umbrella(cv, k, rng, pal, "pine", 11.6, 5.0, 0.62, 0.6, 0.6)


def draw_acacia(cv, k, rng, pal, box=None):
    """アカシア。低い幹の上に、広く平たい樹冠。幅 10m。"""
    umbrella(cv, k, rng, pal, "acacia", 11.6, 3.2, 0.6, 0.5, -0.5)


def draw_kapok(cv, k, rng, pal, box=None):
    """パンヤ（熱帯の高木）。太い幹の上に、広い暗い樹冠。幅 12m。"""
    H = hpx("kapok", k)
    dark_b, light_b = BARK["kapok"]
    trunk(cv, H * 0.55, max(3, 1.4 * PX_W * k * 1.1), dark_b, light_b, taper=0.55)
    x, y = BASE
    cr = 5.1 * k * PX_W
    ry = cr * 0.70
    cz = H - ry
    blobs = [(0.0, 0.0, 1.0), (-0.55, 0.15, 0.62), (0.55, 0.15, 0.62), (-0.25, -0.3, 0.6), (0.3, -0.3, 0.56), (0.0, 0.3, 0.55)]
    blobs.sort(key=lambda b: b[1] * -1)
    for bx, by, br in blobs:
        cv.ball(x + bx * cr, y - cz + by * ry, cr * br, ry * br, pal["dark"], pal["light"])
    speckle(cv, rng, x, y - cz, cr * 0.95, ry * 0.95, int(60 * k + 10), 2.4 * max(0.5, k), pal["spk"])


def draw_palm(cv, k, rng, pal, box=None):
    """ヤシ。少し曲がった細い幹の先に、垂れる葉を放射状に広げる。幅 8m。"""
    H = hpx("palm", k)
    x, y = BASE
    dark_b, light_b = BARK["palm"]
    L = 4.3 * k * PX_W  # 葉の長さ（横の広がりの半分）
    bend = 1.0 * k * PX_W
    # 葉の先の高さを先に求めて、一番上が H に届くように幹の先の高さを決める
    lift, droop = 0.55, 0.9
    fronds = []
    n = 8
    for i in range(n):
        a = math.tau * i / n + (0.2 if i % 2 else 0.0)
        dx = math.cos(a)
        fl = L * (0.85 + 0.15 * abs(math.sin(a * 1.7)))
        pts = [(dx * fl * t, -(lift * t - droop * t * t) * fl) for t in [j / 10 for j in range(11)]]
        fronds.append((dx, fl, pts, math.sin(a)))
    top_rel = min(py for _, _, pts, _ in fronds for _, py in pts) - 0.14 * L  # 葉の幅の分
    crown_y = y - H - top_rel  # 幹の先（葉の付け根）の y
    tx = x + bend
    # 幹: 曲線を折れ線で
    bw = max(2.5, 0.8 * PX_W * k * 1.2)
    prev = (x, y)
    for j in range(1, 9):
        t = j / 8
        cur = (x + bend * t * t, y + (crown_y - y) * t)
        cv.line(prev, cur, bw * (1.0 - 0.3 * t), dark_b)
        cv.line((prev[0] - bw * 0.2, prev[1]), (cur[0] - bw * 0.2, cur[1]), bw * 0.35, light_b)
        prev = cur
    # 奥の葉（sin が負 = 奥）から手前の葉へ
    fronds.sort(key=lambda f: f[3])
    for dx, fl, pts, depth in fronds:
        wmax = 0.14 * L
        top_edge, bot_edge = [], []
        for idx, (px_, py_) in enumerate(pts):
            t = idx / (len(pts) - 1)
            wd = wmax * math.sin(math.pi * min(1.0, t * 1.0)) ** 0.7 + 0.5
            top_edge.append((tx + px_, crown_y + py_ - wd * 0.6))
            bot_edge.append((tx + px_, crown_y + py_ + wd * 0.9))
        col = lerp(pal["dark"], pal["light"], 0.35 + 0.5 * (depth + 1) / 2)
        cv.poly(top_edge + bot_edge[::-1], col)
        cv.line(pts_abs(tx, crown_y, pts[0]), pts_abs(tx, crown_y, pts[-1]), 0.8, lerp(pal["dark"], (20, 50, 20), 0.5))
    cv.ellipse(tx, crown_y, 0.5 * PX_W * k + 1, 0.4 * PX_W * k + 1, dark_b)


def pts_abs(tx, ty, p):
    return (tx + p[0], ty + p[1])


DRAW = {
    "zelkova": draw_zelkova, "cedar": draw_cedar, "birch": draw_birch, "pine": draw_pine,
    "palm": draw_palm, "kapok": draw_kapok, "acacia": draw_acacia, "spruce": draw_spruce,
}


def render_cell(species, look, age, summer_box=None):
    """1 つの見た目・育ちのセルを描く。"""
    spec = SPECIES[species]
    k = (age + 1) / AGES
    ld = LOOK_DEFS[look]
    rng = random.Random(f"{species}-{look}-{age}")
    cv = Canvas()
    bare = spec["deciduous"] and look in ("winter", "snow")
    if bare:
        DRAW[species](cv, k, rng, None, summer_box)
    else:
        leaf = ld["leaf"]
        pal = PAL[species].get(leaf, PAL[species]["summer"])
        pal = snow_palette(pal, ld["snow"])
        DRAW[species](cv, k, rng, pal, None)
    cell = cv.finish()
    if ld["snow"] > 0:
        cell = snowify(cell, ld["snow"], random.Random(f"snow-{species}-{look}-{age}"))
    return cell


def render_fitted(species, look, age, summer_box=None):
    """高さが表の値（成木の高さ × (age+1)/5）に合うまで、補正を掛けて描き直す。"""
    want = SPECIES[species]["height"] * (age + 1) / AGES * PX_H
    bare = SPECIES[species]["deciduous"] and look in ("winter", "snow")
    best, best_err = None, 9.0
    _fit[0] = 1.0
    try:
        for _ in range(6):
            cell = render_cell(species, look, age, summer_box)
            x0, y0, x1, y1 = bbox(cell)
            ratio = (y1 - y0) / want
            if abs(ratio - 1) < best_err:
                best, best_err = cell, abs(ratio - 1)
            if bare or abs(ratio - 1) < 0.012:
                break
            _fit[0] /= ratio
    finally:
        _fit[0] = 1.0
    return best


def sheet(species):
    looks = SPECIES[species]["looks"]
    out = Image.new("RGB", (CELL * AGES, CELL * len(looks)), CLEAR)
    for age in range(AGES):
        summer = render_fitted(species, "summer", age)
        # 落葉樹の冬の枝は、夏の樹冠の枠の中に広げる
        summer_box = crown_box(summer) if SPECIES[species]["deciduous"] else None
        for row, look in enumerate(looks):
            cell = summer if look == "summer" else render_fitted(species, look, age, summer_box)
            out.paste(cell, (CELL * age, CELL * row))
    return out


def crown_box(img):
    """夏の絵の外接枠（樹冠の枠。落葉樹の枝を広げる範囲）。根元側（BASE から上 1/3）は幹なので上の枠だけ使う。"""
    x0, y0, x1, y1 = bbox(img)
    px = img.load()
    # 幅が最大の行を探して、その範囲を枠の左右にする（幹ではなく樹冠の幅）
    best = (0, x0, x1)
    for y in range(y0, y1):
        xs = [x for x in range(CELL) if px[x, y] != CLEAR]
        if xs and xs[-1] - xs[0] > best[0]:
            best = (xs[-1] - xs[0], xs[0], xs[-1] + 1)
    # 樹冠の下の端: 幅が最大の行より下で、幅が最大の 1/3 を割る行
    bottom = y1
    for y in range(y1 - 1, y0, -1):
        xs = [x for x in range(CELL) if px[x, y] != CLEAR]
        if xs and xs[-1] - xs[0] >= best[0] / 3:
            bottom = y + 1
            break
    return best[1], y0, best[2], bottom


def table(species):
    s = SPECIES[species]
    n = len(s["season_map"])
    lines = [
        "obj: tree",
        f"name: {s['name']}",
        "copyright: pak256.LongScale チーム",
        f"climates: {s['climates']}",
        f"distributionweight: {s['weight']}",
        f"seasons: {n}",
        "image:            # image[age][season]。絵は draw_trees.py が描く。season は 0 夏・1 秋・2 冬・3 春・4 雪（seasons=2 は 0 夏・1 雪）",
    ]
    for age in range(AGES):
        refs = ", ".join(f"{i}: {species}.{row}.{age}" for i, row in enumerate(s["season_map"]))
        lines.append(f"  {age}: {{{refs}}}")
    return "\n".join(lines) + "\n"


def main():
    heights = "・".join(f"{k} {v['height']:g}m" for k, v in SPECIES.items())
    header = (
        "# 木（絵は仮）。この表と PNG は draw_trees.py が書き出す。直すときはスクリプトを直して流し直す。\n"
        f"# 1 タイル = 26.4m の縮尺で、成木の高さは {heights}（docs/trees.md）。\n"
    )
    for species in SPECIES:
        sheet(species).save(os.path.join(HERE, f"{species}.png"))
        with open(os.path.join(HERE, f"{species}.yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(header + table(species))


if __name__ == "__main__":
    main()
