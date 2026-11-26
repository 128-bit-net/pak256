"""直線の道の歩行者が、道の端からどれだけ内側にいるかを画面から測る（#172。向き色の印の pak で流す）。MIT License。
使い方（リポジトリの直下から）:
    python -X utf8 docs/records/2026-11-27_pedestrians-screens/positions.py <検証環境> <ポート> <印の pak> <出力> [回数]
1 行が 1 人: タイル、道の向き（5 = 南北、10 = 東西）、絵の向き、道の端からの距離 c（タイル）。"""
import os
import sys
import time

from PIL import Image

sys.path.insert(0, "tools")
sys.path.insert(0, "objects/pedestrian/walkers")
from game import Game  # noqa: E402
import draw_pedestrians as D  # noqa: E402

env, port, pak, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
count = int(sys.argv[5]) if len(sys.argv) > 5 else 40
os.makedirs(out, exist_ok=True)
with open("tools/vehicle_check/road_stop_bus.nut", encoding="utf-8") as f:
    NUT = " ".join(ln for ln in f.read().splitlines() if not ln.strip().startswith("//"))
SCAN = ('local s=""; for(local x=45;x<=115;x++) for(local y=45;y<=80;y++){ local t=square_x(x,y).get_ground_tile(); '
        'if (t.find_object(mo_pedestrian)) { local d=t.get_way_dirs(wt_road); if (d==5 || d==10) s+=x+","+y+","+d+" "; } } return s')
CX, CY = 895, 576  # gui.jump で飛んだタイルの中心（1600x900・拡大 3。白線が道の中心の両側に等しく出る位置）


def blobs(im):
    """印の色の人形（向き, 足元の x, y）。"""
    px = im.load()
    res = []
    for d, color in D.MARKER_COLORS.items():
        pts = {(x, y) for y in range(CY - 160, CY + 160) for x in range(CX - 200, CX + 200)
               if all(abs(a - b) <= 6 for a, b in zip(px[x, y], color))}
        while pts:
            stack = [pts.pop()]
            got = []
            while stack:
                x, y = stack.pop()
                got.append((x, y))
                for dx in (-2, -1, 0, 1, 2):
                    for dy in (-2, -1, 0, 1, 2):
                        q = (x + dx, y + dy)
                        if q in pts:
                            pts.remove(q)
                            stack.append(q)
            if len(got) < 60:
                continue
            xs = [p[0] for p in got]
            res.append((d, (min(xs) + max(xs)) / 2, max(p[1] for p in got)))
    return res


with Game(env, "flat_512_left_v64", port, work=out + "/_w", pak_dir=pak, simuconf_extra=["show_names = 0"]) as g:
    g.sq(NUT)
    time.sleep(15)
    for i in range(count):
        tiles = [tuple(map(int, p.split(","))) for p in g.sq(SCAN).split()]
        if not tiles:
            time.sleep(3)
            continue
        x, y, ribi = tiles[(i * 7) % len(tiles)]
        g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
        time.sleep(0.5)
        path = f"{out}/p{i:02d}_{x}_{y}_{ribi}.png"
        g.capture(path)
        for d, sx, sy in blobs(Image.open(path).convert("RGB")):
            gx, gy = D.V.from_screen(sx - CX, sy - CY)
            if abs(gx) <= 0.5 and abs(gy) <= 0.5:  # 飛んだタイルの中の人だけ
                lateral = gx if ribi == 5 else gy
                print(f"tile={x},{y} ribi={ribi} dir={d} c={0.5 - abs(lateral):.3f}", flush=True)
    if g.left_over:
        sys.exit(1)
