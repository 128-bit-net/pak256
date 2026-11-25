"""街が輸送で育つことの確かめ（#30）。MIT License。tools/game.py の Game で、街を 2 つ置き、バスで旅客を運び、早送りして人口と建物を読む。
使い方: python -X utf8 run.py <検証環境> <ポート> <出力フォルダ> [--extra-pak <車庫の pak>] [--nobus] [--shots 1] [--polls N] [--wait 秒]
人口はスクリプトで足さない。--nobus は車両を出さない比較用（輸送が無いと育たないことの確かめ）。
注意: run_squirrel に渡す文字列にバックスラッシュを入れない（バックスラッシュ+n が本物の改行に化けて、コンパイルが通らない）。"""
import os, sys, time, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
from game import Game

ap = argparse.ArgumentParser()
ap.add_argument("env"); ap.add_argument("port", type=int); ap.add_argument("out")
ap.add_argument("--extra-pak", action="append", default=[])
ap.add_argument("--polls", type=int, default=30)
ap.add_argument("--wait", type=float, default=20.0)
ap.add_argument("--speed", type=int, default=128)
ap.add_argument("--nobus", action="store_true")
ap.add_argument("--shots", default="")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
READ = ('local s=""; foreach (c in city_list_x()) { s += c.get_name()+" pop="+c.get_citizens()[0]+" bld="+c.get_buildings()[0]'
        '+" gen_pax="+c.get_generated_pax()[0]+" tr_pax="+c.get_transported_pax()[0]+" growth="+c.get_growth()[0]+" / "; }'
        ' local t=world.get_time(); s += "year="+t.year+" month="+t.month; return s;')
HEAD = 'local WAY = "ami_road_local"; local DEPOT = ""; local NOBUS = ' + ("true" if a.nobus else "false") + "; "
with Game(a.env, "flat_512_left_v64", a.port, extra_paks=a.extra_pak) as g:
    log = open(os.path.join(a.out, "growth.log"), "w", encoding="utf-8")

    def note(s):
        print(s, flush=True)
        log.write(s + "\n")
        log.flush()

    def shots(tag):
        g.sq("debug.set_game_speed(1); return 1")
        for name, (x, y) in (("A", (60, 58)), ("B", (100, 58))):
            g.sq(f"gui.jump(coord3d({x},{y},0)); return 1")
            time.sleep(2)
            g.capture(os.path.join(a.out, f"{tag}_{name}.png"))
        if tag != "end":
            g.sq(f"debug.set_game_speed({a.speed}); return 1")

    note("setup: " + g.sq_file(os.path.join(HERE, "setup.nut"), head=HEAD, timeout=120))
    g.sq("gui.set_zoom(3); return 1")
    note("t0: " + g.sq(READ))
    if a.shots:
        shots("start")
    g.sq(f"debug.set_game_speed({a.speed}); return 1")
    for i in range(a.polls):
        time.sleep(a.wait)
        note(f"poll {i}: " + g.sq(READ))
        if a.shots and i == a.polls // 2:
            shots("mid")
    if a.shots:
        shots("end")
    g.sq("debug.set_game_speed(1); return 1")
