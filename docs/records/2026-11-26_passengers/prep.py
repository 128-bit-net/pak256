"""v0.3.1・v0.4.0 の zip を展開し、街の建物の pak だけを入れ替えた組を作る。MIT License。
使い方: python -X utf8 docs/records/2026-11-26_passengers/prep.py <v0.3.1 の zip> <v0.4.0 の zip> <作業フォルダ>
A = v0.3.1、B = v0.4.0、C = v0.4.0 + v0.3.1 の街の建物、D = v0.3.1 + v0.4.0 の街の建物。"""
import pathlib
import shutil
import sys
import zipfile

v031, v040, out = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
CITY = "city.town_buildings.pak"


def extract(zp, name):
    d = out / name
    with zipfile.ZipFile(zp) as z:
        z.extractall(d / "x")
    pk = d / "build" / "pak"
    pk.mkdir(parents=True, exist_ok=True)
    root = d / "x" / "pak256"
    for f in root.glob("*.pak"):
        shutil.copy2(f, pk / f.name)
    shutil.copy2(root / "ami_license.txt", d / "build" / "ami_license.txt")
    return d


a, b = extract(v031, "A"), extract(v040, "B")
for name, base, city in (("C", b, a), ("D", a, b)):
    d = out / name
    shutil.copytree(base, d, dirs_exist_ok=True)
    shutil.copy2(city / "build" / "pak" / CITY, d / "build" / "pak" / CITY)
print(sorted(p.name for p in out.iterdir()))
