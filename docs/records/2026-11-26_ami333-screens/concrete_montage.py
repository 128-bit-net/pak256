"""#134: concrete_scene.py の後の版の画面から、コンクリートの面を同じ大きさで切り抜いて拡大し、並べる。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_ami333-screens/concrete_montage.py <concrete_scene.py の後の版の出力> <出力の PNG>
左の列が tiled_concrete_material の物、右の列が道路のコンクリート（noisy_material）の物（比べる相手が無い所は空き）。
"""
import os
import sys

from PIL import Image, ImageDraw

src, out = sys.argv[1], sys.argv[2]
W, H, SCALE = 60, 44, 6
# (左の名前, 画面, x, y), (右の名前, 画面, x, y) または None
ROWS = (
    (("rail wall", "base_wall", 880, 335), ("road wall", "base_wall", 280, 553)),
    (("rail pier", "elev_pier", 598, 160), ("road pier", "elev_pier", 52, 430)),
    (("tunnel portal", "tunnel", 590, 352), None),
    (("monorail beam", "monorail", 690, 555), None),
    (("turntable apron", "turntable", 794, 553), None),
)


def cell(spec):
    canvas = Image.new("RGB", (W * SCALE, H * SCALE + 16), (255, 255, 255))
    if spec:
        label, view, x, y = spec
        im = Image.open(os.path.join(src, view + ".png")).convert("RGB").crop((x, y, x + W, y + H))
        canvas.paste(im.resize((W * SCALE, H * SCALE), Image.NEAREST), (0, 16))
        ImageDraw.Draw(canvas).text((4, 2), f"{label}  {view} x={x} y={y} x{SCALE}", fill=(0, 0, 0))
    return canvas


sheet = Image.new("RGB", (W * SCALE * 2 + 12, len(ROWS) * (H * SCALE + 24)), (255, 255, 255))
for i, (left, right) in enumerate(ROWS):
    top = i * (H * SCALE + 24)
    sheet.paste(cell(left), (0, top))
    sheet.paste(cell(right), (W * SCALE + 12, top))
sheet.save(out)
