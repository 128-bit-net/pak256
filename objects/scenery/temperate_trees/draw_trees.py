"""温帯の木 3 種の絵と表を書き出す（docs/trees.md）。MIT License。絵は仮（数式で描いた物）で、見た目は後から描き直す。

- 種類: ケヤキ風の広葉樹（zelkova）、スギ風の針葉樹（cedar）、シラカバ風の細い広葉樹（birch）
- 縮尺（docs/concept.md の 3 章 C）: 1 タイル = 16 単位 × 1.65m = 26.4m。256px のタイルの菱形から、
  地面の距離は 1m = 約 6.9px、高さは 1m = 約 5.9px（2:1 の斜め上からの見え方で、高さは 0.866 倍）。
- 木の育ち age 0〜4 は、高さを 0.2・0.4・0.6・0.8・1.0 倍にする。絵は 256px のセルを横に 5 つ並べたシート。
  根元はタイルの中心 (128, 192)（地面の菱形の中心。docs/ground.md）。
- 季節の絵は後（seasons=1）。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/scenery/temperate_trees/draw_trees.py
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

# makeobj が特別な色として読む色（描いた色がこれに当たると別の意味になるので、避ける）
_SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}

# 種類ごとの決め事: 高さ（m）、名前、重み（distributionweight）
SPECIES = {
    "zelkova": dict(name="pak256_zelkova", height=18.0, weight=2),
    "cedar": dict(name="pak256_cedar", height=24.0, weight=2),
    "birch": dict(name="pak256_birch", height=14.0, weight=1),
}


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def safe(rgb):
    r, g, b = (max(0, min(255, int(round(v)))) for v in rgb)
    if (r << 16 | g << 8 | b) in _SPECIAL:
        b = b + 1 if b < 255 else b - 1
    return (r, g, b)


class Canvas:
    """SS 倍に拡大した 1 セル分の透明な画。座標は等倍の px で受ける。"""

    def __init__(self):
        self.im = Image.new("RGBA", (CELL * SS, CELL * SS), (0, 0, 0, 0))
        self.dr = ImageDraw.Draw(self.im)

    def ellipse(self, cx, cy, rx, ry, rgb):
        self.dr.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], fill=safe(rgb) + (255,))

    def poly(self, pts, rgb):
        self.dr.polygon([(x * SS, y * SS) for x, y in pts], fill=safe(rgb) + (255,))

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


def trunk(cv, h_px, w_px, dark, light, taper=0.6):
    """根元から高さ h_px までの幹。左半分を明るく、右半分を暗くする。"""
    x, y = BASE
    top_w = w_px * taper
    cv.poly([(x - w_px / 2, y), (x + w_px / 2, y), (x + top_w / 2, y - h_px), (x - top_w / 2, y - h_px)], dark)
    cv.poly([(x - w_px / 2, y), (x, y), (x, y - h_px), (x - top_w / 2, y - h_px)], light)


def speckle(cv, rng, cx, cy, rx, ry, n, size, colors):
    """葉の粒。球の中に小さな点を散らして、のっぺりを避ける。"""
    for _ in range(n):
        a = rng.random() * math.tau
        d = math.sqrt(rng.random()) * 0.9
        x, y = cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d
        s = size * (0.6 + rng.random() * 0.8)
        cv.ellipse(x, y, s, s * 0.8, colors[rng.randrange(len(colors))])


def draw_zelkova(cv, k, rng):
    """広葉樹。幹の上に、大きな樹冠（球をいくつか重ねる）。樹冠の幅は 13m ほど。"""
    h = SPECIES["zelkova"]["height"] * k
    H = h * PX_H
    trunk(cv, H * 0.42, max(3, 1.0 * PX_W * k * 1.1), (84, 58, 38), (122, 88, 58))
    x, y = BASE
    cr = 5.6 * k * PX_W  # 樹冠の半径（横。球の端まで入れた幅が 13m ほどになる）
    cz = 0.69 * H  # 樹冠の中心の高さ
    ry = cr * 0.80
    blobs = [(0.0, 0.0, 1.0), (-0.55, 0.1, 0.62), (0.55, 0.1, 0.62), (-0.25, -0.35, 0.6), (0.3, -0.38, 0.56), (0.0, 0.3, 0.55)]
    blobs.sort(key=lambda b: b[1] * -1)
    for bx, by, br in blobs:
        cx, cy = x + bx * cr, y - cz + by * ry
        cv.ball(cx, cy, cr * br, ry * br, (38, 82, 36), (112, 160, 62))
    speckle(cv, rng, x, y - cz, cr * 0.95, ry * 0.95, int(60 * k + 10), 2.4 * max(0.5, k), [(34, 76, 34), (96, 146, 54), (132, 176, 74)])


def draw_cedar(cv, k, rng):
    """針葉樹。細い幹に、段になった円錐の枝（下の段ほど広い）。樹冠の幅は高さの 0.3 倍ほど。"""
    h = SPECIES["cedar"]["height"] * k
    H = h * PX_H
    trunk(cv, H * 0.30, max(3, 0.7 * PX_W * k * 1.2), (80, 56, 40), (118, 86, 58))
    x, y = BASE
    cr = 3.6 * k * PX_W
    tiers = 6
    for i in range(tiers):  # 下の段から描き、上の段を後で重ねる
        t = i / (tiers - 1)
        z0 = H * (0.16 + 0.60 * t)  # 段の下の縁の高さ
        w = cr * (1.0 - 0.78 * t)
        top = z0 + H * 0.275 * (1.0 - 0.127 * t)  # 一番上の段の頂点が H に届く
        base_y = y - z0
        # 円錐: 頂点・左右の縁・下の縁の楕円
        apex = (x, y - top)
        ry = w * 0.45
        cv.poly([apex, (x - w, base_y), (x + w, base_y)], (24, 66, 40))
        cv.ellipse(x, base_y, w, ry, (24, 66, 40))
        cv.poly([apex, (x - w, base_y), (x - w * 0.1, base_y + ry * 0.9)], (46, 100, 56))
        cv.poly([apex, (x - w * 0.1, base_y + ry * 0.9), (x + w * 0.5, base_y + ry * 0.7)], (34, 84, 48))
    speckle(cv, rng, x, y - H * 0.5, cr * 0.5, H * 0.32, int(30 * k + 6), 1.8 * max(0.5, k), [(20, 56, 34), (60, 118, 70)])


def draw_birch(cv, k, rng):
    """シラカバ。白い細い幹に、細長い明るい樹冠。樹冠の幅は高さの 0.35 倍ほど。"""
    h = SPECIES["birch"]["height"] * k
    H = h * PX_H
    x, y = BASE
    trunk(cv, H * 0.72, max(2.5, 0.35 * PX_W * k * 1.2), (176, 172, 160), (232, 230, 218), taper=0.5)
    for _ in range(int(6 * k) + 2):  # 幹の黒い筋
        sy = y - rng.random() * H * 0.6
        cv.ellipse(x + rng.uniform(-1.5, 1.5), sy, 1.6, 0.9, (56, 52, 48))
    cr = 2.6 * k * PX_W
    cz = 0.66 * H
    ry = H * 0.30
    blobs = [(0.0, 0.1, 1.0), (-0.3, 0.45, 0.7), (0.3, 0.4, 0.72), (0.0, -0.4, 0.75)]
    blobs.sort(key=lambda b: -b[1])
    for bx, by, br in blobs:
        cv.ball(x + bx * cr, y - cz + by * ry, cr * br, ry * br * 0.8, (64, 120, 52), (156, 202, 84))
    speckle(cv, rng, x, y - cz, cr * 0.9, ry * 0.9, int(40 * k + 8), 2.0 * max(0.5, k), [(58, 112, 48), (150, 196, 78), (186, 220, 108)])


DRAW = {"zelkova": draw_zelkova, "cedar": draw_cedar, "birch": draw_birch}


def sheet(species):
    out = Image.new("RGB", (CELL * AGES, CELL), CLEAR)
    for age in range(AGES):
        cv = Canvas()
        rng = random.Random(f"{species}-{age}")
        DRAW[species](cv, (age + 1) / AGES, rng)
        out.paste(cv.finish(), (CELL * age, 0))
    return out


def table(species):
    s = SPECIES[species]
    lines = [
        f"obj: tree",
        f"name: {s['name']}",
        "copyright: pak256.LongScale チーム",
        "climates: temperate",
        f"distributionweight: {s['weight']}",
        "seasons: 1",
        "image:            # image[age][season]。絵は draw_trees.py が描く",
    ]
    for age in range(AGES):
        lines.append(f"  {age}: {{0: {species}.0.{age}}}")
    return "\n".join(lines) + "\n"


def main():
    heights = "・".join(f"{k} {v['height']:g}m" for k, v in SPECIES.items())
    header = (
        "# 温帯の木（絵は仮）。この表と PNG は draw_trees.py が書き出す。直すときはスクリプトを直して流し直す。\n"
        f"# 1 タイル = 26.4m の縮尺で、成木の高さは {heights}（docs/trees.md）。\n"
    )
    for species in SPECIES:
        sheet(species).save(os.path.join(HERE, f"{species}.png"))
        with open(os.path.join(HERE, f"{species}.yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(header + table(species))


if __name__ == "__main__":
    main()
