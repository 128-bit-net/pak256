import os, sys, time  # MIT License。使い方: python -X utf8 run3.py <検証環境>（リポジトリの直下から。ポートは 47880〜47899）
sys.path.insert(0, "tools")
from game import Game
V = "work/v031"
HEAD = 'local WAY = "ami_road_local"; local RWAY = "ami_rail_ballast"; '
READ = ('local s=""; foreach (i,c in world.get_convoy_list()) { local p=c.get_pos(); '
        's += i+":"+c.get_name()+" pos="+p.x+","+p.y+" rev="+c.get_revenue()[0]+" / "; } '
        'local t=world.get_time(); s += "year="+t.year+" month="+t.month; return s;')
with Game(sys.argv[1], "flat_512_left_v64", 47884, work=V + "/w3", build=V + "/ci/build", root=V + "/ci/x/pak256") as g:
    print("setup:", g.sq_file("docs/records/2026-11-25_alpha03-screens/setup.nut", head=HEAD, timeout=120).replace("\n", " | ")[-400:])
    g.settle(25)
    print("depot:", g.sq('local t=tile_x(125,61,0); local d=t.find_object(mo_depot_road); return d==null?"none":"depot ok";'))
    g.sq("debug.set_game_speed(128); return 1")
    for i in range(12):
        time.sleep(10)
        print("poll", i, g.sq(READ))
    g.sq("debug.set_game_speed(1); return 1")
    g.sq("gui.set_zoom(3); gui.close_all_windows(); gui.open_dialog_tool(15); return 1"); time.sleep(2)
    g.capture(V + "/run3_convoys.png")
    if g.left_over: sys.exit(1)
