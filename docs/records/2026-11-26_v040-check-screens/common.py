"""#105 の確かめの共通部分。MIT License。"""
import sys
import time

sys.path.insert(0, "tools")
from game import Game  # noqa: E402,F401

V = "work/a04"
HEAD = 'local WAY = "ami_road_local"; local RWAY = "ami_rail_ballast"; '
SETUP = "docs/records/2026-11-25_alpha03-screens/setup.nut"
# 編成: 位置・収入（今月・先月）
READ = ('local s=""; foreach (i,c in world.get_convoy_list()) { local p=c.get_pos(); local r=c.get_revenue(); '
        's += i+":"+c.get_name()+" pos="+p.x+","+p.y+","+p.z+" rev="+r[0]+"/"+r[1]+" depot="+c.is_in_depot()+" ; "; } '
        'local t=world.get_time(); s += "year="+t.year+" month="+t.month; return s;')
TILES = [[59, 60], [101, 60], [119, 60], [139, 60], [125, 61], [46, 110], [92, 110], [70, 111],
         [55, 75], [70, 75], [85, 75], [62, 66], [64, 66], [66, 66]]
# タイルの物: 建物の名前・車庫（道路・線路）・木・道路・停留所
OBJ = ('local s=""; foreach (p in %s) { local t=tile_x(p[0],p[1],0); local o=[]; '
       'local b=t.find_object(mo_building); if (b!=null) o.append("b:"+b.get_desc().get_name()); '
       'if (t.find_object(mo_depot_road)!=null) o.append("depot_road"); '
       'if (t.find_object(mo_depot_rail)!=null) o.append("depot_rail"); '
       'local tr=t.find_object(mo_tree); if (tr!=null) o.append("tree:"+tr.get_desc().get_name()); '
       'local w=t.find_object(mo_way); if (w!=null) o.append("way:"+w.get_desc().get_name()); '
       'local h=t.get_halt(); if (h!=null) o.append("halt:"+h.get_name()); '
       's += p[0]+","+p[1]+"=["; foreach (v in o) s += v+" "; s += "]; "; } return s;') % str(TILES)
HALTS = 'local s=""; foreach (h in halt_list_x()) { s += h.get_name()+" ("+h.get_tile_list().len()+"); "; } return s;'


def poll(g, n, wait=10, speed=128):
    g.sq(f"debug.set_game_speed({speed}); return 1")
    for i in range(n):
        time.sleep(wait)
        print("poll", i, g.sq(READ), flush=True)
    g.sq("debug.set_game_speed(1); return 1")


def shot(g, x, y, path):
    g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(3)
    g.capture(path)
