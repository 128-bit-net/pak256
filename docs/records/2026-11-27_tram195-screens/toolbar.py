"""#195: 路面電車のツールバー（停留所の道具の絵）を撮る。MIT License。

    python -X utf8 docs/records/2026-11-27_tram195-screens/toolbar.py <本体の検証環境> <MCP のポート> <build のフォルダ> <出力の PNG>

上の帯の路面電車のボタンの位置（x = 312）は、1600x900 の画面の物（#189 の toolbar.py と同じ）。
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
with Game(env, "flat_512_left_v64", port, build=build) as g:
    g.sq("gui.close_all_windows(); gui.click(312, 24); return 1")
    time.sleep(2)
    g.capture(out)
    if g.left_over:
        sys.exit(1)
