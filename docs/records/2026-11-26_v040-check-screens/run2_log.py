"""run2 の追加: 本体の起動のログを取り（起動に -log -debug 3 を足す）、跡の名札を撮り直す。MIT License。
使い方: python -X utf8 run2_log.py <compat031 を置いた環境の写し> <ポート> <pak の名前: v031 か ci>"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403
import game  # noqa: E402

_orig = game.launch_command
game.launch_command = lambda *a, **k: _orig(*a, **k) + ["-log", "-debug", "3"]

side = sys.argv[3]
with Game(sys.argv[1], "compat031", int(sys.argv[2]), work=V + "/w2b_" + side, build=V + f"/{side}/build",
          root=V + f"/{side}/x/pak256", keep=True) as g:
    print("halts:", g.sq(HALTS), flush=True)
    poll(g, 4)
    if side == "ci":
        shot(g, 55, 75, V + "/v040_label_before.png")
        for x, name in [(55, "pak256_bus_stop"), (85, "pak256_bus_stop"), (70, "pak256_truck_stop")]:
            print("replace", x, g.station(x, 75, name), flush=True)
        g.settle(20)
        shot(g, 55, 75, V + "/v040_label_after.png")
        print("halts:", g.sq(HALTS), flush=True)
    if g.left_over:
        sys.exit(1)
