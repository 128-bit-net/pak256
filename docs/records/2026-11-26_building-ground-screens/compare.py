"""scene.py の直す前と後の画像を、左右に並べる。MIT License（Pillow が要る）。
使い方: python -X utf8 docs/records/2026-11-26_building-ground-screens/compare.py <直す前のフォルダ> <直した後のフォルダ> <出力フォルダ>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

before, after, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
FONT = ImageFont.truetype("meiryo.ttc", 22)
BOX = (0, 56, 1600, 856)  # ツールバーと下の帯を除く


def panel(folder, name, text):
    im = Image.open(os.path.join(folder, name + ".png")).convert("RGB").crop(BOX).resize((800, 400), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, d.textlength(text, font=FONT) + 16, 34], fill=(0, 0, 0))
    d.text((8, 2), text, font=FONT, fill=(255, 255, 255))
    return im


def rows(items, name):
    out_im = Image.new("RGB", (1606, len(items) * 406 - 6), (255, 255, 255))
    for i, (shot, label) in enumerate(items):
        out_im.paste(panel(before, shot, "直す前: " + label), (0, i * 406))
        out_im.paste(panel(after, shot, "直した後: " + label), (806, i * 406))
    out_im.save(os.path.join(out, name + ".png"), optimize=True)


rows([("summer_temperate_town", "温帯・夏 (70,142)"), ("winter_temperate_town", "温帯・冬 (70,142)")], "town_temperate")
rows([("summer_snow_town", "雪の気候・夏 (310,142)"), ("winter_snow_town", "雪の気候・冬 (310,142)")], "town_snow")
rows([("summer_temperate_townhall", "役場・温帯・夏 (61,140)"), ("winter_snow_townhall", "役場・雪の気候・冬 (301,140)")], "townhall")
rows([("summer_temperate_infra", "停留所・車庫・産業 (72,159)"), ("summer_temperate_rail", "駅 (71,163)")], "stops")
