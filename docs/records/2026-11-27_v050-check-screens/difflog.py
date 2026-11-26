"""2 つの simu.log の Warning・ERROR の行を比べる（数字は # にそろえる）。MIT License。
使い方: python -X utf8 docs/records/2026-11-27_v050-check-screens/difflog.py <前の版の simu.log> <今の版の simu.log>"""
import collections
import re
import sys


def lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read().splitlines()
    got = collections.Counter()
    for i, line in enumerate(text):
        if re.search(r"warning|error", line, re.I):
            # 本体は「Warning: 関数:」の次の行に本文を書くことがある
            body = line.strip()
            if body.endswith(":") and i + 1 < len(text):
                body += " " + text[i + 1].strip()
            got[re.sub(r"\d+", "#", body)] += 1
    return got


a, b = lines(sys.argv[1]), lines(sys.argv[2])
print("A", sum(a.values()), "B", sum(b.values()))
for title, only in (("only A", set(a) - set(b)), ("only B", set(b) - set(a))):
    print(title, len(only))
    for k in sorted(only):
        print("  ", (a + b)[k], k)
