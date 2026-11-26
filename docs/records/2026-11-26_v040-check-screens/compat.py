"""run1.py・run2.py・run2_log.py・run3.py が撮った画像から、記録の compat.png・convoys.png・convoys_loaded.png を作る。MIT License（Pillow が要る）。
使い方: python -X utf8 docs/records/2026-11-26_v040-check-screens/compat.py work/a04 <出力フォルダ>"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

src, dst = sys.argv[1], sys.argv[2]
FONT = ImageFont.truetype("meiryo.ttc", 18)


def load(name, box):
    return Image.open(os.path.join(src, name + ".png")).convert("RGB").crop(box)


def panel(name, box, text):
    im = load(name, box)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, d.textlength(text, font=FONT) + 16, 28], fill=(0, 0, 0))
    d.text((8, 2), text, font=FONT, fill=(255, 255, 255))
    return im


TRUCK = (640, 340, 1120, 660)
BUS = (660, 280, 1140, 600)
items = [panel("v031_ami_stop", TRUCK, "v0.3.1: 荷役所 (70,75)"), panel("v040_ami_stop", TRUCK, "読み込み直後"),
         panel("v040_replaced", TRUCK, "pak256 の荷役所を置き直し"),
         panel("v031_ami_bus", BUS, "v0.3.1: バス停 (55,75)"), panel("v040_ami_bus", BUS, "読み込み直後（名札の跡）"),
         panel("v040_label_after", BUS, "pak256 のバス停を置き直し")]
w, h = items[0].size
out = Image.new("RGB", (w * 3 + 12, h * 2 + 6), (255, 255, 255))
for i, im in enumerate(items):
    out.paste(im, ((i % 3) * (w + 6), (i // 3) * (h + 6)))
out.save(os.path.join(dst, "compat.png"), optimize=True)


def window(name):
    """編成一覧の窓を切り抜く。窓はマウスの位置に出るので、窓の地の色の範囲を探す。"""
    im = Image.open(os.path.join(src, name + ".png")).convert("RGB")
    body = (208, 232, 240)
    mask = Image.new("1", im.size)
    mask.putdata([p == body for p in im.getdata()])
    # 下の知らせの帯も同じ色なので、除く
    box = mask.crop((0, 48, im.width, 855)).getbbox()
    if box is None:
        sys.exit(f"{name}: 窓が写っていない")
    left, top, right, bottom = box
    return im.crop((max(left - 2, 0), max(top + 48 - 24, 48), right + 2, bottom + 48 + 2))


window("new_convoys").save(os.path.join(dst, "convoys.png"), optimize=True)
window("v040_convoys").save(os.path.join(dst, "convoys_loaded.png"), optimize=True)
