"""v0.4.0 の配布の zip の中身だけで場面を作り、compat040 として保存する。MIT License。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-27_v050-check-screens/make_save.py <検証環境> <ポート>"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403

with Game(sys.argv[1], "flat_512_left_v64", int(sys.argv[2]), work=V + "/w1", keep=True, **pak("v040")) as g:
    print("setup:", g.sq_file(SETUP, head=HEAD, timeout=120).replace(chr(10), " | "), flush=True)
    # 木は公共プレーヤーで植える
    for x, name in [(62, "pak256_zelkova"), (64, "pak256_birch"), (66, "pak256_cedar")]:
        code = f'return command_x(tool_plant_tree).work(player_x(1), coord3d({x},66,0), "11,{name}")'
        print("tree", name, g.sq(code, player_nr=1), flush=True)
    g.settle(25)
    poll(g, 6)
    print("tiles:", g.sq(OBJ), flush=True)
    print("halts:", g.sq(HALTS), flush=True)
    print("final:", g.sq(READ), flush=True)
    shot(g, 60, 60, V + "/v040_bus.png")
    shot(g, 93, 110, V + "/v040_rail.png")
    print("save:", g.sq('world.save_game("compat040"); return 1'), flush=True)
    time.sleep(5)
    if g.left_over:
        sys.exit(1)
