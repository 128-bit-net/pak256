"""#204: vehicle-rail.md のコードブロックをそのまま dat にし、仮の形の画像を作って makeobj で組む。

リポジトリの直下で `python -X utf8 docs/records/2026-11-27_spec-rail-vehicles-screens/page_dat.py`（Pillow と、PATH の makeobj が要る）。
組んだ物は一時フォルダに置く。各行は「例の番号・終了コード・Warning と ERROR の行・組んだ物」。
"""
import os
import re
import subprocess
import tempfile

from PIL import Image

out = tempfile.mkdtemp()
text = open("site/spec/vehicle-rail.md", encoding="utf-8").read()
blocks = re.findall(r"^```\n(.*?)^```", text, re.S | re.M)
for name, cell in (("railcar", 512), ("trailer", 512), ("tramcar", 256)):
    img = Image.new("RGBA", (cell * 8, cell), (0, 0, 0, 0))
    for i in range(8):
        img.paste((200, 100, 50, 255), (i * cell + cell // 2, cell // 2, i * cell + cell // 2 + 40, cell // 2 + 20))
    img.save(os.path.join(out, name + ".png"))
for i, block in enumerate(blocks):
    with open(os.path.join(out, "ex%d.dat" % i), "w", encoding="utf-8", newline="\n") as f:
        f.write(block)
    r = subprocess.run(["makeobj", "pak256", "vehicle.ex%d.pak" % i, "ex%d.dat" % i], cwd=out, capture_output=True)
    log = (r.stdout + r.stderr).decode(errors="replace")
    bad = [l for l in log.splitlines() if "warning" in l.lower() or "error" in l.lower()]
    packed = [l.strip() for l in log.splitlines() if "packing" in l]
    print(i, r.returncode, bad, packed)
