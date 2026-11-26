"""同じ場面を v0.3.1 と今の pak で走らせ、編成ごとの月ごとの運んだ数と収入（新しい月が先）を比べる。MIT License。
使い方: python -X utf8 docs/records/2026-11-26_v040-check-screens/run4.py <検証環境> <ポート> <v031 か ci>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403

side = sys.argv[3]
HIST = ('local s=""; foreach (c in world.get_convoy_list()) { s += c.get_name()+" 運んだ="; '
        'foreach (v in c.get_transported_goods()) s += v+","; s += " 収入="; '
        'foreach (v in c.get_revenue()) s += v+","; s += " 走行="; foreach (v in c.get_traveled_distance()) s += v+",";s += " 容量="; foreach (v in c.get_capacity()) if (v > 0) s += v+","; s += " ; "; } '
        'local t=world.get_time(); s += "year="+t.year+" month="+t.month; return s;')
with Game(sys.argv[1], "flat_512_left_v64", int(sys.argv[2]), work=V + "/w4_" + side, build=V + f"/{side}/build",
          root=V + f"/{side}/x/pak256") as g:
    g.sq_file(SETUP, head=HEAD, timeout=120)
    g.settle(25)
    poll(g, 12)
    print("hist:", g.sq(HIST), flush=True)
    print("halts:", g.sq('local s=""; foreach (h in halt_list_x()) { s += h.get_name()+" 到着="; '
                         'foreach (v in h.get_arrived()) s += v+","; s += " 出発="; foreach (v in h.get_departed()) s += v+","; s += " ; "; } return s;'),
          flush=True)
    if g.left_over:
        sys.exit(1)
