"""#207: 仕様のページに載せる船・港、飛行機・空港、川の画面の撮影。MIT License。

リポジトリの直下で、先に tools/build.py を流してから:
    python -X utf8 docs/records/2026-11-27_spec-ship-air-screens/shoot.py <検証環境> <ポート> <出力> <場面>
場面:
- ship: tools/vehicle_check/ship.nut（海の桟橋・岸壁と、運河の船着き場）。港と、走る船を何枚も撮る。
- air: tools/vehicle_check/air_run.py の空港 2 つと旅客機。空港の全体（縮小）と、旅客機を追った画面を撮る。
- river: river_terrain.nut と river_enlarge.nut（地図の拡大で川を引く）。合流の所と河口を撮る。
MCP のクライアントは環境変数 MCP_CLIENT（docs/game-check.md）。ページには、出力から選んで切り出した物を載せる（crop.py）。
"""
import os
import sys
import time

sys.path.insert(0, "tools")
sys.path.insert(0, "tools/vehicle_check")
from game import Game  # noqa: E402

env, port, out, scene = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), sys.argv[4]
os.makedirs(out, exist_ok=True)


def jump(g, x, y, z=0, zoom=3):
    g.sq(f"gui.set_zoom({zoom}); gui.close_all_windows(); gui.jump(coord3d({x},{y},{z})); return 1")
    time.sleep(0.8)


def shot(g, name):
    g.capture(f"{out}/{name}.png")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def convoys(g):
    return g.sq('local s=""; foreach (c in world.get_convoy_list()) { local p=c.get_pos(); s+=p.x+" "+p.y+" "+p.z+";"; } return s')


with Game(env, "flat_512_left_v64", port, work=out + "/_w", simuconf_extra=["show_names = 0"]) as g:
    if scene == "ship":
        print(g.sq(read("tools/vehicle_check/ship.nut"), timeout=120), flush=True)
        g.settle(25)
        jump(g, 49, 86, -1, 3)
        shot(g, "sea_mid")
        for name, (x, y, z) in (("pier", (49, 80, -1)), ("quay", (49, 92, -1)), ("wharf", (75, 104, 0)),
                                ("wharf2", (96, 104, 0))):
            jump(g, x, y, z)
            shot(g, f"{name}_still")
        g.sq("debug.set_game_speed(4); return 1")
        for i in range(40):
            time.sleep(1.0)
            rows = [r.split() for r in convoys(g).split(";") if r]
            print(i, rows, flush=True)
            # 順に: 海の旅客船、貨物船、運河の旅客船
            for k, row in enumerate(rows):
                if i % 3 == k:
                    x, y, z = (int(v) for v in row)
                    jump(g, x, y, z)
                    shot(g, f"ship{k}_{i:02d}_{x}_{y}")
    elif scene == "air":
        import air_run
        # 街の建物は駅の手前に並んで駅と飛行機を隠すので、置かない（旅客は乗らない）
        print(g.sq(air_run.HEAD + read("tools/vehicle_check/air.nut"), timeout=120), flush=True)
        g.settle(20)
        for zoom in (4, 5, 6):
            jump(g, 69, 102, 0, zoom)
            shot(g, f"airport_zoom{zoom}")
        g.sq("debug.set_game_speed(1); return 1")
        for i in range(60):
            time.sleep(1.5)
            row = [r for r in g.sq(air_run.QUERY).split(";") if r]
            if not row:
                continue
            x, y, z = (int(v) for v in row[0].split()[:3])
            jump(g, x, y, z)
            shot(g, f"plane_{i:02d}_{x}_{y}_{z}")
    elif scene == "river":
        terrain = read("tools/vehicle_check/river_terrain.nut")
        enlarge = read("tools/vehicle_check/river_enlarge.nut")
        for y0 in range(100, 320, 20):
            print(g.sq(f"local STEP = 0, Y0 = {y0}, HILL = 0;\n" + terrain, timeout=280), flush=True)
        print(g.sq("local STEP = 2, Y0 = 0, HILL = 0;\n" + terrain, timeout=280), flush=True)
        for hill in range(12):
            print(g.sq(f"local STEP = 1, Y0 = 0, HILL = {hill};\n" + terrain, timeout=280), flush=True)
        g.sq("gui.close_all_windows(); return gui.open_dialog_tool(24)")
        for what, n in (("size", 0), ("climate", 0), ("rivers", 9), ("start", 0)):
            r = g.sq(f'local WHAT = "{what}", N = {n};\n' + enlarge, timeout=280)
            print(what, r, flush=True)
            if r.startswith("no "):
                sys.exit(r)
            time.sleep(1)
        # 海の近くの大きな川の合流（3 方向以上につながる升）を探す
        found = g.sq(
            'local s=""; local n=0; for (local x=186; x>20 && n<8; x--) for (local y=100; y<320 && n<8; y++) {'
            ' local g=square_x(x,y).get_ground_tile(); local w=g.get_way(wt_water); if (w==null) continue;'
            ' local d=g.get_way_dirs(wt_water); if ((d==7||d==11||d==13||d==14) && w.get_desc().get_name()=="pak256_river_30")'
            ' { s+=x+" "+y+" "+g.z+";"; n++; y+=15; } } return s', timeout=200)
        print("junctions", found, flush=True)
        for i, row in enumerate([r.split() for r in found.split(";") if r]):
            x, y, z = (int(v) for v in row)
            for zoom in (3, 5):
                jump(g, x, y, z, zoom)
                shot(g, f"junction{i}_zoom{zoom}_{x}_{y}")
    else:
        sys.exit(f"知らない場面: {scene}")
    if g.left_over:
        sys.exit(1)
