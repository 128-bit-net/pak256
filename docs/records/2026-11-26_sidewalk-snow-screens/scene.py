"""歩道つきの道路の下の地面（#136）の再現と確かめ。MIT License。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-26_sidewalk-snow-screens/scene.py <検証環境> <ポート> <build のフォルダ> <出力フォルダ>
街の道路（歩道つき）を、温帯（x<256）と雪の気候（x>=256）の同じ並びに敷いて撮る。直す前と後の build を渡して 2 回流す。
- 平ら: 5x5 の格子（角 4・分かれ目 4・十字 1）
- 坂: 1 段の台地を 4 方向から登る道路（坂の 4 向き）と、台地の上の角・分かれ目
歩道は公共のプレーヤーが街の道路の道具で建てたときに付く。run_squirrel は呼び出しの player_nr のプレーヤーで道具を使い、
スクリプトの中の player_x(1) は効かない（mcp_client.py の既定は 0）ので、道路は --player-nr 1 で流す。"""
import json
import os
import sys
import time

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
AREAS = {"temperate": 60, "snow": 316}
FLAT_Y, HILL_Y = 100, 130
ZOOM = 3  # 等倍


def say(*a):
    print(*a, flush=True)


def sq_public(g, code):
    """公共のプレーヤー（1）として Squirrel を流す。"""
    r = g._client("--player-nr", "1", "--run-squirrel", code, timeout=30)
    return str(json.loads(r.stdout.strip().splitlines()[-1])["result"])


def city_road(g, x1, y1, z1, x2, y2, z2):
    return sq_public(g, f'return command_x(tool_build_cityroad).work(player_x(1), coord3d({x1},{y1},{z1}), '
                        f'coord3d({x2},{y2},{z2}), "")')


def flat(g, x0, y0):
    for d in (0, 2, 4):
        city_road(g, x0, y0 + d, 0, x0 + 4, y0 + d, 0)
        city_road(g, x0 + d, y0, 0, x0 + d, y0 + 4, 0)


def hill(g, cx, cy):
    """台地の上のタイルは cx-2..cx+2（z=1）、その外の一周が 1 段の坂。"""
    for y in range(cy - 2, cy + 4):
        for x in range(cx - 2, cx + 4):
            g.sq(f"return command_x.grid_raise(player_x(1), coord3d({x},{y},0))")


def hill_roads(g, cx, cy):
    # 端から端を 1 回で敷くと台地を避けて回るので、坂を登る区間と台地の上の区間に分ける
    for a, b in ((-5, -2), (-2, 2), (2, 5)):
        za, zb = int(abs(a) <= 2), int(abs(b) <= 2)
        say("ns", city_road(g, cx, cy + a, za, cx, cy + b, zb), "ew", city_road(g, cx + a, cy, za, cx + b, cy, zb))
    for d in (-2, 2):
        say("top", city_road(g, cx - 2, cy + d, 1, cx + 2, cy + d, 1), city_road(g, cx + d, cy - 2, 1, cx + d, cy + 2, 1))


def probe(g, x, y):
    return g.sq(f"local t=square_x({x},{y}).get_ground_tile(); local w=t.find_object(mo_way); "
                f'return t.z + ":" + t.get_slope() + ":" + (w ? w.get_desc().get_name() + ":" + w.has_sidewalk() : "no way")')


def shot(g, x, y, z, name):
    g.sq(f"gui.set_zoom({ZOOM}); gui.close_all_windows(); gui.jump(coord3d({x},{y},{z})); return 1")
    time.sleep(4)
    g.capture(os.path.join(out, name + ".png"))


with Game(env, "flat_512_left_v64", port, work=out + "/_w", build=build, simuconf_extra=["show_names = 0"]) as g:
    for x0 in AREAS.values():
        hill(g, x0 + 2, HILL_Y)
    # 気候は地形の後に塗る
    for area, x0 in AREAS.items():
        say("climate", g.climate(x0 - 12, FLAT_Y - 10, x0 + 16, HILL_Y + 14,
                                 "temperate" if area == "temperate" else "arctic", timeout=120))
    for x0 in AREAS.values():
        flat(g, x0, FLAT_Y)
        hill_roads(g, x0 + 2, HILL_Y)
    for area, x0 in AREAS.items():
        cx = x0 + 2
        for p in [(x0, FLAT_Y), (x0 + 2, FLAT_Y + 2), (cx, HILL_Y), (cx - 3, HILL_Y), (cx + 3, HILL_Y), (cx, HILL_Y - 3),
                  (cx, HILL_Y + 3), (cx - 2, HILL_Y - 2)]:
            say("probe", area, p, probe(g, *p))
    g.wait_month(6)
    time.sleep(8)
    for area, x0 in AREAS.items():
        shot(g, x0 + 2, FLAT_Y + 2, 0, f"{area}_flat")
        shot(g, x0 + 2, HILL_Y, 1, f"{area}_hill")
        shot(g, x0 + 2 - 3, HILL_Y, 0, f"{area}_slope_w")
        shot(g, x0 + 2 + 3, HILL_Y, 0, f"{area}_slope_e")
        shot(g, x0 + 2, HILL_Y - 3, 0, f"{area}_slope_n")
        shot(g, x0 + 2, HILL_Y + 3, 0, f"{area}_slope_s")
    if g.left_over:
        sys.exit(1)
