"""#205: vehicle-road.md・citycar.md・pedestrian.md のコードブロックをそのまま dat にし、仮の形の画像を作って makeobj で組む。

リポジトリの直下で `python -X utf8 docs/records/2026-11-27_spec-road-vehicles-screens/page_dat.py`（Pillow と、PATH の makeobj が要る）。
組んだ物は一時フォルダに置く。各行は「ページ・例の番号・終了コード・Warning と ERROR の行・組んだ物」。
"""
import os
import re
import subprocess
import tempfile

from PIL import Image

out = tempfile.mkdtemp()
for name, rows in (("bus", 1), ("truck", 2), ("car", 1), ("walker", 1)):
    img = Image.new("RGBA", (256 * 8, 256 * rows), (0, 0, 0, 0))
    for r in range(rows):
        for i in range(8):
            img.paste((200, 100, 50, 255), (i * 256 + 128, r * 256 + 128, i * 256 + 168, r * 256 + 148))
    img.save(os.path.join(out, name + ".png"))
for page in ("vehicle-road", "citycar", "pedestrian"):
    text = open("site/spec/%s.md" % page, encoding="utf-8").read()
    for i, block in enumerate(re.findall(r"^```\n(.*?)^```", text, re.S | re.M)):
        dat = "%s_%d.dat" % (page, i)
        with open(os.path.join(out, dat), "w", encoding="utf-8", newline="\n") as f:
            f.write(block)
        r = subprocess.run(["makeobj", "pak256", "x.%s%d.pak" % (page, i), dat], cwd=out, capture_output=True)
        log = (r.stdout + r.stderr).decode(errors="replace")
        bad = [l for l in log.splitlines() if "warning" in l.lower() or "error" in l.lower()]
        packed = [l.strip() for l in log.splitlines() if "packing" in l]
        print(page, i, r.returncode, bad, packed)
