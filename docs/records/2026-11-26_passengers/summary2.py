"""条件ごとの中央値と、2 条件の差の並べ替え検定（平均の差、両側）。MIT License。
使い方: python -X utf8 docs/records/2026-11-26_passengers/summary2.py <jsonl> [<jsonl> ...]"""
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


def halt(r, i):
    return sum(int(h.split(":")[i]) for h in r["halts"].split(",") if h)


COLS = [("気動車の運んだ数", lambda r: conv(r, "rail")), ("バスの運んだ数", lambda r: conv(r, "bus")),
        ("石炭の運んだ数", lambda r: conv(r, "coal")),
        ("駅の範囲の建物レベル", lambda r: r["start"]["cov_railA"]["level"] + r["start"]["cov_railB"]["level"]),
        ("停留所の範囲の建物レベル", lambda r: r["start"]["cov_busA"]["level"] + r["start"]["cov_busB"]["level"]),
        ("駅の出発", lambda r: halt(r, 0)), ("駅の経路なし", lambda r: halt(r, 4)), ("駅の徒歩", lambda r: halt(r, 5))]


def perm(x, y, n=20000):
    obs = abs(statistics.mean(x) - statistics.mean(y))
    pool, rng, hit = x + y, random.Random(1), 0
    for _ in range(n):
        rng.shuffle(pool)
        hit += abs(statistics.mean(pool[:len(x)]) - statistics.mean(pool[len(x):])) >= obs - 1e-9
    return hit / n


conds = sorted({r["cond"] for r in rows})
for name, f in COLS:
    vals = {c: [f(r) for r in rows if r["cond"] == c] for c in conds}
    line = "  ".join(f"{c}: n={len(v)} 中央値 {statistics.median(v):g} 平均 {statistics.mean(v):.1f} ({min(v)}〜{max(v)})" for c, v in vals.items())
    extra = f"  A-B の p={perm(vals['A'], vals['B']):.3f}" if "A" in vals and "B" in vals else ""
    print(f"{name}\n  {line}{extra}")
