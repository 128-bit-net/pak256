import os, sys, time  # MIT License。使い方: python -X utf8 run1.py <検証環境>（リポジトリの直下から。ポートは 47880〜47899）
sys.path.insert(0, "tools")
from game import Game
V = "work/v031"
HEAD = 'local WAY = "ami_road_local"; local RWAY = "ami_rail_ballast"; '
READ = ('local s=""; foreach (i,c in world.get_convoy_list()) { local p=c.get_pos(); '
        's += i+":"+c.get_name()+" pos="+p.x+","+p.y+" rev="+c.get_revenue()[0]+" / "; } '
        'local t=world.get_time(); s += "year="+t.year+" month="+t.month; return s;')
with Game(sys.argv[1], "flat_512_left_v64", 47882, work=V + "/w1", build=V + "/v030/build", root=V + "/v030/x/pak256", keep=True) as g:
    print("setup:", g.sq_file("docs/records/2026-11-25_alpha03-screens/setup.nut", head=HEAD, timeout=120))
    g.settle(25)
    print("t0:", g.sq(READ))
    g.sq("debug.set_game_speed(128); return 1")
    for i in range(6):
        time.sleep(10)
        print("poll", i, g.sq(READ))
    g.sq("debug.set_game_speed(1); return 1")
    print("save:", g.sq('world.save_game("compat030"); return 1'))
    time.sleep(3)
print(os.listdir(V + "/w1/save"))
