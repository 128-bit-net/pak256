"""バス停の奥の暗い帯を、直す前と直した後で 8 倍にして並べる（#139）。MIT License。Pillow が要る。

撮り方は 2026-11-26_stop-overlap-screens/run.py（直す前・直した後の pak でそれぞれ流す）。画面の中心の停留所のタイルを切り抜く。
使い方: python -X utf8 zoom.py <直す前のフォルダ> <直した後のフォルダ> <出力の PNG>
"""
import sys

from PIL import Image, ImageDraw, ImageFont

SCALE = 8
ROWS = [  # (画面, 切り抜き (x0, y0, x1, y1), 見出し)
    ("ew_empty", (740, 435, 860, 505), "東西の道路・バス停 3 タイル・車両なし (73〜75,60) の画面の x=740 y=435"),
    ("ns_near", (810, 505, 930, 575), "南北の道路・バス停 (90,46) の画面の x=810 y=505"),
    ("ns_empty", (630, 580, 750, 650), "南北の道路・荷役所 3 タイルの端（変えていない）の画面の x=630 y=580"),
]


def main():
    before, after, out = sys.argv[1:4]
    font = ImageFont.truetype("meiryo.ttc", 20)
    w = (ROWS[0][1][2] - ROWS[0][1][0]) * SCALE
    h = (ROWS[0][1][3] - ROWS[0][1][1]) * SCALE
    sheet = Image.new("RGB", (w * 2 + 8, 36 + (h + 30) * len(ROWS)), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    d.text((8, 6), "温帯・拡大 3 の 8 倍　左 = 直す前（今の main）、右 = 直した後", font=font, fill=(255, 255, 255))
    for i, (shot, box, label) in enumerate(ROWS):
        y = 36 + (h + 30) * i
        d.text((8, y), label, font=font, fill=(255, 255, 255))
        for j, folder in enumerate((before, after)):
            part = Image.open(f"{folder}/{shot}.png").convert("RGB").crop(box)
            sheet.paste(part.resize((w, h), Image.NEAREST), (j * (w + 8), y + 30))
    sheet.save(out, optimize=True)


if __name__ == "__main__":
    main()
