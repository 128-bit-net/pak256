"""v0.5.0 の配布の zip の中身だけで、架線の無い路面電車の走る場面を作り、compat050 として保存する。MIT License。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-27_ami189-screens/compat_save.py <検証環境> <ポート> <v0.5.0 の zip> <作業フォルダ>
場面は #153 の tram.nut（架線を足す前の版。v0.5.0 のタグから取る）と tram_cities.nut。作業フォルダは新しい場所を渡す。"""
import os
import shutil
import subprocess
import sys
import time
import zipfile

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, zpath, work = sys.argv[1], int(sys.argv[2]), sys.argv[3], os.path.abspath(sys.argv[4])
x, build = os.path.join(work, "x"), os.path.join(work, "build")
with zipfile.ZipFile(zpath) as z:
    z.extractall(x)
os.makedirs(os.path.join(build, "pak"), exist_ok=True)
for name in os.listdir(os.path.join(x, "pak256")):
    if name.endswith(".pak"):
        shutil.copyfile(os.path.join(x, "pak256", name), os.path.join(build, "pak", name))
    if name == "ami_license.txt":
        shutil.copyfile(os.path.join(x, "pak256", name), os.path.join(build, name))
nut = subprocess.run(["git", "show", "v0.5.0:tools/vehicle_check/tram.nut"], capture_output=True, check=True).stdout.decode("utf-8")
cities = open("tools/vehicle_check/tram_cities.nut", encoding="utf-8").read()
HEAD = "OX <- 60; OY <- 60; CARS <- 1;\n"
READ = ('local s=""; foreach (c in world.get_convoy_list()) { local p=c.get_pos(); local g=0; foreach (v in c.get_transported_goods()) g+=v; '
        's += c.get_name()+" pos="+p.x+","+p.y+" goods12="+g+" depot="+c.is_in_depot()+"; "; } return s')

with Game(env, "flat_512_left_v64", port, work=os.path.join(work, "game"), keep=True,
          build=build, root=os.path.join(x, "pak256"), simuconf_extra=["show_names = 0"]) as g:
    print("tram:", g.sq(HEAD + nut, timeout=90), flush=True)
    print("city:", g.sq(HEAD + cities, timeout=90, player_nr=1), flush=True)
    g.settle(25)
    g.sq("debug.set_game_speed(32); return 1")
    time.sleep(20)
    g.sq("debug.set_game_speed(1); return 1")
    print("read:", g.sq(READ), flush=True)
    g.sq("gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d(66,60,0)); return 1")
    time.sleep(2)
    g.capture(os.path.join(work, "v050_before.png"))
    print("save:", g.sq('world.save_game("compat050"); return 1'), flush=True)
    time.sleep(5)
    if g.left_over:
        sys.exit(1)
