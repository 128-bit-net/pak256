"""GUI の絵（ツールバーのアイコン・記号・カーソル・その他）と dat を書き出す。MIT License。

使い方（このフォルダで）:
    python -X utf8 draw_gui.py [出力先]     出力先の既定はこのフォルダ

絵はすべてこのスクリプトが描く仮の絵（他の pak の絵は使わない）。決め事は docs/gui.md。
書き出すもの（dat の Obj と Name ＝ 本体が探す名前）:
    menu    GeneralTools / SimpleTools / DialogeTools / BarTools   ツールバーのアイコン（128px）
    cursor  GeneralTools / Builder / Marked                        タイルの上のカーソル（256px）
    symbol  Seasons / MessageOptions / ColorOptions / Logo / NewYear / NewWorld / Flags /
            Message / Electricity / InTown / Passagiere / Post / Waren
    misc    RibiArrow / PowerSource / PowerDest / Construction / Sidewalk / TunnelTexture

アイコンの番号は config/menuconf.tab が使う番号。menuconf.tab を読んで、使われる番号だけ描く。
アイコンの表示の大きさ（menuconf.tab の icon_width）は、本体が絵を表示幅へ縮めるので、元の絵（128px）とは別に決められる。
"""
import math
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "objects", "ground", "temperate"))
import draw_ground as dg  # noqa: E402  タイルの形（column_span など）を借りる

COPYRIGHT = dg.COPYRIGHT
ICON = 128          # アイコンの元の絵
TILE = 256
GUI_BLUE = (36, 84, 140)
# 本体は GeneralTools のカーソルを Z_PLAN（4/64 タイル = 16px）下げて描く。タイルの強調表示に重なるよう、絵を 16px 上に描く
CURSOR_DY = -16

TYPE_STYLE = {      # 種類: (表示の記号, 色)
    "general": ("G", (46, 125, 110)),
    "simple": ("S", (190, 110, 30)),
    "dialog": ("D", (52, 96, 170)),
    "bar": ("B", (120, 70, 150)),
}
MENU_NAME = {"general": "GeneralTools", "simple": "SimpleTools", "dialog": "DialogeTools", "bar": "BarTools"}


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def special_safe(c):
    """makeobj の特別な色を避ける（draw_ground の rgba と同じ決まり）。"""
    return dg.rgba(*c)


class Sheet:
    """cell px のマスを cols 列に並べた PNG。"""

    def __init__(self, name, count, cell, cols=10):
        self.name, self.cell, self.cols = name, cell, cols
        self.rows = max(1, -(-count // cols))
        self.im = Image.new("RGBA", (cols * cell, self.rows * cell), (0, 0, 0, 0))

    def put(self, i, img):
        self.im.paste(img, ((i % self.cols) * self.cell, (i // self.cols) * self.cell))

    def ref(self, i):
        return f"{self.name}.{i // self.cols}.{i % self.cols}"

    def save(self, outdir):
        self.im.save(os.path.join(outdir, self.name + ".png"))


def write_dat(outdir, filename, obj, name, lines, cell, comment=""):
    text = ["# " + comment] if comment else []
    text += [f"Obj={obj}", f"Name={name}", f"copyright={COPYRIGHT}", f"cell_size={cell}"]
    text += lines
    with open(os.path.join(outdir, filename), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(text) + "\n")


def image_lines(sheet, images, unzoom):
    """images: 番号 -> 絵 or None（空き）。"""
    lines = []
    last = max(images) if images else -1
    for i in range(last + 1):
        if images.get(i) is None:
            lines.append(f"Image[{i}]=-")
        else:
            lines.append(f"Image[{i}]={'> ' if unzoom else ''}{sheet.ref(i)}")
    return lines


# ---------------------------------------------------------------- menuconf.tab から使う番号を読む

def used_icons():
    """menuconf.tab で使われるアイコンの番号を、種類ごとに返す。"""
    path = os.path.join(ROOT, "config", "menuconf.tab")
    used = {k: set() for k in TYPE_STYLE}
    defaults = {}
    kind_of = {"general_tool": "general", "simple_tool": "simple", "dialog_tool": "dialog"}
    with open(path, encoding="utf-8") as f:
        text = f.read().splitlines()
    for ln in text:
        ln = ln.split("#")[0].strip()
        m = re.match(r"(general_tool|simple_tool|dialog_tool)\[(\d+)\]\s*=\s*(.*)", ln)
        if m:
            first = m.group(3).split(",")[0].strip()
            kind = kind_of[m.group(1)]
            defaults[(kind, int(m.group(2)))] = int(first) if first else None
            if first:
                used[kind].add(int(first))
            continue
        m = re.match(r"toolbar\[\d+\]\[\d+\]\s*=\s*(general_tool|simple_tool|dialog_tool|toolbar)\[(\d+)\](.*)", ln)
        if m:
            # ツールバーの行の 2 つめの値（アイコンの番号）は、道具の種類に関わらず BarTools の番号（本体の tool_t::read_menu）
            parts = m.group(3).split(",")
            icon = parts[1].strip() if len(parts) > 1 else ""
            kind = kind_of.get(m.group(1))
            if icon:
                used["bar"].add(int(icon))
            elif kind and defaults.get((kind, int(m.group(2)))) is not None:
                used[kind].add(defaults[(kind, int(m.group(2)))])
    return used


# ---------------------------------------------------------------- アイコン

def tool_icon(kind, n):
    letter, col = TYPE_STYLE[kind]
    im = Image.new("RGBA", (ICON, ICON), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, ICON - 1, ICON - 1), 18, fill=special_safe((*col, 255)))
    d.rounded_rectangle((8, 8, ICON - 9, ICON - 9), 12, outline=special_safe((235, 235, 235, 255)), width=3)
    f = font(64)
    d.text((ICON / 2, ICON / 2 + 4), str(n), font=f, fill=special_safe((255, 255, 255, 255)), anchor="mm")
    d.text((20, 18), letter, font=font(24), fill=special_safe((255, 255, 255, 255)))
    return im


def build_menu(outdir, used):
    for kind, nums in used.items():
        if not nums:
            continue
        name = "menu_" + kind
        sheet = Sheet(name, max(nums) + 1, ICON)
        images = {}
        for n in sorted(nums):
            sheet.put(n, tool_icon(kind, n))
            images[n] = True
        sheet.save(outdir)
        write_dat(outdir, name + ".dat", "menu", MENU_NAME[kind], image_lines(sheet, images, True), ICON,
                  "ツールバーのアイコン。番号は config/menuconf.tab のもの（道具の既定のアイコンは種類ごとの表、ツールバーの行で指定した番号は BarTools）。使われない番号は空き（-）")


# ---------------------------------------------------------------- タイルの上の絵

def outline_diamond(color, width=6, fill=None, dy=0):
    """平らなタイルの菱形の輪郭（カーソル）。タイルの菱形は行 128〜255。"""
    pix = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(pix)
    pts = [(128, 128 + dy), (255, 192 + dy), (128, 255 + dy), (0, 192 + dy)]
    if fill:
        d.polygon(pts, fill=special_safe(fill))
    d.line(pts + [pts[0]], fill=special_safe(color), width=width, joint="curve")
    return pix


def cursor_image(n, color=(255, 230, 0, 255)):
    im = outline_diamond(color, dy=CURSOR_DY)
    d = ImageDraw.Draw(im)
    d.text((128, 192 + CURSOR_DY), str(n), font=font(48), fill=special_safe(color), anchor="mm")
    return im


def build_cursors(outdir, count):
    sheet = Sheet("cursor_general", count, TILE, cols=8)
    for i in range(count):
        sheet.put(i, cursor_image(i))
    sheet.save(outdir)
    write_dat(outdir, "cursor_general.dat", "cursor", "GeneralTools",
              image_lines(sheet, {i: True for i in range(count)}, False), TILE,
              "道具のカーソル。タイルの菱形の輪郭に番号。番号は menuconf.tab の general_tool の 2 つめ")

    # Builder: 建てるときの印（太い橙の菱形）。Marked: 印を付けた所（赤の菱形）
    for fname, name, color, fill in (
        ("cursor_builder", "Builder", (255, 160, 0, 255), (255, 160, 0, 60)),
        ("cursor_marked", "Marked", (230, 40, 40, 255), (230, 40, 40, 50)),
    ):
        s = Sheet(fname, 1, TILE)
        s.put(0, outline_diamond(color, 8, fill))
        s.save(outdir)
        write_dat(outdir, fname + ".dat", "cursor", name, image_lines(s, {0: True}, False), TILE)


def stripes_diamond(c1, c2, period=40):
    spans = dg.column_span(0, 0, 0, 0)
    pix = [(0, 0, 0, 0)] * (TILE * TILE)
    for y in range(128, TILE):
        for x in range(TILE):
            if dg.covered(spans, x, y):
                k = ((x + 2 * y) // period) % 2
                pix[y * TILE + x] = special_safe((*(c1 if k else c2), 255))
    return dg.from_pixels(pix)


def build_construction(outdir):
    # 0 基礎の穴・1 観光地(街)・2 観光地(田舎)・3 記念物・4 工場・5 役場・6 その他・7 住宅・8 商業・9 工業
    tints = [(200, 150, 40), (170, 120, 200), (120, 170, 90), (190, 190, 190), (150, 150, 160),
             (200, 90, 90), (140, 110, 80), (80, 170, 80), (80, 130, 200), (190, 150, 60)]
    sheet = Sheet("construction", 10, TILE, cols=5)
    for i, t in enumerate(tints):
        sheet.put(i, stripes_diamond(t, (60, 60, 60)))
    sheet.save(outdir)
    write_dat(outdir, "construction.dat", "misc", "Construction",
              image_lines(sheet, {i: True for i in range(10)}, False), TILE,
              "工事中の地面。0 基礎の穴・1 観光地(街)・2 観光地(田舎)・3 記念物・4 工場・5 役場・6 その他・7 住宅・8 商業・9 工業")


SINGLE_SLOPES = [0, 1, 3, 4, 9, 10, 12, 13, 27, 28, 30, 31, 36, 37, 39]   # 本体の slopetable の順（単段の坂 15 通り）


def slope_corners(code, mul=1):
    return (code % 3) * mul, ((code // 3) % 3) * mul, ((code // 9) % 3) * mul, (code // 27) * mul


def paved_tile(corners, base, line):
    """坂 corners=(sw, se, ne, nw) の面を base で塗り、縁に line の細い線を引く。"""
    spans = dg.column_span(*corners)
    pix = [(0, 0, 0, 0)] * (TILE * TILE)
    for y in range(40, TILE):
        for x in range(TILE):
            if dg.covered(spans, x, y):
                t, b = spans[x]
                edge = (y - t < 4) or (b - y <= 4)
                pix[y * TILE + x] = special_safe((*(line if edge else base), 255))
    return dg.from_pixels(pix)


def build_ground_like(outdir, fname, name, base, line, note):
    """Sidewalk・TunnelTexture。番号は本体の imageid（単段 0〜14、複段は slopetable + 12 で 12〜26）。"""
    sheet = Sheet(fname, 27, TILE, cols=9)
    for i in range(27):
        if i < 15:
            corners = slope_corners(SINGLE_SLOPES[i])
        else:   # 複段（番号 12〜14 は単段と重なるので、単段を使う）
            corners = slope_corners(SINGLE_SLOPES[i - 12], 2)
        sheet.put(i, paved_tile(corners, base, line))
    sheet.save(outdir)
    write_dat(outdir, fname + ".dat", "misc", name, image_lines(sheet, {i: True for i in range(27)}, False), TILE, note)


def arrow(d, c, vec, color, size=70):
    dx, dy = vec
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    # 菱形の上なので縦は半分に潰す
    def p(a, b):
        return (c[0] + a * ux - b * uy * 1, c[1] + (a * uy + b * ux) / 2)
    d.line([p(0, 0), p(size * 0.2 - 10, 0)], fill=color, width=6)
    d.polygon([p(size * 0.2 + 14, 0), p(size * 0.2 - 18, -20), p(size * 0.2 - 18, 20)], fill=color)


def build_ribi_arrow(outdir):
    # ribi: 北 1・東 2・南 4・西 8。画面上は北が右上、東が右下、南が左下、西が左上（タイルの菱形の辺の向き）
    vec = {1: (2, -1), 2: (2, 1), 4: (-2, 1), 8: (-2, -1)}
    sheet = Sheet("ribi_arrow", 16, TILE, cols=4)
    col = special_safe((255, 255, 255, 255))
    for r in range(16):
        im = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for bit, v in vec.items():
            if r & bit:
                arrow(d, (128, 192), v, col, 90)
        sheet.put(r, im)
    sheet.save(outdir)
    write_dat(outdir, "ribi_arrow.dat", "misc", "RibiArrow", image_lines(sheet, {i: True for i in range(16)}, False), TILE,
              "一方通行などの向き。番号 = ribi（北 1・東 2・南 4・西 8）。道を通れる向きに矢印を出す")


def build_power(outdir):
    # 本体は動作中の絵を番号 1 で引く（leitung2.cc）。0 = 止まっている（くすんだ色）、1 = 動いている
    for fname, name, col, label in (("power_source", "PowerSource", (255, 200, 0), "+"),
                                    ("power_dest", "PowerDest", (90, 200, 255), "-")):
        s = Sheet(fname, 2, TILE, cols=2)
        for frame in (0, 1):
            im = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            c = col if frame else tuple(v // 2 for v in col)
            d.ellipse((98, 172, 158, 212), fill=special_safe((*c, 255)), outline=special_safe((20, 20, 20, 255)), width=4)
            d.text((128, 192), label, font=font(36), fill=special_safe((20, 20, 20, 255)), anchor="mm")
            s.put(frame, im)
        s.save(outdir)
        write_dat(outdir, fname + ".dat", "misc", name, image_lines(s, {0: True, 1: True}, False), TILE,
                  "発電所と使う側の印（送電網の表示）。0 止まっている・1 動いている")


# ---------------------------------------------------------------- 記号（小さな絵）

def glyph(kind, size):
    """size px の記号。縁まで描く（makeobj が透明な縁を切るので、位置がずれないように）。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = lambda *a: special_safe((*a, 255))
    s = size - 1
    if kind == "person":
        d.rectangle((0, 0, s, s), fill=c(230, 230, 230))
        d.ellipse((s * .3, 0, s * .7, s * .4), fill=c(60, 90, 160))
        d.rectangle((s * .15, s * .45, s * .85, s), fill=c(60, 90, 160))
    elif kind == "mail":
        d.rectangle((0, 0, s, s), fill=c(250, 240, 200))
        d.rectangle((0, 0, s, s), outline=c(170, 60, 50), width=max(1, size // 10))
        d.line((0, 0, s / 2, s * .6, s, 0), fill=c(170, 60, 50), width=max(1, size // 10))
    elif kind == "goods":
        d.rectangle((0, 0, s, s), fill=c(190, 140, 80))
        d.rectangle((0, 0, s, s), outline=c(110, 80, 40), width=max(1, size // 10))
        d.line((s / 2, 0, s / 2, s), fill=c(110, 80, 40), width=max(1, size // 10))
    elif kind == "bolt":
        d.rectangle((0, 0, s, s), fill=c(40, 40, 40))
        d.polygon([(s * .6, 0), (s * .15, s * .55), (s * .5, s * .55), (s * .35, s), (s * .85, s * .4), (s * .5, s * .4)], fill=c(255, 220, 0))
    elif kind == "town":
        d.rectangle((0, 0, s, s), fill=c(200, 200, 210))
        d.polygon([(0, s * .5), (s / 2, 0), (s, s * .5)], fill=c(160, 60, 50))
        d.rectangle((s * .15, s * .5, s * .85, s), fill=c(230, 220, 190))
    elif kind == "stop":
        d.rectangle((0, 0, s, s), fill=c(250, 250, 250))
        d.rectangle((0, 0, s, s), outline=c(30, 90, 170), width=max(1, size // 8))
        d.text((s / 2, s / 2), "H", font=font(max(8, size * 3 // 4)), fill=c(30, 90, 170), anchor="mm")
    elif kind == "color":
        d.rectangle((0, 0, s, s), fill=c(30, 30, 30))
        d.ellipse((2, 2, s - 2, s - 2), fill=special_safe((128, 128, 128, 255)), outline=c(240, 240, 240))
    elif kind == "flag":
        d.rectangle((0, 0, s, s * .5), fill=c(240, 240, 240))
        d.rectangle((0, s * .5, s, s), fill=c(200, 40, 40))
    elif kind == "news":
        d.rectangle((0, 0, s, s), fill=c(240, 235, 200))
        d.rectangle((0, 0, s, s), outline=c(80, 80, 80), width=max(2, size // 16))
        for k in range(4):
            y = s * (.25 + .17 * k)
            d.line((s * .15, y, s * .85, y), fill=c(80, 80, 80), width=max(1, size // 20))
    elif kind == "world":
        d.rectangle((0, 0, s, s), fill=c(20, 40, 90))
        d.ellipse((2, 2, s - 2, s - 2), fill=c(60, 130, 200))
        d.ellipse((s * .25, s * .25, s * .6, s * .65), fill=c(80, 160, 80))
    elif kind == "newyear":
        d.rectangle((0, 0, s, s), fill=c(30, 30, 80))
        d.text((s / 2, s / 2), "+1", font=font(max(8, size // 2)), fill=c(255, 220, 0), anchor="mm")
    elif kind == "logo":
        d.rectangle((0, 0, s, s), fill=c(*GUI_BLUE))
        d.text((s / 2, s / 2), "pak256", font=font(max(8, size // 6)), fill=c(255, 255, 255), anchor="mm")
    return im


SEASON_COLORS = [(90, 190, 70), (200, 120, 40), (235, 240, 250), (160, 220, 110)]   # 夏・秋・冬・春（本体の season の 0〜3。夏が 0）


def build_symbols(outdir):
    def single(fname, name, im, size, note=""):
        s = Sheet(fname, 1, size)
        s.put(0, im)
        s.save(outdir)
        write_dat(outdir, fname + ".dat", "symbol", name, image_lines(s, {0: True}, True), size, note)

    single("sym_passengers", "Passagiere", glyph("person", 16), 16)
    single("sym_mail", "Post", glyph("mail", 16), 16)
    single("sym_goods", "Waren", glyph("goods", 16), 16)
    single("sym_electricity", "Electricity", glyph("bolt", 16), 16)
    single("sym_intown", "InTown", glyph("town", 16), 16)
    single("sym_coloroptions", "ColorOptions", glyph("color", 16), 16)
    single("sym_flags", "Flags", glyph("flag", 32), 32)
    single("sym_message", "Message", glyph("news", 64), 64)
    single("sym_newworld", "NewWorld", glyph("world", 64), 64)
    single("sym_newyear", "NewYear", glyph("newyear", 64), 64)
    single("sym_logo", "Logo", glyph("logo", 128), 128)

    # 駅・車庫の窓が NULL を確かめずに使う記号（本体は無くても起動するが、窓を開くと落ちる）。仮の同じ絵
    for name in ("TrainStop", "CarStop", "ShipStop", "BusStop", "AirStop", "MonorailStop", "MaglevStop",
                 "NarrowgaugeStop", "TramStop"):
        single("sym_" + name.lower(), name, glyph("stop", 16), 16)

    # Seasons: 状態の行に出る季節の印（番号 = 季節。0 夏・1 秋・2 冬・3 春）
    s = Sheet("sym_seasons", 4, 16, cols=4)
    for i, col in enumerate(SEASON_COLORS):
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        ImageDraw.Draw(im).rectangle((0, 0, 15, 15), fill=special_safe((*col, 255)))
        s.put(i, im)
    s.save(outdir)
    write_dat(outdir, "sym_seasons.dat", "symbol", "Seasons", image_lines(s, {i: True for i in range(4)}, True), 16)

    # MessageOptions: 通知の窓の 3 つの印（番号 0〜2）
    s = Sheet("sym_messageoptions", 3, 32, cols=3)
    for i, col in enumerate([(60, 150, 60), (200, 60, 60), (60, 90, 190)]):
        im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 31, 31), fill=special_safe((*col, 255)))
        d.text((16, 16), str(i), font=font(20), fill=special_safe((255, 255, 255, 255)), anchor="mm")
        s.put(i, im)
    s.save(outdir)
    write_dat(outdir, "sym_messageoptions.dat", "symbol", "MessageOptions", image_lines(s, {i: True for i in range(3)}, True), 32)


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(outdir, exist_ok=True)
    used = used_icons()
    build_menu(outdir, used)
    build_cursors(outdir, 16)
    build_construction(outdir)
    build_ground_like(outdir, "sidewalk", "Sidewalk", (150, 150, 150), (110, 110, 110),
                      "歩道つきの道の下の地面。番号は本体の imageid（単段 0〜14、複段 15〜26。12〜14 は単段と重なる）。雪の絵は無い")
    build_ground_like(outdir, "tunnel_texture", "TunnelTexture", (70, 60, 55), (45, 38, 35),
                      "トンネルの中の地面。並びは Sidewalk と同じ")
    build_ribi_arrow(outdir)
    build_power(outdir)
    build_symbols(outdir)
    print("書き出した:", outdir)


if __name__ == "__main__":
    main()
