"""今の配布の zip の中身だけで新しい場面を作って運送を走らせ、demo.sve を -load でも読む。MIT License。
使い方（リポジトリの直下から）:
  python -X utf8 docs/records/2026-11-27_v050-check-screens/new_run.py run <検証環境> <ポート>
  python -X utf8 docs/records/2026-11-27_v050-check-screens/new_run.py demo <demo.sve を置いた環境の写し> <ポート>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403

mode, env, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
if mode == "run":
    with Game(env, "flat_512_left_v64", port, work=V + "/w3", keep=True, **pak("ci")) as g:
        print("setup:", g.sq_file(SETUP, head=HEAD, timeout=120).replace(chr(10), " | "), flush=True)
        g.settle(25)
        print("tiles:", g.sq(OBJ), flush=True)
        print("halts:", g.sq(HALTS), flush=True)
        poll(g, 12)
        convoys(g, V + "/new_convoys.png")
        if g.left_over:
            sys.exit(1)
else:
    debug_log()
    with Game(env, "demo", port, work=V + "/w4", keep=True, rewrite_roads=False, **pak("ci")) as g:
        g.capture(V + "/demo_loaded.png")  # 足りない物の窓があれば映る
        print("convoys:", g.sq(READ), flush=True)
        if g.left_over:
            sys.exit(1)
