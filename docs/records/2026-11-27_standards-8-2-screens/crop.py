"""MIT License。#176: 撮った画面を切り抜いて、札を付けて 1 枚に並べる。

使い方: python -X utf8 crop.py <出す PNG> <列の数> <札>=<画像>:<x0>,<y0>,<x1>,<y1>[:<倍率>] ...
"""
import sys

from PIL import Image, ImageDraw, ImageFont

out, cols = sys.argv[1], int(sys.argv[2])
try:
    font = ImageFont.truetype("meiryo.ttc", 18)
except OSError:
    font = ImageFont.load_default()
tiles = []
for spec in sys.argv[3:]:
    label, rest = spec.split("=", 1)
    parts = rest.rsplit(":", 2)
    if "," in parts[-1]:
        path, box, k = rest.rsplit(":", 1)[0], parts[-1], 1.0
    else:
        path, box, k = parts[0], parts[1], float(parts[2])
    im = Image.open(path).convert("RGB").crop(tuple(int(v) for v in box.split(",")))
    if k != 1.0:
        im = im.resize((int(im.width * k), int(im.height * k)), Image.NEAREST)
    tile = Image.new("RGB", (im.width, im.height + 28), (255, 255, 255))
    tile.paste(im, (0, 28))
    ImageDraw.Draw(tile).text((6, 2), label, fill=(0, 0, 0), font=font)
    tiles.append(tile)
w, h = max(t.width for t in tiles), max(t.height for t in tiles)
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (w + 6), rows * (h + 6)), (255, 255, 255))
for i, t in enumerate(tiles):
    sheet.paste(t, ((i % cols) * (w + 6), (i // cols) * (h + 6)))
sheet.save(out, optimize=True)
print(out, sheet.size)
