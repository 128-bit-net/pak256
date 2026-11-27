"""#206: 撮った画面から、仕様のページに載せる分を切り出して 256 色にする。MIT License。

リポジトリの直下で:
    python -X utf8 docs/records/2026-11-27_spec-stations-screens/crop.py <撮影の出力の親>
親の下に rail/・rail_ne/・road/（shoot.py）・tram/（tools/vehicle_check/tram_run.py）・mono/（monorail_run.py）がある形。出力は site/public/spec/。
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

src = sys.argv[1]
out = "site/public/spec"


def load(name):
    return Image.open(os.path.join(src, name)).convert("RGB")


def save(im, name):
    im.quantize(256).save(os.path.join(out, name), optimize=True)


if "--signal-only" not in sys.argv:  # 信号の画面だけ撮り直したときは、ほかの出力を作らない
    save(load("rail/station_02.png").crop((60, 60, 660, 400)), "station-rail.png")
    save(load("road/truck_stop_00.png").crop((280, 120, 640, 360)).resize((720, 480), Image.NEAREST), "station-truck.png")
    save(load("tram/own_stop_0.png").crop((560, 340, 1160, 700)), "station-tram.png")
    save(load("mono/ground_station.png").crop((440, 340, 1040, 700)), "station-monorail.png")

# 信号: 列車がいないとき、手前の側の信号の脇、奥の側の信号の脇（2 倍の最近傍）
box, far = (300, 100, 500, 300), (320, 90, 520, 290)
pair = Image.new("RGB", (1240, 440), (250, 250, 248))
d = ImageDraw.Draw(pair)
font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 18)
for i, (name, area, label) in enumerate((("rail/signal_left_empty.png", box, "列車が脇にいないとき"),
                                         ("rail/signal_s_00.png", box, "手前の側の信号（s）の脇"),
                                         ("rail_ne/signal_n_01.png", far, "奥の側の信号（n）の脇"))):
    pair.paste(load(name).crop(area).resize((400, 400), Image.NEAREST), (i * 420, 40))
    d.text((i * 420 + 200, 8), label, font=font, fill=(30, 30, 30), anchor="ma")
save(pair, "signal-screen.png")
