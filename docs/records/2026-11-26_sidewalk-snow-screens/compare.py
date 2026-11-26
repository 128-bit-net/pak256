"""直す前と後の画像を並べ、画素の違いを数える（#136）。MIT License。
使い方: python -X utf8 docs/records/2026-11-26_sidewalk-snow-screens/compare.py <前のフォルダ> <後のフォルダ> <出力フォルダ>"""
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont

before, after, out = sys.argv[1:4]
# 上のツールバーと下の状態の行（日付・時刻が違う）を除いた範囲
BOX = (0, 48, 1600, 878)
NAMES = {"flat": "平ら: 角・分かれ目・十字", "hill": "台地の上と 4 向きの坂", "slope_w": "西の坂", "slope_e": "東の坂",
         "slope_n": "北の坂", "slope_s": "南の坂"}
AREAS = {"temperate": ("温帯", 62), "snow": ("雪の気候", 318)}  # 名前と、画面の中心の x
FONT = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 30)


def load(folder, name):
    return Image.open(os.path.join(folder, name + ".png")).convert("RGB").crop(BOX)


def pair(area, key):
    a, b = load(before, f"{area}_{key}"), load(after, f"{area}_{key}")
    w, h = a.size
    im = Image.new("RGB", (w * 2 + 12, h + 48), (255, 255, 255))
    d = ImageDraw.Draw(im)
    jp, x = AREAS[area]
    at = f"中心 ({x}, 102)" if key == "flat" else f"中心 ({x}, 130)"
    for i, (pic, head) in enumerate(((a, "直す前"), (b, "直した後"))):
        im.paste(pic, (i * (w + 12), 48))
        d.text((i * (w + 12) + 8, 4), f"{head}: {jp} {NAMES[key]}  {at}・夏（7 月）・等倍", font=FONT, fill=(0, 0, 0))
    return im


os.makedirs(out, exist_ok=True)
for area in AREAS:
    for key in NAMES:
        diff = ImageChops.difference(load(before, f"{area}_{key}"), load(after, f"{area}_{key}"))
        r, g, b = diff.split()
        largest = ImageChops.lighter(ImageChops.lighter(r, g), b)  # 画素ごとの色の違いの最大
        n = largest.width * largest.height - largest.histogram()[0]
        print(f"{area}_{key}: 違う画素 {n}")
    for key in ("flat", "hill"):
        pair(area, key).save(os.path.join(out, f"{area}_{key}.png"), optimize=True)
