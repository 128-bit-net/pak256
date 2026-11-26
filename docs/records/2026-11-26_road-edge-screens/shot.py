"""#111 の道路と線路の縁を撮る: 平地に直線・十字・曲がりを置き、拡大 3 で道路と線路を 1 枚ずつ撮る。前後で同じ位置を撮る。

使い方（リポジトリの直下で。先に tools/build.py）:
    python -X utf8 docs/records/2026-11-26_road-edge-screens/shot.py <本体の検証環境> <MCP のポート> <出力の頭>
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]

with Game(env, "flat_512_left_v64", port) as g:
    for way, y in (("ami_road_local", 100), ("ami_rail_ballast", 108)):
        g.road(100, y, 106, y, way)
        g.road(103, y - 3, 103, y + 3, way)
        g.road(106, y, 106, y + 3, way)
    for name, y in (("road", 100), ("rail", 108)):
        g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(103,{y},0)); return 1")
        time.sleep(3)
        g.capture(f"{out}_{name}.png")
