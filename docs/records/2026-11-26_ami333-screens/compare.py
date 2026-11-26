"""直す前と後の画面の同じ所を、最近傍で拡大して左右に並べる（#134。#111 の同じ道具の写し）。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_ami333-screens/compare.py <前のフォルダ> <後のフォルダ> <出力の PNG> \
        <画面の名前>:<x>,<y>,<幅>,<高さ>[,<倍率>] ...
左が前、右が後。1 つの指定が 1 段になる。
"""
import os
import sys

from PIL import Image, ImageDraw

before, after, out, specs = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
rows = []
for spec in specs:
    name, _, box = spec.partition(":")
    values = [int(v) for v in box.split(",")]
    x, y, w, h = values[:4]
    scale = values[4] if len(values) > 4 else 6
    pair = []
    for label, folder in (("before", before), ("after", after)):
        im = Image.open(os.path.join(folder, name + ".png")).convert("RGB")
        part = im.crop((x, y, x + w, y + h)).resize((w * scale, h * scale), Image.NEAREST)
        canvas = Image.new("RGB", (part.width, part.height + 16), (255, 255, 255))
        canvas.paste(part, (0, 16))
        ImageDraw.Draw(canvas).text((4, 2), f"{label}  {name}  x={x} y={y}  x{scale}", fill=(0, 0, 0))
        pair.append(canvas)
    row = Image.new("RGB", (pair[0].width * 2 + 12, pair[0].height), (255, 0, 0))
    row.paste(pair[0], (0, 0))
    row.paste(pair[1], (pair[0].width + 12, 0))
    rows.append(row)
sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height + 8 for r in rows)), (255, 255, 255))
top = 0
for r in rows:
    sheet.paste(r, (0, top))
    top += r.height + 8
sheet.save(out)
