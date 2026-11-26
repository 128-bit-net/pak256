"""v0.4.0 で作った保存データ compat040 を読み込み、物・停留所・編成を読んで走らせる。MIT License。
道路名の書き換えは止め（遊ぶ人の読み込みと同じ）、起動のログを取る。
使い方（リポジトリの直下から）:
  python -X utf8 docs/records/2026-11-27_v050-check-screens/load_save.py <compat040 を置いた環境の写し> <ポート> <v040 か ci>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403

side = sys.argv[3]
debug_log()
with Game(sys.argv[1], "compat040", int(sys.argv[2]), work=V + "/w2_" + side, keep=True, rewrite_roads=False,
          **pak(side)) as g:
    g.capture(V + f"/{side}_loaded.png")  # 読み込んだ直後（足りない物の窓があれば映る）
    print("t0:", g.sq(READ), flush=True)
    print("tiles:", g.sq(OBJ), flush=True)
    print("halts:", g.sq(HALTS), flush=True)
    shot(g, 60, 60, V + f"/{side}_bus.png")
    shot(g, 93, 110, V + f"/{side}_rail.png")
    poll(g, 12)
    print("tiles2:", g.sq(OBJ), flush=True)
    print("halts2:", g.sq(HALTS), flush=True)
    convoys(g, V + f"/{side}_convoys.png")
    if g.left_over:
        sys.exit(1)
