"""今の配布の zip で tools/vehicle_check/ship.nut を流し、速さ 64 で進めて編成の運んだ数を読む。MIT License。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-27_v050-check-screens/ship_run.py <検証環境> <ポート>"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403

with Game(sys.argv[1], "flat_512_left_v64", int(sys.argv[2]), work=V + "/w6", **pak("ci")) as g:
    print("ship:", g.sq_file("tools/vehicle_check/ship.nut", timeout=120).replace(chr(10), " | "), flush=True)
    g.settle(25)
    poll(g, 8, wait=30, speed=64)
    g.sq("gui.close_all_windows(); gui.jump(coord3d(50,86,-1)); gui.set_zoom(3); return 1")
    time.sleep(2)
    g.capture(V + "/ship.png")
    if g.left_over:
        sys.exit(1)
