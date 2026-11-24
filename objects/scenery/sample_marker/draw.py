"""見本の物 sample_marker の絵を描く（docs/layout.md の「見本の物」）。仮の物で、#9 で木が入ったら消す。

256px のセルを横に 5 つ並べ、木の育ち（age 0〜4）ごとに大きくなる印（柱と菱形の台）を描く。
タイルの菱形はセルの下半分（上の頂点 (128,128)、幅 256、高さ 128）。

使い方（Pillow が要る。描いた PNG は git に入れる）:
    python -X utf8 objects/scenery/sample_marker/draw.py
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = 256
AGES = 5
CLEAR = (231, 255, 255)  # makeobj の透明色


def main():
    im = Image.new("RGB", (CELL * AGES, CELL), CLEAR)
    dr = ImageDraw.Draw(im)
    for age in range(AGES):
        cx, cy = CELL * age + CELL // 2, CELL * 3 // 4  # タイルの中心
        r = 10 + 4 * age  # 台の半幅
        dr.polygon([(cx, cy - r // 2), (cx + r, cy), (cx, cy + r // 2), (cx - r, cy)], fill=(120, 120, 120))
        h = 24 + 16 * age  # 柱の高さ
        dr.rectangle([cx - 3, cy - h, cx + 3, cy], fill=(200, 60, 40))
        dr.rectangle([cx - 3, cy - h, cx, cy], fill=(240, 90, 60))
    im.save(os.path.join(HERE, "sample_marker.png"))


if __name__ == "__main__":
    main()
