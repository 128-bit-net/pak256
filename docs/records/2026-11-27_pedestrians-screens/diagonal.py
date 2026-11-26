"""斜めの道（1 タイルごとに曲がる階段の道）の歩行者を撮る（#172）。MIT License。印の pak で使う。
使い方（リポジトリの直下から）:
    python -X utf8 docs/records/2026-11-27_pedestrians-screens/diagonal.py <検証環境> <ポート> <pak のフォルダ> <出力>"""
import os
import sys
import time

from PIL import Image

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, pak, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
CX, CY = 895, 576  # scene.py と同じ
STEPS, X0, Y0 = 14, 60, 100

with Game(env, "flat_512_left_v64", port, work=out + "/_w", pak_dir=pak, simuconf_extra=["show_names = 0"]) as g:
    g.wait_month(6)
    for i in range(STEPS):
        x, y = X0 + i, Y0 + i
        g.road(x, y, x + 1, y, "ami_road_local")
        g.road(x + 1, y, x + 1, y + 1, "ami_road_local")
    # 階段の道の脇に街を置き、建物が旅客を出すと歩行者が出る
    print("city", g.sq(f"return command_x(tool_add_city).work(player_x(1), coord3d({X0 + 10},{Y0 + 3},0))"), flush=True)
    print("size", g.sq("foreach (c in city_list_x()) c.change_size(400); return 1"), flush=True)
    time.sleep(20)
    scan = ('local s=""; for(local x=%d;x<=%d;x++) for(local y=%d;y<=%d;y++){ local t=square_x(x,y).get_ground_tile(); '
            'if (t.find_object(mo_pedestrian)) { local d=t.get_way_dirs(wt_road); '
            'if (d==3 || d==6 || d==9 || d==12) s+=x+","+y+" "; } } return s') % (X0, X0 + STEPS + 1, Y0, Y0 + STEPS + 1)
    crops, seen = [], {}
    for i in range(150):
        tiles = [tuple(map(int, p.split(","))) for p in g.sq(scan).split()]
        if tiles:
            x, y = min(tiles, key=lambda t: seen.get(t, 0))
            seen[(x, y)] = seen.get((x, y), 0) + 1
            g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
            time.sleep(0.5)
            path = f"{out}/d{len(crops):02d}.png"
            g.capture(path)
            crops.append(Image.open(path).convert("RGB").crop((CX - 200, CY - 120, CX + 200, CY + 120)))
            if len(crops) >= 24:
                break
        else:
            time.sleep(2)
    print("diagonal", len(crops), flush=True)
    if crops:
        big = Image.new("RGB", (1600, 240 * ((len(crops) + 3) // 4)))
        for i, im in enumerate(crops):
            big.paste(im, (400 * (i % 4), 240 * (i // 4)))
        big.save(f"{out}/sheet.png")
    if g.left_over:
        sys.exit(1)
