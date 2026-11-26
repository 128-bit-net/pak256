"""歩く位置を撮る（#172）。MIT License。
使い方（リポジトリの直下から）:
    python -X utf8 docs/records/2026-11-27_pedestrians-screens/walk.py loops <検証環境> <ポート> <印の pak> <出力>
        小さな四角の周回路（角 4 つ）を並べ、角にいる歩行者を撮って、斜めの 4 向き（sw・se・ne・nw）の色を拾う
    ... walk.py places <検証環境> <ポート> <pak> <出力>
        直線・交差点・階段の道（1 タイルごとに曲がる）にいる歩行者を撮る。ファイル名は 種類_番号_x_y"""
import os
import sys
import time

from PIL import Image

sys.path.insert(0, "tools")
sys.path.insert(0, "objects/pedestrian/walkers")
from game import Game  # noqa: E402
import draw_pedestrians as D  # noqa: E402

mode, env, port, pak, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
os.makedirs(out, exist_ok=True)
CX, CY = 895, 576  # positions.py と同じ
WAY = "ami_road_local"


def peds(g, area, ribis=None):
    x0, x1, y0, y1 = area
    cond = "" if ribis is None else " && (" + " || ".join(f"d=={r}" for r in ribis) + ")"
    s = g.sq(f'local s=""; for(local x={x0};x<={x1};x++) for(local y={y0};y<={y1};y++){{ local t=square_x(x,y).get_ground_tile(); '
             f'local d=t.get_way_dirs(wt_road); if (t.find_object(mo_pedestrian){cond}) s+=x+","+y+" "; }} return s')
    return [tuple(map(int, p.split(","))) for p in s.split()]


def shot(g, x, y, path):
    g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(0.4)
    g.capture(path)
    return Image.open(path).convert("RGB")


def city(g, x, y, size):
    g.sq(f"return command_x(tool_add_city).work(player_x(1), coord3d({x},{y},0))")
    g.sq(f"foreach (c in city_list_x()) c.change_size({size}); return 1")


with Game(env, "flat_512_left_v64", port, work=out + "/_w", pak_dir=pak, simuconf_extra=["show_names = 0"]) as g:
    g.wait_month(6)
    if mode == "loops":
        # 1 辺 3 タイルの周回路を 3×3 個。周回路の中と間に建物が建って旅客を出す
        for i in range(3):
            for j in range(3):
                x, y = 60 + i * 5, 100 + j * 5
                g.road(x, y, x + 2, y, WAY)
                g.road(x + 2, y, x + 2, y + 2, WAY)
                g.road(x + 2, y + 2, x, y + 2, WAY)
                g.road(x, y + 2, x, y, WAY)
        city(g, 58, 98, 600)
        time.sleep(20)
        area = (60, 72, 100, 112)
        diagonal = ("sw", "se", "ne", "nw")
        found = {d: [] for d in diagonal}
        for n in range(400):
            tiles = peds(g, area, (3, 6, 9, 12))
            if not tiles:
                time.sleep(1)
                continue
            x, y = tiles[n % len(tiles)]
            im = shot(g, x, y, f"{out}/last.png")
            px = im.load()
            for d in diagonal:
                pts = [(a, b) for b in range(CY - 100, CY + 100) for a in range(CX - 130, CX + 130)
                       if all(abs(p - q) <= 6 for p, q in zip(px[a, b], D.MARKER_COLORS[d]))]
                if len(pts) >= 60 and len(found[d]) < 4:
                    found[d].append(im.crop((CX - 160, CY - 100, CX + 160, CY + 100)))
                    print("found", d, x, y, flush=True)
            if all(len(v) >= 4 for v in found.values()):
                break
        sheet = Image.new("RGB", (320 * 4, 200 * 4))
        for row, d in enumerate(diagonal):
            for i, im in enumerate(found[d]):
                sheet.paste(im, (320 * i, 200 * row))
        sheet.save(f"{out}/loops_sheet.png")
        print("count", {d: len(v) for d, v in found.items()}, flush=True)
    else:
        with open("tools/vehicle_check/road_stop_bus.nut", encoding="utf-8") as f:
            g.sq(" ".join(ln for ln in f.read().splitlines() if not ln.strip().startswith("//")))
        for i in range(14):
            g.road(60 + i, 100 + i, 61 + i, 100 + i, WAY)
            g.road(61 + i, 100 + i, 61 + i, 101 + i, WAY)
        city(g, 70, 103, 400)
        time.sleep(20)
        kinds = {"straight": ((45, 115, 45, 80), (5, 10)), "cross": ((45, 115, 45, 80), (7, 11, 13, 14, 15)),
                 "stairs": ((60, 75, 100, 115), (3, 6, 9, 12))}
        for kind, (area, ribis) in kinds.items():
            got = 0
            for n in range(120):
                tiles = peds(g, area, ribis)
                if not tiles:
                    time.sleep(1)
                    continue
                # 直線は、歩行者の多いタイルのまわりほど両側の人が写る
                x, y = tiles[(n * 7) % len(tiles)]
                shot(g, x, y, f"{out}/{kind}_{got:02d}_{x}_{y}.png")
                got += 1
                time.sleep(1)
                if got >= 12:
                    break
            print(kind, got, flush=True)
    if g.left_over:
        sys.exit(1)
