"""#206: 撮った画面から、仕様のページに載せる分を切り出して 256 色にする。MIT License。

リポジトリの直下で:
    python -X utf8 docs/records/2026-11-27_spec-stations-screens/crop.py <撮影の出力の親>
親の下に rail/・road/（shoot.py）・tram/（tools/vehicle_check/tram_run.py）・mono/（monorail_run.py）がある形。出力は site/public/spec/。
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


save(load("rail/station_02.png").crop((60, 60, 660, 400)), "station-rail.png")
save(load("road/truck_stop_00.png").crop((280, 120, 640, 360)).resize((720, 480), Image.NEAREST), "station-truck.png")
save(load("tram/own_stop_0.png").crop((560, 340, 1160, 700)), "station-tram.png")
save(load("mono/ground_station.png").crop((440, 340, 1040, 700)), "station-monorail.png")

# 信号: 列車がいないときと、手前に立つ信号の脇を列車が通るとき（同じ切り出し。2 倍の最近傍）
box = (300, 100, 500, 300)
pair = Image.new("RGB", (820, 440), (250, 250, 248))
d = ImageDraw.Draw(pair)
font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 18)
for i, (name, label) in enumerate((("rail/signal_left_empty.png", "列車がいないとき"), ("rail/signal_s_00.png", "列車が脇を通るとき"))):
    pair.paste(load(name).crop(box).resize((400, 400), Image.NEAREST), (i * 420, 40))
    d.text((i * 420 + 200, 8), label, font=font, fill=(30, 30, 30), anchor="ma")
save(pair, "signal-screen.png")
