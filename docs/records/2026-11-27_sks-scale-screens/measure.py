"""MIT License。使い方（リポジトリの直下で）: python -X utf8 measure.py <_ref_sks>
SKS と pak256 の船・飛行機の絵の外接枠を同じ測り方で測る（#164）。vehicle_sizes.py と同じ定義。
sw=横向き（長さ）、se=正面向き（幅）、高さ=横向きの縦 − 幅/2。"""
import os
import sys
from PIL import Image

REF = sys.argv[1]
WT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CLEAR = (231, 255, 255)
# dat の並び S,E,SE,SW,N,W,NW,NE が SKS の列の順。pak256 の表は s,w,sw,se,n,e,ne,nw
SKS_COL = {"s": 0, "e": 1, "se": 2, "sw": 3, "n": 4, "w": 5, "nw": 6, "ne": 7}
OWN_COL = {"s": 0, "w": 1, "sw": 2, "se": 3, "n": 4, "e": 5, "ne": 6, "nw": 7}


def sprite(path, cell, row, col):
    im = Image.open(path).convert("RGBA").crop((col * cell, row * cell, (col + 1) * cell, (row + 1) * cell))
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if p[3] and p[:3] == CLEAR:
                px[x, y] = (0, 0, 0, 0)
    return im


def size(path, cell, row, colmap):
    box = {}
    for k in ("sw", "se", "e"):
        b = sprite(path, cell, row, colmap[k]).getchannel("A").point(lambda a: 255 if a > 127 else 0).getbbox()
        box[k] = (b[2] - b[0], b[3] - b[1])
    L, W = box["sw"][0], box["se"][0]
    return L, W, box["sw"][1] - W / 2, box["e"], box["sw"][1]


atr = REF + r"\SKS_ATR_ver1\source\SKS_ATR_1.png"
snf = REF + r"\SKS_SNF_ver1.1\source\SKS_SNF_1_size384.png"
rows = [
    # 名前, png, cell, row, colmap, 拡大, 実物の長さ・幅・高さ(m)
    ("SKS ATR42-600 (1x)", atr, 128, 0, SKS_COL, 1, (22.67, 24.57, 7.59)),
    ("SKS ATR72-600 (1x)", atr, 128, 2, SKS_COL, 1, (27.17, 27.05, 7.65)),
    ("SKS ATR42-600 (2x)", atr, 128, 0, SKS_COL, 2, (22.67, 24.57, 7.59)),
    ("SKS ATR72-600 (2x)", atr, 128, 2, SKS_COL, 2, (27.17, 27.05, 7.65)),
    ("pak256_airliner (Ju52)", WT + r"\objects\vehicle\air\airliner\airliner.png", 512, 0, OWN_COL, 1, (18.9, 29.25, 4.5)),
    ("SKS SNF (1x)", snf, 384, 0, SKS_COL, 1, (224.5, None, None)),
    ("SKS SNF (2x)", snf, 384, 0, SKS_COL, 2, (224.5, None, None)),
    ("pak256_ferry", WT + r"\objects\vehicle\water\ferry\ferry.png", 512, 0, OWN_COL, 1, (30, 7, None)),
    ("pak256_cargo_ship", WT + r"\objects\vehicle\water\cargo_ship\cargo_ship.png", 512, 0, OWN_COL, 1, (36, 8, None)),
]
# pak256 の実物比例: 横向きは 1m = 6.86px
print("| 物 | 横向き長さpx | 正面幅px | 高さpx(概算) | 横向き外接枠の縦px | 実物の長さm | px/m | 6.86比 | 翼/船幅 px/m | 軸向きe 外接枠 |")
for name, p, cell, row, cm, k, (rl, rw, rh) in rows:
    L, W, H, e, swh = size(p, cell, row, cm)
    L, W, H, swh, e = L * k, W * k, H * k, swh * k, (e[0] * k, e[1] * k)
    print(f"| {name} | {L} | {W} | {H:.0f} | {swh} | {rl} | {L / rl:.2f} | {L / rl / 6.86:.2f} | {format(W / rw, ".2f") if rw else "-"} | {e[0]}x{e[1]} |")
