"""#205: shoot.py の出力から、ページに載せる画面を切り出して site/public/spec/ に書く（256 色）。MIT License。

リポジトリの直下で `python -X utf8 docs/records/2026-11-27_spec-road-vehicles-screens/crop.py <shoot.py の出力>`。
コマの名前と切り出す範囲は 2026-11-27 に撮った回の物で、撮り直すと合わなくなる。
"""
import sys

from PIL import Image

src = sys.argv[1]
for frame, box, zoom, name in (
    ("stop_10", (0, 0, 800, 480), 1, "road-vehicles"),
    ("ped_06", (0, 0, 800, 480), 1, "road-trucks"),
    ("ped_01", (0, 0, 800, 480), 1, "road-citycars"),
    ("ped_01", (320, 110, 640, 310), 3, "pedestrians"),
):
    im = Image.open(f"{src}/{frame}.png").convert("RGB").crop(box)
    if zoom != 1:
        im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    im.quantize(256, dither=Image.Dither.NONE).save(f"site/public/spec/{name}.png", optimize=True)
    print(name, im.size)
