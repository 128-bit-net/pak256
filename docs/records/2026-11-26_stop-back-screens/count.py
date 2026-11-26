"""停留所の奥の帯と草のあいだに残る暗い行数を、列ごとに数える（#139）。MIT License。Pillow が要る。

列を上から見て、草の下端の次に続く暗い画素の数を数える。その下に帯の灰色が 8px 以上続く列だけを数える。
撮り方は 2026-11-26_stop-overlap-screens/run.py の ew_empty.png（バス停 3 タイル）・ns_empty.png（荷役所 3 タイル）。
x の範囲は、画面の中央の 3 タイル続きの停留所。
使い方: python -X utf8 count.py <撮った画面のフォルダ> ...
"""
import collections
import sys

from PIL import Image

SHOTS = [("ew_empty", 770, 1130, "バス停"), ("ns_empty", 660, 1020, "荷役所")]


def grass(p):
    return p[1] > p[0] + 15 and p[1] > p[2] + 15


def dark(p):
    return max(p) < 80


def concrete(p):
    r, g, b = p
    return 110 < r < 215 and abs(r - g) < 12 and 0 <= r - b < 25


def count(path, x0, x1):
    px = Image.open(path).convert("RGB").load()
    hist = collections.Counter()
    for x in range(x0, x1):
        y = 52  # ツールバーの下から
        while y < 860 and not (grass(px[x, y]) and not grass(px[x, y + 1])):
            y += 1
        y += 1
        n = 0
        while y < 860 and dark(px[x, y]):
            y += 1
            n += 1
        if all(concrete(px[x, y + i]) for i in range(8)):
            hist[n] += 1
    return dict(sorted(hist.items()))


def main():
    for folder in sys.argv[1:]:
        for shot, x0, x1, label in SHOTS:
            print(f"{folder}/{shot}.png（{label}、x={x0}〜{x1}）暗い行数: 列数 = {count(f'{folder}/{shot}.png', x0, x1)}")


if __name__ == "__main__":
    main()
