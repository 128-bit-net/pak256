"""AMI の zip の pak の中の物の名前と、写した訳の名前を突き合わせる（#219）。MIT License。
使い方（リポジトリの直下で。makeobj は PATH のもの）: python -X utf8 docs/records/2026-11-27_ami219-screens/names_vs_paks.py <AMI の 256 版の zip>"""
import os
import sys

sys.path.insert(0, os.path.abspath("tools"))
import build_ami256 as B  # noqa: E402

objs = set()
for pak in B.zip_objects(sys.argv[1]).values():
    objs |= pak
names = {n for _, n in objs}
signs = sorted(n for k, n in objs if n.startswith("ami_sign_"))
print(f"pak の物 {len(objs)}（名前 {len(names)}）。標識 {len(signs)}: {' '.join(signs)}")
for lang in ("ja", "en"):
    with open(os.path.join(B.TEXT_DIR, f"{lang}.ami.tab"), encoding="utf-8") as f:
        keys = set([ln for ln in f.read().split("\n")[1:] if ln and not ln.startswith("#")][::2])
    print(f"{lang}: 訳の名前 {len(keys)}。pak にあって訳が無い {sorted(names - keys)}。訳にあって pak に無い {len(keys - names)}: {sorted(keys - names)[:12]}")
