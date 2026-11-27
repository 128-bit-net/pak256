"""架線の無い路面軌道で路面電車（electric）がどうなるかを確かめる。MIT License。
使い方（リポジトリの直下で）: python -X utf8 docs/records/2026-11-27_ami189-screens/nocat.py <検証環境> <ポート> <build のフォルダ> <出力フォルダ>
tools/vehicle_check/tram.nut を、架線なし（CATENARY 0）と道路の区間と車庫だけ（2）で流し、編成の場所・車庫の中か・運んだ数を読んで撮る。"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
os.makedirs(out, exist_ok=True)
nut = open("tools/vehicle_check/tram.nut", encoding="utf-8").read()
READ = ('local s=""; foreach (c in world.get_convoy_list()) { local p=c.get_pos(); local g=0; foreach (v in c.get_transported_goods()) g+=v; '
        's += "pos="+p.x+","+p.y+" depot="+c.is_in_depot()+" waiting="+c.is_waiting()+" goods12="+g+"; "; } return s')
for cat in (0, 2):
    with Game(env, "flat_512_left_v64", port, work=os.path.join(out, f"_w{cat}"), build=build,
              simuconf_extra=["show_names = 0"]) as g:
        print(cat, g.sq(f"OX <- 60; OY <- 60; CARS <- 1; CATENARY <- {cat};\n" + nut, timeout=90), flush=True)
        g.settle(25)
        g.sq("debug.set_game_speed(16); return 1")
        for i in range(4):
            time.sleep(8)
            print(cat, "read", i, g.sq(READ), flush=True)
        g.sq("debug.set_game_speed(1); return 1")
        pos = g.sq("local c=world.get_convoy_list(); foreach (v in c) { local p=v.get_pos(); return p.x+\",\"+p.y } return \"\"")
        x, y = (int(v) for v in pos.split(",")) if pos else (57, 60)
        g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
        time.sleep(2)
        g.capture(os.path.join(out, f"nocat{cat}.png"))
        g.dialog(15)  # 乗り物の一覧
        time.sleep(1)
        g.capture(os.path.join(out, f"nocat{cat}_list.png"))
    if g.left_over:
        sys.exit(1)
