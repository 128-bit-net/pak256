"""α0.3 の確かめ（#70）。MIT License。配布の zip（main の CI）から取り出した pak だけで、借り物なしにゲームを起動し、
バス・石炭のトラック・列車を走らせて収入を読み、昼の絵を撮る。
使い方: python -X utf8 run.py <検証環境> <ポート> <出力フォルダ> <pak/ を持つ build の代わりのフォルダ> --root <zip を展開した pak256/（config/・text/ を持つ）> [--polls N] [--wait 秒]
注意: run_squirrel に渡す文字列にバックスラッシュを入れない。"""
import os, sys, time, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
from game import Game

ap = argparse.ArgumentParser()
ap.add_argument("env"); ap.add_argument("port", type=int); ap.add_argument("out"); ap.add_argument("build")
ap.add_argument("--root", required=True)
ap.add_argument("--polls", type=int, default=24)
ap.add_argument("--wait", type=float, default=15.0)
ap.add_argument("--speed", type=int, default=128)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
READ = ('local s=""; foreach (i,c in world.get_convoy_list()) { local p=c.get_pos(); '
        's += i+":"+c.get_name()+" pos="+p.x+","+p.y+" rev="+c.get_revenue()[0]+" profit="+c.get_profit()[0]+" / "; } '
        'local t=world.get_time(); s += "year="+t.year+" month="+t.month; return s;')
POS = ('local s=""; foreach (i,c in world.get_convoy_list()) { local p=c.get_pos(); s += i+":"+p.x+","+p.y+","+c.get_speed()+";"; } return s;')
HEAD = 'local WAY = "ami_road_local"; local RWAY = "ami_rail_ballast"; '
with Game(a.env, "flat_512_left_v64", a.port, build=a.build, root=a.root) as g:
    log = open(os.path.join(a.out, "run.log"), "w", encoding="utf-8")

    def note(s):
        print(s, flush=True)
        log.write(s + "\n")
        log.flush()

    note("setup: " + g.sq_file(os.path.join(HERE, "setup.nut"), head=HEAD, timeout=120))
    g.settle(25)  # 建物の建設中の絵が終わるまで
    g.sq("gui.set_zoom(3); return 1")
    note("t0: " + g.sq(READ))
    g.sq(f"debug.set_game_speed({a.speed}); return 1")
    for i in range(a.polls):
        time.sleep(a.wait)
        note(f"poll {i}: " + g.sq(READ))
    g.sq("debug.set_game_speed(1); return 1")
    note("pos: " + g.sq(POS))
    note("end: " + g.sq(READ))
    pos = [tuple(int(v) for v in item.split(":")[1].split(",")[:2]) for item in g.sq(POS).split(";") if item]
    for i, (x, y) in enumerate(pos):
        g.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
        time.sleep(2)
        g.capture(os.path.join(a.out, f"convoy{i}_{x}_{y}.png"))
    for name, (x, y) in (("townA", (60, 59)), ("rail_stationA", (47, 110)), ("rail_stationB", (93, 110))):
        g.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
        time.sleep(2)
        g.capture(os.path.join(a.out, f"{name}.png"))
    for name, n in (("finances", 5), ("convoys", 15)):
        note(f"open {name}: " + g.sq(f"gui.close_all_windows(); gui.open_dialog_tool({n}); return 1"))
        time.sleep(2)
        g.capture(os.path.join(a.out, f"{name}.png"))
    if g.left_over:
        sys.exit(1)
