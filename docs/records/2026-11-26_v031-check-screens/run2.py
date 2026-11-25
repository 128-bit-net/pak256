import os, sys, time  # MIT License。使い方: run1.py の後、work/v031/w1/save/compat030.sve を work/v031/env2/save/ に置き（env2 は検証環境の写し）、python -X utf8 run2.py（リポジトリの直下から）
sys.path.insert(0, "tools")
from game import Game
V = "work/v031"
READ = ('local s=""; foreach (i,c in world.get_convoy_list()) { local p=c.get_pos(); '
        's += i+":"+c.get_name()+" pos="+p.x+","+p.y+" rev="+c.get_revenue()[0]+" / "; } '
        'local t=world.get_time(); s += "year="+t.year+" month="+t.month; return s;')
BLD = ('local s=""; foreach (p in [[59,60],[101,60],[119,60],[139,60],[125,61],[46,110],[47,110],[48,110],[92,110],[93,110],[94,110],[60,110]]) { '
       'local t=tile_x(p[0],p[1],0); local b=t.find_object(mo_building); s += p[0]+","+p[1]+"="+(b==null?"none":b.get_desc().get_name())+"; "; } return s;')
with Game(V + "/env2", "compat030", 47883, work=V + "/w2", build=V + "/ci/build", root=V + "/ci/x/pak256", keep=True) as g:
    print("t0:", g.sq(READ))
    print("buildings:", g.sq(BLD))
    print("halts:", g.sq('local s=""; foreach (h in halt_list_x()) { s += h.get_name()+"; "; } return s;'))
    g.sq("debug.set_game_speed(128); return 1")
    for i in range(6):
        time.sleep(10)
        print("poll", i, g.sq(READ))
    g.sq("debug.set_game_speed(1); return 1")
    print("buildings2:", g.sq(BLD))
    g.sq("gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d(93,110,0)); return 1"); time.sleep(2)
    g.capture(V + "/load_rail.png")
    g.sq("gui.close_all_windows(); gui.jump(coord3d(100,60,0)); return 1"); time.sleep(2)
    g.capture(V + "/load_road.png")
print(open(V + "/w2/debug.log", encoding="utf-8", errors="replace").read()[-300:] if os.path.exists(V + "/w2/debug.log") else "")
