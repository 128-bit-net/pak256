"""#219 の直し（AMI #393 路面軌道の架線の曲がりの柱・#394 リニアの行き止まりと車庫の側壁）の場面を敷き、拡大 3 で撮る。MIT License。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-27_ami219-screens/scene.py <本体の検証環境> <MCP のポート> <build のフォルダ> <出力のフォルダ>
<build のフォルダ> は pak/ を持つフォルダ。前（alpha.9）と後（alpha.10）で同じ場所を撮る。
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
os.makedirs(out, exist_ok=True)
OY = 60
ORIGINS = {"temperate": 60, "snow": 316}
# 架線の輪（1 辺 4 タイル。4 つの角が 4 つの向きの曲がり）: 名前、下の道路、原点の x
LOOPS = (("local", "ami_road_local", 0), ("general", "ami_road_general", 8), ("ground", None, 16))
# リニアの線（4 タイル。片方の端に車庫、反対の端は車庫の無い行き止まり）: 向き、車庫の端、行き止まりの端
LINES = (("west", (0, 0), (3, 0)), ("east", (9, 0), (6, 0)), ("north", (12, -2), (12, 1)), ("south", (16, 1), (16, -2)))
# 名前、way、way-object、原点からの y、高さ（高架は車庫と way-object を 2 段上に置く）
MAGLEV = (("guideway", "ami_maglev_guideway_single", "ami_maglev_guide", 14, 0),
          ("tube", "ami_maglev_tube_single", "ami_maglev_tube_cover", 22, 0),
          ("guideway_elev", "ami_maglev_guideway_elev_single", "ami_maglev_guide", 30, 2),
          ("tube_elev", "ami_maglev_tube_elev_single", "ami_maglev_tube_cover", 38, 2))


def lay(g, ox):
    log = []

    def pos(x, y, z=0):
        return f"coord3d({ox + x},{OY + y},{z})"

    def sq(label, code):
        r = g.sq(f'try {{ {code} }} catch (e) {{ return "error " + e }}')
        if r not in ("None", "", "null"):
            log.append(f"{label}: {r}")

    def way(name, x1, y1, x2, y2):
        sq(f"{name} ({x1},{y1})-({x2},{y2})",
           f'return command_x.build_way(player_x(0), {pos(x1, y1)}, {pos(x2, y2)}, way_desc_x("{name}"), true)')

    def wayobj(name, x1, y1, x2, y2, z=0):
        sq(f"{name} ({x1},{y1})-({x2},{y2})",
           f'return command_x.build_wayobj(player_x(0), {pos(x1, y1, z)}, {pos(x2, y2, z)}, wayobj_desc_x("{name}"))')

    for _, road, x in LOOPS:
        segs = ((x, 0, x + 3, 0), (x + 3, 0, x + 3, 3), (x + 3, 3, x, 3), (x, 3, x, 0))
        if road:
            for s in segs:
                way(road, *s)
        for s in segs:
            way("ami_tram", *s)
        for s in segs:
            wayobj("ami_tram_catenary", *s)
    for _, name, obj, y, z in MAGLEV:
        for _, depot, end in LINES:
            seg = (depot[0], y + depot[1], end[0], y + end[1])
            way(name, *seg)
            if z:
                way("ami_pier_rail", *seg)
            wayobj(obj, *seg, z=z)
            sq(f"depot ({depot[0]},{y + depot[1]}) {name}",
               'foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) '
               'if (d.get_name() == "ami_maglev_depot") return command_x.build_depot(player_x(0), '
               f'{pos(depot[0], y + depot[1], z)}, d); return "no desc"')
    # 置けたことを確かめる（build_way は敷けなくても何も返さないことがある）
    for _, name, _, y, z in MAGLEV:
        for side, depot, end in LINES:
            for what, (x, dy) in (("depot", depot), ("end", end)):
                code = (f'local t = tile_x({ox + x},{OY + y + dy},{z}); '
                        'return "" + t.has_way(wt_maglev) + " " + (t.get_depot() != null)')
                r = g.sq(f'try {{ {code} }} catch (e) {{ return "error " + e }}')
                want = "true " + ("true" if what == "depot" else "false")
                if r != want:
                    log.append(f"{name} {side} {what} ({x},{y + dy},{z}): has_way・車庫 = {r}（{want} のはず）")
    return log


def views():
    """(名前, 原点からの x, y)。輪は (x+2, 2) に飛ぶと、上の角の高い柱まで画面に収まる。リニアは見るタイルに飛ぶ。"""
    for name, _, x in LOOPS:
        yield f"loop_{name}", x + 2, 2
    for name, _, _, y, _ in MAGLEV:
        for side, depot, end in LINES:
            yield f"{name}_{side}_depot", depot[0], y + depot[1]
            yield f"{name}_{side}_end", end[0], y + end[1]


with Game(env, "flat_512_left_v64", port, build=build, simuconf_extra=["show_names = 0"]) as g:
    for climate, ox in ORIGINS.items():
        for line in lay(g, ox):
            print(f"[{climate}] {line}", flush=True)
    g.climate(ORIGINS["snow"] - 8, OY - 8, ORIGINS["snow"] + 28, OY + 48, "arctic", timeout=180)
    g.settle(30)
    for climate, ox in ORIGINS.items():
        for name, x, y in views():
            g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d({ox + x},{OY + y},0)); return 1")
            time.sleep(1.5)
            g.capture(os.path.join(out, f"{climate}_{name}.png"))
if g.left_over:
    sys.exit(1)
