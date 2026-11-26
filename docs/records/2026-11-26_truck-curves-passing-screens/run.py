"""太くしたトラックの十字路・坂と、編成どうしのすれ違いを撮る（#116）。MIT License。tools/game.py の Game の上で動く。

温帯（x<256）の平らな地図（左側通行）に、次の場面を一度に置き、条件が合った場面を順に撮る。
- cross : 十字路。郵便と石炭のトラックが、直進と右左折で通る
- slope_ew / slope_ns : 高さ 1 の台を越える道路（東西と南北）。上りと下りの坂
- pass_ew / pass_ns : 直線の道路（東西と南北）で、向かい合う郵便と石炭のトラックがすれ違う
- rail : 隣り合う 2 本の線路で、気動車 + 付随車の 2 編成がすれ違う

使い方: python -X utf8 run.py <検証環境> <ポート> <出力フォルダ（git 管理外）> [--seconds 420]   （先に tools/build.py）
通った場面ごとの撮った座標は標準出力に出る。曲がり（直角・斜め）は tools/vehicle_check/run.py で撮る。
"""
import argparse
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import game  # noqa: E402
from game import Game  # noqa: E402

_day_night_off = game.append_day_night_off


def _no_names(simuconf):
    """昼夜の停止に加えて、名前の札を消す（作業フォルダの写しだけ）。"""
    _day_night_off(simuconf)
    with open(simuconf, "a", encoding="utf-8") as f:
        f.write("show_names = 0" + chr(10))


game.append_day_night_off = _no_names

ap = argparse.ArgumentParser()
ap.add_argument("env")
ap.add_argument("port", type=int)
ap.add_argument("out")
ap.add_argument("--seconds", type=float, default=420.0)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)

ROAD, RAIL = "ami_road_local", "ami_rail_ballast"
MAIL, COAL = "pak256_mail_truck", "pak256_coal_truck"


ZF = "local c = function(x, y) { return coord3d(x, y, square_x(x, y).get_ground_tile().z); }; "


def check(label, result):
    """置く道具が何か返したら（失敗）、場面が崩れるので止める。"""
    if result != "ok":
        sys.exit(f"{label}: {result}")


def lay(g, x0, y0, x1, y1, way):
    """隣のタイルへ 1 つずつ敷く（長く敷くと、本体が坂をよける経路を選ぶことがある）。1 回の Squirrel で通す。"""
    dx, dy = (x1 > x0) - (x1 < x0), (y1 > y0) - (y1 < y0)
    n = abs(x1 - x0) + abs(y1 - y0)
    check(f"way {x0},{y0}-{x1},{y1}", g.sq(
        ZF + f"for (local i = 0; i < {n}; i++) {{ local x = {x0} + ({dx}) * i, y = {y0} + ({dy}) * i; "
        f'local e = command_x(tool_build_way).work(player_x(0), c(x, y), c(x + ({dx}), y + ({dy})), "{way}"); '
        'if (e != null) return x + "," + y + " " + e; } return "ok"', timeout=90))


def depot(g, x, y, side_x, side_y, way, name):
    """(x, y) の線の脇 (side_x, side_y) に車庫を置く。"""
    lay(g, x, y, side_x, side_y, way)
    check(f"depot {side_x},{side_y}", g.sq(
        ZF + "local dd = null; foreach (d in building_desc_x.get_building_list(building_desc_x.depot)) "
        f'if (d.get_name() == "{name}") dd = d; local e = command_x.build_depot(player_x(0), c({side_x}, {side_y}), dd); '
        'return e == null ? "ok" : e'))


def convoy(g, dx, dy, wt, vehicles, points):
    """(dx, dy) の車庫で編成を作り、points を回るダイヤで出す。"""
    entries = ",".join(f"schedule_entry_x(c({x}, {y}), 0, 0)" for x, y in points)
    code = (ZF + f"local pl = player_x(0); local depot = depot_x({dx}, {dy}, c({dx}, {dy}).z); local cnv = convoy_x(0); ")
    for i, name in enumerate(vehicles):
        code += (f'local v{i} = null; foreach (v in vehicle_desc_x.get_available_vehicles({wt})) '
                 f'if (v.get_name() == "{name}") v{i} = v; depot.append_vehicle(pl, cnv, v{i}); '
                 f"local l{i} = depot.get_convoy_list(); cnv = l{i}[l{i}.len() - 1]; ")
    code += (f"cnv.change_schedule(pl, schedule_x({wt}, [{entries}])); depot.start_convoy(pl, cnv); "
             "gui.close_all_windows(); return cnv.id")
    cid = int(g.sq(code, timeout=60))
    print(f"[convoy] id={cid} {vehicles} {dx},{dy} {points}", flush=True)
    return cid


def positions(g):
    s = g.sq('local s=""; foreach (v in world.get_convoy_list()) { local p=v.get_pos();'
             ' s += v.id + " " + p.x + " " + p.y + " " + v.get_speed() + ";"; } return s')
    out = {}
    for row in filter(None, s.split(";")):
        cid, x, y, speed = (int(v) for v in row.split())
        out[cid] = (x, y, speed)
    return out


with Game(a.env, "flat_512_left_v64", a.port) as g:
    # --- 地形（道路を敷く前に台を作る） ---
    # slope_ew: y=130 の道路の x=80..82 が高さ 1。slope_ns: x=110 の道路の y=100..102 が高さ 1
    for x in range(80, 84):
        for y in range(130, 132):
            g.sq(f"return command_x.grid_raise(player_x(0), coord3d({x},{y},0))")
    for y in range(100, 104):
        for x in range(110, 112):
            g.sq(f"return command_x.grid_raise(player_x(0), coord3d({x},{y},0))")

    # --- cross: 十字は (80,100) ---
    lay(g, 72, 100, 88, 100, ROAD)
    lay(g, 80, 92, 80, 108, ROAD)
    depot(g, 74, 100, 74, 99, ROAD, "ami_road_depot")
    depot(g, 80, 94, 81, 94, ROAD, "ami_road_depot")
    depot(g, 86, 100, 86, 101, ROAD, "ami_road_depot")
    depot(g, 80, 106, 79, 106, ROAD, "ami_road_depot")
    # --- slope ---
    lay(g, 70, 130, 94, 130, ROAD)
    depot(g, 72, 130, 72, 129, ROAD, "ami_road_depot")
    depot(g, 92, 130, 92, 129, ROAD, "ami_road_depot")
    lay(g, 110, 90, 110, 114, ROAD)
    depot(g, 110, 92, 109, 92, ROAD, "ami_road_depot")
    depot(g, 110, 112, 109, 112, ROAD, "ami_road_depot")
    # --- pass ---
    lay(g, 70, 150, 100, 150, ROAD)
    depot(g, 72, 150, 72, 149, ROAD, "ami_road_depot")
    depot(g, 98, 150, 98, 149, ROAD, "ami_road_depot")
    lay(g, 130, 90, 130, 120, ROAD)
    depot(g, 130, 92, 129, 92, ROAD, "ami_road_depot")
    depot(g, 130, 118, 129, 118, ROAD, "ami_road_depot")
    # --- rail: 隣り合う 2 本 y=170 と y=171 ---
    lay(g, 60, 170, 108, 170, RAIL)
    lay(g, 60, 171, 108, 171, RAIL)
    for y in (170, 171):
        for x in (64, 65, 66, 102, 103, 104):
            r = g.station(x, y, "pak256_train_station")
            check(f"station {x},{y}", "ok" if r == "None" else r)
    depot(g, 70, 170, 70, 169, RAIL, "ami_rail_depot")
    depot(g, 98, 171, 98, 172, RAIL, "ami_rail_depot")
    g.settle(25)

    scenes = {}
    scenes["cross"] = [
        convoy(g, 74, 99, "wt_road", [MAIL], [(88, 100), (72, 100)]),
        convoy(g, 81, 94, "wt_road", [COAL], [(80, 108), (80, 92)]),
        convoy(g, 86, 101, "wt_road", [COAL], [(80, 92), (88, 100)]),
        convoy(g, 79, 106, "wt_road", [MAIL], [(72, 100), (80, 108)]),
    ]
    scenes["slope_ew"] = [
        convoy(g, 72, 129, "wt_road", [MAIL], [(94, 130), (70, 130)]),
        convoy(g, 92, 129, "wt_road", [COAL], [(70, 130), (94, 130)]),
    ]
    scenes["slope_ns"] = [
        convoy(g, 109, 92, "wt_road", [COAL], [(110, 114), (110, 90)]),
        convoy(g, 109, 112, "wt_road", [MAIL], [(110, 90), (110, 114)]),
    ]
    scenes["pass_ew"] = [
        convoy(g, 72, 149, "wt_road", [MAIL], [(100, 150), (70, 150)]),
        convoy(g, 98, 149, "wt_road", [COAL], [(70, 150), (100, 150)]),
    ]
    scenes["pass_ns"] = [
        convoy(g, 129, 92, "wt_road", [COAL], [(130, 120), (130, 90)]),
        convoy(g, 129, 118, "wt_road", [MAIL], [(130, 90), (130, 120)]),
    ]
    scenes["rail"] = [
        convoy(g, 70, 169, "wt_rail", ["pak256_railcar", "pak256_railcar_trailer"], [(103, 170), (65, 170)]),
        convoy(g, 98, 172, "wt_rail", ["pak256_railcar", "pak256_railcar_trailer"], [(65, 171), (103, 171)]),
    ]
    g.sq("debug.set_game_speed(1); gui.set_zoom(3); gui.close_all_windows(); return 1")

    CENTER = {"cross": (80, 100), "slope_ew": (81, 130), "slope_ns": (110, 101), "pass_ew": (85, 150),
              "pass_ns": (130, 105), "rail": (84, 170)}

    def shoot(path, mx, my):
        g.sq(ZF + f"gui.close_all_windows(); gui.jump(c({mx}, {my})); return 1")
        g.capture(path)

    # 組み上がりの確かめ（場面ごとに 1 枚）
    for name, (mx, my) in CENTER.items():
        shoot(os.path.join(a.out, f"static_{name}.png"), mx, my)

    LIMIT = {"pass_ew": 30, "pass_ns": 30, "rail": 40}
    shots = {name: 0 for name in scenes}
    prev, heading, done = {}, {}, set()

    def near(name, p):
        if name == "cross":
            return abs(p[0] - 80) <= 1 and abs(p[1] - 100) <= 1
        if name == "slope_ew":
            return p[1] == 130 and 79 <= p[0] <= 83
        return p[0] == 110 and 99 <= p[1] <= 103

    t0 = time.time()
    while time.time() - t0 < a.seconds:
        pos = positions(g)
        for cid, (x, y, _) in pos.items():
            if cid in prev and prev[cid] != (x, y):
                ox, oy = prev[cid]
                heading[cid] = ("e" if x > ox else "w" if x < ox else "") + ("s" if y > oy else "n" if y < oy else "")
            prev[cid] = (x, y)
        for name, ids in scenes.items():
            pts = [pos[i] for i in ids if i in pos]
            if name in ("cross", "slope_ew", "slope_ns"):
                # 編成・タイル・向きの組を 1 回ずつ撮る
                for k, cid in enumerate(ids):
                    if cid not in pos or cid not in heading or not near(name, pos[cid]):
                        continue
                    x, y, _ = pos[cid]
                    key = (cid, x, y, heading[cid])
                    if key in done:
                        continue
                    done.add(key)
                    mx, my = CENTER[name]
                    path = os.path.join(a.out, f"{name}_c{k}_{heading[cid]}_{x}_{y}.png")
                    shoot(path, mx, my)
                    after = positions(g).get(cid)
                    print(f"[shot] {os.path.basename(path)} before={x},{y} after={after}", flush=True)
                    shots[name] += 1
            elif len(pts) == 2 and shots[name] < LIMIT[name]:
                p, q = pts
                axis = 1 if name == "pass_ns" else 0
                gap = abs(p[axis] - q[axis])
                if gap <= (3 if name == "rail" else 2) and p[2] > 0 and q[2] > 0:
                    key = (name, p[:2], q[:2])
                    if key in done:
                        continue
                    done.add(key)
                    mx, my = (p[0] + q[0]) // 2, (p[1] + q[1]) // 2
                    path = os.path.join(a.out, f"{name}_{shots[name]:02d}_gap{gap}.png")
                    shoot(path, mx, my)
                    after = positions(g)
                    print(f"[shot] {os.path.basename(path)} jump={mx},{my} before={p[:2]},{q[:2]} "
                          f"after={[after[i][:2] for i in ids if i in after]}", flush=True)
                    shots[name] += 1
        time.sleep(0.1)
    print("[done]", shots, flush=True)
if g.left_over:
    sys.exit(1)
