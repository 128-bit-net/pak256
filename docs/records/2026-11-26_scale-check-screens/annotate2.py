"""bigger2.py の撮影に見出しと札を書き込む（#104）。MIT License。

使い方: python -X utf8 annotate2.py <bigger2.py の出力フォルダ> <出す先>
札の位置は、この記録の撮影の画素に合わせた固定の値。Windows のメイリオを使う。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

SRC, DST = sys.argv[1], sys.argv[2]
FONT = "C:/Windows/Fonts/meiryo.ttc"
F = ImageFont.truetype(FONT, 18)
FB = ImageFont.truetype(FONT, 20)


def label(d, at, to, text):
    box = d.multiline_textbbox((to[0] + 6, to[1] + 4), text, font=F)
    d.line([at, ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)], fill=(255, 255, 0), width=2)
    d.rectangle([to[0], to[1], box[2] + 6, box[3] + 6], fill=(0, 0, 0))
    d.multiline_text((to[0] + 6, to[1] + 4), text, font=F, fill=(255, 255, 255))


def save(src, dst, title, labels):
    im = Image.open(os.path.join(SRC, src)).convert("RGB")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1599, 47], fill=(20, 20, 20))
    d.text((10, 10), title, font=FB, fill=(255, 255, 255))
    for at, to, text in labels:
        label(d, at, to, text)
    im.save(os.path.join(DST, dst), optimize=True)


save("road_z3.png", "G_road_2x.png", "G 手本の 2 倍の試し絵: バスと郵便のトラック（温帯・夏・拡大 3）。自動車は pak128 の 2 倍", [
    ((440, 440), (180, 150), "バス 今\nlength 7"),
    ((690, 560), (420, 700), "バス 試し\nlength 9"),
    ((965, 705), (800, 360), "郵便トラック 今\nlength 4"),
    ((1212, 825), (1330, 520), "郵便トラック 試し\nlength 6"),
])
save("coal_z3.png", "H_coal_2x.png", "H 手本の 2 倍の試し絵: 石炭のトラック（温帯・夏・拡大 3）。自動車は pak128 の 2 倍", [
    ((580, 515), (200, 620), "石炭のトラック 今\nlength 4"),
    ((950, 685), (1100, 540), "石炭のトラック 試し\nlength 8"),
])
save("rail_z3.png", "I_rail_2x.png", "I 手本の 2 倍の試し絵: 気動車 + 付随車と駅（温帯・夏・拡大 3）。鉄道は pak128.Japan の 2 倍", [
    ((600, 415), (860, 180), "今（length 12 × 2）\n幅 8%・高さ 8%"),
    ((860, 800), (1100, 700), "試し（length 12 × 2）\n幅 11%・高さ 9%"),
])

# 駅のホームと車体: 同じ大きさで切り出して 4 倍にして並べる
rail = Image.open(os.path.join(SRC, "rail_z3.png")).convert("RGB")
crops = [rail.crop((580, 385, 720, 485)), rail.crop((835, 765, 975, 865))]
out = Image.new("RGB", (560 * 2 + 12, 440), (20, 20, 20))
d = ImageDraw.Draw(out)
for i, (im, cap) in enumerate(zip(crops, ("今の気動車（幅 2.8m 相当）", "試し（幅 4.1m 相当）"))):
    d.text((i * 572 + 8, 8), cap, font=FB, fill=(255, 255, 255))
    out.paste(im.resize((560, 400), Image.NEAREST), (i * 572, 40))
out.save(os.path.join(DST, "J_platform_2x.png"), optimize=True)
