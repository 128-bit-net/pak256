"""#134 の記録の画像を作る（compare.py を呼ぶ。全体の図は、拡大した所を赤い枠で示す）。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_ami333-screens/montage.py <前のフォルダ> <後のフォルダ> <出力のフォルダ>
<前のフォルダ>・<後のフォルダ> は scene.py の出力。
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

before, after, out = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))


def zoom(name, *specs):
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(here, "compare.py"), before, after,
                    os.path.join(out, name), *specs], check=True)


def overview(name, rows):
    """1 段 = (画面の名前, 赤い枠 [(x, y, 幅, 高さ), ...])。画面の中の道具の帯と下の帯を除いて半分に縮め、左が前、右が後。"""
    cells = []
    for view, boxes in rows:
        pair = []
        for label, folder in (("before", before), ("after", after)):
            im = Image.open(os.path.join(folder, view + ".png")).convert("RGB")
            draw = ImageDraw.Draw(im)
            for x, y, w, h in boxes:
                draw.rectangle((x - 3, y - 3, x + w + 3, y + h + 3), outline=(255, 0, 0), width=4)
            part = im.crop((0, 48, 1600, 878)).resize((800, 415), Image.LANCZOS)
            canvas = Image.new("RGB", (800, 431), (255, 255, 255))
            canvas.paste(part, (0, 16))
            ImageDraw.Draw(canvas).text((4, 2), f"{label}  {view}", fill=(0, 0, 0))
            pair.append(canvas)
        row = Image.new("RGB", (1612, 431), (255, 0, 0))
        row.paste(pair[0], (0, 0))
        row.paste(pair[1], (812, 0))
        cells.append(row)
    sheet = Image.new("RGB", (1612, sum(c.height + 8 for c in cells)), (255, 255, 255))
    top = 0
    for c in cells:
        sheet.paste(c, (0, top))
        top += c.height + 8
    sheet.save(os.path.join(out, name))


os.makedirs(out, exist_ok=True)
overview("0_where.png", [
    ("temperate_slope_road", [(866, 462, 60, 32), (735, 430, 60, 32)]),
    ("temperate_slope2_road", [(866, 430, 60, 32), (738, 430, 60, 32)]),
    ("temperate_bridge_slope2", [(1140, 730, 60, 48)]),
    ("temperate_bridge", [(858, 194, 28, 16)]),
    ("temperate_stop", [(855, 490, 60, 40)]),
])
zoom("1_cross_corner.png", "temperate_slope_road:866,462,60,32,8", "temperate_slope2_road:866,430,60,32,8",
     "snow_slope_road:866,462,60,32,8", "snow_slope2_road:866,430,60,32,8")
zoom("2_slope_seam_and_back_edge.png", "temperate_slope_road:735,430,60,32,8", "temperate_slope2_road:738,430,60,32,8",
     "temperate_t_junction:610,368,60,32,8", "snow_slope_road:735,430,60,32,8")
zoom("3_bridge_end_2steps.png", "temperate_bridge_slope2:1140,730,60,48,8", "snow_bridge_slope2:1140,730,60,48,8")
zoom("4_white_line_gap.png", "temperate_slope2_road:859,450,28,16,14", "temperate_bridge:858,194,28,16,14",
     "temperate_bridge_end:986,515,28,16,14", "temperate_diagonal_road:986,194,28,16,14",
     "temperate_elevated:1500,642,28,16,14", "snow_slope2_road:850,444,100,30,8")
zoom("5_stop_back_edge.png", "temperate_stop:855,490,60,40,8", "temperate_stop:1000,555,60,40,8")
overview("6_others_temperate.png", [(f"temperate_{n}", []) for n in
                                    ("tram_road", "pier", "canal", "sidewalk", "crossing", "elevated", "t_junction")])
zoom("8_tram.png", "temperate_tram_road:300,258,60,40,8", "temperate_tram_road:1320,780,100,60,6",
     "snow_tram_road:300,258,60,40,8")
overview("7_others_snow.png", [(f"snow_{n}", []) for n in
                               ("slope_road", "slope2_road", "bridge_slope2", "tram_road", "pier", "canal", "sidewalk",
                                "crossing", "elevated", "bridge", "bridge_end", "t_junction")])
