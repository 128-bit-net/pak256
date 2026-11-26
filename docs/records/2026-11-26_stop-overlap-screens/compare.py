"""run.py で撮った直す前・直した後の画面を、同じ位置で切り抜いて 2 倍にして並べる（#115）。MIT License。Pillow が要る。

使い方: python -X utf8 compare.py <直す前のフォルダ> <直した後のフォルダ> <出力フォルダ>
撮った画面の中心（800, 462 付近）が、gui.jump した停留所のタイル。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

BOX = (680, 470, 1080, 690)  # 停留所のタイルと、停まった車両が入る範囲
SCALE = 2
before, after, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
font = ImageFont.truetype("meiryo.ttc", 20)

SHEETS = {
    "ew_road_z3.png": ("東西の道路（拡大 3 の 2 倍）", [("ew_bus", "バス停とバス (60,60)"), ("ew_mail", "荷役所と郵便のトラック (65,60)"), ("ew_coal", "荷役所と石炭のトラック (70,60)"), ("ew_empty", "バス停 3 タイル・車両なし (73〜75,60)"), ("ew_near", "手前の車線のバス (79,60)")]),
    "ns_road_z3.png": ("南北の道路（拡大 3 の 2 倍）", [("ns_bus", "バス停とバス (90,66)"), ("ns_mail", "荷役所と郵便のトラック (90,61)"), ("ns_coal", "荷役所と石炭のトラック (90,56)"), ("ns_empty", "荷役所 3 タイル・車両なし (90,50〜52)"), ("ns_near", "手前の車線のバス (90,46)")]),
}
for name, (title, rows) in SHEETS.items():
    w, h = (BOX[2] - BOX[0]) * SCALE, (BOX[3] - BOX[1]) * SCALE
    sheet = Image.new("RGB", (w * 2 + 8, 36 + (h + 30) * len(rows)), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    d.text((8, 6), f"{title}　左 = 直す前、右 = 直した後", font=font, fill=(255, 255, 255))
    for i, (shot, label) in enumerate(rows):
        y = 36 + (h + 30) * i
        d.text((8, y), label, font=font, fill=(255, 255, 255))
        for j, folder in enumerate((before, after)):
            part = Image.open(os.path.join(folder, shot + ".png")).convert("RGB").crop(BOX)
            sheet.paste(part.resize((w, h), Image.NEAREST), (j * (w + 8), y + 30))
    sheet.save(os.path.join(out, name), optimize=True)
    print(name, sheet.size)
