"""#159（AMI #360・#365 の直し）の前後を同じ位置で撮る: 道の基盤の版（base）の形と、道路の上と土の上の路面軌道の境・路面軌道の車庫の前を、
温暖と降雪に敷いて拡大 3 で撮る。MIT License。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_ami159-screens/scene.py <本体の検証環境> <MCP のポート> <build のフォルダ> <出力のフォルダ>
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
OY = 60
ORIGINS = {"temperate": 60, "snow": 316}
BASES = ("ami_road_local_base_single", "ami_road_general_base_single", "ami_road_trunk_base_single",
         "ami_road_expressway_base_single", "ami_road_trunk_base_front", "ami_road_trunk_base_back",
         "ami_road_trunk_base_center", "ami_road_expressway_base_center")
# 撮る所の名前と、原点からのずれ
VIEWS = tuple((n.replace("ami_road_", ""), 3, 3 + 10 * i) for i, n in enumerate(BASES)) + (
    ("tram_boundary_ew", 24, 4), ("tram_boundary_ns", 24, 20), ("tram_depot_w", 20, 36), ("tram_depot_n", 30, 38),
    ("tram_depot_e", 24, 50), ("tram_depot_s", 36, 46))


def lay(g, ox):
    log = []

    def pos(x, y):
        return f"coord3d({ox + x},{OY + y},0)"

    def check(label, r):
        if r not in ("None", "", "null"):
            log.append(f"{label}: {r}")

    def way(name, x1, y1, x2, y2):
        check(f"{name} ({x1},{y1})-({x2},{y2})",
              g.sq(f'return command_x(tool_build_way).work(player_x(0), {pos(x1, y1)}, {pos(x2, y2)}, "{name}")'))
        for x, y in ((x1, y1), (x2, y2)):
            wt = "wt_rail" if name == "ami_tram" else "wt_road"  # 軌道の way の waytype は線路
            if g.sq(f"return tile_x({ox + x},{OY + y},0).has_way({wt})") != "true":
                log.append(f"{name} が無い ({x},{y})")

    def depot(x, y):
        check(f"depot ({x},{y})", g.sq(
            'foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) '
            f'if (d.get_name() == "ami_tram_depot") return command_x.build_depot(player_x(0), {pos(x, y)}, d); return "no desc"'))

    # 基盤の版: 5x5 の格子（角・分かれ目・十字）と、東へ伸びる斜め
    for i, name in enumerate(BASES):
        y0 = 1 + 10 * i
        for d in (0, 2, 4):
            way(name, 0, y0 + d, 4, y0 + d)
            way(name, d, y0, d, y0 + 4)
        for k in range(3):
            way(name, 7 + k, y0 + k, 8 + k, y0 + k)
            way(name, 8 + k, y0 + k, 8 + k, y0 + k + 1)
    # 路面軌道の境（東西）: 土 20〜22、道路の上 23〜25、土 26〜28
    way("ami_road_local", 23, 4, 25, 4)
    way("ami_tram", 20, 4, 28, 4)
    # 路面軌道の境（南北）
    way("ami_road_local", 24, 19, 24, 21)
    way("ami_tram", 24, 16, 24, 24)
    # 車庫の前（4 つの向き）。車庫は軌道の行き止まりに置く。西向きの端と北向きの端は奥の辺がつながる
    way("ami_tram", 20, 36, 24, 36)
    depot(20, 36)
    way("ami_tram", 30, 38, 30, 42)
    depot(30, 38)
    way("ami_tram", 20, 50, 24, 50)
    depot(24, 50)
    way("ami_tram", 36, 42, 36, 46)
    depot(36, 46)
    return log


with Game(env, "flat_512_left_v64", port, build=build) as g:
    for climate, ox in ORIGINS.items():
        for line in lay(g, ox):
            print(f"[{climate}] {line}", flush=True)
    g.climate(ORIGINS["snow"] - 8, OY - 8, ORIGINS["snow"] + 44, OY + 82, "arctic", timeout=180)
    g.settle(10)
    for climate, ox in ORIGINS.items():
        for name, x, y in VIEWS:
            g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d({ox + x},{OY + y},0)); return 1")
            time.sleep(2)
            g.capture(os.path.join(out, f"{climate}_{name}.png"))
