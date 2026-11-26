"""PR と記録の画像を作る（#172）。MIT License。scene.py が撮った画面（work/ の下。git に入れない）から切り出す。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-27_pedestrians-screens/figures.py <scene.py の出力の親（work）> <出力>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "objects/pedestrian/walkers")
sys.path.insert(0, "tools")
import draw_pedestrians as D  # noqa: E402

work, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
FONT = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 22)
CX, CY = 895, 576  # 飛んだタイルの中心（scene.py と同じ）


def crop(path, box):
    """タイルの中心からの範囲 (x0, y0, x1, y1) を切り出す。"""
    im = Image.open(os.path.join(work, path)).convert("RGB")
    return im.crop((CX + box[0], CY + box[1], CX + box[2], CY + box[3]))


def labeled(im, text, scale=2):
    im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    page = Image.new("RGB", (im.width, im.height + 36), (255, 255, 255))
    page.paste(im, (0, 36))
    ImageDraw.Draw(page).text((6, 2), text, font=FONT, fill=(0, 0, 0))
    return page


def stack(pages, path, horizontal=False):
    w = sum(p.width for p in pages) + 8 * (len(pages) - 1) if horizontal else max(p.width for p in pages)
    h = max(p.height for p in pages) if horizontal else sum(p.height for p in pages) + 8 * (len(pages) - 1)
    page = Image.new("RGB", (w, h), (255, 255, 255))
    x = y = 0
    for p in pages:
        page.paste(p, (x, y))
        if horizontal:
            x += p.width + 8
        else:
            y += p.height + 8
    page.save(os.path.join(out, path), optimize=True)


# 1. 大きさ違いを同じ画面の同じ位置に貼った比べ（地は 10px の回の撮影。人は絵をそのまま貼る）
SIZE_BOX = (-40, -90, 220, 60)  # バス停・郵便のトラック・建物が入る範囲
base_path = "scene_h10/temperate_meet_00.png"
pages = []
for adult, label in ((10, "10px（実物の大きさ。大人 約1.7m）"), (16, "16px（中間）"), (24, "24px（手本の2倍。車両と同じ扱い）")):
    base = Image.open(os.path.join(work, base_path)).convert("RGBA")
    # 停留所の先の路肩の 3 か所（画面の座標）。男性・女性・子ども
    for spec, (fx, fy) in zip(D.WALKERS, ((1037, 588), (1059, 599), (1081, 610))):
        for (x, y), color in D.draw_figure(spec, "e", adult).px.items():
            base.putpixel((fx + x, fy - y), color + (255,))
    box = (CX + SIZE_BOX[0], CY + SIZE_BOX[1], CX + SIZE_BOX[2], CY + SIZE_BOX[3])
    pages.append(labeled(base.convert("RGB").crop(box), label, 3))
stack(pages, "1_size_compare.png")

# 2. 入れる大きさ（16px）がゲームで歩いた画面。温帯の停留所のそば
stack([labeled(crop("scene_h16/temperate_meet_03.png", (-200, -120, 200, 100)), "温帯（バス停とバス）"),
       labeled(crop("scene_h16/temperate_meet_05.png", (-200, -120, 200, 100)), "温帯（バス・郵便のトラック）")],
      "2_temperate.png")

# 3. 雪の気候
stack([labeled(crop("scene_h16/snow_03.png", (-320, -220, 0, -10)), "雪の気候（バス停のそば）"),
       labeled(crop("scene_h16/snow_meet_05.png", (-40, -90, 260, 90)), "雪の気候（郵便のトラックと建物）")], "3_snow.png")
