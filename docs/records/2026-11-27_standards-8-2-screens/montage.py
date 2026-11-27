"""MIT License。#176: 撮った画面から、記録の画像（このフォルダの PNG）を組み直す。

使い方（リポジトリの根元で）: python -X utf8 montage.py [work の場所。省くと work]
撮った画面の場所は、記録の「手順」のとおり（s1〜s4・snow_mail・snow_coal・longbus）。無い物は飛ばす。
"""
import glob
import os
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
W = sys.argv[1] if len(sys.argv) > 1 else "work"
ROAD = ["e", "se", "s", "sw", "w", "nw", "n", "ne", "corner_nw", "corner_sw"]
SHIP = {"1_0": "東", "1_1": "南東", "0_1": "南", "-1_1": "南西", "-1_0": "西", "-1_-1": "北西", "0_-1": "北", "1_-1": "北東"}


def sheet(name, cols, tiles):
    """tiles は (札, 画像, 切り抜き, 倍率)。倍率 None は画像の全体を 0.4 倍。"""
    specs = []
    for label, path, box, k in tiles:
        if not os.path.isfile(path):
            continue
        if box is None:
            box = "0,0,%d,%d" % Image.open(path).size
        specs.append(f"{label}={path}:{box}:{k}")
    if not specs:
        print(name, "画面が無いので飛ばす")
        return
    out = os.path.join(HERE, name + ".png")
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "crop.py"), out, str(cols), *specs], check=True)
    im = Image.open(out).convert("RGB")  # 幅と色数を減らす
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
    im.quantize(256, dither=Image.Dither.NONE).save(out, optimize=True)


s1, s2, s3, s4 = (os.path.join(W, n) for n in ("s1", "s2", "s3", "s4"))
sheet("factories", 2, [(f"産業 {n}（仮の箱）", f"{s1}/factory_{n}.png", "0,58,1600,880", 0.45) for n in ("4x4", "6x6")])
sheet("stations", 2, [("停留所（stop）の dims 2,1: 置かれるのは 1 タイルだけ", f"{s1}/stop_2x1.png", "640,420,1180,700", 1),
                      ("駅舎（extension）の 2×1（奥）・2×2（手前）と pak256 の駅", f"{s1}/extension.png", "360,300,1180,780", 1)])
sheet("road_stops", 2, [(f"ami_road_{n}", f"{s1}/road_{n}.png", "740,470,1060,660", 2)
                        for n in ("local", "general", "trunk", "expressway")])
sheet("rail_stations", 2, [(f"ami_rail_{n}", f"{s1}/rail_{n}.png", "740,430,1060,660", 2)
                           for n in ("ballast", "concrete", "slab", "ladder")])
for n in ("bow", "mid"):
    sheet(f"ship_{n}", 2, [(f"進む升の向き {v}", f"{s2}/t8_ship_{n}_{k}.png", "0,58,1600,878", 0.4) for k, v in SHIP.items()])
sheet("ship_threads", 2, [(label, f"{d}/t8_ship_bow_{k}.png", box, 1)
                          for k, box, v in (("-1_0", "560,300,1200,760", "西"), ("-1_1", "560,300,1360,640", "南西"))
                          for d, label in ((s2, f"本体の既定: {v}（右端が切れる）"), (s3, f"描画 1 スレッド: {v}"))])
for name, folder in (("snow_mail", "snow_mail"), ("snow_coal", "snow_coal"), ("longbus", "longbus")):
    tiles = []
    for d in ROAD:
        files = sorted(glob.glob(f"{W}/{folder}/left_{d}_*car_*_zoom.png"))  # 1 両の絵を先に使う
        if files:
            tiles.append((d, files[0], None, 0.4))
    sheet(name, 5, tiles)
for name, spots, cols in (("slope", ("slope_up", "slope_top", "slope_down"), 4), ("diag", ("diagonal", "switch", "branch"), 4),
                          ("tram", ("tram_road_up", "tram_road_down", "tram_own_up", "tram_own_down"), 4),
                          ("double", ("double_up", "double_down"), 4)):
    sheet(name, cols, [(f"{n} {f[:-4].split('_')[-3]}", f, "620,360,1240,720", 0.6)
                       for n in spots for f in sorted(glob.glob(f"{s4}/{n}_*.png"))])
