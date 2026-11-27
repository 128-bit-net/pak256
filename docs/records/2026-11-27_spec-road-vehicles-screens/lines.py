"""#205: AMI の生活道路（ami_road_local）の東西の直線の画像から、白線の位置を測る。

リポジトリの直下で、先に tools/build.py を流してから `python -X utf8 docs/records/2026-11-27_spec-road-vehicles-screens/lines.py`。
出力は、道路の端から白線までの距離（タイルの単位と 1/256 タイル）の範囲。
"""
import subprocess
import sys
import tempfile
import glob

from PIL import Image

out = tempfile.mkdtemp()
subprocess.run([sys.executable, "-X", "utf8", "tools/pakimage.py", "export", "ami_road_local:2/10", "-o", out], check=True,
               stdout=subprocess.DEVNULL)
path = glob.glob(out + "/*.png")[0]
im = Image.open(path).convert("RGBA")
# 書き出した絵はセル（256x256）の座標。大きさが違うときは止める
assert im.size == (256, 256), im.size
sides = {-1: [], 1: []}
for sy in range(256):
    for sx in range(256):
        r, g, b, a = im.getpixel((sx, sy))
        if a == 255 and min(r, g, b) >= 200:
            # 地面の座標（タイルの中心が原点）。東西の道路なので y が道路に直交する
            y = ((sy + 0.5 - 192) / 64 - (sx + 0.5 - 128) / 128) / 2
            sides[1 if y > 0 else -1].append(0.5 - abs(y))
for side, v in sides.items():
    v.sort()
    lo, hi = v[len(v) // 20], v[len(v) * 19 // 20]
    print(side, len(v), "端から %.3f〜%.3f タイル（%.0f〜%.0f /256）" % (lo, hi, lo * 256, hi * 256))
