"""大きさ違い（h10・h16・h24）と向き色の印（marker）の歩行者を組み、build/pak の写しの歩行者だけを差し替えた
pak のフォルダを work/var172/<名前>/pak に作る（#172）。MIT License。
使い方（リポジトリの直下から。先に tools/build.py）: python -X utf8 docs/records/2026-11-27_pedestrians-screens/variants.py"""
import os
import shutil
import subprocess
import sys

sys.path.insert(0, "tools")
import datgen  # noqa: E402

VARIANTS = {"h10": ["--adult", "10"], "h16": ["--adult", "16"], "h24": ["--adult", "24"], "marker": ["--marker", "--adult", "24"]}
for name, args in VARIANTS.items():
    src = os.path.join("work", "var172", name, "src")
    pak = os.path.join("work", "var172", name, "pak")
    shutil.rmtree(os.path.join("work", "var172", name), ignore_errors=True)
    os.makedirs(src)
    shutil.copytree(os.path.join("build", "pak"), pak)
    subprocess.run([sys.executable, "-X", "utf8", "objects/pedestrian/walkers/draw_pedestrians.py", "--out", src] + args, check=True)
    with open(os.path.join(src, "walkers.dat"), "w", encoding="utf-8", newline="\n") as f:
        f.write(datgen.yaml_to_dat(os.path.join(src, "walkers.yaml")))
    r = subprocess.run([os.environ.get("MAKEOBJ", "makeobj"), "pak256", os.path.join(pak, "pedestrian.walkers.pak"),
                        src.replace(os.sep, "/") + "/walkers.dat"], capture_output=True, text=True, errors="replace")
    bad = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.startswith(("Warning", "ERROR"))]
    if r.returncode or bad:
        sys.exit(f"{name}: {bad}")
    print(name, "ok")
