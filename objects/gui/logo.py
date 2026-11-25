"""pak256.LongScale のロゴの絵（BigLogo・Logo）。MIT License。

draw_gui.py から使う。自分で描いた絵（他の pak の絵は使わない）。意匠は 3 案（variant）。
  A  1 タイルの菱形（256px のタイル）から、はみ出して長く伸びる列車（長さを実物に比例させる = LongScale）
  B  菱形を 3 つ連ねた上に、1 両で菱形 2 つ分の長い車両
  C  「256」を大きく、下に長い帯（列車）
本体は BigLogo を 4 枚（左上・右上・左下・右下）で 2×2 に並べる（simloadingscreen.cc）。
絵は全面が不透明な四角（makeobj が透明な縁を切って 4 枚の位置がずれないように）。
"""
from PIL import Image, ImageDraw, ImageFont

BIG = 384          # 4 枚を並べた全体の一辺
SS = 4             # 縮小前の倍率
NAVY = (20, 40, 78)
NAVY2 = (36, 84, 140)
WHITE = (245, 245, 240)
GOLD = (240, 190, 60)
TEAL = (70, 190, 190)
RED = (210, 70, 60)

DEFAULT_VARIANT = "A"


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _safe(c):
    """makeobj の特別な色（プレイヤー色など）を避ける: 近い色へ 1 ずらす。"""
    r, g, b = c
    if (r, g, b) in ((0, 0, 255), (0, 255, 0)):
        return (r, g, max(0, b - 1))
    return c


def _iso(cx, cy, k):
    def p(u, v, z=0.0):
        return (cx + (u - v) * k, cy + (u + v) * k / 2 - z * k * 0.8)
    return p


def _box(d, p, u0, u1, v0, v1, z0, z1, top, left, right):
    """u 方向に長い箱（3 面）。右が +u+v 側、左が +u−v 側の面。"""
    # 手前の 2 面: v1 側（右下向き）と u1 側（左下向き）。視点は +u +v 側
    d.polygon([p(u0, v1, z0), p(u1, v1, z0), p(u1, v1, z1), p(u0, v1, z1)], fill=_safe(right))
    d.polygon([p(u1, v0, z0), p(u1, v1, z0), p(u1, v1, z1), p(u1, v0, z1)], fill=_safe(left))
    d.polygon([p(u0, v0, z1), p(u1, v0, z1), p(u1, v1, z1), p(u0, v1, z1)], fill=_safe(top))


def _text(d, xy, s, size, fill):
    d.text(xy, s, font=_font(size), fill=_safe(fill), anchor="mm")


def _background(d, w):
    for y in range(w):
        t = y / (w - 1)
        c = tuple(int(NAVY[i] * (1 - t) + NAVY2[i] * t) for i in range(3))
        d.line((0, y, w, y), fill=c)


def _tile(d, p, u0, u1, v0, v1, fill, outline, width):
    pts = [p(u0, v0), p(u1, v0), p(u1, v1), p(u0, v1)]
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=outline, width=width, joint="curve")


def _train(d, p, u_start, u_end, v, cars, gap, height, colors):
    n = cars
    length = (u_end - u_start - gap * (n - 1)) / n
    for i in range(n):
        u0 = u_start + i * (length + gap)
        top, left, right = colors[i % len(colors)]
        _box(d, p, u0, u0 + length, v - 0.22, v + 0.22, 0.0, height, top, left, right)
        # 窓の帯
        d.polygon([p(u0 + length * .08, v + 0.22, height * .45), p(u0 + length * .92, v + 0.22, height * .45),
                   p(u0 + length * .92, v + 0.22, height * .8), p(u0 + length * .08, v + 0.22, height * .8)],
                  fill=_safe((30, 50, 80)))


def draw_big(variant=DEFAULT_VARIANT):
    """BIG×BIG の絵（全面不透明）。"""
    w = BIG * SS
    im = Image.new("RGBA", (w, w), NAVY + (255,))
    d = ImageDraw.Draw(im)
    _background(d, w)
    k = 60 * SS
    s = SS
    if variant == "A":
        p = _iso(w / 2, 225 * s, k)
        _tile(d, p, -1, 1, -1, 1, (46, 110, 120), TEAL, 3 * s)
        for t in (-0.5, 0, 0.5):                       # タイルの格子（128px 単位ではなく 1 タイル）
            pass
        _train(d, p, -2.6, 2.6, 0.0, 5, 0.12, 0.5,
               [((250, 250, 245), (190, 195, 205), (225, 228, 232)),
                ((250, 220, 130), (200, 150, 40), (240, 190, 60))])
        _text(d, (w / 2, 62 * s), "pak256", 78 * s, WHITE)
        _text(d, (w / 2, 345 * s), "LongScale", 34 * s, GOLD)
    elif variant == "B":
        p = _iso(w / 2, 215 * s, 40 * SS)
        for i in range(3):
            c = (i - 1) * 2.0
            _tile(d, p, c - 1, c + 1, -1, 1, (46, 110, 120), TEAL, 3 * s)
        _train(d, p, -3.0, 3.0, 0.0, 2, 0.15, 0.5,
               [((250, 250, 245), (190, 195, 205), (225, 228, 232))])
        _text(d, (w / 2, 62 * s), "pak256", 78 * s, WHITE)
        _text(d, (w / 2, 345 * s), "LongScale", 34 * s, GOLD)
    else:  # C
        _text(d, (w / 2, 150 * s), "256", 190 * s, WHITE)
        d.rectangle((24 * s, 262 * s, 360 * s, 296 * s), fill=_safe(GOLD))
        for i in range(1, 7):
            x = (24 + i * 48) * s
            d.rectangle((x - 3 * s, 268 * s, x + 3 * s, 290 * s), fill=_safe(NAVY))
        _text(d, (w / 2, 335 * s), "pak256.LongScale", 36 * s, TEAL)
        _text(d, (w / 2, 40 * s), "pak", 34 * s, GOLD)
    out = im.resize((BIG, BIG), Image.LANCZOS)
    # 半透明を作らない（背景は全面不透明なので alpha は 255 のまま）
    return out


def big_cells(variant=DEFAULT_VARIANT):
    """BigLogo の 4 枚（左上・右上・左下・右下）。"""
    im = draw_big(variant)
    h = BIG // 2
    return [im.crop((x, y, x + h, y + h)) for y in (0, h) for x in (0, h)]


def small(variant=DEFAULT_VARIANT, size=128):
    """小さな Logo。大きな絵と同じ意匠を縮めたもの。"""
    return draw_big(variant).resize((size, size), Image.LANCZOS)
