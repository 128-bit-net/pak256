"""MIT License。#164 の画面を記録用に整える: 全体の切り抜きに番号を振り、等倍の切り抜きを同じ大きさで並べる。使い方: montage.py <scene.py の出す先> <記録の画像の置き場>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
F = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 22)


def label(im, xy, text):
    d = ImageDraw.Draw(im)
    x, y = xy
    box = d.textbbox((x, y), text, font=F)
    d.rectangle((box[0] - 6, box[1] - 4, box[2] + 6, box[3] + 4), fill=(0, 0, 0))
    d.text((x, y), text, font=F, fill=(255, 255, 255))


def overview(name, crop, title, tags):
    im = Image.open(os.path.join(src, name + ".png")).convert("RGB").crop(crop)
    for (x, y), t in tags:
        label(im, (x - crop[0], y - crop[1]), t)
    label(im, (10, 8), title)
    im.save(os.path.join(out, name.split("_")[0] + "_all.png"), optimize=True)


overview("ships_z6", (0, 100, 1700, 1035), "船の並び（flat_512_left_v64 の温帯、(49,60) 付近、0.5 倍に縮小）",
         [((300, 395), "① pak256 旅客船"), ((540, 520), "② pak256 貨物船"), ((860, 700), "③ SKS フェリー 等倍"),
          ((1230, 975), "④ SKS フェリー 2 倍")])
overview("planes_z6", (0, 100, 1700, 1035), "飛行機の並び（同じ地図、(45,135) 付近）",
         [((430, 335), "① pak256 旅客機"), ((640, 560), "② ATR42 等倍"), ((850, 645), "③ ATR72 等倍"),
          ((1050, 745), "④ ATR42 2 倍"), ((1330, 840), "⑤ ATR72 2 倍")])


def tiles(files, rect, cols, outname):
    w, h = rect[2] - rect[0], rect[3] - rect[1]
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), (40, 40, 40))
    for i, (f, text) in enumerate(files):
        im = Image.open(os.path.join(src, f + ".png")).convert("RGB").crop(rect)
        label(im, (10, 8), text)
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    d = ImageDraw.Draw(sheet)
    for c in range(1, cols):
        d.line([(c * w, 0), (c * w, h * rows)], fill=(255, 255, 255), width=2)
    for r in range(1, rows):
        d.line([(0, r * h), (w * cols, r * h)], fill=(255, 255, 255), width=2)
    sheet.save(os.path.join(out, outname), optimize=True)


tiles([("ship_pak256_ferry", "① pak256 旅客船（30m）"), ("ship_pak256_cargo_ship", "② pak256 貨物船（36m）"),
       ("ship_sks_ferry_x1", "③ SKS フェリー 等倍（224.5m）"), ("ship_sks_ferry_x2", "④ SKS フェリー 2 倍（224.5m）")],
      (520, 560, 1240, 1000), 2, "ships_1x.png")
tiles([("plane_pak256_airliner", "① pak256 旅客機（18.9m）"), ("plane_sks_atr42_x1", "② ATR42 等倍（22.7m）"),
       ("plane_sks_atr72_x1", "③ ATR72 等倍（27.2m）"), ("plane_sks_atr42_x2", "④ ATR42 2 倍"),
       ("plane_sks_atr72_x2", "⑤ ATR72 2 倍")],
      (640, 660, 1060, 880), 3, "planes_1x.png")
