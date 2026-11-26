"""run.py の画面で、白線が停留所に隠れていないかを列ごとに数える（#115）。MIT License。Pillow が要る。

道路を横切る列を 1px ずつ調べ、白（RGB がすべて 200 超）の縦の連なりが「2px が 2 本、上端の差 86px」の列を数える。
車両のいない ew_empty.png・ns_empty.png に使う。
使い方: python -X utf8 lines.py <画面の PNG> ...
"""
import sys

from PIL import Image

X0, X1 = 600, 1000  # 停留所 3 タイルが入る列の範囲（画面の中心 800 の左右）

for path in sys.argv[1:]:
    im = Image.open(path).convert("RGB")
    px = im.load()
    ok, bad = 0, []
    for x in range(X0, X1):
        runs, y = [], 48
        while y < 876:
            if min(px[x, y]) > 200:
                s = y
                while y < 876 and min(px[x, y]) > 200:
                    y += 1
                runs.append((s, y - s))
            y += 1
        if len(runs) == 2 and all(n == 2 for _, n in runs) and runs[1][0] - runs[0][0] == 86:
            ok += 1
        else:
            bad.append((x, runs))
    print(f"{path}: 白線 2 本がそのままの列 {ok}/{X1 - X0}", bad[:4])
