"""#159: 記録の画像（0〜6）を作る。左（前）が alpha.7、右（後）が alpha.8。MIT License。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_ami159-screens/montage.py <撮影の根のフォルダ> <出力のフォルダ>
<撮影の根のフォルダ> の下に、前（b_）と後（a_）を次の名前で置く:
    b_old・a_old    ../2026-11-26_ami333-screens/scene.py の出力
    b_new・a_new    scene.py の出力
    b_seamk・a_seamk seam_scene.py の出力
    b_seam・a_seam   ../2026-11-26_snow-road-seam-screens/scene.py の出力（道路名を書き換える既定。街の道路は ami_road_local）
    b_con・a_con    ../2026-11-26_ami333-screens/concrete_scene.py の出力
切り抜き（1・3・4・5）は ../2026-11-26_ami333-screens/compare.py で作る。コンクリートの列は、左が alpha.7、中が alpha.8、右が道路のコンクリート（alpha.8）。
"""
import os
import subprocess
import sys

from PIL import Image, ImageDraw

root, out = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
COMPARE = os.path.join(here, "..", "2026-11-26_ami333-screens", "compare.py")
seam_b, seam_a, con_b, con_a = (os.path.join(root, n) for n in ("b_seamk", "a_seamk", "b_con", "a_con"))


def label(im, text):
    canvas = Image.new("RGB", (im.width, im.height + 16), (255, 255, 255))
    canvas.paste(im, (0, 16))
    ImageDraw.Draw(canvas).text((4, 2), text, fill=(0, 0, 0))
    return canvas


def row(cells):
    sheet = Image.new("RGB", (sum(c.width for c in cells) + 12 * (len(cells) - 1), max(c.height for c in cells)), (255, 0, 0))
    x = 0
    for c in cells:
        sheet.paste(c, (x, 0))
        x += c.width + 12
    return sheet


def stack(rows):
    sheet = Image.new("RGB", (max(r.width for r in rows), sum(r.height + 8 for r in rows)), (255, 255, 255))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height + 8
    return sheet


def shot(folder, name):
    return Image.open(os.path.join(folder, name + ".png")).convert("RGB")


# 街の道路（雪）。後の画面の点線の所（画面の画素）を赤い枠で囲む
BOX = (808, 325, 1000, 385)
rows = []
cells = []
for text, folder in (("before (alpha.7)", seam_b), ("after (alpha.8)", seam_a)):
    im = shot(folder, "city")
    ImageDraw.Draw(im).rectangle(BOX, outline=(255, 0, 0), width=3)
    cells.append(label(im.crop((240, 220, 1360, 870)).resize((800, 464), Image.LANCZOS), f"{text}  snow city road"))
rows.append(row(cells))
for box, text in (((808, 325, 1000, 385), "road (x=808 y=325)"), ((800, 355, 940, 415), "sidewalk inner edge (x=800 y=355)")):
    rows.append(row([label(shot(f, "city").crop(box).resize(((box[2] - box[0]) * 6, (box[3] - box[1]) * 6), Image.NEAREST),
                           f"{t}  {text}  x6") for t, f in (("before", seam_b), ("after", seam_a))]))
rows.append(row([label(shot(os.path.join(root, side + "_seam"), "city").crop((240, 220, 1360, 870)).resize((800, 464), Image.LANCZOS),
                       f"{text}  snow city road = ami_road_local (default)")
                 for text, side in (("before (alpha.7)", "b"), ("after (alpha.8)", "a"))]))
stack(rows).save(os.path.join(out, "2_snow_city.png"))

# コンクリートの粒（切り抜きの位置は #134 の concrete_montage.py と同じ）
W, H, SCALE = 60, 44, 6
ROWS = (
    (("rail wall", "base_wall", 880, 335), ("road wall", "base_wall", 280, 553)),
    (("rail pier", "elev_pier", 598, 160), ("road pier", "elev_pier", 52, 430)),
    (("rail elevated girder", "elev_pier", 880, 270), ("road elevated girder", "elev_pier", 280, 510)),
    (("rail bridge ramp", "bridge", 1445, 590), ("road bridge ramp", "bridge", 190, 522)),
    (("tunnel portal", "tunnel", 590, 352), None),
    (("straddle beam", "monorail", 690, 555), None),
    (("suspended beam", "monorail", 30, 590), None),
    (("turntable apron", "turntable", 794, 553), None),
)


def cell(spec, folder, end):
    if not spec:
        return Image.new("RGB", (W * SCALE, H * SCALE + 16), (255, 255, 255))
    name, view, x, y = spec
    return label(shot(folder, view).crop((x, y, x + W, y + H)).resize((W * SCALE, H * SCALE), Image.NEAREST),
                 f"{name} {end}  x={x} y={y}")


stack([row([cell(left, con_b, "before"), cell(left, con_a, "after"), cell(right, con_a, "after")])
       for left, right in ROWS]).save(os.path.join(out, "6_concrete_grain.png"))


def zoom(name, kind, *specs):
    subprocess.run([sys.executable, "-X", "utf8", COMPARE, os.path.join(root, "b_" + kind), os.path.join(root, "a_" + kind),
                    os.path.join(out, name), *specs], check=True)


zoom("1_white_line.png", "old", "temperate_slope2_road:859,450,28,16,14", "temperate_bridge:858,194,28,16,14",
     "temperate_bridge_end:986,515,28,16,14", "temperate_diagonal_road:986,194,28,16,14",
     "temperate_elevated:1500,642,28,16,14", "snow_slope2_road:850,444,100,30,8")
zoom("3_snow_base.png", "new", "snow_local_base_single:300,585,60,36,8", "snow_general_base_single:330,600,60,36,8",
     "snow_trunk_base_single:330,598,60,36,8", "snow_expressway_base_single:330,598,60,36,8",
     "snow_trunk_base_front:330,598,60,36,8")
zoom("4_tram.png", "new", "temperate_tram_boundary_ew:645,455,90,50,8", "temperate_tram_boundary_ew:1045,645,90,50,8",
     "temperate_tram_boundary_ns:690,655,90,50,8", "temperate_tram_boundary_ns:1060,465,90,50,8",
     "snow_tram_boundary_ew:645,455,90,50,8", "temperate_tram_depot_w:915,565,90,50,8", "snow_tram_depot_n:815,570,90,50,8")
zoom("5_no_regression.png", "old", "temperate_slope_road:866,462,60,32,6", "temperate_slope2_road:866,430,60,32,6",
     "temperate_slope_road:735,430,60,32,6", "temperate_bridge_slope2:1140,730,60,48,6", "temperate_stop:855,490,60,40,6")

# 拡大した所の全体（半分に縮め、切り抜きの場所を赤い枠で示す）
WHERE = (("old", "temperate_slope2_road", [(859, 450, 28, 16), (866, 430, 60, 32)]),
         ("old", "temperate_diagonal_road", [(986, 194, 28, 16)]),
         ("new", "snow_local_base_single", [(300, 585, 60, 36)]),
         ("new", "temperate_tram_boundary_ew", [(645, 455, 90, 50), (1045, 645, 90, 50)]),
         ("new", "temperate_tram_depot_w", [(915, 565, 90, 50)]))
rows = []
for kind, view, boxes in WHERE:
    pair = []
    for text, side in (("before (alpha.7)", "b_"), ("after (alpha.8)", "a_")):
        im = shot(os.path.join(root, side + kind), view)
        draw = ImageDraw.Draw(im)
        for x, y, w, h in boxes:
            draw.rectangle((x - 3, y - 3, x + w + 3, y + h + 3), outline=(255, 0, 0), width=4)
        pair.append(label(im.crop((0, 48, 1600, 878)).resize((800, 415), Image.LANCZOS), f"{text}  {view}"))
    rows.append(row(pair))
stack(rows).save(os.path.join(out, "0_where.png"))
