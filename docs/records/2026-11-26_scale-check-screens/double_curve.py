"""隣り合う 2 本の線路の曲がりで、描き直した気動車 + 付随車が隣の線路にはみ出さないかを撮る（#104）。MIT License。

使い方: python -X utf8 double_curve.py <検証環境> <ポート> <出力フォルダ（git 管理外）>   （先に tools/build.py）
外側の線路（北の辺 y=100 → 東の辺 x=52）と、1 タイル内側の線路（y=101 → x=51）に、それぞれ 1 編成を往復させ、
どちらかの先頭が曲がりの角の近くに来るたびに、角を真ん中にして撮る。
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
from game import Game  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("env")
ap.add_argument("port", type=int)
ap.add_argument("out")
ap.add_argument("--seconds", type=float, default=240.0)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
RAIL = "ami_rail_ballast"


def c(x, y):
    return f"coord3d({x},{y},0)"


with Game(a.env, "flat_512_left_v64", a.port) as g:
    # (角の x, 北の辺の y, 車庫の脇の向き)
    for cx, y, side in ((52, 100, -1), (51, 101, 1)):
        # 線路は隣のタイルへ 1 つずつ敷く（長く敷くと本体が別の経路を選ぶことがある。rail_curve.nut と同じ）
        tiles = [(x, y) for x in range(36, cx + 1)] + [(cx, yy) for yy in range(y + 1, 115)]
        for (x0, y0), (x1, y1) in zip(tiles, tiles[1:]):
            r = g.road(x0, y0, x1, y1, RAIL)
            if r != "None":
                print("way", x0, y0, r)
        for x in range(40, 43):
            print(g.station(x, y, "pak256_train_station"))
        for yy in range(109, 112):
            print(g.station(cx, yy, "pak256_train_station"))
        g.road(38, y + side, 38, y, RAIL)
        print(g.sq('local dd=null; foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) '
                   'if (d.get_name()=="ami_rail_depot") dd=d; '
                   f'return command_x.build_depot(player_x(0), {c(38, y + side)}, dd)'))
    for cx, y, side in ((52, 100, -1), (51, 101, 1)):
        code = (f'local pl=player_x(0); local depot=depot_x(38,{y + side},0); local car=null, tr=null; '
                'foreach (v in vehicle_desc_x.get_available_vehicles(wt_rail)) { '
                'if (v.get_name()=="pak256_railcar") car=v; if (v.get_name()=="pak256_railcar_trailer") tr=v; } '
                'depot.append_vehicle(pl, convoy_x(0), car); local l=depot.get_convoy_list(); local cnv=l[l.len()-1]; '
                'depot.append_vehicle(pl, cnv, tr); '
                f'cnv.change_schedule(pl, schedule_x(wt_rail, [schedule_entry_x({c(41, y)},0,0), '
                f'schedule_entry_x({c(cx, 110)},0,0)])); depot.start_convoy(pl, cnv); return "ok"')
        print(g.sq(code, timeout=60))
    g.settle(20)
    g.sq("debug.set_game_speed(1); gui.set_zoom(3); return 1")
    query = ('local s=""; foreach (v in world.get_convoy_list()) { local p=v.get_pos(); s += p.x + " " + p.y + ";"; } return s')
    t0, n, last = time.time(), 0, None
    while time.time() - t0 < a.seconds and n < 40:
        pos = [tuple(int(v) for v in r.split()) for r in g.sq(query).split(";") if r]
        near = [p for p in pos if abs(p[0] - 51) <= 2 and abs(p[1] - 101) <= 2]
        if near and pos != last:
            g.sq(f"gui.close_all_windows(); gui.jump({c(51, 101)}); return 1")
            g.capture(os.path.join(a.out, f"curve_{n:02d}_{len(near)}.png"))
            print("[shot]", n, pos, flush=True)
            n, last = n + 1, pos
        time.sleep(0.3)
