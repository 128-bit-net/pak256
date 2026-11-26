"""#134: concrete_scene.py の前後の画面から、コンクリートの面を同じ大きさで切り抜いて拡大し、並べる。切り抜きの前後の違う画素も出す。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_ami333-screens/concrete_montage.py <前の版の出力> <後の版の出力> <出力の PNG>
左の列が tiled_concrete_material の物の前の版（alpha.6）、中の列が後の版（alpha.7）、右の列が道路のコンクリート
（noisy_material）の物の後の版（比べる相手が無い所は空き）。
"""
import os
import sys

from PIL import Image, ImageChops, ImageDraw

before, after, out = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, SCALE = 60, 44, 6
# (左の名前, 画面, x, y), (右の名前, 画面, x, y) または None
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


def crop(folder, view, x, y):
    return Image.open(os.path.join(folder, view + ".png")).convert("RGB").crop((x, y, x + W, y + H))


def cell(spec, folder, label_end):
    canvas = Image.new("RGB", (W * SCALE, H * SCALE + 16), (255, 255, 255))
    if spec:
        label, view, x, y = spec
        canvas.paste(crop(folder, view, x, y).resize((W * SCALE, H * SCALE), Image.NEAREST), (0, 16))
        ImageDraw.Draw(canvas).text((4, 2), f"{label} {label_end}  {view} x={x} y={y}", fill=(0, 0, 0))
    return canvas


sheet = Image.new("RGB", (W * SCALE * 3 + 24, len(ROWS) * (H * SCALE + 24)), (255, 255, 255))
for i, (left, right) in enumerate(ROWS):
    top = i * (H * SCALE + 24)
    old = left if left[1] != "turntable" else None  # alpha.6 に転車台は無い
    sheet.paste(cell(old, before, "before"), (0, top))
    sheet.paste(cell(left, after, "after"), (W * SCALE + 12, top))
    sheet.paste(cell(right, after, "after"), (W * SCALE * 2 + 24, top))
    if old:
        diff = ImageChops.difference(crop(before, *old[1:]), crop(after, *old[1:]))
        print(f"{old[0]}: 違う範囲 {diff.getbbox()}、最大の差 {max(e[1] for e in diff.getextrema())}")
sheet.save(out)
