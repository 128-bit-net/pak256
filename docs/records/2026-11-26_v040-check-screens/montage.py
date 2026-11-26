"""shots.py が撮った画像から、Release の説明に付ける画像を並べる。MIT License（Pillow が要る）。
使い方: python -X utf8 docs/records/2026-11-26_v040-check-screens/montage.py <shots.py の出力フォルダ> <出力フォルダ>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
FONT = ImageFont.truetype("meiryo.ttc", 18)


def load(name, box):
    return Image.open(os.path.join(src, name + ".png")).convert("RGB").crop(box)


def label(im, text):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, d.textlength(text, font=FONT) + 16, 28], fill=(0, 0, 0))
    d.text((8, 2), text, font=FONT, fill=(255, 255, 255))
    return im


def grid(items, cols, name):
    w, h = items[0].size
    rows = (len(items) + cols - 1) // cols
    out = Image.new("RGB", (cols * w + (cols - 1) * 6, rows * h + (rows - 1) * 6), (255, 255, 255))
    for i, im in enumerate(items):
        out.paste(im, ((i % cols) * (w + 6), (i // cols) * (h + 6)))
    out.save(os.path.join(dst, name + ".png"), optimize=True)


# 中央 640x360（1600x900 の画面）
MID = (480, 270, 1120, 630)
grid([label(load(f"forest_{c}_summer", MID), ja) for c, ja in [
    ("tropic", "熱帯"), ("desert", "砂漠"), ("mediterran", "地中海"),
    ("temperate", "温帯"), ("tundra", "ツンドラ"), ("arctic", "雪")]], 3, "climates")
grid([label(load(f"forest_temperate_{s}", MID), ja) for s, ja in [
    ("summer", "夏"), ("autumn", "秋"), ("winter", "冬")]], 3, "seasons")
TOWN = (160, 170, 1420, 870)
grid([label(load("town_summer", TOWN), "夏"), label(load("town_winter", TOWN), "冬")], 2, "town")
load("transport", (0, 60, 1440, 780)).save(os.path.join(dst, "transport.png"), optimize=True)
print(sorted(os.listdir(dst)))
