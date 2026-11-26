"""#134: AMI の tiled_concrete_material を使う物（線路の基盤・壁・高架・橋脚・橋・トンネル、モノレール、転車台）を、
道路のコンクリート（noisy_material）の物と並べて温暖に敷き、拡大 3 で撮る。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-26_ami333-screens/concrete_scene.py <本体の検証環境> <MCP のポート> <build のフォルダ> <出力のフォルダ>
alpha.6 には転車台が無いので、前の版では [log] に失敗が出る。
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
OX, OY = 60, 60
VIEWS = (("base_wall", 4, 2), ("elev_pier", 4, 14), ("bridge", 5, 24), ("tunnel", 4, 32), ("monorail", 4, 42),
         ("turntable", 3, 52))

with Game(env, "flat_512_left_v64", port, build=build) as g:
    def sq(label, code):
        r = g.sq(code)
        if r not in ("None", "", "null"):
            print(f"[log] {label}: {r}", flush=True)

    def pos(x, y, z=0):
        return f"coord3d({OX + x},{OY + y},{z})"

    def way(name, x1, y1, x2, y2):
        sq(f"{name} ({x1},{y1})", f'try {{ return command_x.build_way(player_x(0), {pos(x1, y1)}, {pos(x2, y2)}, way_desc_x("{name}"), true) }} '
           f'catch (e) {{ return "{name}: " + e }}')

    def wall(name, x1, y1, x2, y2):
        sq(name, f'return command_x.build_wayobj(player_x(0), {pos(x1, y1)}, {pos(x2, y2)}, wayobj_desc_x("{name}"))')

    # 線路の基盤と壁（上）と、道路の基盤と壁（下）
    way("ami_rail_ballast_base_single", 0, 0, 8, 0)
    wall("ami_wall_rail_single", 0, 0, 8, 0)
    way("ami_road_local_base_single", 0, 4, 8, 4)
    wall("ami_wall_road_single", 0, 4, 8, 4)
    # 線路の高架と橋脚（上）と、道路の高架と橋脚（下）
    way("ami_rail_ballast_elev_single", 0, 12, 8, 12)
    way("ami_pier_rail", 0, 12, 8, 12)
    way("ami_road_local_elev_single", 0, 16, 8, 16)
    way("ami_pier_road", 0, 16, 8, 16)
    # 橋
    for bridge, name, y in (("ami_rail_ballast_bridge", "ami_rail_ballast", 22), ("ami_road_local_bridge", "ami_road_local", 26)):
        sq(bridge, f'return command_x.build_bridge(player_x(0), {pos(2, y)}, {pos(8, y)}, bridge_desc_x("{bridge}"))')
        way(name, 0, y, 2, y)
        way(name, 8, y, 10, y)
    # トンネル（2 段の丘）
    for x in range(3, 6):
        for k in range(2):
            sq("raise", f"return command_x.set_slope(player_x(0), {pos(x, 32, k)}, slope.all_up_slope)")
    sq("rampW", f"return command_x.set_slope(player_x(0), {pos(2, 32)}, 24)")
    sq("rampE", f"return command_x.set_slope(player_x(0), {pos(6, 32)}, 56)")
    sq("tunnel", f'return command_x(tool_build_tunnel).work(player_x(0), {pos(2, 32)}, "ami_rail_ballast_tunnel")')
    way("ami_rail_ballast", 0, 32, 2, 32)
    # モノレール（跨座式の地上と高架、懸垂式）
    way("ami_monorail_straddle", 0, 40, 8, 40)
    way("ami_monorail_straddle_elev_back", 0, 43, 8, 43)
    way("ami_monorail_suspended_center", 0, 46, 8, 46)
    # 転車台（左右は線路の行き止まり）
    way("ami_rail_ballast", 0, 52, 2, 52)
    way("ami_rail_ballast", 4, 52, 6, 52)
    way("ami_rail_turntable", 3, 52, 3, 52)
    g.settle(10)
    for name, x, y in VIEWS:
        g.sq(f"gui.close_all_windows(); gui.set_zoom(3); gui.jump({pos(x, y)}); return 1")
        time.sleep(2)
        g.capture(os.path.join(out, f"{name}.png"))
