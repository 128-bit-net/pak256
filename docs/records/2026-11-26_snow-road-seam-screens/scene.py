"""雪の道路の下の縁の線（#141）の切り分け。MIT License。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-26_snow-road-seam-screens/scene.py <検証環境> <ポート> <build のフォルダ> <出力フォルダ>
雪の気候（x>=256）に同じ形の格子（5x5。角・分かれ目・十字）を 3 通りで敷いて撮り、街を 1 つ置いて街が建てた道の way を数える。
- city: 街の道路の道具（公共のプレーヤー。歩道つき） y=100
- base: ami_road_local_base_single を手で敷く（歩道なし） y=130
- hand: ami_road_local を手で敷く（歩道なし） y=160
街は (320, 300)。"""
import json
import os
import sys
import time

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
X0 = 316
ROWS = {"city": 100, "base": 130, "hand": 160}
COUNT = ("local c={}; for(local x=300;x<340;x++) for(local y=280;y<320;y++) {"
         " local w=square_x(x,y).get_ground_tile().find_object(mo_way);"
         ' if(w){ local k=w.get_desc().get_name()+"/sidewalk="+w.has_sidewalk(); c[k] <- (k in c ? c[k] : 0)+1 } };'
         ' local s=""; foreach(k,v in c) s+=k+":"+v+"; "; return s')


def say(*a):
    print(*a, flush=True)


def sq_public(g, code):
    """公共のプレーヤー（1）として Squirrel を流す。"""
    r = g._client("--player-nr", "1", "--run-squirrel", code, timeout=30)
    return str(json.loads(r.stdout.strip().splitlines()[-1])["result"])


def shot(g, x, y, name):
    g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(4)
    g.capture(os.path.join(out, name + ".png"))


with Game(env, "flat_512_left_v64", port, work=out + "/_w", build=build, simuconf_extra=["show_names = 0"]) as g:
    g.climate(X0 - 16, 90, X0 + 24, 176, "arctic", timeout=120)
    g.climate(300, 280, 340, 320, "arctic", timeout=120)
    for kind, y0 in ROWS.items():
        for d in (0, 2, 4):
            for a, b in (((X0, y0 + d), (X0 + 4, y0 + d)), ((X0 + d, y0), (X0 + d, y0 + 4))):
                if kind == "city":
                    sq_public(g, f'return command_x(tool_build_cityroad).work(player_x(1), coord3d({a[0]},{a[1]},0), '
                                 f'coord3d({b[0]},{b[1]},0), "")')
                else:
                    g.road(a[0], a[1], b[0], b[1], "ami_road_local_base_single" if kind == "base" else "ami_road_local")
        say(kind, g.sq(f"local t=square_x({X0},{y0}).get_ground_tile(); local w=t.find_object(mo_way); "
                       f'return w ? w.get_desc().get_name() + ":" + w.has_sidewalk() : "no way"'))
    g.sq("return command_x(tool_add_city).work(player_x(1), coord3d(320,300,0))")
    say("town", g.sq(COUNT))
    g.wait_month(6)
    time.sleep(8)
    for kind, y0 in ROWS.items():
        shot(g, X0 + 2, y0 + 2, kind)
    g.settle(15)
    shot(g, 320, 300, "town")
    if g.left_over:
        sys.exit(1)
