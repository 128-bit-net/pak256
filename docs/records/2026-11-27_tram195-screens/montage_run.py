"""#195: 直した後のツールバー（toolbar.py）と、路面電車が停留所に来た画面（tools/vehicle_check/tram_run.py）を 1 枚に並べる。MIT License。

    python -X utf8 docs/records/2026-11-27_tram195-screens/montage_run.py <toolbar.py の PNG> <tram_run.py の出力のフォルダ> <出力の PNG>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

toolbar, run, out = sys.argv[1:4]
FONT = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 22)
# (見出し, 画像, 切り抜き（1600x900 の画面の px）)。どれも 2 倍にする
PARTS = (
    ("路面電車のツールバー（右下の端が停留所の道具の絵）・2 倍", toolbar, (432, 56, 872, 180)),
    ("専用の軌道の停留所に来た路面電車（架線あり）・温暖・2 倍", os.path.join(run, "own_stop_0.png"), (620, 440, 1060, 700)),
    ("道路の上の停留所に来た路面電車（架線あり）・温暖・2 倍", os.path.join(run, "road_stop_0.png"), (860, 480, 1300, 740)),
)
crops = []
for title, path, box in PARTS:
    im = Image.open(path).convert("RGB").crop(box)
    crops.append((title, im.resize((im.width * 2, im.height * 2), Image.NEAREST)))
BAR = 36
sheet = Image.new("RGB", (max(c.width for _, c in crops), sum(c.height + BAR for _, c in crops)), (0, 0, 0))
d = ImageDraw.Draw(sheet)
y = 0
for title, c in crops:
    d.text((6, y + 4), title, font=FONT, fill=(255, 220, 90))
    sheet.paste(c, (0, y + BAR))
    y += c.height + BAR
sheet.save(out, optimize=True)
