"""#189 の撮った画面を、PR と記録に載せる画像に並べる。MIT License。
使い方（リポジトリの直下で）: python -X utf8 docs/records/2026-11-27_ami189-screens/montage.py <撮った画面の親フォルダ> <出力フォルダ>
<撮った画面の親フォルダ> には new_after・new_before・conc_before・conc_after・seam_before・seam_after・tram_cat・toolbar・nocat・compat がある。
切り抜きは 1600x900 の画面の画素（画面は拡大 3 の等倍）。"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
FONT = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 15)
CENTER = (400, 210, 1200, 690)  # 画面の真ん中の 800x480


def crop(path, box=CENTER, zoom=1):
    im = Image.open(os.path.join(src, path)).convert("RGB").crop(box)
    return im.resize((im.width * zoom, im.height * zoom), Image.NEAREST) if zoom != 1 else im


def sheet(name, items, cols=2):
    """items = [(見出し, 画像)]。同じ大きさの画像を cols 列に並べる。"""
    w, h = items[0][1].size
    rows = (len(items) + cols - 1) // cols
    img = Image.new("RGB", (w * cols + 4 * (cols - 1), (h + 24) * rows), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, (title, im) in enumerate(items):
        x, y = (i % cols) * (w + 4), (i // cols) * (h + 24)
        d.text((x + 4, y + 2), title, fill=(255, 230, 80), font=FONT)
        img.paste(im, (x, y + 24))
    img.save(os.path.join(out, name), optimize=True)


# 座標は温帯の原点 (60,60)・降雪の原点 (316,60) に、new_scene.py のずれを足した物
sheet("1_catenary.png", [
    ("温帯 道路の上の直線 (64,72)", crop("new_after/temperate_cat_road.png")),
    ("温帯 道路の上の曲がり (68,72)", crop("new_after/temperate_cat_corner.png")),
    ("温帯 土の上の十字 (64,80)", crop("new_after/temperate_cat_dirt.png")),
    ("温帯 斜め (78,75)", crop("new_after/temperate_cat_diagonal.png")),
    ("温帯 車庫 (61,86)", crop("new_after/temperate_cat_depot.png")),
    ("降雪 道路の上の直線 (320,72)", crop("new_after/snow_cat_road.png")),
])
T = (650, 330, 950, 580)
sheet("2_tram_run.png", [
    ("道路の直線を走る（2 倍）", crop("tram_cat/road_straight_0.png", T, 2)),
    ("道路の曲がり（2 倍。柱が道路の内側に立つ）", crop("tram_cat/road_corner_0.png", T, 2)),
    ("専用の軌道（2 倍。集電装置の舟が線に届く）", crop("tram_cat/own_straight_0.png", T, 2)),
    ("専用の停留所（2 倍。柱が上屋を貫く）", crop("tram_cat/own_stop_0.png", T, 2)),
])
S = (250, 250, 1550, 880)
sheet("3_snow_curve.png", [
    ("alpha.8 base_single を手で敷く (318,192)", crop("seam_before/base.png", S)),
    ("alpha.9", crop("seam_after/base.png", S)),
    ("alpha.8 街の道路の道具 (318,162)", crop("seam_before/city.png", S)),
    ("alpha.9", crop("seam_after/city.png", S)),
])
sheet("4_concrete.png", [
    (f"{v} {n}", crop(f"conc_{s}/{f}.png"))
    for f, n in (("base_wall", "線路の壁 (64,62)"), ("elev_pier", "高架と橋脚 (64,74)"), ("bridge", "橋 (65,84)"),
                 ("tunnel", "坑口 (64,92)"), ("monorail", "モノレール (64,102)"))
    for s, v in (("before", "alpha.8"), ("after", "alpha.9"))
])
sheet("5_maglev.png", [
    ("超電導とガイド (66,94)", crop("new_after/temperate_maglev_guideway.png")),
    ("超電導の曲がり (68,93)", crop("new_after/temperate_maglev_guideway_corner.png")),
    ("常電導 (66,100)", crop("new_after/temperate_maglev_beam.png")),
    ("チューブ式の曲がり (68,105)", crop("new_after/temperate_maglev_tube_corner.png")),
    ("高架の曲がり (70,113)", crop("new_after/temperate_maglev_elev_corner.png")),
    ("高架（常電導とチューブ） (66,122)", crop("new_after/temperate_maglev_elev_tube.png")),
    ("トンネル (64,130)", crop("new_after/temperate_maglev_tunnel.png")),
    ("車庫 (62,140)。手前に軌道の側壁が重なる", crop("new_after/temperate_maglev_depot.png")),
    ("降雪 超電導 (322,94)", crop("new_after/snow_maglev_guideway.png")),
    ("降雪 チューブ式の曲がり (324,105)", crop("new_after/snow_maglev_tube_corner.png")),
])
sheet("6_scenic_narrow.png", [
    ("環状交差点の路面表示 (66,152)", crop("new_after/temperate_roundabout.png")),
    ("降雪 (322,152)", crop("new_after/snow_roundabout.png")),
    ("説明用の色の線 (82,150)", crop("new_after/temperate_describe.png")),
    ("高架の説明用の線 (82,164)", crop("new_after/temperate_describe_elev.png")),
    ("盛土の建物 (100,152)", crop("new_after/temperate_embankment_building.png")),
    ("降雪 (356,152)", crop("new_after/snow_embankment_building.png")),
    ("狭軌 (66,174)。pak には入る。ツールバーは無い", crop("new_after/temperate_narrow.png")),
])
sheet("7_monorail_corner.png", [
    (f"{v} {n}", crop(f"new_{s}/temperate_monorail_corner_{d}.png"))
    for d, n in (("ne", "北東の曲がり (63,61)"), ("sw", "南西の曲がり (63,66)"), ("se", "南東の曲がり (68,65)"))
    for s, v in (("before", "alpha.8"), ("after", "alpha.9"))
])
def window(name, rows):
    """サブメニューの窓（位置は起動ごとに違う）を、題の帯の色で探して 1400 の幅の黒地に置く。"""
    im = Image.open(os.path.join(src, f"toolbar/{name}.png")).convert("RGB")
    px = im.load()
    pts = [(x, y) for y in range(60, 870) for x in range(im.width)
           if abs(px[x, y][0] - 210) < 8 and abs(px[x, y][1] - 66) < 8 and px[x, y][2] < 10]
    x0, y0, x1 = min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts) + 1
    base = Image.new("RGB", (1400, 175), (0, 0, 0))
    base.paste(im.crop((x0, y0, x1, y0 + 22 + 48 * rows)), (0, 0))
    return base


top = Image.new("RGB", (1400, 175), (0, 0, 0))
top.paste(crop("toolbar/toolbar_edit.png", (0, 0, 1400, 48)), (0, 0))
sheet("8_toolbar.png", [
    ("線路（架線と高架の説明用の線が並ぶ）", window("toolbar_rail", 3)),
    ("路面電車（路面表示・盛土・説明用の線）", window("toolbar_tram", 2)),
    ("リニア（新しい段）", window("toolbar_maglev", 1)),
    ("編集（公共のプレーヤー。左から 5 つ目が足した名所の窓）", window("toolbar_edit", 1)),
    ("上の帯（モノレールの次がリニア）", top),
], cols=1)
d = Image.open(os.path.join(src, "toolbar/curiosity.png")).convert("RGB").crop((400, 70, 940, 530))
d.save(os.path.join(out, "10_curiosity.png"), optimize=True)
sheet("9_catenary_missing.png", [
    ("架線が道路の区間と車庫だけ", crop("nocat/nocat2_list.png", (0, 100, 1600, 900))),
    ("v0.5.0 の保存データを読んで走らせた後", crop("compat/nocat.png", (0, 100, 1600, 900))),
    ("その後に架線を張ると走る", crop("compat/cat.png", (0, 100, 1600, 900))),
    ("v0.5.0 の保存データを読んだ直後", crop("compat/loaded.png", (0, 100, 1600, 900))),
])
