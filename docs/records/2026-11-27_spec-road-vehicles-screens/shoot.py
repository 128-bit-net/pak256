"""#205: 仕様のページに載せる道路の画面の撮影。MIT License。

リポジトリの直下で、先に tools/build.py を流してから:
    python -X utf8 docs/records/2026-11-27_spec-road-vehicles-screens/shoot.py <検証環境> <ポート> <出力>
東西の道に街 2 つ・バス停・バスと郵便のトラックを置き（tools/vehicle_check/road_stop_bus.nut）、街の車を置いて、
バス停の周り・街の車のいる所・歩行者のいる所を何枚も撮る。ページには、出力から選んで切り出した物を載せる。
"""
import os
import sys
import time

from PIL import Image

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
os.makedirs(out, exist_ok=True)
CX, CY = 895, 576  # gui.jump で飛んだタイルの中心が出る所（1600x900・拡大 3）
CARS = ("pak256_citycar_small", "pak256_citycar_sedan", "pak256_citycar_large")


def shot(g, x, y, name):
    g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(0.5)
    path = f"{out}/{name}.png"
    g.capture(path)
    Image.open(path).convert("RGB").crop((CX - 400, CY - 240, CX + 400, CY + 240)).save(path)


def sheet(names, name, cols=3):
    images = [Image.open(f"{out}/{n}.png") for n in names]
    big = Image.new("RGB", (800 * cols, 480 * ((len(images) + cols - 1) // cols)))
    for i, im in enumerate(images):
        big.paste(im, (800 * (i % cols), 480 * (i // cols)))
    big.resize((big.width // 2, big.height // 2)).save(f"{out}/{name}.png")


with Game(env, "flat_512_left_v64", port, work=out + "/_w", simuconf_extra=["show_names = 0"]) as g:
    g.wait_month(6)
    with open("tools/vehicle_check/road_stop_bus.nut", encoding="utf-8") as f:
        print(g.sq(" ".join(ln for ln in f.read().splitlines() if not ln.strip().startswith("//"))), flush=True)
    g.sq("foreach (c in city_list_x()) c.change_size(500); return 1")
    g.settle(20)
    # 街の車: バス停の近くの道に、3 種を順に置く
    i = 0
    for x in range(63, 80):
        e = g.sq(f'local e = command_x(tool_add_citycar).work(player_x(1), coord3d({x},60,0), "{CARS[i % 3]}"); return e == null ? "ok" : e')
        if e.strip().endswith("ok"):
            i += 1
        if i >= 9:
            break
    print("citycars", i, flush=True)
    cars, stops = [], []
    for n in range(12):
        time.sleep(1.0)
        shot(g, 66 + (n % 4) * 3, 60, f"cars_{n:02d}")
        cars.append(f"cars_{n:02d}")
        shot(g, 60, 60, f"stop_{n:02d}")
        stops.append(f"stop_{n:02d}")
    sheet(cars, "cars_sheet")
    sheet(stops, "stop_sheet")
    peds = []
    scan = ('local s=""; for(local x=45;x<=115;x++) for(local y=45;y<=75;y++){ local t=square_x(x,y).get_ground_tile(); '
            'if (t.find_object(mo_pedestrian)) s+=x+","+y+" "; } return s')
    for n in range(200):
        tiles = [tuple(map(int, p.split(","))) for p in g.sq(scan).split()]
        if not tiles:
            time.sleep(1)
            continue
        x, y = tiles[(n * 5) % len(tiles)]
        shot(g, x, y, f"ped_{len(peds):02d}")
        peds.append(f"ped_{len(peds):02d}")
        time.sleep(1)
        if len(peds) >= 12:
            break
    print("peds", len(peds), flush=True)
    if peds:
        sheet(peds, "ped_sheet")
    if g.left_over:
        sys.exit(1)
