"""run.py の撮影に、見出し（場所・座標・気候・拡大率）と実物の寸法の札を書き込み、道路・線路の帯の幅を測った図を作る（#104）。MIT License。

使い方: python -X utf8 annotate.py <run.py の出力フォルダ> <出す先>
札の位置は、この記録の撮影の画素に合わせた固定の値（run.py の配置を変えたら直す）。Windows のメイリオを使う。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

SRC, DST = sys.argv[1], sys.argv[2]
FONT = "C:/Windows/Fonts/meiryo.ttc"
F = ImageFont.truetype(FONT, 17)
FB = ImageFont.truetype(FONT, 20)
TILE_M = 26.4


def label(d, at, to, text):
    """to の札（左上）から at の点へ線を引く。"""
    box = d.multiline_textbbox((to[0] + 5, to[1] + 3), text, font=F)
    d.line([at, ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2)], fill=(255, 255, 0), width=2)
    d.rectangle([to[0], to[1], box[2] + 5, box[3] + 4], fill=(0, 0, 0))
    d.multiline_text((to[0] + 5, to[1] + 3), text, font=F, fill=(255, 255, 255))
    d.ellipse([at[0] - 3, at[1] - 3, at[0] + 3, at[1] + 3], fill=(255, 255, 0))


def header(d, text):
    d.rectangle([0, 0, 1599, 47], fill=(20, 20, 20))
    d.text((10, 10), text, font=FB, fill=(255, 255, 255))


def save(name, title, labels):
    im = Image.open(os.path.join(SRC, name)).convert("RGB")
    d = ImageDraw.Draw(im)
    header(d, title)
    for at, to, text in labels:
        label(d, at, to, text)
    im.save(os.path.join(DST, name), optimize=True)


COMMON = "温帯・夏・拡大 3（等倍）・1 タイル = 26.4m・高さ 1m = 5.94px"
save("A_road_z3.png", f"A 道路の列（x 58〜67, y 59〜61）　{COMMON}", [
    ((360, 300), (200, 130), "戸建て 9×7m\n棟 8.6m"),
    ((510, 350), (440, 190), "戸建て（大）12×9m\n棟 9m"),
    ((705, 385), (640, 270), "ケヤキ 18m"),
    ((760, 470), (610, 590), "商店 11×8m\n高 7.5m"),
    ((880, 470), (850, 300), "集合住宅 22×12m\n高 15.6m"),
    ((920, 560), (1000, 420), "スギ 24m"),
    ((1130, 690), (990, 570), "町工場 13×10m"),
    ((1280, 660), (1180, 520), "役場 22×16m\n時計塔まで約 20m"),
    ((1540, 790), (1385, 600), "オフィス 16×14m\n高 23m（機械室 25m）"),
    ((300, 500), (150, 600), "シラカバ 14m"),
    ((570, 505), (330, 660), "バス 全長 11.55m（length 7）\n幅 2.5m・高 3.2m"),
    ((965, 705), (700, 780), "郵便のトラック 全長 6.6m（length 4）"),
    ((1222, 835), (880, 830), "石炭のトラック 6.6m（length 4）"),
])
save("B_rail_z3.png", f"B 線路の列（x 58〜67, y 65〜66）　{COMMON}", [
    ((350, 290), (130, 140), "長屋 20×9m\n棟 11m"),
    ((400, 300), (500, 180), "スギ 24m"),
    ((470, 540), (140, 640), "駅（pak256 の物）3 タイル = 79m\nホーム高 0.9m"),
    ((760, 620), (800, 400), "気動車 + 付随車\n全長 19.8m × 2（length 12）"),
    ((1000, 590), (1100, 420), "量販店 20×12m\n高 14.3m（看板塔 16.8m）"),
    ((1250, 640), (1330, 520), "ケヤキ 18m"),
    ((1280, 760), (950, 790), "倉庫 22×14m・棟 9.8m"),
    ((1530, 790), (1380, 660), "工場 22×16m\n煙突 19m"),
])
save("C_industry_z3.png", f"C 産業の列（x 57〜65, y 73〜76）　{COMMON}", [
    ((520, 175), (620, 100), "炭鉱 2×2 タイル（52.8m）\n立坑の櫓 17m"),
    ((348, 185), (80, 80), "ケヤキ 18m"),
    ((860, 550), (720, 640), "スギ 24m"),
    ((585, 515), (300, 640), "石炭のトラック 6.6m（length 4）"),
    ((1415, 430), (1100, 260), "火力発電所 3×3 タイル（79.2m）\n煙突 28m（本絵では 100m 級にする仮の値）"),
])
save("D_overview_z6.png", "D 全体（x 52〜74, y 59〜76）　温帯・夏・拡大 6（1/2）　上から 道路の列 → 線路の列 → 産業の列", [])


def band(name, crop, x, y0, y1, marks):
    """crop を 2 倍にして、列 x に帯の幅の寸法線を引く。marks は (上の y, 下の y, 札, 横のずらし)。"""
    im = Image.open(os.path.join(SRC, name)).convert("RGB").crop(crop)
    im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for top, bot, text, off in marks:
        px = (x - crop[0] + off) * 2
        a, b = (top - crop[1] + off // 2) * 2, (bot - crop[1] + off // 2) * 2
        d.line([(px, a), (px, b)], fill=(255, 255, 0), width=3)
        for yy in (a, b):
            d.line([(px - 10, yy), (px + 10, yy)], fill=(255, 255, 0), width=3)
        m = (bot - top) / 128 * TILE_M
        label(d, (px, (a + b) // 2), (px + 24, (a + b) // 2 - 12), f"{text} {bot - top}px = {m:.0f}m 相当")
    return im


road = band("A_road_z3.png", (40, 200, 440, 480), 100, 0, 0,
            [(242, 371, "舗装の端から端", 0), (262, 350, "白線の外から外", 170)])
rail = band("B_rail_z3.png", (40, 220, 440, 380), 100, 0, 0, [(284, 333, "道床の帯", 0)])
stop = Image.open(os.path.join(SRC, "A_road_z3.png")).convert("RGB").crop((378, 470, 628, 590)).resize((1000, 480), Image.NEAREST)
out = Image.new("RGB", (1000, 60 + road.height + rail.height + stop.height + 100), (20, 20, 20))
d = ImageDraw.Draw(out)
d.text((10, 14), "E 道路・線路の帯の縦の厚み（画面の 1 列で測る。128px = 1 タイル = 26.4m）", font=FB, fill=(255, 255, 255))
y = 60
for im, cap in ((road, "AMI の生活道路 ami_road_local（2 倍）"), (rail, "AMI の線路 ami_rail_ballast（2 倍）"),
                (stop, "pak256 のバス停とバス（4 倍）: 待合と歩道が白線の上に重なる。バスの屋根の幅 約 13px（2.7m）、1 車線 約 44px（9m）")):
    d.text((10, y + 4), cap, font=F, fill=(255, 255, 255))
    out.paste(im, (0, y + 32))
    y += 32 + im.height
out.crop((0, 0, 1000, y + 4)).save(os.path.join(DST, "E_width.png"), optimize=True)
