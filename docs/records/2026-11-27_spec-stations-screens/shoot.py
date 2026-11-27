"""#206: 仕様のページに載せる駅・停留所・信号の画面の撮影。MIT License。

リポジトリの直下で、先に tools/build.py を流してから:
    python -X utf8 docs/records/2026-11-27_spec-stations-screens/shoot.py <検証環境> <ポート> <出力> <場面>
場面:
- rail: tools/vehicle_check/signal.nut（周回の線路・駅・車庫・信号・編成）。駅と、信号の脇を列車が通る所を何枚も撮る。
- road: tools/vehicle_check/road_stop_bus.nut と road_stop_coal.nut。バス停と荷役所に車が停まる所を何枚も撮る。
ページには、出力から選んで切り出した物を載せる（crop.py）。
"""
import os
import sys
import time

from PIL import Image

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, out, scene = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
CX, CY = 895, 576  # gui.jump で飛んだタイルの中心が出る所（1600x900・拡大 3）


def jump(g, x, y):
    g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(0.5)


def shot(g, name):
    path = f"{out}/{name}.png"
    g.capture(path)
    Image.open(path).convert("RGB").crop((CX - 400, CY - 240, CX + 400, CY + 240)).save(path)


def squirrel(path, head=""):
    with open(path, encoding="utf-8") as f:
        body = " ".join(ln for ln in f.read().splitlines() if not ln.strip().startswith("//"))
    return head + body


def vehicle_on(g, tiles):
    """tiles のどれかに車両がいれば、そのタイル。"""
    code = "local s=\"\"; foreach (p in [%s]) { local t=square_x(p[0],p[1]).get_ground_tile(); if (t.find_object(mo_train) || t.find_object(mo_car)) s+=p[0]+\",\"+p[1]+\" \"; } return s"
    return g.sq(code % ",".join(f"[{x},{y}]" for x, y in tiles)).split()


def watch(g, tiles, name, count, limit=150):
    """tiles に車両が来るたびに撮る（count 枚まで）。"""
    jump(g, *tiles[len(tiles) // 2])
    end, n = time.monotonic() + limit, 0
    while n < count and time.monotonic() < end:
        if vehicle_on(g, tiles):
            shot(g, f"{name}_{n:02d}")
            n += 1
            time.sleep(0.7)
        else:
            time.sleep(0.3)
    print(name, n, flush=True)


with Game(env, "flat_512_left_v64", port, work=out + "/_w", simuconf_extra=["show_names = 0"]) as g:
    g.wait_month(6)
    if scene == "rail":
        print(g.sq(squirrel("tools/vehicle_check/signal.nut"), timeout=90), flush=True)
        g.settle(20)
        jump(g, 46, 60)
        shot(g, "station_empty")
        jump(g, 56, 68)
        shot(g, "station2_empty")
        jump(g, 54, 60)
        shot(g, "signal_top_empty")
        jump(g, 40, 63)
        shot(g, "signal_left_empty")
        g.sq("debug.set_game_speed(4); return 1")
        watch(g, [(45, 60), (46, 60), (47, 60)], "station", 8)
        watch(g, [(54, 60)], "signal_w", 10)
        watch(g, [(60, 60)], "signal_w2", 6)
        watch(g, [(40, 63)], "signal_s", 10)
    elif scene == "road":
        print(g.sq(squirrel("tools/vehicle_check/road_stop_bus.nut"), timeout=90), flush=True)
        print(g.sq(squirrel("tools/vehicle_check/road_stop_coal.nut", "").replace("OX <- 60; OY <- 60;", "OX <- 60; OY <- 90;"), timeout=90), flush=True)
        g.sq("foreach (c in city_list_x()) c.change_size(300); return 1")
        g.settle(20)
        g.sq("debug.set_game_speed(2); return 1")
        watch(g, [(60, 60)], "bus_stop", 8)
        watch(g, [(63, 93)], "truck_stop", 8)
        jump(g, 60, 60)
        shot(g, "bus_stop_last")
    else:
        sys.exit(f"知らない場面: {scene}")
    if g.left_over:
        sys.exit(1)
