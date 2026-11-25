"""街に商業・工業が建つこと、夏と冬の絵（#103）の確かめ。MIT License。tools/game.py の Game で、街を 2 つ置き（A = 温帯 x<256、B = 雪の気候 x>=256）、
人口をスクリプトで足して早送りし、建物の種類ごとの数を読み、季節ごとに撮る。
使い方: python -X utf8 run.py <検証環境> <ポート> <出力フォルダ> [--polls N] [--wait 秒]
注意: run_squirrel に渡す文字列にバックスラッシュを入れない。"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
from game import Game  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("env")
ap.add_argument("port", type=int)
ap.add_argument("out")
ap.add_argument("--polls", type=int, default=40)
ap.add_argument("--wait", type=float, default=15.0)
ap.add_argument("--speed", type=int, default=128)
ap.add_argument("--add", type=int, default=15)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

CITIES = {"A1": (60, 60), "A2": (100, 60), "A3": (140, 60), "A4": (180, 60), "A5": (60, 120), "A6": (100, 120), "B1": (300, 60), "B2": (340, 60)}
GROW = ('foreach (c in city_list_x()) c.change_size(%d); return 1;')
READ = ('local s=""; foreach (c in city_list_x()) { s += c.get_name()+" pop="+c.get_citizens()[0]+" bld="+c.get_buildings()[0]+" / "; }'
        ' local t=world.get_time(); s += "year="+t.year+" month="+t.month; return s;')


def count(cx, cy):
    """街の周り 33x33 の建物を名前ごとに数える（1 文字ずつ）。改行を使わず、区切りは ; にする。"""
    return ('local cnt={}; for (local y=%d-16;y<=%d+16;y++) for (local x=%d-16;x<=%d+16;x++) {'
            ' local b=square_x(x,y).get_ground_tile().find_object(mo_building);'
            ' if (b!=null) { local n=b.get_desc().get_name(); if (!(n in cnt)) cnt[n]<-0; cnt[n]++; } }'
            ' local s=""; foreach (k,v in cnt) s+=k+"="+v+" "; return s;') % (cy, cy, cx, cx)


def shot(g, name, key, zoom=3, dx=0, dy=0):
    cx, cy = CITIES[key]
    g.sq("debug.set_game_speed(1); return 1")
    g.sq(f"gui.close_all_windows(); gui.set_zoom({zoom}); gui.jump(coord3d({cx + dx},{cy + dy},0)); return 1")
    time.sleep(2)
    g.capture(os.path.join(a.out, name))


with Game(a.env, "flat_512_left_v64", a.port) as g:
    log = open(os.path.join(a.out, "run.log"), "w", encoding="utf-8")

    def note(s):
        print(s, flush=True)
        log.write(s + "\n")
        log.flush()

    for key, (cx, cy) in CITIES.items():
        note(f"city {key}: " + g.sq(f"return command_x(tool_add_city).work(player_x(0), coord3d({cx},{cy},0))"))
    note("t0: " + g.sq(READ))
    g.sq("debug.set_game_speed(%d); return 1" % a.speed)
    for i in range(a.polls):
        time.sleep(a.wait)
        g.sq(GROW % a.add)
        note(f"poll {i}: " + g.sq(READ))
        for key, (cx, cy) in CITIES.items():
            note(f"  {key}: " + g.sq(count(cx, cy)))
    g.sq("debug.set_game_speed(1); return 1")
    note("final: " + g.sq(READ))
    best = {}
    for key, (cx, cy) in CITIES.items():
        c = g.sq(count(cx, cy))
        n = sum(int(t.split("=")[1]) for t in c.split() if any(w in t for w in ("shop", "store", "office", "workshop", "warehouse", "factory")))
        tot = sum(int(t.split("=")[1]) for t in c.split())
        note(f"count {key}: com+ind={n} all={tot} {c}")
        if key[0] not in best or (n, tot) > best[key[0]][0]:
            best[key[0]] = ((n, tot), key)
    SEL = [v[1] for v in best.values()]
    note("selected " + str(SEL))
    # 季節: 月を読み、冬（12・1・2 月）と夏（6〜8 月）が来るまで進めて撮る
    shots = {"winter": False, "summer": False}
    for _ in range(40):
        m = int(g.sq("return world.get_time().month"))
        note(f"month raw={m}")
        season = "winter" if m in (11, 0, 1) else "summer" if m in (5, 6, 7) else None
        if season and not shots[season]:
            for key in SEL:
                shot(g, f"{season}_{key}_z3.png", key)
                shot(g, f"{season}_{key}_z2.png", key, zoom=2)
            shots[season] = True
        if all(shots.values()):
            break
        g.sq("debug.set_game_speed(%d); return 1" % a.speed)
        time.sleep(6)
    g.sq("debug.set_game_speed(1); return 1")
    note("done " + str(shots))
