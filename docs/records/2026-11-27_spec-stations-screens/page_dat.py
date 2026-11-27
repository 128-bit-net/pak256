"""#206: station.md・signal.md のコードブロックをそのまま dat にし、仮の形の画像を作って makeobj で組む。MIT License。

リポジトリの直下で `python -X utf8 docs/records/2026-11-27_spec-stations-screens/page_dat.py`（Pillow と、PATH の makeobj が要る）。
組んだ物は一時フォルダに置く。各行は「ページ・例の番号・終了コード・Warning と ERROR の行・組んだ物」。
"""
import os
import re
import subprocess
import tempfile

from PIL import Image

out = tempfile.mkdtemp()
for name, cols, rows in (("station", 8, 3), ("signal", 8, 2)):
    img = Image.new("RGBA", (256 * cols, 256 * rows), (0, 0, 0, 0))
    for r in range(rows):
        for i in range(cols):
            img.paste((200, 100, 50, 255), (i * 256 + 128, r * 256 + 128, i * 256 + 168, r * 256 + 148))
    img.save(os.path.join(out, name + ".png"))
for page in ("station", "signal"):
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
