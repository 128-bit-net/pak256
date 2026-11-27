"""煙の確かめの場面を置いて、続けて撮る（#174 の記録）。MIT License。

    python -X utf8 docs/records/2026-11-27_smoke-screens/run.py <検証環境> <ポート> <撮る場所> --scene plant|rail|ship [--snow] [--night]

pak は build/pak/（先に tools/build.py）。撮った連番の画像は、煙の出ているコマを選んで使う。
- plant: 石炭の連鎖。発電所が石炭を受け取ってから 30 枚。
- rail: 気動車の発車の加速を 8 枚。
- ship: 船が港を出る所を 14 枚。--ship canal（運河の旅客船。既定）・sea（海の旅客船）・cargo（運河の車庫から出す貨物船）。
--snow は雪の気候に置く（plant・rail は x が 256 以上の所。ship は場面の周りを雪の気候に塗る）。
--night は昼夜を止めず、画面が暗くなるまで進めてから撮る。
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from game import Game  # noqa: E402

CHECK = os.path.join(ROOT, "tools", "vehicle_check")


def read(name):
    with open(os.path.join(CHECK, name), encoding="utf-8") as f:
        return f.read()


def wait_until(cond, timeout, step=0.2):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return
        time.sleep(step)
    sys.exit("待ちが時間切れ")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("env")
    ap.add_argument("port", type=int)
    ap.add_argument("out")
    ap.add_argument("--scene", choices=("plant", "rail", "ship"), required=True)
    ap.add_argument("--snow", action="store_true")
    ap.add_argument("--night", action="store_true")
    ap.add_argument("--ship", choices=("canal", "sea", "cargo"), default="canal")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    kind = args.scene if args.scene != "ship" else "ship_" + args.ship
    tag = kind + ("_snow" if args.snow else "") + ("_night" if args.night else "")
    with Game(args.env, "flat_512_left_v64", args.port, night=args.night) as g:
        def shot(i):
            g.capture(os.path.join(args.out, f"{tag}_{i:02d}.png"))

        def convoy(prefix):
            """名前が prefix で始まる編成の (x, y, 速さ)。"""
            r = g.sq('local s=""; foreach (c in world.get_convoy_list()) { local n = c.get_name(); '
                     f'if (n.find("{prefix}") == 0) {{ local p = c.get_pos(); s = p.x + " " + p.y + " " + c.get_speed(); }} }} return s')
            return tuple(int(v) for v in r.split())

        if args.scene == "plant":
            x = 300 if args.snow else 60
            g.sq(read("road_stop_coal.nut").replace("OX <- 60;", f"OX <- {x};"), timeout=120)
        elif args.scene == "rail":
            x = 280 if args.snow else 40
            g.sq(f'OX <- {x}; OY <- 130; WAY <- "ami_rail_ballast"; CITIES <- 0; CARS <- 1; TRAILER <- 1;\n'
                 + read("rail.nut"), timeout=120)
        else:
            g.sq(read("ship.nut"), timeout=200)
            if args.snow:  # 気候は地形の後に塗る（docs/game-check.md の「気候と月」）
                g.climate(34, 68, 66, 104, "arctic")
                g.climate(66, 96, 106, 112, "arctic")
            if args.ship == "cargo":
                g.sq('local pl=player_x(0); local v=null; foreach (d in vehicle_desc_x.get_available_vehicles(wt_water)) '
                     'if (d.get_name() == "pak256_cargo_ship") v=d; local depot=depot_x(85,105,0); '
                     'depot.append_vehicle(pl, convoy_x(0), v); local l=depot.get_convoy_list(); local c=l[l.len()-1]; '
                     'c.change_schedule(pl, schedule_x(wt_water, [schedule_entry_x(coord3d(74,104,0), 0, 0), '
                     'schedule_entry_x(coord3d(97,104,0), 0, 0)])); depot.start_convoy(pl, c); return 1')
        g.settle(25)
        g.sq("debug.set_game_speed(1); gui.set_zoom(3); gui.close_all_windows(); return 1")

        if args.scene == "plant":
            g.sq("debug.set_game_speed(64); return 1")
            query = f"local f=factory_x({x + 22},60); return f.input.Kohle.get_received()[0] + f.input.Kohle.get_received()[1]"
            wait_until(lambda: g.sq(query).strip() != "0", 300, 5)
            g.sq(f"debug.set_game_speed(1); gui.jump(coord3d({x + 23},61,0)); return 1")

        if args.night:
            from PIL import Image
            probe = os.path.join(args.out, f"{tag}_probe.png")

            def dark():
                g.capture(probe)
                hist = Image.open(probe).convert("L").crop((0, 100, 400, 400)).histogram()
                return sum(v * n for v, n in enumerate(hist)) / sum(hist) < 55

            g.sq("debug.set_game_speed(8); return 1")
            wait_until(dark, 600, 0.5)
            g.sq("debug.set_game_speed(1); return 1")

        if args.scene == "plant":
            for i in range(30):
                shot(i)
                time.sleep(0.5)
            return
        # 車両と船: 止まるのを待ち、発車したら撮る。船の編成の番号は ship.nut が出す順（1 海の旅客船・
        # 2 海の貨物船・3 運河の旅客船）で、4 は上で足す貨物船
        name = "(1)" if args.scene == "rail" else {"sea": "(1)", "canal": "(3)", "cargo": "(4)"}[args.ship]
        wait_until(lambda: convoy(name)[2] == 0, 300, 0.2)
        px, py, _ = convoy(name)
        z = -1 if args.scene == "ship" and args.ship == "sea" else 0
        g.sq(f"gui.close_all_windows(); gui.jump(coord3d({px},{py},{z})); return 1")
        wait_until(lambda: convoy(name)[2] > 0, 300)
        for i in range(8 if args.scene == "rail" else 14):
            if args.scene == "rail":
                px, py, _ = convoy(name)
                g.sq(f"gui.jump(coord3d({px},{py},0)); return 1")
            shot(i)
            time.sleep(0.5 if args.scene == "rail" else 0.15)


if __name__ == "__main__":
    main()
