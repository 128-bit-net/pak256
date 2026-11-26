"""B-A の平均の差のブートストラップ区間（95%）と、街の建物の数。MIT License。使い方: python -X utf8 docs/records/2026-11-26_passengers/stats.py <jsonl> [<jsonl> ...]"""
import json
import random
import statistics
import sys

rows = []
for p in sys.argv[1:]:
    rows += [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]
rows = [r for r in rows if "error" not in r]


def conv(r, name):
    for x in r["convoys"].split(","):
        if x.startswith(name + "="):
            return int(x.split("=")[1].split(":")[0])


def cities(r, rail):
    out = [0, 0]
    for x in r["end"]["cities"].split(","):
        if x:
            px, py, pop, n = (int(v) for v in x.split(":"))
            if (py > 90) == rail:
                out[0] += pop
                out[1] += n
    return out


for name in ("rail", "bus"):
    a = [conv(r, name) for r in rows if r["cond"] == "A"]
    b = [conv(r, name) for r in rows if r["cond"] == "B"]
    rng = random.Random(1)
    d = sorted(statistics.mean(rng.choices(b, k=len(b))) - statistics.mean(rng.choices(a, k=len(a))) for _ in range(20000))
    lo, hi, ma = d[500], d[19500], statistics.mean(a)
    print(f"{name}: B-A {statistics.mean(b) - ma:+.1f}  95% [{lo:+.1f}, {hi:+.1f}]  (A の平均 {ma:.1f} の {100 * lo / ma:+.0f}% 〜 {100 * hi / ma:+.0f}%)")
for c in ("A", "B"):
    rs = [r for r in rows if r["cond"] == c]
    for rail, label in ((True, "線路の街 2 つ"), (False, "道の街 2 つ")):
        v = [cities(r, rail) for r in rs]
        print(c, label, "終わりの人口の平均", round(statistics.mean(x[0] for x in v)), "建物の平均", round(statistics.mean(x[1] for x in v), 1))
    if rs and rs[0].get("placed"):
        print(c, "置けた住宅", [int(r["placed"]) for r in rs])
