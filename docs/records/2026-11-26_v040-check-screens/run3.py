"""今の配布の zip の中身だけで新しい場面を作り、運送を走らせる。MIT License。
使い方（リポジトリの直下から）: python -X utf8 run3.py <検証環境> <ポート>"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403

with Game(sys.argv[1], "flat_512_left_v64", int(sys.argv[2]), work=V + "/w3", build=V + "/ci/build",
          root=V + "/ci/x/pak256", keep=True) as g:
    print("setup:", g.sq_file(SETUP, head=HEAD, timeout=120).replace(chr(10), " | "), flush=True)
    g.settle(25)
    print("tiles:", g.sq(OBJ), flush=True)
    print("halts:", g.sq(HALTS), flush=True)
    poll(g, 12)
    shot(g, 59, 60, V + "/new_bus_stop.png")
    shot(g, 93, 110, V + "/new_rail.png")
    shot(g, 125, 61, V + "/new_depot.png")
    g.sq("gui.close_all_windows(); gui.open_dialog_tool(15); return 1")
    time.sleep(2)
    g.capture(V + "/new_convoys.png")
    g.sq("gui.close_all_windows(); gui.open_dialog_tool(5); return 1")
    time.sleep(2)
    g.capture(V + "/new_finances.png")
    if g.left_over:
        sys.exit(1)
