"""MIT License。#176: 大きな足跡の産業、複数タイルの駅舎、AMI の道路の停留所と線路の駅を置いて撮る。

使い方: python -X utf8 place.py <検証環境> <build_test.py の出す先> <撮る場所（git 管理外）> <ポート>。先に tools/build.py。
"""
import glob
import os
import sys

env, t8, out, port = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
os.makedirs(out, exist_ok=True)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools")))
from game import Game  # noqa: E402

# そのタイルの建物の名前を並べる（無いタイルは -）
AT = ('function at(x, y) { local b = tile_x(x, y, square_x(x, y).get_ground_tile().z).find_object(mo_building);'
      ' return b ? b.get_desc().get_name() : "-"; }'
      ' function area(x0, y0, w, h) { local s = ""; for (local y = y0; y < y0 + h; y++) { for (local x = x0; x < x0 + w; x++)'
      ' s += at(x, y) + " "; s += "/ "; } return s; }')
extra = glob.glob(os.path.join(t8, "pak", "*.pak"))

with Game(env, "flat_512_left_v64", port, extra_paks=extra, simuconf_extra=["show_names = 0"]) as g:
    def sq(code, **kw):
        r = g.sq(code, timeout=90, **kw)
        print(r, flush=True)
        return r

    def shot(name, x, y):
        g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d({x},{y},0)); return 1")
        g.settle(3)
        g.capture(os.path.join(out, name + ".png"))

    # 産業: 4×4 と 6×6
    for name, x, size in (("t8_factory_4x4", 40, 4), ("t8_factory_6x6", 52, 6)):
        sq(f'return "build {name}: " + command_x(tool_build_factory).work(player_x(1), coord3d({x},40,0), "0050,{name}")',
           player_nr=1)
        sq(AT + f' return area({x}, 40, {size + 1}, {size + 1})')

    # 駅舎: 東西の線路。x=45 に 2×1 の type=stop、x=60〜62 に pak256 の駅、その北に type=extension
    sq('return command_x(tool_build_way).work(player_x(0), coord3d(40,70,0), coord3d(75,70,0), "ami_rail_ballast")')
    sq('return "stop2x1: " + command_x(tool_build_station).work(player_x(0), coord3d(45,70,0), "t8_stop_2x1")')
    sq(AT + ' return area(44, 69, 4, 3)')
    for x in (60, 61, 62):
        sq(f'return command_x(tool_build_station).work(player_x(0), coord3d({x},70,0), "pak256_train_station")')
    sq('return "ext2x1: " + command_x(tool_build_station).work(player_x(0), coord3d(60,69,0), "t8_ext_2x1")')
    sq('return "ext2x2: " + command_x(tool_build_station).work(player_x(0), coord3d(60,71,0), "t8_ext_2x2")')
    sq(AT + ' return area(59, 68, 5, 5)')
    sq('local h = tile_x(60,69,0).get_halt(), h2 = tile_x(60,70,0).get_halt(), h3 = tile_x(61,72,0).get_halt();'
       ' return "ext halt=" + (h ? h.get_name() : "-") + " stop halt=" + (h2 ? h2.get_name() : "-") + " ext2x2 halt=" + (h3 ? h3.get_name() : "-")')

    # AMI の道路の種類ごとに、直線に pak256 の停留所（バス・トラック）
    for i, road in enumerate(("ami_road_local", "ami_road_general", "ami_road_trunk", "ami_road_expressway")):
        y = 100 + i * 4
        sq(f'return "{road} " + command_x(tool_build_way).work(player_x(0), coord3d(40,{y},0), coord3d(50,{y},0), "{road}")')
        sq(f'return "bus " + command_x(tool_build_station).work(player_x(0), coord3d(43,{y},0), "pak256_bus_stop")')
        sq(f'return "truck " + command_x(tool_build_station).work(player_x(0), coord3d(47,{y},0), "pak256_truck_stop")')

    # AMI の線路の種類ごとに、pak256 の駅
    for i, rail in enumerate(("ami_rail_ballast", "ami_rail_concrete", "ami_rail_slab", "ami_rail_ladder")):
        y = 130 + i * 3
        sq(f'return "{rail} " + command_x(tool_build_way).work(player_x(0), coord3d(40,{y},0), coord3d(50,{y},0), "{rail}")')
        for x in (44, 45):
            sq(f'return command_x(tool_build_station).work(player_x(0), coord3d({x},{y},0), "pak256_train_station")')

    g.settle(30)
    shot("factory_4x4", 42, 42)
    shot("factory_6x6", 55, 43)
    shot("stop_2x1", 45, 70)
    shot("extension", 61, 70)
    # 道路と線路は種類ごとに、停留所・駅を画面の真ん中にして撮る
    for i, road in enumerate(("local", "general", "trunk", "expressway")):
        shot(f"road_{road}", 43, 100 + i * 4)
    for i, rail in enumerate(("ballast", "concrete", "slab", "ladder")):
        shot(f"rail_{rail}", 44, 130 + i * 3)
if g.left_over:
    sys.exit(1)
