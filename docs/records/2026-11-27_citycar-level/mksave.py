"""街の車が出ない状態で街とバスを作り、このフォルダに town182.sve を保存する（pak256#182）。MIT License。

    PAK256_GAME_ENV=<検証環境> python -X utf8 mksave.py
"""
import os, shutil, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ENV = os.environ["PAK256_GAME_ENV"]  # 本体の検証環境（docs/game-check.md の --env）
sys.path.insert(0, os.path.join(ROOT, "tools"))
from game import Game

HERE = os.path.dirname(os.path.abspath(__file__))
with Game(ENV, "flat_512_left_v64", 47886, simuconf_extra=["show_names = 0"]) as g:
    g.sq("settings.set_traffic_level(0); return 1")
    time.sleep(1)
    print(g.sq_file(os.path.join(HERE, "setup.nut"), timeout=200))
    time.sleep(1)
    g.settle(20)
    print(g.sq('local s=""; foreach(c in city_list_x()) { local p=c.get_pos(); s+=p.x+","+p.y+":"+c.get_citizens()[0]+" "; } local n=0; foreach(c in world.get_convoy_list()) n++; return s + " convoys " + n'))
    print(g.sq('return world.get_time().year + " " + world.get_time().month'))
    g.sq('world.save_game("town182"); return 1')
    time.sleep(10)
    src = os.path.join(g.work, "save", "town182.sve")
    print(os.listdir(os.path.join(g.work, "save")), os.listdir(g.work)[:30])
    shutil.copy(src, os.path.join(HERE, "town182.sve"))
    print("saved", os.path.getsize(os.path.join(HERE, "town182.sve")))
