"""pak256.LongScale のロゴの絵（BigLogo・Logo）。MIT License。

draw_gui.py から使う。自分で描いた絵（他の pak の絵は使わない）。
意匠: 1 タイルの菱形（256px のタイル）から、はみ出して長く伸びる先頭車 1 両（長さを実物に比例させる = LongScale）。
下に「LongScale」を大きく。
本体は BigLogo を 4 枚（左上・右上・左下・右下）で 2×2 に並べる（simloadingscreen.cc）。
絵は全面が不透明な四角（makeobj が透明な縁を切って 4 枚の位置がずれないように）。
"""
import draw_ground as dg  # draw_gui.py が path に足す。特別な色を避ける rgba を借りる
from PIL import Image, ImageDraw, ImageFont

BIG = 384          # 4 枚を並べた全体の一辺
SS = 4             # 縮小前の倍率
NAVY = (20, 40, 78)
NAVY2 = (36, 84, 140)
WHITE = (245, 245, 240)
GOLD = (240, 190, 60)
TEAL = (70, 190, 190)


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _safe(c):
    """makeobj の特別な色（プレイヤー色など）を避ける（draw_ground の rgba と同じ決まり）。"""
    return dg.rgba(*c)[:3]


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


def _long_car(d, p, u0, u1, v, height):
    """車両長の長い先頭車 1 両。側面に窓を並べ、先頭（+u 側）に運転席の窓を付ける。"""
    w = 0.26
    _box(d, p, u0, u1, v - w, v + w, 0.0, height, (250, 250, 245), (190, 195, 205), (225, 228, 232))
    length = u1 - u0
    # 帯（金）
    d.polygon([p(u0, v + w, height * .18), p(u1, v + w, height * .18), p(u1, v + w, height * .3), p(u0, v + w, height * .3)],
              fill=_safe(GOLD))
    # 側面の窓
    n = 9
    for i in range(n):
        a = u0 + length * (0.04 + 0.86 * i / n)
        b = a + length * 0.86 / n * 0.62
        d.polygon([p(a, v + w, height * .5), p(b, v + w, height * .5), p(b, v + w, height * .85), p(a, v + w, height * .85)],
                  fill=_safe((30, 50, 80)))
    # 先頭の面（+u 側）の窓
    d.polygon([p(u1, v - w * .75, height * .5), p(u1, v + w * .75, height * .5),
               p(u1, v + w * .75, height * .88), p(u1, v - w * .75, height * .88)], fill=_safe((30, 50, 80)))


def draw_big():
    """BIG×BIG の絵（全面不透明）。"""
    w = BIG * SS
    s = SS
    im = Image.new("RGBA", (w, w), NAVY + (255,))
    d = ImageDraw.Draw(im)
    _background(d, w)
    p = _iso(w / 2, 205 * s, 60 * s)
    _tile(d, p, -1, 1, -1, 1, (46, 110, 120), TEAL, 3 * s)
    _long_car(d, p, -2.6, 2.6, 0.0, 0.5)
    _text(d, (w / 2, 50 * s), "pak256", 64 * s, WHITE)
    # LongScale は大きく、太く（縁取りで太らせる）、明るい金で
    d.text((w / 2, 335 * s), "LongScale", font=_font(60 * s), fill=_safe(GOLD), anchor="mm",
           stroke_width=2 * s, stroke_fill=_safe(GOLD))
    return im.resize((BIG, BIG), Image.LANCZOS)  # 背景が全面不透明なので alpha は 255 のまま


def big_cells():
    """BigLogo の 4 枚（左上・右上・左下・右下）。"""
    im = draw_big()
    h = BIG // 2
    return [im.crop((x, y, x + h, y + h)) for y in (0, h) for x in (0, h)]


def small(size=128):
    """小さな Logo。大きな絵と同じ意匠を縮めたもの。"""
    return draw_big().resize((size, size), Image.LANCZOS)
