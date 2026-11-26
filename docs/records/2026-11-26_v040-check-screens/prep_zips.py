"""MIT License。zip を展開して build/pak の形に並べ、pak の物（makeobj list）の名前を比べる。
使い方: python -X utf8 docs/records/2026-11-26_v040-check-screens/prep_zips.py <v0.3.1 の zip> work/a04/v031 <今の zip> work/a04/ci"""
import pathlib
import shutil
import subprocess
import sys
import zipfile


def prep(zp, out):
    out = pathlib.Path(out)
    x = out / "x"
    pk = out / "build" / "pak"
    pk.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zp) as z:
        z.extractall(x)
    root = x / "pak256"
    for f in root.glob("*.pak"):
        shutil.copy2(f, pk / f.name)
    lic = root / "ami_license.txt"
    if lic.exists():
        shutil.copy2(lic, out / "build" / "ami_license.txt")
        shutil.copy2(lic, pk / "ami_license.txt")
    return pk


def objs(pk):
    res = {}
    for f in sorted(pk.glob("*.pak")):
        o = subprocess.run(["makeobj", "list", str(f)], capture_output=True).stdout.decode(errors="replace")
        for line in o.splitlines():
            parts = line.split()
            if len(parts) >= 2 and not line.startswith(("Contents", "type", "----", "Makeobj", "(c)")):
                res.setdefault((parts[0], parts[1]), []).append(f.name)
        res.setdefault(("_raw", f.name), []).append(o)
    return res


a = prep(sys.argv[1], sys.argv[2])
b = prep(sys.argv[3], sys.argv[4])
oa, ob = objs(a), objs(b)
raw = next(v for k, v in oa.items() if k[0] == "_raw")
print(raw[0][:600])
ka = {k for k in oa if k[0] != "_raw"}
kb = {k for k in ob if k[0] != "_raw"}
print("A paks", len(list(a.glob("*.pak"))), "objs", len(ka), "| B paks", len(list(b.glob("*.pak"))), "objs", len(kb))
print("paks only A:", sorted({p.name for p in a.glob("*.pak")} - {p.name for p in b.glob("*.pak")}))
print("paks only B:", sorted({p.name for p in b.glob("*.pak")} - {p.name for p in a.glob("*.pak")}))
print("REMOVED:")
for k in sorted(ka - kb):
    print(" ", k, oa[k])
print("ADDED:")
for k in sorted(kb - ka):
    print(" ", k, ob[k])
