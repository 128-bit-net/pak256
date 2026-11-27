"""v0.5.0 で作った保存データ compat050（架線の無い路面電車が走る）を、今の pak で読む。MIT License。
使い方（リポジトリの直下で）: python -X utf8 docs/records/2026-11-27_ami189-screens/compat_load.py <compat050 を置いた環境の写し> <ポート> <build のフォルダ> <出力フォルダ>
環境の写しは docs/records/2026-11-26_v040-check-screens/mkenv.py で作る（検証環境には書かない）。道路名は書き換えない。
起動のログ（-log -debug 3 の simu.log）の Warning・ERROR も出す。読み込んだ後に走らせ、架線を張って車庫に戻せば再び走ることも見る。"""
import os
import sys
import time

sys.path.insert(0, "tools")
import game  # noqa: E402
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
os.makedirs(out, exist_ok=True)
orig = game.launch_command
game.launch_command = lambda *a, **k: orig(*a, **k) + ["-log", "-debug", "3"]
READ = ('local s=""; foreach (c in world.get_convoy_list()) { local p=c.get_pos(); local g=0; foreach (v in c.get_transported_goods()) g+=v; '
        's += c.get_name()+" pos="+p.x+","+p.y+" goods12="+g+" depot="+c.is_in_depot()+" electric_needed="+c.needs_electrification()+"; "; } return s')
CAT = ('local pl=player_x(0); local w=wayobj_desc_x("ami_tram_catenary"); local s=""; '
       'foreach (g in [[[57,60],[76,60]],[[76,60],[76,68]],[[76,68],[76,74]],[[76,74],[96,74]],[[96,74],[96,68]]]) { '
       'local e=command_x.build_wayobj(pl, coord3d(g[0][0],g[0][1],0), coord3d(g[1][0],g[1][1],0), w); if (e!=null) s+=e+" " } return s')


def poll(g, label, n):
    g.sq("debug.set_game_speed(16); return 1")
    for i in range(n):
        time.sleep(8)
        print(label, i, g.sq(READ), flush=True)
    g.sq("debug.set_game_speed(1); return 1")


def shot(g, name):
    pos = g.sq('foreach (c in world.get_convoy_list()) { local p=c.get_pos(); return p.x+","+p.y } return "66,60"')
    x, y = (int(v) for v in pos.split(","))
    g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(2)
    g.capture(os.path.join(out, name))


with Game(env, "compat050", port, build=build, work=os.path.join(out, "_w"), keep=True, rewrite_roads=False,
          simuconf_extra=["show_names = 0"]) as g:
    g.capture(os.path.join(out, "loaded.png"))
    print("t0", g.sq(READ), flush=True)
    poll(g, "nocat", 4)
    shot(g, "nocat.png")
    print("catenary:", g.sq(CAT), flush=True)
    poll(g, "cat", 6)
    shot(g, "cat.png")
    if g.left_over:
        sys.exit(1)
