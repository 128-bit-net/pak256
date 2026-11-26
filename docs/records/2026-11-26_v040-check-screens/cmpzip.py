"""MIT License。2 つの zip の中のファイルを SHA-256 で比べる。使い方: python -X utf8 docs/records/2026-11-26_v040-check-screens/cmpzip.py <zip A> <zip B>"""
import hashlib
import sys
import zipfile


def digest(p):
    with zipfile.ZipFile(p) as z:
        return {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith("/")}


a, b = digest(sys.argv[1]), digest(sys.argv[2])
print("files", len(a), len(b), "pak", sum(n.endswith(".pak") for n in a), sum(n.endswith(".pak") for n in b))
print("only A", sorted(set(a) - set(b)))
print("only B", sorted(set(b) - set(a)))
print("differ", sorted(n for n in set(a) & set(b) if a[n] != b[n]))
