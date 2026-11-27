"""#207: 撮った画面から、仕様のページに載せる分を切り出して 256 色にする。MIT License。

リポジトリの直下で:
    python -X utf8 docs/records/2026-11-27_spec-ship-air-screens/crop.py <撮影の出力の親>
親の下に ship/・air/（街を置いて撮った回）・air2/（街を置かずに撮った回）・river/（shoot.py）がある形。出力は site/public/spec/。
撮るたびに車両の位置と川の形は変わるので、撮り直したときは画像の名前と範囲を選び直す。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

src = sys.argv[1]
out = "site/public/spec"


def load(name):
    return Image.open(os.path.join(src, name)).convert("RGB")


def save(im, name):
    im.quantize(256).save(os.path.join(out, name), optimize=True)


def pair(parts, name):
    """(画像, 範囲, 見出し) を左右に並べる。"""
    font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 18)
    crops = [(load(n).crop(box), label) for n, box, label in parts]
    w = sum(c.width for c, _ in crops) + 20 * (len(crops) - 1)
    img = Image.new("RGB", (w, crops[0][0].height + 36), (250, 250, 248))
    d = ImageDraw.Draw(img)
    x = 0
    for c, label in crops:
        img.paste(c, (x, 36))
        d.text((x + c.width / 2, 6), label, font=font, fill=(30, 30, 30), anchor="ma")
        x += c.width + 20
    save(img, name)


pair([("ship/ship0_03_49_81.png", (760, 300, 1320, 660), "桟橋と旅客船"),
      ("ship/quay_still.png", (560, 480, 1120, 840), "岸壁")], "ship-sea.png")
save(load("ship/ship2_32_77_104.png").crop((300, 250, 1020, 610)), "ship-canal.png")
save(load("air2/airport_zoom5.png").crop((180, 60, 1580, 840)), "air-airport.png")
pair([("air2/plane_21_65_105_0.png", (660, 360, 1140, 680), "駅に停まった旅客機"),
      ("air/plane_25_65_100_0.png", (320, 100, 800, 420), "離陸した直後（下の黒い形が影）")], "air-plane.png")
save(load("river/junction2_zoom3_138_197.png").crop((0, 60, 1260, 860)), "river-screen.png")
