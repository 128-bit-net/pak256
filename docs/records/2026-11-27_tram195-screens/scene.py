"""#195: 路面電車の停留所と架線の柱を、架線あり・なし、東西・南北、土の上・道路の上で撮る。MIT License。

使い方（リポジトリの直下で。<build のフォルダ> は pak/ を持つ組んだフォルダ）:
    python -X utf8 docs/records/2026-11-27_tram195-screens/scene.py <本体の検証環境> <MCP のポート> <build のフォルダ> <出力のフォルダ>
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
os.makedirs(out, exist_ok=True)
OX, OY = 60, 60
RUN = (3, 4, 5)  # 3 升の連なり
SINGLE = 10      # 単独の升
# 名前: (原点からのずれ x, y, 軸, 道路の上か, 架線)
LINES = {}
for cat, dy in (("cat", 0), ("nocat", 40)):
    LINES[f"{cat}_dirt_ew"] = (0, dy, "ew", False, cat == "cat")
    LINES[f"{cat}_dirt_ns"] = (22, dy, "ns", False, cat == "cat")
    LINES[f"{cat}_road_ew"] = (0, dy + 22, "ew", True, cat == "cat")
    LINES[f"{cat}_road_ns"] = (34, dy + 4, "ns", True, cat == "cat")


def tile(x, y, axis, i):
    return (x + i, y) if axis == "ew" else (x, y + i)


with Game(env, "flat_512_left_v64", port, build=build, simuconf_extra=["show_names = 0"]) as g:
    def sq(label, code):
        r = g.sq(f'try {{ {code} }} catch (e) {{ return "error " + e }}')
        if r not in ("None", "", "null", "true"):
            print(f"[log] {label}: {r}", flush=True)

    def pos(p):
        return f"coord3d({OX + p[0]},{OY + p[1]},0)"

    for name, (x, y, axis, road, cat) in LINES.items():
        a, b = tile(x, y, axis, 0), tile(x, y, axis, 14)
        for way in (["ami_road_local"] if road else []) + ["ami_tram"]:
            sq(name + " " + way, f'return command_x.build_way(player_x(0), {pos(a)}, {pos(b)}, way_desc_x("{way}"), true)')
        if cat:
            sq(name + " cat", f'return command_x.build_wayobj(player_x(0), {pos(a)}, {pos(b)}, wayobj_desc_x("ami_tram_catenary"))')
        for i in RUN + (SINGLE,):
            p = tile(x, y, axis, i)
            r = g.station(OX + p[0], OY + p[1], "pak256_tram_stop")
            if r not in ("None", "", "null"):
                print(f"[log] {name} stop {p}: {r}", flush=True)
    g.settle(25)
    for name, (x, y, axis, road, cat) in LINES.items():
        for view, i in (("run", 4), ("single", SINGLE)):
            p = tile(x, y, axis, i)
            g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump({pos(p)}); return 1")
            time.sleep(1.5)
            g.capture(os.path.join(out, f"{name}_{view}.png"))
    if g.left_over:
        sys.exit(1)
