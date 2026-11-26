"""#141 の記録の画像を組む。MIT License。
使い方（リポジトリの直下から）:
  python -X utf8 docs/records/2026-11-26_snow-road-seam-screens/figures.py <scene.py の出力> <今の pak の撮影> <置き換えた pak の撮影>
後ろの 2 つは、../2026-11-26_sidewalk-snow-screens/scene.py の出力（snow_hill.png を使う）。"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
scene, now, patched = sys.argv[1:4]
font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 18)


def panels(items, name, width, height):
    """items: [(見出し, 画像)]。横に並べる。"""
    sheet = Image.new("RGB", (len(items) * (width + 8) - 8, height + 56), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, (title, im) in enumerate(items):
        ox = i * (width + 8)
        for k, line in enumerate(title.split("\n")):
            d.text((ox, 2 + 26 * k), line, fill=(0, 0, 0), font=font)
        sheet.paste(im, (ox, 56))
    sheet.save(os.path.join(HERE, name))


def load(folder, name):
    return Image.open(os.path.join(folder, name + ".png")).convert("RGB")


kinds = (("city", "街の道路の道具（歩道つき）= base_single", 102),
         ("base", "手で敷いた local_base_single（歩道なし）", 132),
         ("hand", "手で敷いた ami_road_local（歩道なし）", 162))
panels([(f"{t}\n雪の気候 中心 (318, {y})・7 月・等倍", load(scene, k).crop((250, 330, 710, 730)))
        for k, t, y in kinds], "variants.png", 460, 400)
panels([(f"{t}\n左の画像の左下の縁を 8 倍", load(scene, k).crop((290, 575, 340, 615)).resize((400, 320), Image.NEAREST))
        for k, t, _ in kinds], "variants_zoom.png", 460, 320)
panels([("街が建てた道（local_base_single）\n雪の気候 中心 (320, 300)・7 月・等倍", load(scene, "town").crop((200, 300, 1200, 878)))],
       "town.png", 1000, 578)
panels([("今の pak\n雪の気候 台地 中心 (318, 130)・7 月・等倍", load(now, "snow_hill").crop((300, 148, 1100, 808))),
        ("確かめ用: pak の写しで下端の画素を置き換え（直しではない）\n同じ位置",
         load(patched, "snow_hill").crop((300, 148, 1100, 808)))], "patched.png", 800, 660)
