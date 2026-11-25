"""α0.2 の確かめ（#45）。MIT License。配布の zip（main の CI）から取り出した pak だけで、借り物なしにゲームを起動し、
バスと石炭のトラックを走らせて収入を読み、昼の絵を撮る。
使い方: python -X utf8 run.py <検証環境> <ポート> <出力フォルダ> <pak を取り出した build の代わりのフォルダ（pak/ を持つ）> [--polls N] [--wait 秒]
注意: run_squirrel に渡す文字列にバックスラッシュを入れない。"""
import os, sys, time, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
from game import Game

ap = argparse.ArgumentParser()
ap.add_argument("env"); ap.add_argument("port", type=int); ap.add_argument("out"); ap.add_argument("build")
ap.add_argument("--polls", type=int, default=24)
ap.add_argument("--wait", type=float, default=15.0)
ap.add_argument("--speed", type=int, default=128)
ap.add_argument("--trace", action="store_true")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
READ = ('local s=""; foreach (c in world.get_convoy_list()) { local p=c.get_pos(); '
        's += c.get_name()+" pos="+p.x+","+p.y+" rev="+c.get_revenue()[0]+" profit="+c.get_profit()[0]+" cap="+c.get_capacity()[0]+" / "; } '
        'local t=world.get_time(); s += "year="+t.year+" month="+t.month; return s;')
POS = ('local s=""; foreach (i,c in world.get_convoy_list()) { local p=c.get_pos(); s += i+":"+p.x+","+p.y+","+c.get_speed()+";"; } return s;')
HEAD = 'local WAY = "ami_road_local"; '
with Game(a.env, "flat_512_left_v64", a.port, build=a.build) as g:
    log = open(os.path.join(a.out, "run.log"), "w", encoding="utf-8")

    def note(s):
        print(s, flush=True)
        log.write(s + "\n")
        log.flush()

    note("setup: " + g.sq_file(os.path.join(HERE, "setup.nut"), head=HEAD, timeout=120))
    g.sq("gui.set_zoom(3); return 1")
    note("t0: " + g.sq(READ))
    g.sq(f"debug.set_game_speed({a.speed}); return 1")
    for i in range(a.polls):
        time.sleep(a.wait)
        note(f"poll {i}: " + g.sq(READ))
        if a.trace:  # 止まったときの原因（ダイアログ）を見るための撮影
            g.capture(os.path.join(a.out, "trace", f"poll{i:02d}.png"))
    g.sq("debug.set_game_speed(1); return 1")
    note("pos: " + g.sq(POS))
    note("end: " + g.sq(READ))
    # 昼の絵（昼夜は止めてある）。編成の今の場所へ飛んで撮る
    pos = [tuple(int(v) for v in item.split(":")[1].split(",")[:2]) for item in g.sq(POS).split(";") if item]
    for i, (x, y) in enumerate(pos):
        g.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
        time.sleep(2)
        g.capture(os.path.join(a.out, f"convoy{i}_{x}_{y}.png"))
    for name, (x, y) in (("townA", (60, 59)), ("townB", (100, 59)), ("coal", (128, 59))):
        g.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
        time.sleep(2)
        g.capture(os.path.join(a.out, f"{name}.png"))
    for name, n in (("finances", 5), ("convoys", 15), ("factories", 18)):
        note(f"open {name}: " + g.sq(f"gui.close_all_windows(); gui.open_dialog_tool({n}); return 1"))
        time.sleep(2)
        g.capture(os.path.join(a.out, f"{name}.png"))
    if g.left_over:
        sys.exit(1)
