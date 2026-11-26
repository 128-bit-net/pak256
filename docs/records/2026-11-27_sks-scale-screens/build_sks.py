"""MIT License。SKS（CC0）の ATR と新日本海フェリーを、256 の地図に置く版（そのまま x1 と 2 倍 x2）に組み直す（#164）。
絵と dat は scratchpad にだけ書く。使い方: python -X utf8 build_sks.py <_ref_sks> <出す先>

基準点: pak128 の車両の基準点は 128 のマスの (64,96)（SNF は位置合わせ -128,-96 なので 384 のマスの (192,192)）。
256 の地図の基準点 (128,192) に合わせて置き直す。画素は x1 はそのまま、x2 は最近傍で 2 倍。
"""
import os
import re
import subprocess
import sys

from PIL import Image

REF, OUT = sys.argv[1], sys.argv[2]
DIRS = ["S", "E", "SE", "SW", "N", "W", "NW", "NE"]
os.makedirs(os.path.join(OUT, "pak"), exist_ok=True)


def blocks(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for b in re.split(r"(?m)^-{5,}.*$", f.read()):
            d = dict(line.strip().split("=", 1) for line in b.splitlines() if "=" in line and not line.startswith("#"))
            if "name" in d:
                yield d


def build(tag, src_dat, src_png, name, new_name, src_cell, k):
    d = next(b for b in blocks(src_dat) if b["name"] == name)
    row = int(d["EmptyImage[S]"].split(",")[0].split(".")[-2])
    sheet = Image.open(src_png).convert("RGBA")
    ship = src_cell == 384
    cell = 768 if ship else 256
    out = Image.new("RGBA", (cell * 8, cell), (0, 0, 0, 0))
    for i, direction in enumerate(DIRS):
        r, c = (int(v) for v in d[f"EmptyImage[{direction}]"].split(",")[0].split(".")[-2:])
        im = sheet.crop((c * src_cell, r * src_cell, (c + 1) * src_cell, (r + 1) * src_cell))
        if k == 2:
            im = im.resize((src_cell * 2, src_cell * 2), Image.NEAREST)
        pos = (0, 0) if k == 2 else ((192, 192) if ship else (64, 96))
        out.paste(im, (i * cell + pos[0], pos[1]))
    folder = os.path.join(OUT, "src", new_name)
    os.makedirs(folder, exist_ok=True)
    out.save(os.path.join(folder, new_name + ".png"))
    lines = ["obj=vehicle", f"name={new_name}", "copyright=sika_sen_be"]
    for key in ("intro_year", "intro_month", "waytype", "engine_type", "freight", "payload", "speed", "cost",
                "weight", "power", "gear", "runningcost", "length", "loading_time"):
        if key in d:
            lines.append(f"{key}={d[key]}")
    lines = [("intro_year=1900" if x.startswith("intro_year") else x) for x in lines]  # 保存データの年（1930 年代）で買えるように
    offset = ",-256,-192" if ship else ""
    lines += [f"EmptyImage[{direction}]={new_name}.0.{i}{offset}" for i, direction in enumerate(DIRS)]
    with open(os.path.join(folder, new_name + ".dat"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    pak = os.path.join(OUT, "pak", f"vehicle.{new_name}.pak")
    r = subprocess.run(["makeobj", f"pak{cell}", pak, folder.replace(os.sep, "/") + "/"], capture_output=True)
    log = (r.stdout + r.stderr).decode("utf-8", "replace")
    bad = [x for x in log.splitlines() if "Warning" in x or "ERROR" in x]
    print(new_name, "row", row, "cell", cell, "ok" if os.path.exists(pak) and not bad else bad or log)


atr = os.path.join(REF, "SKS_ATR_ver1", "source")
snf = os.path.join(REF, "SKS_SNF_ver1.1", "source")
for k in (1, 2):
    for short, name in (("atr42", "SKS_JAC_ATR42_600_1_2nd"), ("atr72", "SKS_JAC_ATR72_600_1_2nd")):
        build("atr", os.path.join(atr, "SKS_ATR_1.dat"), os.path.join(atr, "SKS_ATR_1.png"), name, f"sks_{short}_x{k}", 128, k)
    build("snf", os.path.join(snf, "SKS_SNF_1_size384.dat"), os.path.join(snf, "SKS_SNF_1_size384.png"), "SKS_SNF_Akashia",
          f"sks_ferry_x{k}", 384, k)
