"""アドオン作者向けの仕様の寸法の図を描く（MIT）。

使い方（リポジトリの直下で。Pillow が要る）:
    python -X utf8 site/figures/draw_spec_figures.py
出力は site/public/spec/ の PNG で、コミットする（CI では描かない）。
文字の書体は環境の日本語の書体を使うので、環境が違うと文字の画素は変わる。
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "public", "spec")
FONTS = (
    "C:/Windows/Fonts/meiryo.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
)

TILE_M = 26.4
HEIGHT_PX_PER_M = 5.94

BG = (250, 250, 248)
INK = (30, 30, 30)
CELL = (110, 110, 120)
GROUND = (170, 205, 150)
MARK = (200, 40, 40)
DIM = (30, 80, 170)


def font(size):
    for path in FONTS:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    raise SystemExit("日本語の書体が見つからない。FONTS に足す。")


def text(d, xy, s, size=15, fill=INK, anchor="la"):
    d.text(xy, s, font=font(size), fill=fill, anchor=anchor)


def dim_line(d, a, b, fill=DIM):
    """両端に短い縦線の付いた寸法線。"""
    d.line([a, b], fill=fill, width=2)
    n = math.hypot(b[0] - a[0], b[1] - a[1])
    ox, oy = -(b[1] - a[1]) / n * 6, (b[0] - a[0]) / n * 6
    for x, y in (a, b):
        d.line([(x - ox, y - oy), (x + ox, y + oy)], fill=fill, width=2)


def cell(d, ox, oy, size, k):
    """左上が (ox, oy) の size px のセルを k 倍で描き、基準点を返す。"""
    shift = (size - 256) // 2

    def p(x, y):
        return (ox + (x + shift) * k, oy + (y + shift) * k)

    d.rectangle([ox, oy, ox + size * k, oy + size * k], fill=(255, 255, 255), outline=CELL, width=2)
    if size == 512:
        for i in range(0, 16, 2):
            # 中央の 256 の枠は破線
            a, b = shift + 256 * i / 16, shift + 256 * (i + 1) / 16
            for y in (shift, shift + 256):
                d.line([(ox + a * k, oy + y * k), (ox + b * k, oy + y * k)], fill=CELL)
            for x in (shift, shift + 256):
                d.line([(ox + x * k, oy + a * k), (ox + x * k, oy + b * k)], fill=CELL)
    top, right, bottom, left = p(128, 128), p(256, 192), p(128, 256), p(0, 192)
    d.polygon([top, right, bottom, left], fill=GROUND, outline=INK)
    base = p(128, 192)
    d.line([(base[0] - 10, base[1]), (base[0] + 10, base[1])], fill=MARK, width=2)
    d.line([(base[0], base[1] - 10), (base[0], base[1] + 10)], fill=MARK, width=2)
    return base


def tile_and_cell():
    img = Image.new("RGB", (1300, 720), BG)
    d = ImageDraw.Draw(img)

    k = 1.5
    ox, oy = 130, 90
    text(d, (ox, 30), "256 のセル（1 タイル。自前の物の既定）", 20)
    base = cell(d, ox, oy, 256, k)
    text(d, (base[0] + 14, base[1] - 24), "基準点 (128, 192)", 15, MARK)
    for xy, label, anchor in (
        ((128, 128), "上 (128, 128)", "md"),
        ((0, 192), "左 (0, 192)", "rd"),
        ((256, 192), "右 (256, 192)", "ld"),
        ((128, 256), "下 (128, 256)", "ld"),
    ):
        text(d, (ox + xy[0] * k, oy + xy[1] * k - 6), label, 14, INK, anchor)
    y = oy + 256 * k + 20
    dim_line(d, (ox, y), (ox + 256 * k, y))
    text(d, (ox + 128 * k, y + 8), "タイルの幅 256px（= 26.4m の正方形の対角線）", 15, DIM, "ma")
    x = ox - 82
    dim_line(d, (x, oy + 128 * k), (x, oy + 256 * k))
    text(d, (x - 6, oy + 192 * k), "128px", 15, DIM, "rm")

    k = 1.0
    ox, oy = 710, 90
    text(d, (ox, 30), "512 のセル（大きな建物・長い車両）", 20)
    base = cell(d, ox, oy, 512, k)
    text(d, (base[0] + 14, base[1] - 24), "基準点 (256, 320)", 15, MARK)
    text(d, (ox + 132, oy + 134), "破線 = 中央の 256 のセル", 14, CELL)
    text(d, (ox + 256, oy + 400), "256 のセルの座標に +128（位置合わせ ,-128,-128）", 15, INK, "ma")
    y = oy + 512 + 20
    dim_line(d, (ox, y), (ox + 512, y))
    text(d, (ox + 256, y + 8), "512px", 15, DIM, "ma")
    img.save(os.path.join(OUT, "tile-and-cell.png"), optimize=True)


def scale():
    img = Image.new("RGB", (1000, 660), BG)
    d = ImageDraw.Draw(img)
    k = 2.5
    # タイルの画面の座標。(u, v) はタイルの 2 辺に沿った 0..1 の位置。
    cx, top = 400, 230

    def p(u, v, h=0.0):
        return (cx + (u - v) * 128 * k, top + (u + v) * 64 * k - h * HEIGHT_PX_PER_M * k)

    text(d, (30, 24), "1 タイル = 16 単位 = 26.4m 四方（1 単位 = 1.65m）", 20)
    text(d, (30, 56), "画面の px は 256px のタイルでの値（図は 2.5 倍）", 15)
    d.polygon([p(0, 0), p(1, 0), p(1, 1), p(0, 1)], fill=GROUND, outline=INK)

    # 例の建物: 9m × 7m、高さ 6m の箱
    u0, v0 = 0.28, 0.34
    u1, v1 = u0 + 9 / TILE_M, v0 + 7 / TILE_M
    h = 6.0
    d.polygon([p(u0, v1), p(u1, v1), p(u1, v1, h), p(u0, v1, h)], fill=(225, 215, 200), outline=INK)
    d.polygon([p(u1, v0), p(u1, v1), p(u1, v1, h), p(u1, v0, h)], fill=(185, 175, 162), outline=INK)
    d.polygon([p(u0, v0, h), p(u1, v0, h), p(u1, v1, h), p(u0, v1, h)], fill=(160, 90, 70), outline=INK)
    text(d, (p(u1, v1)[0] - 4, p(u1, v1)[1] + 46), "例: 9m × 7m、高さ 6m の箱", 15, INK, "ma")

    # 辺の長さ
    a, b = p(0, 1), p(1, 1)
    a, b = (a[0] - 10, a[1] + 18), (b[0] - 10, b[1] + 18)
    dim_line(d, a, b)
    _, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    text(d, (30, my + 50), "辺 26.4m", 16, DIM, "la")
    text(d, (30, my + 76), "辺に沿った 1m ≒ 横 4.85px・縦 2.42px", 15, DIM, "la")

    # 対角線
    y = p(1, 1)[1] + 60
    dim_line(d, (p(0, 1)[0], y), (p(1, 0)[0], y))
    text(d, (cx, y + 10), "対角線 256px ≒ 37.3m（この向きは 1m ≒ 6.86px）", 15, DIM, "ma")

    # 高さの目盛り
    x = 800
    ground = p(1, 0)[1]
    for m in range(0, 21, 5):
        yy = ground - m * HEIGHT_PX_PER_M * k
        d.line([(x - 6, yy), (x + 6, yy)], fill=DIM, width=2)
        text(d, (x + 12, yy), "%dm = %dpx" % (m, round(m * HEIGHT_PX_PER_M)), 15, DIM, "lm")
    d.line([(x, ground), (x, ground - 20 * HEIGHT_PX_PER_M * k)], fill=DIM, width=2)
    text(d, (x - 20, ground + 20), "高さ 1m ≒ 5.94px", 16, DIM, "la")
    img.save(os.path.join(OUT, "scale.png"), optimize=True)


def vehicle_position():
    """線路の車両（length=12）を、タイルの基準点から後ろへ伸ばした図。向きは e（右下へ進む）と ne（右へ進む）。"""
    img = Image.new("RGB", (1040, 500), BG)
    d = ImageDraw.Draw(img)
    length = 12 / 16  # タイルの単位
    half = 3.9 / TILE_M / 2  # 幅 3.9m（2.8m × 1.40）
    for ox, title, heading, label in (
        (20, "e（右下へ進む。軸の向き）", (1.0, 0.0), "length 12 = 19.8m"),
        (520, "ne（右へ進む。横の斜め）", (math.sqrt(0.5), -math.sqrt(0.5)), "length 12 = 画面で約 136px（図は 0.75 倍）"),
    ):
        k = 0.75  # 3×2 のタイルが半分の幅に収まる倍率
        cx, cy = ox + 300, 300  # 基準点（タイルの中心）

        def p(x, y):
            return (cx + (x - y) * 128 * k, cy + (x + y) * 64 * k)

        # 周りの 3×3 のタイル
        for tx in (-1, 0):
            for ty in (-1, 0, 1):
                corners = [p(tx - 0.5 + a, ty - 0.5 + b) for a, b in ((0, 0), (1, 0), (1, 1), (0, 1))]
                d.polygon(corners, fill=GROUND if (tx, ty) == (0, 0) else (214, 228, 200), outline=CELL)
        hx, hy = heading
        rx, ry = -hy, hx
        box = [(hx * a + rx * s, hy * a + ry * s) for a, s in ((0, half), (0, -half), (-length, -half), (-length, half))]
        d.polygon([p(*q) for q in box], fill=(214, 196, 150), outline=INK)
        d.line([p(*box[0]), p(*box[1])], fill=DIM, width=4)
        d.line([(cx - 10, cy), (cx + 10, cy)], fill=MARK, width=3)
        d.line([(cx, cy - 10), (cx, cy + 10)], fill=MARK, width=3)
        text(d, (ox + 10, 20), title, 18)
        text(d, (cx + 14, cy + 14), "基準点", 15, MARK)
        text(d, (ox + 10, 52), "青の辺 = 車体の前の端（基準点を通る）", 15, DIM)
        text(d, (ox + 10, 76), label, 15)
        a = p(0, 0)
        b = p(-hx * 0.9, -hy * 0.9)
        d.line([a, b], fill=MARK, width=1)
        text(d, (b[0], b[1] - 8), "後ろへ", 14, MARK, "md")
    img.save(os.path.join(OUT, "vehicle-position.png"), optimize=True)


def vehicle_directions():
    """pak256 の仮の気動車のシート（objects/vehicle/rail/railcar/railcar.png）の 8 方向に、キーと基準点を書き足す。"""
    sheet = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..",
                                    "objects", "vehicle", "rail", "railcar", "railcar.png")).convert("RGBA")
    keys = ("s", "w", "sw", "se", "n", "e", "ne", "nw")
    ways = ("左下", "左上", "左（真横）", "下（手前）", "右上", "右下", "右（真横）", "上（奥）")
    w, h = 320, 280  # 1 枠。512 のセルの基準点 (256, 320) を (160, 170) に置く
    img = Image.new("RGB", (w * 4, h * 2), BG)
    d = ImageDraw.Draw(img)
    for i, (key, way) in enumerate(zip(keys, ways)):
        ox, oy = (i % 4) * w, (i // 4) * h
        bx, by = ox + 160, oy + 170
        d.rectangle([ox, oy, ox + w - 1, oy + h - 1], outline=CELL)
        d.polygon([(bx, by - 64), (bx + 128, by), (bx, by + 64), (bx - 128, by)], fill=GROUND)
        car = sheet.crop((i * 512 + 256 - 160, 320 - 170, i * 512 + 256 + 160, 320 + 110))
        img.paste(car, (ox, oy), car)
        d.line([(bx - 10, by), (bx + 10, by)], fill=MARK, width=2)
        d.line([(bx, by - 10), (bx, by + 10)], fill=MARK, width=2)
        text(d, (ox + 10, oy + 8), "%s: 画面の%sへ進む" % (key, way), 17)
    img.save(os.path.join(OUT, "vehicle-directions.png"), optimize=True)


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
# 道路の車両の右側の車線の点（基準点からのずれ。256px のタイル）。site/spec/vehicle-road.md の表と同じ
LANE = {"s": (-24, -12), "w": (24, -12), "sw": (0, -12), "se": (-24, 0),
        "n": (24, 12), "e": (-24, 12), "ne": (0, 12), "nw": (24, 0)}


def road_tile(d, cx, cy, k):
    """基準点が (cx, cy) の平らなタイルと、東西（画面の左上から右下）の舗装を描き、地面の座標の変換を返す。"""

    def p(x, y):
        return (cx + (x - y) * 128 * k, cy + (x + y) * 64 * k)

    d.polygon([p(-0.5, -0.5), p(0.5, -0.5), p(0.5, 0.5), p(-0.5, 0.5)], fill=GROUND, outline=CELL)
    d.polygon([p(-0.5, -0.344), p(0.5, -0.344), p(0.5, 0.344), p(-0.5, 0.344)], fill=(150, 150, 154))
    for y in (-0.344, 0.344):
        d.line([p(-0.5, y), p(0.5, y)], fill=(245, 245, 245), width=2)
    return p


def cross(d, xy, fill=MARK, r=9):
    x, y = xy
    d.line([(x - r, y), (x + r, y)], fill=fill, width=3)
    d.line([(x, y - r), (x, y + r)], fill=fill, width=3)


def road_lane():
    """東へ進む車両（e）の、右側の車線の点と、左側通行で本体がずらした点。"""
    img = Image.new("RGB", (640, 900), BG)
    d = ImageDraw.Draw(img)
    k = 1.9
    length, half = 9 / 16, 3.1 / TILE_M / 2  # バス
    for oy, title, shift in ((90, "右側通行: 絵のとおり", (0, 0)), (450, "左側通行: 本体が (48, -24) ずらす", (48, -24))):
        cx, cy = 330, oy + 190
        p = road_tile(d, cx, cy, k)
        # e の右側の車線の点 (-24, 12) は、地面では (0, 3/16)
        front, side = 0.0, 3 / 16
        box = [p(front, side - half), p(front, side + half), p(front - length, side + half), p(front - length, side - half)]
        box = [(x + shift[0] * k, y + shift[1] * k) for x, y in box]
        d.polygon(box, fill=(214, 196, 150), outline=INK)
        d.line([box[0], box[1]], fill=DIM, width=4)
        cross(d, (cx, cy))
        point = (cx + (LANE["e"][0] + shift[0]) * k, cy + (LANE["e"][1] + shift[1]) * k)
        cross(d, point, DIM)
        d.line([(cx, cy), point], fill=MARK, width=1)
        text(d, (20, oy), title, 22)
        text(d, (cx + 14, cy + 14), "基準点", 19, MARK)
    text(d, (20, 16), "例: 東へ進む車両（キー e）", 22)
    text(d, (20, 50), "青の十字 = 車体の前の端の中央、青の辺 = 前の端", 18, DIM)
    text(d, (20, 820), "絵の点は基準点から (-24, 12)。左側通行では (48, -24) が", 19)
    text(d, (20, 846), "足され、基準点の反対側 (24, -12) に出る", 19)
    text(d, (20, 874), "灰色は舗装の目安（実際の道路は AMI の版で変わる）", 16, CELL)
    img.save(os.path.join(OUT, "road-lane.png"), optimize=True)


def pedestrian_foot():
    """offset=18 の歩行者の足元の点（東へ進む e と西へ進む w）。"""
    img = Image.new("RGB", (900, 560), BG)
    d = ImageDraw.Draw(img)
    k = 2.0
    cx, cy = 450, 300
    p = road_tile(d, cx, cy, k)
    o = 18 / 256
    y = 0.5 - o
    for sign, key, offset in ((1, "e", (-55, 27.5)), (-1, "w", (55, -27.5))):
        foot = (cx + offset[0] * k, cy + offset[1] * k)
        d.line([p(-0.5, sign * y), p(0.5, sign * y)], fill=DIM, width=1)
        cross(d, foot, DIM)
        d.line([(cx, cy), foot], fill=MARK, width=1)
    cross(d, (cx, cy))
    a, b = p(0.25, 0.5), p(0.25, 0.5 - o)
    d.line([a, b], fill=INK, width=3)
    text(d, (a[0] + 10, a[1]), "道路の端から offset/256 タイル", 15)
    text(d, (cx + 14, cy - 24), "基準点", 15, MARK)
    text(d, (20, 20), "offset=18 の足元の点（青の十字）。進む向きの右側に描く", 20)
    text(d, (20, 56), "東へ進む（e）: 基準点から (-55, 27.5)　西へ進む（w）: (55, -27.5)", 16, DIM)
    text(d, (20, 520), "灰色は舗装の目安。足元は舗装の外の路肩に来る", 14, CELL)
    img.save(os.path.join(OUT, "pedestrian-foot.png"), optimize=True)


def road_directions():
    """pak256 の仮のバスと石炭のトラックのシートの 8 方向に、キーと基準点を書き足す。"""
    keys = ("s", "w", "sw", "se", "n", "e", "ne", "nw")
    w, h = 256, 180  # 1 枠。256 のセルの基準点 (128, 192) を (128, 112) に置く
    img = Image.new("RGB", (w * 4, h * 4), BG)
    d = ImageDraw.Draw(img)
    for row, name in enumerate(("bus", "coal_truck")):
        sheet = Image.open(os.path.join(ROOT, "objects", "vehicle", "road", name, name + ".png")).convert("RGBA")
        for i, key in enumerate(keys):
            ox, oy = (i % 4) * w, (row * 2 + i // 4) * h
            bx, by = ox + 128, oy + 112
            d.rectangle([ox, oy, ox + w - 1, oy + h - 1], outline=CELL)
            d.polygon([(bx, by - 64), (bx + 127, by), (bx, by + 64), (bx - 128, by)], fill=GROUND)
            car = sheet.crop((i * 256, 192 - 112, i * 256 + 256, 192 - 112 + h))
            img.paste(car, (ox, oy), car)
            cross(d, (bx, by), MARK, 7)
            text(d, (ox + 10, oy + 8), key, 17)
    img.save(os.path.join(OUT, "road-directions.png"), optimize=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    road_lane()
    pedestrian_foot()
    road_directions()
    tile_and_cell()
    scale()
    vehicle_position()
    vehicle_directions()
    print("OK:", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
