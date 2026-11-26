"""旅客の数と、駅の範囲・街の建物を、条件ごとに何回も測る（#131）。MIT License。
使い方（リポジトリの直下から）:
  python -X utf8 docs/records/2026-11-26_passengers/measure.py <検証環境> <条件のフォルダ> <出力の jsonl> --conds A,B,C,D --reps 6 --jobs 4 --port 47820
場面は α0.3 の setup.nut（#105 の run4.py と同じ）。置いた直後と、ゲーム内の 30 か月後に読む。
--fixed は、人口を足さずに、駅と停留所の範囲へ集合住宅を置く（置けない所があるので、数は回ごとに違う）。"""
import argparse
import json
import os
import queue
import sys
import threading
import time

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("env")
ap.add_argument("conds_dir")
ap.add_argument("out")
ap.add_argument("--conds", default="A,B,C,D")
ap.add_argument("--reps", type=int, default=6)
ap.add_argument("--jobs", type=int, default=4)
ap.add_argument("--port", type=int, default=47820)
ap.add_argument("--months", type=int, default=30)
ap.add_argument("--fixed", action="store_true", help="街の育ちに頼らず、範囲に同じ集合住宅を置く")
a = ap.parse_args()
# 線路の駅の範囲（y=108・109）と、バス停の範囲（y=58）に集合住宅を置く。置けた数を setup の戻りに足す
FIXED = ('local placed=0; foreach (p in [[44,108],[46,108],[48,108],[50,108],[45,109],[47,109],[49,109],'
         '[90,108],[92,108],[94,108],[96,108],[91,109],[93,109],[95,109],'
         '[58,58],[60,58],[62,58],[98,58],[100,58],[102,58]]) { '
         'if (command_x(tool_build_house).work(player_x(0), coord3d(p[0],p[1],0), "00pak256_apartment") == null) placed++; } '
         's += "placed=" + placed; ')

HEAD = 'local WAY = "ami_road_local"; local RWAY = "ami_rail_ballast"; '
SETUP = "docs/records/2026-11-25_alpha03-screens/setup.nut"
RES = ["pak256_house_small", "pak256_house_wide", "pak256_row_house", "pak256_apartment"]
COM = ["pak256_shop", "pak256_store", "pak256_office"]
IND = ["pak256_workshop", "pak256_warehouse", "pak256_factory"]
LEVEL = {"pak256_house_small": 1, "pak256_house_wide": 1, "pak256_row_house": 2, "pak256_apartment": 3,
         "pak256_shop": 1, "pak256_store": 2, "pak256_office": 3,
         "pak256_workshop": 1, "pak256_warehouse": 2, "pak256_factory": 3, "pak256_townhall": 0}

# 範囲の中の建物を名前ごとに数える。矩形は (x1,y1,x2,y2)
COUNT = ('local cnt={}; for (local y=%d;y<=%d;y++) for (local x=%d;x<=%d;x++) { local t=square_x(x,y).get_ground_tile(); '
         'local b=t.find_object(mo_building); if (b!=null) { local n=b.get_desc().get_name(); if (!(n in cnt)) cnt[n]<-0; cnt[n]++; } } '
         'local s=""; foreach (k,v in cnt) s+=k+"="+v+","; return s;')
# 駅の範囲（station_coverage = 2。駅は x=46..48 と 92..94、y=110）と、街の周り
AREAS = {"cov_railA": (44, 108, 50, 112), "cov_railB": (90, 108, 96, 112),
         "cov_busA": (57, 58, 64, 62), "cov_busB": (97, 58, 104, 62),
         "city_railA": (32, 90, 64, 109), "city_railB": (76, 90, 108, 109)}
CONV = ('local s=""; foreach (c in world.get_convoy_list()) { local t=0; foreach (v in c.get_transported_goods()) t+=v; '
        'local d=0; foreach (v in c.get_traveled_distance()) d+=v; local p=c.get_pos(); '
        's+=(p.y>100?"rail":(c.get_vehicles()[0].get_name()=="pak256_bus"?"bus":"coal"))+"="+t+":"+d+","; } return s;')
HALT = ('local s=""; foreach (p in [[46,110],[92,110]]) { local h=tile_x(p[0],p[1],0).get_halt(); '
        'local f=function(a) { local t=0; foreach (v in a) t+=v; return t; }; '
        's+=f(h.get_departed())+":"+f(h.get_arrived())+":"+f(h.get_happy())+":"+f(h.get_unhappy())+":"+f(h.get_noroute())+":"+f(h.get_walked())+","; } return s;')
CITY = 'local s=""; foreach (c in city_list_x()) { local p=c.get_pos(); s+=p.x+":"+p.y+":"+c.get_citizens()[0]+":"+c.get_buildings()[0]+","; } return s;'
NOW = "local t=world.get_time(); return t.year*12+t.month"
lock = threading.Lock()


def parse_counts(s):
    d = dict((k, int(v)) for k, v in (x.split("=") for x in s.split(",") if x))
    return {"res": sum(d.get(n, 0) for n in RES), "com": sum(d.get(n, 0) for n in COM), "ind": sum(d.get(n, 0) for n in IND),
            "level": sum(LEVEL.get(n, 0) * v for n, v in d.items())}


def snapshot(g):
    r = {k: parse_counts(g.sq(COUNT % (y1, y2, x1, x2))) for k, (x1, y1, x2, y2) in AREAS.items()}
    r["cities"] = g.sq(CITY)
    return r


def one(cond, rep, port):
    base = os.path.join(a.conds_dir, cond)
    work = os.path.join(a.conds_dir, f"_w{port}")
    with Game(a.env, "flat_512_left_v64", port, work=work, build=base + "/build", root=base + "/x/pak256") as g:
        if a.fixed:
            # 街の育ちの偶然を消す: change_size を呼ばず、駅と停留所の範囲に同じ集合住宅を決まった所へ置く
            text = open(SETUP, encoding="utf-8").read()
            assert "c.change_size(300);" in text
            fixed = os.path.join(a.conds_dir, f"_setup{port}.nut")
            with open(fixed, "w", encoding="utf-8", newline="\n") as f:
                f.write(text.replace("c.change_size(300);", "c.get_pos();").replace('return s + "ok";', FIXED + 'return s + " ok";'))
            setup = g.sq_file(fixed, head=HEAD, timeout=200)
        else:
            setup = g.sq_file(SETUP, head=HEAD, timeout=200)
        g.settle(25)
        res = {"cond": cond, "rep": rep, "setup_ok": setup.strip().endswith("ok"), "start": snapshot(g),
               "placed": setup.split("placed=")[-1].split()[0] if "placed=" in setup else None}
        t0 = int(g.sq(NOW))
        g.sq("debug.set_game_speed(128); return 1")
        limit = time.time() + 600
        while int(g.sq(NOW)) < t0 + a.months:
            if time.time() > limit:
                raise RuntimeError("時間切れ")
            time.sleep(3)
        g.sq("debug.set_game_speed(1); return 1")
        res["end"] = snapshot(g)
        res["convoys"] = g.sq(CONV)
        res["halts"] = g.sq(HALT)
    return res


jobs = queue.Queue()
for rep in range(a.reps):
    for cond in a.conds.split(","):
        jobs.put((cond, rep))


def worker(port):
    while True:
        try:
            cond, rep = jobs.get_nowait()
        except queue.Empty:
            return
        try:
            res = one(cond, rep, port)
        except Exception as e:  # 1 回の失敗で全部を止めない
            res = {"cond": cond, "rep": rep, "error": str(e)[-300:]}
        with lock:
            with open(a.out, "a", encoding="utf-8") as f:
                f.write(json.dumps(res, ensure_ascii=False) + "\n")
            print(cond, rep, res.get("convoys", res.get("error")), flush=True)


threads = [threading.Thread(target=worker, args=(a.port + i,)) for i in range(a.jobs)]
for th in threads:
    th.start()
    time.sleep(5)
for th in threads:
    th.join()
print("done")
