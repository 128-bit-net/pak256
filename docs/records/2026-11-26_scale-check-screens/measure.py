"""撮った画面（札を書く前の物）の中から、素材の PNG の絵を探して、画面の上の大きさを測る（#104）。MIT License。

使い方: python -X utf8 measure.py <run.py の出力フォルダ>   （numpy・Pillow）
絵の不透明な画素の 9 割以上が画面の画素と合う場所を探し、合った絵の外接枠の高さ・幅を出す。
バスは、絵の中ほどの 1 列で、屋根の色（いちばん上の面）が続く画素数（車幅の縦の厚み）も出す。
"""
import glob
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
SRC = sys.argv[1]
TOL = 10  # 本体は 16 ビットの色で描くので、少しの色の差を許す


def find(screen, cell):
    """screen の中で cell の不透明な画素がいちばん合う左上と、合った割合。"""
    alpha = cell[:, :, 3] > 0
    ys, xs = np.nonzero(alpha)
    y0, x0 = ys.min(), xs.min()
    ys, xs = ys - y0, xs - x0
    colors = cell[ys + y0, xs + x0, :3].astype(np.int16)
    h, w = screen.shape[0] - ys.max(), screen.shape[1] - xs.max()
    probe = np.linspace(0, len(ys) - 1, 12).astype(int)
    hit = np.zeros((h, w), np.int16)
    for i in probe:
        part = screen[ys[i]:ys[i] + h, xs[i]:xs[i] + w]
        hit += (np.abs(part - colors[i]).max(axis=2) <= TOL)
    best = (0.0, None)
    for y, x in zip(*np.nonzero(hit >= 9)):
        score = (np.abs(screen[ys + y, xs + x] - colors).max(axis=1) <= TOL).mean()
        if score > best[0]:
            best = (score, (x, y))
    return best + (int(xs.max()) + 1, int(ys.max()) + 1)


def cell(png, col, row):
    im = np.array(Image.open(os.path.join(ROOT, png)).convert("RGBA"))
    part = im[row * 256:(row + 1) * 256, col * 256:(col + 1) * 256].copy()
    part[(part[:, :, :3] == (231, 255, 255)).all(axis=2), 3] = 0  # makeobj の透明の色
    return part


def screen(name):
    return np.array(Image.open(os.path.join(SRC, name)).convert("RGB")).astype(np.int16)


shots = {n: screen(n) for n in ("A_road_z3.png", "B_rail_z3.png", "C_industry_z3.png")}
for tree, m in (("zelkova", 18), ("cedar", 24), ("birch", 14)):
    c = cell(f"objects/scenery/trees/{tree}.png", 4, 0)  # 成木（age 4）の夏
    best = max((find(s, c) + (n,) for n, s in shots.items()), key=lambda r: r[0])
    score, at, w, h, name = best
    print(f"{tree}: {name} 左上 {at} 一致 {score:.0%} 高さ {h}px 幅 {w}px（表の {m}m x 5.9 = {m * 5.9:.0f}px）")

best = (0, None)
for png in glob.glob(os.path.join(ROOT, "objects/vehicle/road/bus/*.png")):
    sheet = Image.open(png)
    for col in range(sheet.width // 256):
        c = cell(os.path.relpath(png, ROOT), col, 0)
        r = find(shots["A_road_z3.png"], c)
        if r[0] > best[0]:
            best = (r[0], r[1], r[2], r[3], col, c)
score, at, w, h, col, c = best
print(f"bus: A_road_z3.png 左上 {at} 一致 {score:.0%} 絵の列 {col} 外接枠 {w}x{h}px")
ys, xs = np.nonzero(c[:, :, 3] > 0)
x = (xs.min() + xs.max()) // 2
col_px = c[ys.min():ys.max() + 1, x]
runs, prev = [], "start"
for p in col_px:
    key = tuple(p[:3]) if p[3] else None
    if key == prev:
        runs[-1][1] += 1
    else:
        runs.append([key, 1])
        prev = key
print("bus の中ほどの 1 列（上から、色と画素数）:", [(tuple(int(v) for v in k) if k else None, n) for k, n in runs])
