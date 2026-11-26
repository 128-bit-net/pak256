"""歩行者の確かめと撮影（#172）。MIT License。
温帯（x<256）と雪の気候（x>=256）に、同じ並びの街 2 つ・道・バス停・バスと郵便のトラックを置き
（tools/vehicle_check/road_stop_bus.nut）、バス停の周りを何枚も撮る。
使い方（リポジトリの直下から。先に tools/build.py。--pak は歩行者を差し替えた pak のフォルダ）:
    python -X utf8 docs/records/2026-11-27_pedestrians-screens/scene.py <検証環境> <ポート> <pak のフォルダ> <出力> [枚数]
corners を足すと、角のタイル（斜めの向き）にいる歩行者も撮る（印の pak で使う）。"""
import os
import sys
import time

from PIL import Image

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, pak, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
count = int(sys.argv[5]) if len(sys.argv) > 5 else 16
corners = "corners" in sys.argv
os.makedirs(out, exist_ok=True)
AREAS = {"temperate": 60, "snow": 316}
STOP_Y = 60
CX, CY = 895, 576  # gui.jump で飛んだタイルの中心が出る所（1600x900・拡大 3。白線の位置から測った）


def nut(ax):
    with open("tools/vehicle_check/road_stop_bus.nut", encoding="utf-8") as f:
        text = " ".join(ln for ln in f.read().splitlines() if not ln.strip().startswith("//"))
    return text.replace("ax = 60, ay = 60, bx = 100", f"ax = {ax}, ay = {STOP_Y}, bx = {ax + 40}")


def shot(g, x, y, path):
    g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
    time.sleep(0.6)
    g.capture(path)
    return Image.open(path).convert("RGB").crop((CX - 400, CY - 240, CX + 400, CY + 240))


def sheet(images, path, cols=4):
    out_img = Image.new("RGB", (800 * cols, 480 * ((len(images) + cols - 1) // cols)))
    for i, im in enumerate(images):
        out_img.paste(im, (800 * (i % cols), 480 * (i // cols)))
    out_img.save(path)


with Game(env, "flat_512_left_v64", port, work=out + "/_w", pak_dir=pak, simuconf_extra=["show_names = 0"]) as g:
    g.wait_month(6)
    for area, ax in AREAS.items():
        print(area, g.sq(nut(ax)).replace("\n", " "), flush=True)
    g.settle(20)
    for area, ax in AREAS.items():
        crops = []
        for i in range(count):
            crops.append(shot(g, ax + 1, STOP_Y, f"{out}/{area}_{i:02d}.png"))
            time.sleep(1.5)
        sheet(crops, f"{out}/{area}_sheet.png")
        # 車両のそばに歩行者がいる瞬間を探して撮る（車両と並べて背丈を見る）
        crops = []
        peds = ('local s=""; for(local x=%d;x<=%d;x++) for(local y=54;y<=66;y++){ local t=square_x(x,y).get_ground_tile(); '
                'if (t.find_object(mo_pedestrian)) s+=x+","+y+" "; } return s') % (ax - 12, ax + 52)
        cars = 'local s=""; foreach (c in world.get_convoy_list()) { local p=c.get_pos(); s+=p.x+","+p.y+" "; } return s'
        for _ in range(300):
            near = []
            pos = [tuple(map(int, p.split(","))) for p in g.sq(cars).split()]
            for p in g.sq(peds).split():
                x, y = map(int, p.split(","))
                near += [(x, y) for vx, vy in pos if abs(x - vx) <= 2 and abs(y - vy) <= 1]
            if near:
                crops.append(shot(g, near[0][0], near[0][1], f"{out}/{area}_meet_{len(crops):02d}.png"))
                if len(crops) >= 8:
                    break
            time.sleep(0.5)
        print(area, "meet", len(crops), flush=True)
        if crops:
            sheet(crops, f"{out}/{area}_meet_sheet.png")
    if corners:
        scan = ('local s=""; for(local x=45;x<=115;x++) for(local y=45;y<=80;y++){ local t=square_x(x,y).get_ground_tile(); '
                'if (t.find_object(mo_pedestrian)) { local d=t.get_way_dirs(wt_road); '
                'if (d==3 || d==6 || d==9 || d==12) s+=x+","+y+" "; } } return s')
        crops = []
        for i in range(120):
            tiles = [tuple(map(int, p.split(","))) for p in g.sq(scan).split()]
            if tiles:
                x, y = tiles[i % len(tiles)]
                crops.append(shot(g, x, y, f"{out}/corner_{len(crops):02d}.png").crop((200, 120, 600, 360)))
                if len(crops) >= 16:
                    break
            else:
                time.sleep(2)
        print("corners", len(crops), flush=True)
        if crops:
            big = Image.new("RGB", (1600, 240 * ((len(crops) + 3) // 4)))
            for i, im in enumerate(crops):
                big.paste(im, (400 * (i % 4), 240 * (i // 4)))
            big.save(f"{out}/corner_sheet.png")
    if g.left_over:
        sys.exit(1)
