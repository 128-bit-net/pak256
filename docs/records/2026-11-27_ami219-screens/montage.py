"""#219 の撮った画面を、前（alpha.9）と後（alpha.10）を並べた画像にする。MIT License。
使い方（リポジトリの直下で）: python -X utf8 docs/records/2026-11-27_ami219-screens/montage.py <shot_before> <shot_after> <出力フォルダ>
5_names.png は、第 4 引数に names.py の出力フォルダ（ja・en の両方）を渡したときに作る。
入力は scene.py の撮った画面（1600x900、拡大 3 の等倍）。見出しの座標は flat_512_left_v64 の位置（温暖の原点 (60,60)・降雪の原点 (316,60)）。"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

before, after, out = sys.argv[1], sys.argv[2], sys.argv[3]
names = sys.argv[4] if len(sys.argv) > 4 else None
os.makedirs(out, exist_ok=True)
FONT = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 15)
LOOP = (350, 130, 1450, 870)
DEPOT = (576, 250, 1216, 720)


def pairs(name, rows, box):
    """rows = [(画面の名前, 見出し)]。左が alpha.9、右が alpha.10。"""
    w, h = box[2] - box[0], box[3] - box[1]
    img = Image.new("RGB", (w * 2 + 4, (h + 24) * len(rows)), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, (shot, title) in enumerate(rows):
        for j, (folder, ver) in enumerate(((before, "alpha.9"), (after, "alpha.10"))):
            x, y = j * (w + 4), i * (h + 24)
            d.text((x + 4, y + 2), f"{ver}　{title}", fill=(255, 230, 80), font=FONT)
            img.paste(Image.open(os.path.join(folder, shot + ".png")).convert("RGB").crop(box), (x, y + 24))
    img.save(os.path.join(out, name), optimize=True)


pairs("1_catenary.png", (
    ("temperate_loop_local", "温暖　生活道路の輪 (60,60)-(63,63)"),
    ("temperate_loop_general", "温暖　一般道路の輪 (68,60)-(71,63)"),
    ("temperate_loop_ground", "温暖　専用の軌道の輪 (76,60)-(79,63)"),
    ("snow_loop_local", "降雪　生活道路の輪 (316,60)-(319,63)"),
), LOOP)
pairs("2_maglev_depot.png", (
    ("temperate_guideway_west_depot", "温暖　超電導の車庫 (60,74)"),
    ("temperate_tube_west_depot", "温暖　チューブ式の車庫 (60,82)"),
    ("temperate_tube_north_depot", "温暖　チューブ式の車庫 (72,80)"),
    ("temperate_guideway_elev_west_depot", "温暖　高架の超電導の車庫 (60,90)"),
    ("temperate_tube_elev_south_depot", "温暖　高架のチューブ式の車庫 (76,99)"),
    ("snow_guideway_south_depot", "降雪　超電導の車庫 (332,75)"),
), DEPOT)
pairs("3_maglev_end.png", (
    ("temperate_guideway_west_end", "温暖　超電導の行き止まり (63,74)"),
    ("temperate_guideway_east_end", "温暖　超電導の行き止まり (66,74)"),
    ("temperate_guideway_north_end", "温暖　超電導の行き止まり (72,75)"),
    ("temperate_guideway_south_end", "温暖　超電導の行き止まり (76,72)"),
    ("temperate_guideway_elev_west_end", "温暖　高架の超電導の行き止まり (63,90)"),
    ("snow_guideway_north_end", "降雪　超電導の行き止まり (328,75)"),
    ("temperate_tube_west_end", "温暖　チューブ式の行き止まり (63,82)"),
    ("temperate_tube_south_end", "温暖　チューブ式の行き止まり (76,80)"),
), DEPOT)

# 行き止まりの崩れ（alpha.10）: 4 倍に拡大して、前と違う所を赤い枠で囲む
ZOOM = (("temperate_guideway_west_end", "超電導 (63,74)", (790, 505, 940, 600)),
        ("temperate_guideway_north_end", "超電導 (72,75)", (835, 520, 985, 615)))
img = Image.new("RGB", (600 * 2 + 4, (380 + 24) * len(ZOOM)), (0, 0, 0))
d = ImageDraw.Draw(img)
for i, (shot, title, box) in enumerate(ZOOM):
    for j, (folder, ver) in enumerate(((before, "alpha.9"), (after, "alpha.10"))):
        x, y = j * 604, i * 404
        d.text((x + 4, y + 2), f"{ver}　温暖　{title}　4 倍", fill=(255, 230, 80), font=FONT)
        img.paste(Image.open(os.path.join(folder, shot + ".png")).convert("RGB").crop(box).resize((600, 380), Image.NEAREST), (x, y + 24))
img.save(os.path.join(out, "4_end_defect.png"), optimize=True)

if names:  # 名前が画面に出る窓（左上の 520x444）を、日本語と英語で並べる
    box = (0, 58, 520, 502)
    w, h = box[2] - box[0], box[3] - box[1]
    img = Image.new("RGB", (w * 2 + 4, (h + 24) * 2), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, (lang, label) in enumerate((("ja", "日本語"), ("en", "英語"))):
        for j, (kind, title) in enumerate((("road_info", "一般道路の情報窓 (42,100)"), ("curiosity", "名所の窓（盛土の建物）"))):
            x, y = j * (w + 4), i * (h + 24)
            d.text((x + 4, y + 2), f"{label}　{title}", fill=(255, 230, 80), font=FONT)
            img.paste(Image.open(os.path.join(names, f"{lang}_{kind}.png")).convert("RGB").crop(box), (x, y + 24))
    img.save(os.path.join(out, "5_names.png"), optimize=True)
