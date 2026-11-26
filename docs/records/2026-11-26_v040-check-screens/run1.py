"""v0.3.1 の配布の zip の中身で場面を作り、compat031 として保存する。MIT License。
使い方（リポジトリの直下から）: python -X utf8 run1.py <検証環境> <ポート>"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403

with Game(sys.argv[1], "flat_512_left_v64", int(sys.argv[2]), work=V + "/w1", build=V + "/v031/build",
          root=V + "/v031/x/pak256", keep=True) as g:
    print("setup:", g.sq_file(SETUP, head=HEAD, timeout=120).replace(chr(10), " | "), flush=True)
    print("extra:", g.sq_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "extra.nut"), timeout=120), flush=True)
    # 木は、この保存データでは公共プレイヤーとして流したときだけ植えられる（--player-nr 1）
    for x, name in [(62, "pak256_zelkova"), (64, "pak256_birch"), (66, "pak256_cedar")]:
        code = f'return command_x(tool_plant_tree).work(player_x(1), coord3d({x},66,0), "11,{name}")'
        print("tree", name, g._client("--run-squirrel", code, "--player-nr", "1", timeout=60).stdout.strip(), flush=True)
    g.settle(25)
    print("tiles:", g.sq(OBJ), flush=True)
    print("halts:", g.sq(HALTS), flush=True)
    poll(g, 6)
    shot(g, 70, 75, V + "/v031_ami_stop.png")
    shot(g, 55, 75, V + "/v031_ami_bus.png")
    shot(g, 64, 66, V + "/v031_trees.png")
    shot(g, 93, 110, V + "/v031_rail.png")
    print("tiles2:", g.sq(OBJ), flush=True)
    print("halts2:", g.sq(HALTS), flush=True)
    print("final:", g.sq(READ), flush=True)
    print("save:", g.sq('world.save_game("compat031"); return 1'), flush=True)
    time.sleep(5)
    if g.left_over:
        sys.exit(1)
