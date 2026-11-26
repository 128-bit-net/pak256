"""#159: 道の基盤の版（base）の雪の画像で、前の版にあった不透明な画素のうち、後の版で透明になった数を、道ごとに数える。MIT License。

下の端の暗い点線の直し（AMI #360）は、路面の板の切り口を雪の下に隠すために板を内へ寄せ、その下を透明にした。
この数には、狙いどおりに寄せた手前の縁も、隣のタイルが覆わずに地面が透ける所も含まれる（画像 1 枚からは区別しない）。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_ami159-screens/holes_pak.py <前の ami_road.pak> <後の ami_road.pak>
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "2026-11-26_snow-road-seam-screens"))
from pakimg import images, load, pixels, ways  # noqa: E402

before, after = sys.argv[1], sys.argv[2]
bbuf, broot = load(before)
abuf, aroot = load(after)
aobjs = dict(ways(abuf, aroot))
for name, bobj in ways(bbuf, broot):
    if "_base_" not in name:
        continue
    aimg = dict(images(aobjs[name]))
    lost, images_with = 0, {}
    for path, node in images(bobj):
        if path[0] not in (6, 7):
            continue
        b = pixels(bbuf, node[1])
        a = pixels(abuf, aimg[path][1]) if path in aimg else {}
        gone = [xy for xy in b if xy not in a]
        lost += len(gone)
        if gone:
            images_with["/".join(map(str, path))] = len(gone)
    print(name, "抜けた画素", lost, "画像", len(images_with), sorted(images_with.items(), key=lambda kv: -kv[1])[:4])
