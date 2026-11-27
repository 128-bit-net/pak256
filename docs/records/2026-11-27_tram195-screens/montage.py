"""#195: scene.py で撮った前後の画面を、停留所のまわりを切り抜いて 2 倍にして並べる。MIT License。

    python -X utf8 docs/records/2026-11-27_tram195-screens/montage.py <前の撮影のフォルダ> <後の撮影のフォルダ> <出力のフォルダ>
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

before, after, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
# 飛んだ升の停留所が写る画面の位置（軸ごと。撮った画面から読んだ値。1600x900）
CENTER = {"ew": (950, 510), "ns": (845, 510)}
HALF = (230, 160)    # 切り抜きの半分の大きさ（等倍の px）
SCALE = 2
FONT = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 22)
# 区画の原点（scene.py の LINES。ゲームの座標は 60 を足す）
SITES = {
    "dirt_ew": "土の上・東西", "dirt_ns": "土の上・南北", "road_ew": "道路の上・東西", "road_ns": "道路の上・南北",
}
ORIGIN = {"dirt_ew": (0, 0, "ew"), "dirt_ns": (22, 0, "ns"), "road_ew": (0, 22, "ew"), "road_ns": (34, 4, "ns")}


def label(site, view, cat):
    x, y, axis = ORIGIN[site]
    if cat == "nocat":
        y += 40
    i = 4 if view == "run" else 10
    pos = (60 + x + i, 60 + y) if axis == "ew" else (60 + x, 60 + y + i)
    return f"{SITES[site]}・{'3 升の連なり' if view == 'run' else '単独の升'} ({pos[0]},{pos[1]})"


def crop(path, axis):
    cx, cy = CENTER[axis]
    im = Image.open(path).convert("RGB").crop((cx - HALF[0], cy - HALF[1], cx + HALF[0], cy + HALF[1]))
    return im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)


def sheet(cat, view, name):
    w, h, bar = HALF[0] * 2 * SCALE, HALF[1] * 2 * SCALE, 36
    im = Image.new("RGB", (w * 2 + 8, (h + bar) * len(SITES)), (0, 0, 0))
    d = ImageDraw.Draw(im)
    for r, site in enumerate(SITES):
        for c, (folder, what) in enumerate(((before, "直す前"), (after, "直した後"))):
            x, y = c * (w + 8), r * (h + bar)
            d.text((x + 6, y + 4), f"{what}: {label(site, view, cat)}・温暖・2 倍", font=FONT, fill=(255, 220, 90))
            im.paste(crop(os.path.join(folder, f"{cat}_{site}_{view}.png"), ORIGIN[site][2]), (x, y + bar))
    im.save(os.path.join(out, name), optimize=True)


sheet("cat", "run", "1_catenary_run.png")
sheet("cat", "single", "2_catenary_single.png")
sheet("nocat", "run", "3_no_catenary_run.png")
sheet("nocat", "single", "4_no_catenary_single.png")
