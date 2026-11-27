"""measure.py が撮った画面を、値ごとに並べた 1 枚にする（pak256#182）。MIT License。

    python -X utf8 grid.py <PNG のフォルダ> <出力のフォルダ>（Windows の meiryo.ttc を使う）
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]  # SRC は measure.py が撮った same-town の PNG のフォルダ
os.makedirs(OUT, exist_ok=True)
font = ImageFont.truetype(r"C:\Windows\Fonts\meiryo.ttc", 20)
PANELS = [("L5_D120", "今の値: 5・寿命 120"), ("L8_D36", "案1: 8・寿命 36"), ("L12_D36", "案2: 12・寿命 36"), ("L16_D36", "案3: 16・寿命 36")]
TOWN = {"big": "大きい街（人口 4 万 6 千、中心 160,160）", "mid": "中の街（人口 6 千、中心 60,60）"}
WHEN = {24: "24 か月後（1932 年 4 月）", 72: "72 か月後（1936 年 4 月）"}
for town in ("big", "mid"):
    for m in (24, 72):
        sheet = Image.new("RGB", (1600, 2 * (399 + 30) + 30), (255, 255, 255))
        d = ImageDraw.Draw(sheet)
        d.text((8, 2), f"{TOWN[town]}　{WHEN[m]}　（拡大 3 の画面を半分に縮小。同じ街の保存データから）", font=font, fill=(0, 0, 0))
        for i, (tag, label) in enumerate(PANELS):
            im = Image.open(os.path.join(SRC, f"{tag}_m{m}_{town}.png")).convert("RGB")
            im = im.crop((0, 60, 1600, 858)).resize((800, 399), Image.LANCZOS)
            x, y = (i % 2) * 800, 30 + (i // 2) * 429
            d.text((x + 8, y + 2), label, font=font, fill=(0, 0, 0))
            sheet.paste(im, (x, y + 30))
            d.line([(800, 30), (800, sheet.height)], fill=(255, 255, 255), width=4)
        sheet.save(os.path.join(OUT, f"{town}_m{m}.png"), optimize=True)
        print(town, m, os.path.getsize(os.path.join(OUT, f"{town}_m{m}.png")))
