"""車両の画面の上の大きさを、pak256 と pak128・pak128.Japan の絵（PNG）から同じやり方で測る（#104）。MIT License。

使い方: python -X utf8 vehicle_sizes.py <pak128 のソース> <pak128.Japan のソース> <出す先>
手本の絵は読むだけで、このリポジトリに置かない。出す先（git 管理外）に表（sizes.md）と、1 タイルの幅をそろえた切り抜き（compare_*.png）を書く。

測り方（元の絵の不透明な画素の外接枠。dat の位置合わせは大きさに効かない）:
- 横向き = dat の向き sw（画面で水平に進む）。外接枠の横 = 長さ。
- 正面向き = se（画面で縦に進む）。外接枠の横 = 幅。
- 高さ = 横向きの外接枠の縦 − 幅の半分（横向きでは、幅が画面の縦に半分の長さで写るため）。車輪・屋根の丸み・張り出しを含む概算。
- 斜め = e（道路の軸に沿う向き）の外接枠（横 x 縦）も出す。
"""
import glob
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")
REF128, REFJP, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FONT = "C:/Windows/Fonts/meiryo.ttc"
CLEAR = (231, 255, 255)  # makeobj の透明の色

# (種類, pak の名前, 物の name)
LIST = [
    ("路線バス", "pak256", "pak256_bus"),
    ("路線バス", "pak128", "S_Kroytor_Ikarus-260"),
    ("路線バス", "pak128", "Man_Lions_City"),
    ("路線バス", "128JP", "yoshi_isuzu_bx341"),
    ("路線バス", "128JP", "yoshi_volvo_b10m_m"),
    ("小型トラック（郵便）", "pak256", "pak256_mail_truck"),
    ("小型トラック（郵便）", "pak128", "Mail_Truck_2"),
    ("小型トラック（郵便）", "pak128", "PMNV_Mail_Truck_1"),
    ("小型トラック（郵便）", "128JP", "128_RVg_Type_S_Post"),
    ("普通のトラック", "pak256", "pak256_coal_truck"),
    ("普通のトラック", "pak128", "Bulk_Truck_2"),
    ("普通のトラック", "pak128", "Goods_Truck_0"),
    ("普通のトラック", "128JP", "yoshi_isuzu_piggy_truck"),
    ("普通のトラック", "128JP", "128_RVg_Type_S_Bulk"),
    ("気動車・電車", "pak256", "pak256_railcar"),
    ("気動車・電車", "pak256", "pak256_railcar_trailer"),
    ("気動車・電車", "pak128", "Haru_VT98"),
    ("気動車・電車", "pak128", "TMB_Class_100"),
    ("気動車・電車", "128JP", "yoshi_kiha35_m"),
    ("気動車・電車", "128JP", "yoshi_kiha120"),
    ("気動車・電車", "128JP", "yoshi_kumoha103"),
]
TILE = {"pak256": 256, "pak128": 128, "128JP": 128}


def objects(path):
    """dat の中の物（区切りは - の行）を {キー: 値} で返す。キーは小文字。"""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    for block in re.split(r"(?m)^-.*$", text):
        d = {}
        for line in block.splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                d[k.strip().lower()] = v.strip()
        if "name" in d:
            yield d


def find_ref(folder, name):
    for path in glob.glob(os.path.join(folder, "**", "*.dat"), recursive=True):
        for d in objects(path):
            if d["name"] == name:
                return path, d
    raise SystemExit(f"{name} が無い: {folder}")


def ref_sprite(path, value, cell):
    """"[./dir/]file.row.col[,x,y]" の絵を切る。"""
    ref = value.split(",")[0].strip()
    stem, row, col = ref.rsplit(".", 2)
    png = os.path.normpath(os.path.join(os.path.dirname(path), stem + ".png"))
    im = Image.open(png).convert("RGBA")
    return im.crop((int(col) * cell, int(row) * cell, (int(col) + 1) * cell, (int(row) + 1) * cell))


def own_sprites(name):
    """pak256 の表（yaml）から length と向きごとの絵を読む。"""
    import yaml
    for path in glob.glob(os.path.join(ROOT, "objects", "vehicle", "**", "*.yaml"), recursive=True):
        with open(path, encoding="utf-8") as f:
            d = yaml.safe_load(f)
        if d.get("name") == name:
            cell = d.get("cell_size", 256)
            imgs = {k: ref_sprite(path, v, cell) for k, v in d["emptyimage"].items()}
            return d["length"], imgs
    raise SystemExit(f"{name} が無い")


def trim(im):
    """透明の色と α = 0 を抜いて、不透明な画素の外接枠で切る。"""
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            if px[x, y][3] and px[x, y][:3] == CLEAR:
                px[x, y] = (0, 0, 0, 0)
    box = im.getchannel("A").point(lambda a: 255 if a > 127 else 0).getbbox()
    return im.crop(box)


rows = []
for kind, pak, name in LIST:
    if pak == "pak256":
        length, imgs = own_sprites(name)
        imgs = {k: imgs[k] for k in ("sw", "se", "e")}
    else:
        path, d = find_ref(REF128 if pak == "pak128" else REFJP, name)
        length = int(d.get("length", 8))
        imgs = {k: ref_sprite(path, d[f"emptyimage[{k}]"], 128) for k in ("sw", "se", "e")}
    imgs = {k: trim(v) for k, v in imgs.items()}
    L, W = imgs["sw"].width, imgs["se"].width
    H = imgs["sw"].height - W / 2
    rows.append(dict(kind=kind, pak=pak, name=name, length=length, L=L, W=W, H=H, imgs=imgs, t=TILE[pak]))

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "sizes.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("| 種類 | 物の名前 | pak | length | 長さ px | 幅 px | 高さ px | 長さ %タイル | 幅 %タイル | 高さ %タイル | 斜め(e) px |\n")
    f.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        t = r["t"]
        f.write(f"| {r['kind']} | {r['name']} | {r['pak']} | {r['length']} | {r['L']} | {r['W']} | {r['H']:.0f} | "
                f"{r['L'] / t:.0%} | {r['W'] / t:.0%} | {r['H'] / t:.0%} | {r['imgs']['e'].width}x{r['imgs']['e'].height} |\n")

F = ImageFont.truetype(FONT, 16)
ground = (96, 130, 70)
for i, kind in enumerate(dict.fromkeys(r["kind"] for r in rows)):
    group = [r for r in rows if r["kind"] == kind]
    cw = 270 if i < 3 else 360
    out = Image.new("RGB", (cw * len(group), 400), ground)
    d = ImageDraw.Draw(out)
    for j, r in enumerate(group):
        x = j * cw
        k = 256 // r["t"]  # 1 タイルの幅を 256px にそろえる
        d.text((x + 8, 6), f"{r['pak']} length {r['length']}\n{r['name']}\n長 {r['L'] / r['t']:.0%} 幅 {r['W'] / r['t']:.0%} 高 {r['H'] / r['t']:.0%}",
               font=F, fill=(255, 255, 255))
        for key, base in (("sw", 170), ("se", 270), ("e", 390)):
            s = r["imgs"][key]
            s = s.resize((s.width * k, s.height * k), Image.NEAREST)
            out.paste(s, (x + (cw - s.width) // 2, base - s.height), s)
        d.line([(x, 0), (x, 400)], fill=(255, 255, 255))
    out.save(os.path.join(OUT, f"compare_{i + 1}.png"))
    print(kind, f"compare_{i + 1}.png")
