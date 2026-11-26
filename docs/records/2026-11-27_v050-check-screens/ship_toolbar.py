"""今の配布の zip で船のツールバーを開いて撮る。MIT License。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-27_v050-check-screens/ship_toolbar.py <検証環境> <ポート>"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *  # noqa: F401,F403

with Game(sys.argv[1], "flat_512_left_v64", int(sys.argv[2]), work=V + "/w5", **pak("ci")) as g:
    g.sq("gui.click(360, 24); return 1")  # 上の帯の船の道具
    time.sleep(3)
    g.capture(V + "/ship_toolbar.png")
    if g.left_over:
        sys.exit(1)
