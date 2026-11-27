"""#207: ship.md・air.md・river.md のコードブロックをそのまま dat にし、仮の形の画像を作って makeobj で組む。MIT License。

リポジトリの直下で `python -X utf8 docs/records/2026-11-27_spec-ship-air-screens/page_dat.py`（Pillow と、PATH の makeobj が要る）。
組んだ物は一時フォルダに置く。各行は「ページ・例の番号・終了コード・Warning と ERROR の行・組んだ物」。
"""
import os
import re
import subprocess
import tempfile

from PIL import Image

out = tempfile.mkdtemp()
# (画像の名前, 列, 行, セル)
for name, cols, rows, cell in (("ferry", 8, 1, 512), ("pier", 4, 2, 256), ("plane", 8, 1, 512), ("taxiway", 4, 5, 256),
                               ("hangar", 4, 3, 256), ("river", 8, 6, 256)):
    img = Image.new("RGBA", (cell * cols, cell * rows), (0, 0, 0, 0))
    for r in range(rows):
        for i in range(cols):
            x, y = i * cell + cell // 2, r * cell + cell // 2
            img.paste((200, 100, 50, 255), (x, y, x + 40, y + 20))
    img.save(os.path.join(out, name + ".png"))
for page in ("ship", "air", "river"):
    text = open("site/spec/%s.md" % page, encoding="utf-8").read()
    for i, block in enumerate(re.findall(r"^```\n(.*?)^```", text, re.S | re.M)):
        dat = "%s_%d.dat" % (page, i)
        with open(os.path.join(out, dat), "w", encoding="utf-8", newline="\n") as f:
            f.write(block)
        r = subprocess.run(["makeobj", "pak256", "x.%s%d.pak" % (page, i), dat], cwd=out, capture_output=True)
        log = (r.stdout + r.stderr).decode(errors="replace")
        bad = [ln for ln in log.splitlines() if "warning" in ln.lower() or "error" in ln.lower()]
        packed = [ln.strip() for ln in log.splitlines() if "packing" in ln]
        print(page, i, r.returncode, bad, packed)
