"""#189 で増えた物（路面軌道の架線・リニア・景観の補助・狭軌）と、モノレールの直角の曲がり（AMI #375）を、温暖と降雪に置いて拡大 3 で撮る。MIT License。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-27_ami189-screens/new_scene.py <本体の検証環境> <MCP のポート> <build のフォルダ> <出力のフォルダ>
<build のフォルダ> は pak/ を持つフォルダ。alpha.8 の pak には新しい物が無いので、[log] に失敗が出る（モノレールの曲がりだけは前後を比べられる）。
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
# 撮る所の名前と、原点からのずれ
VIEWS = (("monorail_corner", 4, 3), ("cat_road", 4, 12), ("cat_corner", 8, 12), ("cat_dirt", 4, 20), ("cat_diagonal", 18, 15),
         ("cat_depot", 1, 26),
         ("maglev_guideway", 6, 34), ("maglev_beam", 6, 40), ("maglev_tube", 6, 46), ("maglev_elev", 6, 54),
         ("maglev_elev_tube", 6, 62), ("maglev_tunnel", 4, 70), ("maglev_depot", 2, 80),
         ("roundabout", 6, 92), ("describe", 22, 90), ("describe_elev", 22, 104), ("embankment_building", 40, 92),
         ("narrow", 6, 114), ("maglev_guideway_corner", 8, 33), ("maglev_beam_corner", 8, 39), ("maglev_tube_corner", 8, 45),
         ("maglev_elev_corner", 10, 53), ("maglev_tunnel_east", 7, 68), ("monorail_corner_ne", 3, 1), ("monorail_corner_sw", 3, 6),
         ("monorail_corner_se", 8, 5))


def lay(g, ox):
    log = []

    def pos(x, y, z=0):
        return f"coord3d({ox + x},{OY + y},{z})"

    def sq(label, code, player_nr=0):
        r = g.sq(f'try {{ {code} }} catch (e) {{ return "error " + e }}', player_nr=player_nr)
        if r not in ("None", "", "null"):
            log.append(f"{label}: {r}")

    def way(name, x1, y1, x2, y2):
        sq(f"{name} ({x1},{y1})-({x2},{y2})",
           f'return command_x.build_way(player_x(0), {pos(x1, y1)}, {pos(x2, y2)}, way_desc_x("{name}"), true)')

    def wayobj(name, x1, y1, x2, y2, z=0):
        sq(f"{name} ({x1},{y1})-({x2},{y2})",
           f'return command_x.build_wayobj(player_x(0), {pos(x1, y1, z)}, {pos(x2, y2, z)}, wayobj_desc_x("{name}"))')

    def depot(name, x, y):
        sq(name, 'foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) '
           f'if (d.get_name() == "{name}") return command_x.build_depot(player_x(0), {pos(x, y)}, d); return "no desc"')

    def line(name, obj, segs, z=0):
        for s in segs:
            way(name, *s)
        for s in segs:
            if obj:
                wayobj(obj, *s, z=z)

    # モノレールの直角の曲がり（AMI #375）。4 つの向き
    for name, y in (("ami_monorail_straddle", 0),):
        for s in ((0, y, 3, y), (3, y, 3, y + 6), (3, y + 6, 8, y + 6), (8, y + 6, 8, y)):
            way(name, *s)
    # 路面軌道の架線: 道路の上（直線・曲がり）、土の上（直線・曲がり・十字）、斜め、車庫
    for s in ((0, 12, 8, 12), (8, 12, 8, 15)):
        way("ami_road_local", *s)
    line("ami_tram", "ami_tram_catenary", ((0, 12, 8, 12), (8, 12, 8, 15)))
    line("ami_tram", "ami_tram_catenary", ((0, 20, 8, 20), (8, 20, 8, 23), (4, 17, 4, 23)))
    for k in range(5):
        line("ami_tram", "ami_tram_catenary",
             ((14 + k, 12 + k, 15 + k, 12 + k), (15 + k, 12 + k, 15 + k, 13 + k)))
    way("ami_tram", 1, 26, 5, 26)
    depot("ami_tram_depot", 1, 26)
    wayobj("ami_tram_catenary", 1, 26, 5, 26)
    # リニア: 超電導（ガイド）・常電導・チューブ式（チューブ）の直線と曲がり
    for name, obj, y in (("ami_maglev_guideway_single", "ami_maglev_guide", 32), ("ami_maglev_beam", None, 38),
                         ("ami_maglev_tube_single", "ami_maglev_tube_cover", 44)):
        line(name, obj, ((0, y, 8, y), (8, y, 8, y + 3), (8, y + 3, 12, y + 3)))
    # 高架と橋脚
    for name, obj, y in (("ami_maglev_guideway_elev_single", "ami_maglev_guide", 52), ("ami_maglev_beam_elev_center", None, 56),
                         ("ami_maglev_tube_elev_single", "ami_maglev_tube_cover", 60)):
        for s in ((0, y, 10, y), (10, y, 10, y + 2)):
            way(name, *s)
            if name != "ami_maglev_beam_elev_center":
                way("ami_pier_rail", *s)
        if obj:
            wayobj(obj, 0, y, 10, y, z=2)
            wayobj(obj, 10, y, 10, y + 2, z=2)
    # トンネル（2 段の丘）3 種
    for name, way_name, obj, y in (("ami_maglev_guideway_tunnel", "ami_maglev_guideway_single", "ami_maglev_guide", 68),
                                   ("ami_maglev_beam_tunnel", "ami_maglev_beam", None, 72),
                                   ("ami_maglev_tube_tunnel", "ami_maglev_tube_single", "ami_maglev_tube_cover", 76)):
        for x in range(3, 6):
            for k in range(2):
                sq("raise", f"return command_x.set_slope(player_x(0), {pos(x, y, k)}, slope.all_up_slope)")
        sq("rampW", f"return command_x.set_slope(player_x(0), {pos(2, y)}, 24)")
        sq("rampE", f"return command_x.set_slope(player_x(0), {pos(6, y)}, 56)")
        sq(name, f'return command_x(tool_build_tunnel).work(player_x(0), {pos(2, y)}, "{name}")')
        way(way_name, 0, y, 2, y)
        way(way_name, 6, y, 9, y)
        if obj:
            wayobj(obj, 0, y, 2, y)
    way("ami_maglev_guideway_single", 2, 80, 6, 80)
    depot("ami_maglev_depot", 2, 80)
    # ラウンドアバウト（AMI の scenic_sample.nut の RA。中心 (6,92)）
    for name in ("ami_road_general", "ami_mark_roundabout"):
        for s in ((5, 91, 7, 91), (7, 91, 7, 93), (7, 93, 5, 93), (5, 93, 5, 91)):
            way(name, *s)
    for s in ((7, 92, 11, 92), (5, 92, 1, 92), (6, 91, 6, 87), (6, 93, 6, 97)):
        way("ami_road_general", *s)
    for s in ((7, 92, 8, 92), (5, 92, 4, 92), (6, 91, 6, 90), (6, 93, 6, 94), (6, 92, 6, 92)):
        way("ami_mark_roundabout", *s)
    # 説明用の色の線（地上と高架）
    for i, color in enumerate(("red", "blue", "green", "yellow")):
        name, y = "ami_describe_" + color, 84 + 4 * i
        for s in ((18, y, 24, y), (21, y, 21, y + 2), (26, y, 28, y), (28, y, 28, y + 2)):
            way(name, *s)
    way("ami_describe_red_elev", 18, 104, 24, 104)
    way("ami_describe_blue_elev", 21, 104, 21, 107)
    # 盛土の建物の輪（直線の layout 0 南・1 東・2 北・3 西、角は 0 北西・1 南西・2 南東・3 北東）
    b, k = "ami_embankment_building", "ami_embankment_building_corner"
    for name, x, y, rot in ((k, 39, 91, 2), (b, 40, 91, 2), (k, 41, 91, 1), (b, 39, 92, 3), (b, 41, 92, 1),
                            (k, 39, 93, 3), (b, 40, 93, 0), (k, 41, 93, 0)):
        sq(f"{name} ({x},{y})",
           f'return command_x(tool_build_house).work(player_x(1), {pos(x, y)}, "1{rot}{name}")', player_nr=1)
    # 狭軌（pak には入る。ツールバーは無い）: 道床と木まくら、車庫
    way("ami_narrow_ballast", 0, 112, 8, 112)
    way("ami_narrow_wood", 0, 116, 8, 116)
    way("ami_narrow_wood", 8, 116, 8, 119)
    depot("ami_narrow_depot", 0, 112)
    return log


with Game(env, "flat_512_left_v64", port, build=build, simuconf_extra=["show_names = 0"]) as g:
    for climate, ox in ORIGINS.items():
        for line_ in lay(g, ox):
            print(f"[{climate}] {line_}", flush=True)
    g.climate(ORIGINS["snow"] - 8, OY - 8, ORIGINS["snow"] + 48, OY + 124, "arctic", timeout=180)
    g.settle(20)
    for climate, ox in ORIGINS.items():
        for name, x, y in VIEWS:
            g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d({ox + x},{OY + y},0)); return 1")
            time.sleep(2)
            g.capture(os.path.join(out, f"{climate}_{name}.png"))
    if g.left_over:
        sys.exit(1)
