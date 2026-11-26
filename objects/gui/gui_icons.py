"""ツールバーのアイコンの絵（128px）。MIT License。draw_gui.py から使う。

道具ごとに、見て何をする道具か分かる簡単な図形の絵を描く（他の pak の絵は使わない）。
番号 → 絵の対応は ICONS（種類, 番号）。番号の意味は本体の simmenu.h の列挙（docs/gui.md の「アイコンの絵」）。
512px の絵に描いて 128px に縮め、縁の半透明を切る（makeobj の特別な色は、書き出す draw_gui.tool_icon が draw_ground.rgba で避ける）。
"""
import math

from PIL import Image, ImageDraw, ImageFont

ICON = 128
S = 4  # 描くときの倍率（縮めて縁をなめらかにする）

W = (255, 255, 255)
YEL = (255, 214, 64)
RED = (232, 84, 72)
GRN = (96, 200, 110)
DGRN = (50, 140, 70)
BLU = (130, 195, 255)
BRN = (160, 105, 60)
GRY = (205, 205, 212)
DRK = (40, 44, 52)
ORG = (255, 160, 60)

KIND_BG = {      # 種類ごとの地の色（絵の色が足りないときの手がかり。絵ごとに変えてもよい）
    "general": (46, 125, 110),
    "simple": (176, 100, 28),
    "dialog": (52, 96, 170),
    "bar": (120, 70, 150),
}


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


class Cv:
    """128 の座標で描く。xf で位置と倍率を変えると、小さな飾りを同じ関数で描ける。"""

    def __init__(self, bg):
        self.bg = bg
        self.im = Image.new("RGBA", (ICON * S, ICON * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.ox = self.oy = 64
        self.k = 1.0
        dark = tuple(int(v * 0.65) for v in bg)
        self.d.rounded_rectangle((0, 0, ICON * S - 1, ICON * S - 1), 18 * S, fill=bg, outline=dark, width=4 * S)

    def xf(self, ox=64, oy=64, k=1.0):
        self.ox, self.oy, self.k = ox, oy, k
        return self

    def P(self, p):
        return ((self.ox + (p[0] - 64) * self.k) * S, (self.oy + (p[1] - 64) * self.k) * S)

    def line(self, pts, w=8, col=W):
        q = [self.P(p) for p in pts]
        ww = w * self.k * S
        self.d.line(q, fill=col, width=int(ww), joint="curve")
        r = ww / 2
        for x, y in (q[0], q[-1]):
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=col)

    def poly(self, pts, col, outline=None, w=3):
        q = [self.P(p) for p in pts]
        self.d.polygon(q, fill=col)
        if outline:
            self.d.line(q + [q[0]], fill=outline, width=int(w * self.k * S), joint="curve")

    def rect(self, x0, y0, x1, y1, col, r=0, outline=None, w=0):
        a, b = self.P((x0, y0)), self.P((x1, y1))
        self.d.rounded_rectangle((a[0], a[1], b[0], b[1]), radius=r * self.k * S, fill=col, outline=outline,
                                 width=int(w * self.k * S))

    def ell(self, x0, y0, x1, y1, col=None, outline=None, w=0):
        a, b = self.P((x0, y0)), self.P((x1, y1))
        self.d.ellipse((a[0], a[1], b[0], b[1]), fill=col, outline=outline, width=int(w * self.k * S))

    def arc(self, x0, y0, x1, y1, a0, a1, w=8, col=W):
        a, b = self.P((x0, y0)), self.P((x1, y1))
        self.d.arc((a[0], a[1], b[0], b[1]), a0, a1, fill=col, width=int(w * self.k * S))

    def text(self, xy, t, size, col=W):
        x, y = self.P(xy)
        self.d.text((x, y), t, font=_font(int(size * self.k * S)), fill=col, anchor="mm")

    def done(self):
        im = self.im.resize((ICON, ICON), Image.LANCZOS)
        px = im.load()
        for y in range(ICON):      # 半透明の縁は切る（pak の絵は半透明を持てない）
            for x in range(ICON):
                r, g, b, a = px[x, y]
                px[x, y] = (r, g, b, 255) if a >= 128 else (0, 0, 0, 0)
        return im


def rot(p, c, ang):
    a = math.radians(ang)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a), c[1] + dx * math.sin(a) + dy * math.cos(a))


# ---------------------------------------------------------------- 部品

def arrow(c, x, y, ang, length, col=W, w=10, head=18):
    """(x, y) を中心に、ang 度（0 = 上、時計回り）を向く矢印。"""
    h = length / 2
    pts = [(x - w / 2, y + h), (x - w / 2, y - h + head), (x - head, y - h + head), (x, y - h),
           (x + head, y - h + head), (x + w / 2, y - h + head), (x + w / 2, y + h)]
    c.poly([rot(p, (x, y), ang) for p in pts], col)


def tile(c, cy=84, top=GRN, side=BRN, k=1.0):
    """地面の 1 マス（菱形に厚み）。"""
    a, b, d = 44 * k, 22 * k, 12 * k
    c.poly([(64 - a, cy), (64, cy + b), (64, cy + b + d), (64 - a, cy + d)], side)
    c.poly([(64 + a, cy), (64, cy + b), (64, cy + b + d), (64 + a, cy + d)], tuple(int(v * 0.8) for v in side))
    c.poly([(64, cy - b), (64 + a, cy), (64, cy + b), (64 - a, cy)], top, outline=DRK, w=2)


def house(c, x=64, y=64, k=1.0):
    c.xf(x, y, k)
    c.rect(34, 58, 94, 102, W)
    c.poly([(24, 62), (64, 24), (104, 62)], RED)
    c.rect(54, 76, 74, 102, BRN)
    c.rect(78, 66, 88, 78, BLU)
    c.xf()


def tree(c, x=64, y=64, k=1.0, col=GRN):
    c.xf(x, y, k)
    c.rect(57, 76, 71, 108, BRN)
    c.poly([(64, 14), (92, 50), (36, 50)], col)
    c.poly([(64, 34), (100, 76), (28, 76)], col)
    c.xf()


def person(c, x=64, y=64, k=1.0, col=W):
    c.xf(x, y, k)
    c.ell(44, 18, 84, 58, col)
    c.poly([(22, 108), (22, 84), (40, 66), (88, 66), (106, 84), (106, 108)], col)
    c.xf()


def bus(c, x=64, y=64, k=1.0, col=YEL):
    c.xf(x, y, k)
    c.rect(14, 38, 114, 88, col, r=10)
    for i in range(4):
        c.rect(22 + i * 22, 46, 38 + i * 22, 62, BLU)
    c.ell(24, 78, 46, 100, DRK, outline=W, w=3)
    c.ell(82, 78, 104, 100, DRK, outline=W, w=3)
    c.xf()


def magnifier(c, x=64, y=64, k=1.0, col=W):
    c.xf(x, y, k)
    c.ell(24, 20, 82, 78, outline=col, w=10)
    c.line([(72, 70), (106, 104)], 14, col)
    c.xf()


def gear(c, x=64, y=64, k=1.0):
    c.xf(x, y, k)
    c.ell(30, 30, 98, 98, W)
    for i in range(8):
        t = [rot(p, (64, 64), i * 45) for p in ((54, 14), (74, 14), (74, 34), (54, 34))]
        c.poly(t, W)
    c.ell(48, 48, 80, 80, c.bg)
    c.xf()


def flag(c, x=64, y=64, k=1.0, col=RED):
    c.xf(x, y, k)
    c.line([(40, 108), (40, 18)], 9)
    c.poly([(40, 20), (100, 40), (40, 62)], col)
    c.xf()


def coin(c, x=64, y=64, k=1.0):
    c.xf(x, y, k)
    c.ell(18, 18, 110, 110, YEL, outline=ORG, w=7)
    c.text((64, 66), "$", 78, (130, 80, 0))
    c.xf()


def lines(c, x0=28, x1=100, y0=36, n=3, gap=26, w=9, col=W):
    for i in range(n):
        c.line([(x0, y0 + i * gap), (x1, y0 + i * gap)], w, col)


def road(c, x=64, y=64, k=1.0):
    c.xf(x, y, k)
    c.poly([(48, 16), (80, 16), (116, 112), (12, 112)], (80, 84, 92), outline=W, w=3)
    for y0, y1 in ((28, 42), (56, 76), (90, 108)):
        c.poly([(62, y0), (66, y0), (67, y1), (61, y1)], YEL)
    c.xf()


def cube(c, y=64, k=1.0, hole=False):
    c.xf(64, y, k)
    c.poly([(64, 20), (108, 42), (64, 64), (20, 42)], GRN, outline=DRK, w=2)
    c.poly([(20, 42), (64, 64), (64, 108), (20, 86)], BRN, outline=DRK, w=2)
    c.poly([(108, 42), (64, 64), (64, 108), (108, 86)], (110, 70, 40), outline=DRK, w=2)
    if hole:
        c.poly([(32, 62), (52, 72), (52, 92), (32, 82)], DRK)
    c.xf()


def badge(c, kind):
    """右下の飾り（足す・引く・消す・直す・情報）。"""
    colors = {"plus": GRN, "minus": RED, "x": RED, "edit": ORG, "info": BLU}
    c.xf()
    c.ell(66, 66, 122, 122, colors[kind], outline=W, w=4)
    if kind == "plus":
        c.line([(78, 94), (110, 94)], 8)
        c.line([(94, 78), (94, 110)], 8)
    elif kind == "minus":
        c.line([(78, 94), (110, 94)], 8)
    elif kind == "x":
        c.line([(80, 80), (108, 108)], 8)
        c.line([(108, 80), (80, 108)], 8)
    elif kind == "edit":
        c.line([(82, 108), (106, 84)], 9)
        c.poly([(76, 114), (80, 102), (88, 110)], W)
    elif kind == "info":
        c.text((94, 96), "i", 40)


# ---------------------------------------------------------------- 絵

def g_query(c):
    magnifier(c, 56, 56, 0.95)
    c.text((50, 49), "?", 40)


def g_remove(c):
    c.line([(28, 28), (100, 100)], 18)
    c.line([(100, 28), (28, 100)], 18)


def g_raise(c):
    tile(c, 88, k=0.8)
    arrow(c, 64, 46, 0, 62, W, 16, 22)


def g_lower(c):
    tile(c, 40, k=0.8)
    arrow(c, 64, 82, 180, 62, W, 16, 22)


def g_section(c):
    """土地の断面（段のある地面）。"""
    c.poly([(14, 104), (14, 78), (46, 78), (82, 42), (114, 42), (114, 104)], BRN, outline=W, w=4)
    c.poly([(14, 78), (46, 78), (82, 42), (114, 42), (114, 52), (86, 52), (50, 88), (14, 88)], GRN)


def g_restore(c):
    g_section(c)
    c.arc(34, 14, 86, 66, 200, 340, 8, YEL)
    c.poly([(86, 40), (96, 22), (72, 26)], YEL)


def g_marker(c):
    flag(c)


def g_add_city(c):
    house(c, 44, 70, 0.62)
    house(c, 80, 56, 0.5)
    badge(c, "plus")


def g_plant(c):
    tree(c)


def g_lock(c):
    c.arc(38, 12, 90, 72, 180, 360, 11)
    c.line([(38, 42), (38, 54)], 11)
    c.line([(90, 42), (90, 54)], 11)
    c.rect(26, 50, 102, 108, YEL, r=10)
    c.ell(54, 68, 74, 88, DRK)
    c.rect(60, 78, 68, 98, DRK)


def g_car(c):
    c.rect(12, 62, 116, 92, RED, r=10)
    c.poly([(34, 64), (48, 36), (86, 36), (100, 64)], RED)
    c.poly([(42, 62), (52, 42), (62, 42), (62, 62)], BLU)
    c.poly([(68, 62), (68, 42), (82, 42), (92, 62)], BLU)
    c.ell(24, 78, 48, 102, DRK, outline=W, w=3)
    c.ell(80, 78, 104, 102, DRK, outline=W, w=3)


def g_forest(c):
    tree(c, 36, 74, 0.6)
    tree(c, 92, 74, 0.6)
    tree(c, 64, 62, 0.8)


def g_wayobj_remove(c):
    c.line([(40, 108), (40, 24)], 9)
    c.line([(40, 34), (96, 34)], 7)
    c.line([(24, 52), (60, 52), (96, 52)], 4, GRY)
    badge(c, "x")


def g_buy_land(c):
    """街の建物（家）を買う道具（TOOL_BUY_HOUSE）。"""
    house(c, 52, 58, 0.85)
    coin(c, 92, 96, 0.38)


def g_pause(c):
    c.rect(30, 24, 54, 104, W, r=4)
    c.rect(74, 24, 98, 104, W, r=4)


def g_ff(c):
    c.poly([(16, 26), (16, 102), (62, 64)], W)
    c.poly([(60, 26), (60, 102), (108, 64)], W)


def g_camera(c):
    c.rect(14, 36, 114, 100, GRY, r=10)
    c.rect(38, 26, 66, 40, GRY, r=3)
    c.ell(40, 46, 88, 94, DRK, outline=W, w=6)
    c.ell(54, 60, 74, 80, BLU)
    c.ell(94, 44, 106, 54, YEL)


def g_undo(c):
    c.arc(30, 32, 106, 108, 190, 360, 12)
    c.poly([(14, 62), (48, 62), (30, 92)], W)


def g_player(c):
    person(c, 64, 52, 0.8)
    c.line([(22, 110), (106, 110)], 7, YEL)
    c.poly([(22, 110), (36, 100), (36, 120)], YEL)
    c.poly([(106, 110), (92, 100), (92, 120)], YEL)


def g_zoom_in(c):
    magnifier(c, 56, 56, 0.95)
    c.line([(39, 49), (65, 49)], 7)
    c.line([(52, 36), (52, 62)], 7)


def g_zoom_out(c):
    magnifier(c, 56, 56, 0.95)
    c.line([(39, 49), (65, 49)], 7)


def g_coverage(c):
    c.ell(14, 14, 114, 114, outline=W, w=7)
    c.ell(36, 36, 92, 92, outline=W, w=7)
    c.ell(54, 54, 74, 74, YEL)


def g_names(c):
    c.rect(12, 34, 116, 94, W, r=10)
    c.text((64, 64), "Ab", 56, DRK)


def g_grid(c):
    c.rect(18, 18, 110, 110, None, outline=W, w=7)
    for t in (49, 80):
        c.line([(t, 20), (t, 108)], 6)
        c.line([(20, t), (108, t)], 6)


def g_trees(c):
    tree(c)


def g_houses(c):
    house(c)


def g_underground(c):
    cube(c, 62, 1.0, hole=True)


def g_section_view(c):
    """断面の表示（K。地面を横に切った面）。"""
    cube(c, 62, 1.0)
    c.poly([(8, 66), (64, 38), (120, 66), (64, 94)], YEL, outline=ORG, w=3)


def g_rotate(c):
    c.arc(22, 22, 106, 106, 40, 330, 13)
    c.poly([(98, 10), (118, 50), (74, 44)], W)


def g_quit(c):
    c.arc(24, 26, 104, 106, 300, 240, 12)
    c.line([(64, 14), (64, 62)], 12)


def g_tooltips(c):
    c.poly([(12, 18), (116, 18), (116, 84), (50, 84), (30, 108), (32, 84), (12, 84)], W)
    bus(c, 64, 48, 0.55, col=ORG)


def g_reservation(c):
    """線路の予約（ブロックの予約表示の切り替え）。2 本のレールと枕木のうち、予約された区間を赤く塗る。"""
    for i in range(7):
        c.line([(16 + i * 16, 30), (16 + i * 16, 98)], 7, BRN)
    c.rect(36, 24, 92, 104, RED, r=8)
    for x in (48, 64, 80):
        c.line([(x, 34), (x, 94)], 6, (255, 190, 180))
    c.line([(6, 48), (122, 48)], 9, W)
    c.line([(6, 80), (122, 80)], 9, W)


def g_owner(c):
    person(c, 52, 56, 0.8)
    magnifier(c, 86, 84, 0.5)


def g_help(c):
    c.text((64, 66), "?", 118)


def g_options(c):
    for y, x in ((34, 40), (64, 78), (94, 52)):
        c.line([(20, y), (108, y)], 7, GRY)
        c.ell(x - 12, y - 12, x + 12, y + 12, W, outline=DRK, w=3)


def g_minimap(c):
    c.rect(12, 20, 116, 108, BLU, r=6, outline=W, w=5)
    c.poly([(22, 34), (60, 30), (68, 56), (40, 70), (24, 60)], GRN)
    c.poly([(70, 66), (104, 60), (106, 98), (78, 96)], GRN)
    c.rect(48, 44, 84, 76, None, outline=YEL, w=4)


def g_lines(c):
    c.line([(18, 100), (46, 40), (80, 80), (110, 26)], 8, YEL)
    for p in ((18, 100), (46, 40), (80, 80), (110, 26)):
        c.ell(p[0] - 11, p[1] - 11, p[0] + 11, p[1] + 11, W, outline=DRK, w=3)


def g_messages(c):
    c.poly([(12, 18), (116, 18), (116, 88), (60, 88), (36, 112), (38, 88), (12, 88)], W)
    lines(c, 30, 98, 40, 2, 24, 7, (120, 130, 150))


def g_finance(c):
    coin(c)


def g_players(c):
    person(c, 38, 56, 0.62, GRY)
    person(c, 84, 60, 0.74, W)


def g_display(c):
    c.rect(12, 20, 116, 90, GRY, r=8, outline=W, w=4)
    c.rect(20, 28, 108, 82, DRK)
    c.ell(48, 36, 80, 74, W)
    c.ell(58, 46, 70, 64, BLU)
    c.line([(64, 92), (64, 106)], 8)
    c.line([(38, 108), (90, 108)], 8)


def g_sound(c):
    c.poly([(16, 48), (40, 48), (68, 22), (68, 106), (40, 80), (16, 80)], W)
    c.arc(60, 40, 96, 88, 300, 60, 7)
    c.arc(56, 24, 112, 104, 305, 55, 7)


def g_language(c):
    c.ell(16, 16, 112, 112, outline=W, w=7)
    c.ell(44, 16, 84, 112, outline=W, w=6)
    c.line([(16, 64), (112, 64)], 6)
    c.line([(24, 40), (104, 40)], 5)
    c.line([(24, 88), (104, 88)], 5)


def g_colors(c):
    for (x, y), col in zip(((14, 14), (68, 14), (14, 68), (68, 68)), (RED, YEL, GRN, BLU)):
        c.rect(x, y, x + 46, y + 46, col, r=8, outline=W, w=3)


def g_jump(c):
    c.ell(24, 24, 104, 104, outline=W, w=8)
    c.line([(64, 8), (64, 46)], 8)
    c.line([(64, 82), (64, 120)], 8)
    c.line([(8, 64), (46, 64)], 8)
    c.line([(82, 64), (120, 64)], 8)
    c.ell(54, 54, 74, 74, RED)


def g_load(c):
    c.poly([(12, 40), (46, 40), (56, 52), (116, 52), (116, 108), (12, 108)], YEL)
    arrow(c, 64, 72, 180, 40, DRK, 12, 16)


def g_save(c):
    c.rect(14, 14, 114, 114, W, r=10)
    c.rect(34, 14, 88, 46, GRY)
    c.rect(70, 18, 82, 40, DRK)
    c.rect(30, 66, 98, 114, BLU)
    lines(c, 40, 88, 82, 2, 18, 5)


def g_halt(c):
    c.line([(46, 110), (46, 18)], 9)
    c.rect(46, 18, 108, 62, YEL, r=6, outline=DRK, w=3)
    c.text((77, 41), "H", 36, DRK)


def g_convoys(c):
    bus(c, 64, 56, 0.9)
    lines(c, 24, 104, 100, 1, 0, 8)


def g_towns(c):
    c.rect(14, 54, 50, 108, W)
    c.rect(54, 28, 92, 108, GRY)
    c.rect(96, 62, 116, 108, W)
    for x, y in ((22, 64), (22, 84), (62, 38), (62, 58), (62, 78), (74, 38), (74, 58), (74, 78)):
        c.rect(x, y, x + 8, y + 10, BLU)


def g_goods(c):
    c.poly([(64, 16), (112, 38), (64, 60), (16, 38)], (220, 170, 100), outline=DRK, w=3)
    c.poly([(16, 38), (64, 60), (64, 112), (16, 90)], (190, 140, 80), outline=DRK, w=3)
    c.poly([(112, 38), (64, 60), (64, 112), (112, 90)], (160, 110, 60), outline=DRK, w=3)


def g_factory(c):
    c.rect(14, 56, 114, 108, GRY)
    c.poly([(14, 56), (14, 38), (46, 56)], GRY)
    c.poly([(46, 56), (46, 38), (78, 56)], GRY)
    c.rect(86, 18, 104, 56, (150, 80, 70))
    c.ell(80, 6, 112, 24, (230, 230, 235))
    c.rect(26, 74, 40, 90, BLU)
    c.rect(52, 74, 66, 90, BLU)


def g_tower(c):
    c.rect(38, 36, 90, 108, GRY)
    for x in (34, 54, 74):
        c.rect(x, 20, x + 18, 40, GRY)
    c.rect(54, 80, 74, 108, BRN, r=8)
    c.rect(58, 52, 70, 68, DRK)


def g_edit_house(c):
    house(c, 56, 60, 0.85)
    badge(c, "edit")


def g_edit_tree(c):
    tree(c, 56, 60, 0.85)
    badge(c, "edit")


def g_enlarge(c):
    c.rect(36, 36, 92, 92, None, outline=W, w=6)
    for ang in (45, 135, 225, 315):
        a = math.radians(ang)
        x, y = 64 + 46 * math.sin(a), 64 - 46 * math.cos(a)
        arrow(c, x, y, ang, 36, YEL, 8, 14)


def g_label_list(c):
    flag(c, 40, 62, 0.8)
    lines(c, 70, 112, 40, 3, 24, 7)


def g_info(c):
    c.ell(14, 14, 114, 114, W)
    c.text((64, 66), "i", 86, (52, 96, 170))


def g_doc(c):
    c.poly([(26, 10), (80, 10), (104, 34), (104, 118), (26, 118)], W)
    c.poly([(80, 10), (80, 34), (104, 34)], GRY)
    lines(c, 40, 90, 52, 3, 20, 7, (120, 130, 150))


def g_doc_info(c):
    g_doc(c)
    badge(c, "info")


def g_depot(c):
    c.poly([(10, 54), (64, 18), (118, 54), (118, 112), (10, 112)], GRY)
    c.rect(32, 62, 96, 112, DRK)
    for y in (72, 86, 100):
        c.line([(34, y), (94, y)], 4, GRY)


def g_vehicles(c):
    bus(c, 50, 48, 0.8)
    lines(c, 76, 112, 82, 3, 14, 6)
    lines(c, 14, 62, 82, 3, 14, 6)


def g_script(c):
    c.text((64, 62), "{ }", 74)


def g_bush(c):
    for x, y, r in ((40, 74, 26), (88, 74, 26), (64, 56, 32)):
        c.ell(x - r, y - r, x + r, y + r, GRN, outline=DGRN, w=3)
    c.rect(56, 82, 72, 108, BRN)


def g_edit_bush(c):
    g_bush(c)
    badge(c, "edit")


def g_slope_tool(c):
    g_section(c)
    arrow(c, 78, 28, 0, 30, YEL, 8, 12)


def g_tram_tool(c):
    """路面電車の道具: 前から見た車体と、その下の 2 本のレール。"""
    c.line([(64, 14), (64, 28)], 6, GRY)
    c.line([(46, 14), (82, 14)], 6, GRY)
    c.rect(34, 28, 94, 96, YEL, r=14, outline=W, w=3)
    c.rect(44, 40, 84, 66, DRK, r=4)
    c.rect(34, 76, 94, 86, RED)
    for x in (48, 80):
        c.ell(x - 5, 82, x + 5, 92, W)
    for x0, x1 in ((46, 30), (82, 98)):
        c.line([(x0, 98), (x1, 118)], 7, W)


def g_road_tool(c):
    road(c)


def rail(c, x=64, y=64, k=1.0):
    """線路の帯: 道床に、まくらぎと 2 本のレール。"""
    c.xf(x, y, k)
    c.poly([(48, 16), (80, 16), (116, 112), (12, 112)], (112, 98, 84), outline=W, w=3)
    for y0 in (30, 52, 76, 100):
        c.poly([(46 - (y0 - 16) * 0.5, y0), (82 + (y0 - 16) * 0.5, y0), (82 + (y0 - 16) * 0.5, y0 + 6),
                (46 - (y0 - 16) * 0.5, y0 + 6)], (70, 50, 36))
    for dx in (-8, 8):
        c.poly([(64 + dx - 1, 16), (64 + dx + 1, 16), (64 + dx * 7 + 2, 112), (64 + dx * 7 - 2, 112)], (200, 204, 210))
    c.xf()


def g_rail_tool(c):
    """線路の道具: 道床の帯に、まくらぎと 2 本のレール。"""
    rail(c)


def g_rail_x(c):
    """線路の撤去: 線路の帯に赤い ×。"""
    rail(c, 56, 56, 0.85)
    badge(c, "x")


def ship(c, x=64, y=64, k=1.0):
    """船: 船体と上の船室・煙突、下に波。"""
    c.xf(x, y, k)
    c.poly([(14, 66), (114, 66), (96, 94), (30, 94)], (70, 120, 200), outline=W, w=3)
    c.rect(40, 42, 82, 66, W)
    for i in range(3):
        c.rect(46 + i * 12, 48, 54 + i * 12, 58, BLU)
    c.rect(66, 22, 78, 42, RED)
    c.line([(16, 108), (36, 102), (56, 108), (76, 102), (96, 108), (112, 104)], 7, BLU)
    c.xf()


def g_ship_tool(c):
    ship(c)


def g_canal_x(c):
    """運河の撤去: 水路に赤い ×。"""
    c.poly([(34, 14), (62, 14), (90, 100), (14, 100)], (60, 110, 160), outline=W, w=3)
    badge(c, "x")


def monorail(c, x=64, y=64, k=1.0):
    """跨座式モノレール: 桁と柱の上の車体（正面）。"""
    c.xf(x, y, k)
    c.rect(54, 76, 74, 116, GRY)
    c.rect(24, 24, 104, 96, W, r=16, outline=DRK, w=3)
    c.rect(36, 36, 92, 62, BLU, r=4)
    c.rect(24, 70, 104, 78, (44, 96, 168))
    c.rect(54, 82, 74, 98, GRY)
    c.xf()


def g_monorail_tool(c):
    monorail(c)


def g_monorail_x(c):
    """モノレールの撤去: モノレールに赤い ×。"""
    monorail(c, 56, 56, 0.85)
    badge(c, "x")


def g_signal_x(c):
    """信号の撤去: 信号の柱と灯りに赤い ×。"""
    c.line([(44, 112), (44, 40)], 9)
    c.rect(26, 14, 62, 50, DRK, r=6, outline=W, w=3)
    c.ell(34, 22, 54, 42, GRN)
    c.line([(24, 112), (64, 112)], 7, GRY)
    badge(c, "x")


def plane(c, cx, cy, k):
    """上から見た飛行機（右上を向く）。"""
    c.xf(cx, cy, k)
    c.line([(28, 100), (100, 28)], 15)
    c.poly([(58, 70), (16, 52), (28, 40), (80, 48)], W)  # 左の翼
    c.poly([(58, 70), (76, 112), (88, 100), (80, 48)], W)  # 右の翼
    c.poly([(36, 92), (14, 86), (22, 78), (44, 84)], W)  # 左の尾翼
    c.poly([(36, 92), (42, 114), (50, 106), (44, 84)], W)  # 右の尾翼
    c.xf()


def runway_strip(c, cx, cy, k):
    """上へ細くなる滑走路の帯（中心の破線）。"""
    c.xf(cx, cy, k)
    c.poly([(40, 14), (88, 14), (114, 114), (14, 114)], DRK, outline=W, w=3)
    for y in (24, 54, 86):
        c.line([(64, y), (64, y + 16)], 7, YEL)
    c.xf()


def g_air_tool(c):
    plane(c, 64, 64, 1.0)


def g_airstrip_x(c):
    """滑走路・誘導路の撤去。"""
    runway_strip(c, 56, 56, 0.85)
    badge(c, "x")


def g_special(c):
    pts = []
    for i in range(10):
        r = 52 if i % 2 == 0 else 22
        a = math.radians(i * 36)
        pts.append((64 + r * math.sin(a), 68 - r * math.cos(a)))
    c.poly(pts, YEL, outline=ORG, w=4)


def g_list(c):
    for i in range(3):
        c.ell(16, 24 + i * 32, 32, 40 + i * 32, YEL)
        c.line([(44, 32 + i * 32), (112, 32 + i * 32)], 9)


def g_pencil(c):
    c.poly([(22, 104), (26, 78), (88, 16), (112, 40), (50, 102)], YEL, outline=DRK, w=3)
    c.poly([(22, 104), (26, 78), (48, 100)], W)
    c.poly([(88, 16), (112, 40), (102, 50), (78, 26)], (240, 130, 150))


def _dir_slope(angle, letter, double=False):
    def f(c):
        tile(c, 70, k=1.0)
        a = math.radians(angle)
        arrow(c, 64, 62, angle, 44, YEL, 11, 17)
        if double:
            arrow(c, 64 + 12 * math.sin(a), 62 - 12 * math.cos(a), angle, 44, ORG, 11, 17)
        c.text((64, 108), letter, 26, W)
    return f


def g_tile_up(c):
    tile(c, 82, k=0.8)
    arrow(c, 64, 42, 0, 56, W, 15, 20)


def g_tile_down(c):
    tile(c, 40, k=0.8)
    arrow(c, 64, 78, 180, 56, W, 15, 20)


def g_road_x(c):
    road(c, 56, 56, 0.85)
    badge(c, "x")


def g_city_plus(c):
    house(c, 54, 60, 0.85)
    badge(c, "plus")


def g_city_minus(c):
    house(c, 54, 60, 0.85)
    badge(c, "minus")


def g_city_road(c):
    road(c, 46, 66, 0.8)
    house(c, 90, 44, 0.5)


def _waves(c, y=60, col=W):
    for dy in (0, 28, 56):
        c.arc(8, y + dy - 12, 48, y + dy + 12, 180, 360, 7, col)
        c.arc(40, y + dy - 12, 80, y + dy + 12, 180, 360, 7, col)
        c.arc(72, y + dy - 12, 112, y + dy + 12, 180, 360, 7, col)


def g_water_up(c):
    for dy in (0, 26):
        c.arc(8, 64 + dy - 12, 48, 64 + dy + 12, 180, 360, 7)
        c.arc(40, 64 + dy - 12, 80, 64 + dy + 12, 180, 360, 7)
    arrow(c, 64, 34, 0, 40, W, 12, 16)


def g_water_down(c):
    for dy in (0, 26):
        c.arc(8, 64 + dy - 12, 48, 64 + dy + 12, 180, 360, 7)
        c.arc(40, 64 + dy - 12, 80, 64 + dy + 12, 180, 360, 7)
    arrow(c, 64, 34, 180, 40, W, 12, 16)


def g_cl_water(c):
    _waves(c, 30)


def g_cl_desert(c):
    c.ell(70, 14, 108, 52, YEL)
    c.poly([(8, 108), (40, 62), (66, 94), (92, 70), (120, 108)], (240, 210, 130))
    c.rect(26, 40, 36, 74, GRN, r=5)
    c.rect(18, 50, 26, 62, GRN, r=3)
    c.rect(36, 46, 44, 58, GRN, r=3)


def g_cl_tropic(c):
    c.line([(64, 110), (60, 56)], 9, BRN)
    for ang in (-70, -30, 20, 60):
        a = math.radians(ang)
        c.line([(60, 54), (60 + 44 * math.sin(a), 54 - 30 * math.cos(a) + 10)], 9, GRN)
    c.ell(54, 52, 70, 68, BRN)


def g_cl_medit(c):
    c.rect(58, 70, 70, 112, BRN)
    c.ell(28, 20, 100, 84, (170, 190, 90))
    c.ell(76, 6, 114, 42, YEL)


def g_cl_temperate(c):
    c.rect(58, 70, 70, 112, BRN)
    c.ell(24, 14, 104, 86, GRN, outline=DGRN, w=3)


def g_cl_tundra(c):
    for x in (30, 52, 74, 96):
        c.line([(x, 104), (x - 6, 76)], 6, (190, 210, 160))
        c.line([(x, 104), (x + 4, 72)], 6, (190, 210, 160))
    for x, y in ((20, 28), (60, 20), (100, 34), (40, 52), (84, 54)):
        c.ell(x - 7, y - 7, x + 7, y + 7, W)


def g_cl_rock(c):
    c.poly([(8, 108), (46, 28), (64, 60), (84, 36), (120, 108)], GRY, outline=DRK, w=3)
    c.poly([(46, 28), (36, 50), (46, 46), (54, 52)], W)
    c.poly([(84, 36), (76, 52), (84, 50), (92, 54)], W)


def g_cl_arctic(c):
    for ang in (0, 60, 120):
        p0, p1 = rot((64, 12), (64, 64), ang), rot((64, 116), (64, 64), ang)
        c.line([p0, p1], 8)
    for ang in (0, 60, 120, 180, 240, 300):
        for t in (30, 44):
            q = rot((64, t), (64, 64), ang)
            c.line([q, rot((64 - 12, t - 12), (64, 64), ang)], 5)
            c.line([q, rot((64 + 12, t - 12), (64, 64), ang)], 5)


def g_cube_up(c):
    cube(c, 56, 0.85)
    arrow(c, 96, 96, 0, 40, GRN, 10, 15)


def g_cube_down(c):
    cube(c, 56, 0.85)
    arrow(c, 96, 96, 180, 40, RED, 10, 15)


def g_newgame(c):
    g_doc(c)
    c.poly([(92, 70), (97, 84), (112, 84), (100, 94), (104, 108), (92, 100), (80, 108), (84, 94), (72, 84), (87, 84)],
           YEL, outline=ORG, w=2)


ICONS = {
    # 一般の道具（本体の GENERAL_TOOL の番号）
    ("general", 0): g_query,
    ("general", 1): g_remove,
    ("general", 2): g_raise,
    ("general", 3): g_lower,
    ("general", 5): g_restore,
    ("general", 6): g_marker,
    ("general", 9): g_add_city,
    ("general", 11): g_plant,
    ("general", 28): g_lock,
    ("general", 29): g_car,
    ("general", 30): g_forest,
    ("general", 33): g_wayobj_remove,
    ("general", 35): g_buy_land,
    # 1 回押す道具（SIMPLE_TOOL）
    ("simple", 0): g_pause,
    ("simple", 1): g_ff,
    ("simple", 2): g_camera,
    ("simple", 4): g_undo,
    ("simple", 5): g_player,
    ("simple", 8): g_zoom_in,
    ("simple", 9): g_zoom_out,
    ("simple", 10): g_coverage,
    ("simple", 11): g_names,
    ("simple", 12): g_grid,
    ("simple", 13): g_trees,
    ("simple", 14): g_houses,
    ("simple", 15): g_section_view,
    ("simple", 16): g_rotate,
    ("simple", 17): g_quit,
    ("simple", 20): g_tooltips,
    ("simple", 33): g_reservation,
    ("simple", 34): g_owner,
    # 窓を開く道具（DIALOGE_TOOL）
    ("dialog", 0): g_help,
    ("dialog", 1): g_options,
    ("dialog", 2): g_minimap,
    ("dialog", 3): g_lines,
    ("dialog", 4): g_messages,
    ("dialog", 5): g_finance,
    ("dialog", 6): g_players,
    ("dialog", 7): g_display,
    ("dialog", 8): g_sound,
    ("dialog", 9): g_language,
    ("dialog", 10): g_colors,
    ("dialog", 11): g_jump,
    ("dialog", 12): g_load,
    ("dialog", 13): g_save,
    ("dialog", 14): g_halt,
    ("dialog", 15): g_convoys,
    ("dialog", 16): g_towns,
    ("dialog", 17): g_goods,
    ("dialog", 18): g_factory,
    ("dialog", 19): g_tower,
    ("dialog", 22): g_edit_house,
    ("dialog", 23): g_edit_tree,
    ("dialog", 24): g_enlarge,
    ("dialog", 25): g_label_list,
    ("dialog", 27): gear,
    ("dialog", 28): g_info,
    ("dialog", 30): g_doc,
    ("dialog", 31): g_doc_info,
    ("dialog", 32): g_depot,
    ("dialog", 33): g_vehicles,
    ("dialog", 34): g_script,
    ("dialog", 35): g_edit_bush,
    # ツールバーの行で指定する番号（BarTools）
    ("bar", 0): g_slope_tool,
    ("bar", 1): g_rail_tool,
    ("bar", 3): g_tram_tool,
    ("bar", 4): g_road_tool,
    ("bar", 7): g_special,
    ("bar", 8): g_list,
    ("bar", 9): g_pencil,
    ("bar", 10): _dir_slope(243, "S"),
    ("bar", 11): _dir_slope(63, "N"),
    ("bar", 12): _dir_slope(297, "W"),
    ("bar", 13): _dir_slope(117, "E"),
    ("bar", 14): g_tile_up,
    ("bar", 15): g_tile_down,
    ("bar", 20): g_road_x,
    ("bar", 22): g_cube_up,
    ("bar", 23): g_cube_down,
    ("bar", 25): g_city_plus,
    ("bar", 26): g_city_minus,
    ("bar", 27): g_city_road,
    ("bar", 29): gear,
    ("bar", 30): g_water_up,
    ("bar", 31): g_water_down,
    ("bar", 32): g_cl_water,
    ("bar", 33): g_cl_desert,
    ("bar", 34): g_cl_tropic,
    ("bar", 35): g_cl_medit,
    ("bar", 36): g_cl_temperate,
    ("bar", 37): g_cl_tundra,
    ("bar", 38): g_cl_rock,
    ("bar", 39): g_cl_arctic,
    ("bar", 40): _dir_slope(243, "S", True),
    ("bar", 41): _dir_slope(63, "N", True),
    ("bar", 42): _dir_slope(297, "W", True),
    ("bar", 43): _dir_slope(117, "E", True),
    ("bar", 44): g_underground,
    ("bar", 45): g_newgame,
    ("bar", 46): g_rail_x,
    ("bar", 47): g_signal_x,
    ("bar", 48): g_ship_tool,
    ("bar", 49): g_canal_x,
    ("bar", 52): g_air_tool,
    ("bar", 53): g_airstrip_x,
    ("bar", 56): g_monorail_x,
    ("bar", 57): g_monorail_tool,
}

BG = {      # 地の色を変える絵（気候は色で見分けやすくする）
    ("general", 1): (170, 56, 50),
    ("bar", 20): (170, 56, 50),
    ("bar", 46): (170, 56, 50),
    ("bar", 47): (170, 56, 50),
    ("bar", 49): (170, 56, 50),
    ("bar", 53): (170, 56, 50),
    ("bar", 56): (170, 56, 50),
    ("bar", 32): (30, 90, 170),
    ("bar", 33): (190, 150, 60),
    ("bar", 34): (30, 130, 80),
    ("bar", 35): (120, 130, 60),
    ("bar", 36): (60, 120, 60),
    ("bar", 37): (100, 130, 140),
    ("bar", 38): (95, 95, 105),
    ("bar", 39): (90, 140, 190),
    ("bar", 30): (30, 90, 170),
    ("bar", 31): (30, 90, 170),
}


def draw_icon(kind, n):
    """(種類, 番号) のアイコン。絵が無い番号は KeyError（番号だけの絵は作らない）。"""
    fn = ICONS[(kind, n)]
    c = Cv(BG.get((kind, n), KIND_BG[kind]))
    fn(c)
    return c.done()
