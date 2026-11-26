"""v0.3.1 の保存データ compat031 を v0.4.0 の pak で読み込む。MIT License。
使い方（リポジトリの直下から）: python -X utf8 run2.py <compat031 を置いた環境の写し> <ポート>"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403

with Game(sys.argv[1], "compat031", int(sys.argv[2]), work=V + "/w2", build=V + "/ci/build",
          root=V + "/ci/x/pak256", keep=True) as g:
    print("t0:", g.sq(READ), flush=True)
    print("tiles:", g.sq(OBJ), flush=True)
    print("halts:", g.sq(HALTS), flush=True)
    shot(g, 70, 75, V + "/v040_ami_stop.png")
    shot(g, 55, 75, V + "/v040_ami_bus.png")
    shot(g, 64, 66, V + "/v040_trees.png")
    shot(g, 93, 110, V + "/v040_rail.png")
    poll(g, 12)
    print("tiles2:", g.sq(OBJ), flush=True)
    print("halts2:", g.sq(HALTS), flush=True)
    print("final:", g.sq(READ), flush=True)
    shot(g, 55, 75, V + "/v040_ami_bus_after.png")
    shot(g, 119, 60, V + "/v040_road.png")
    g.sq("gui.close_all_windows(); gui.open_dialog_tool(15); return 1")
    time.sleep(2)
    g.capture(V + "/v040_convoys.png")
    # 消えた停留所の所へ pak256 の停留所を置き直せるか
    for x, name in [(55, "pak256_bus_stop"), (85, "pak256_bus_stop"), (70, "pak256_truck_stop")]:
        print("replace", x, g.station(x, 75, name), flush=True)
    g.settle(20)
    print("tiles3:", g.sq(OBJ), flush=True)
    print("halts3:", g.sq(HALTS), flush=True)
    poll(g, 6)
    print("final3:", g.sq(READ), flush=True)
    shot(g, 70, 75, V + "/v040_replaced.png")
    if g.left_over:
        sys.exit(1)
