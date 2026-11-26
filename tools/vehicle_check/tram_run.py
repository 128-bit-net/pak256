"""路面電車の確かめ（docs/vehicles.md の「路面電車」・#153）。MIT License。

用意したゲームの作業フォルダで本体を起動し、tram.nut で道路の上の軌道・専用の軌道・停留所・車庫・街と 1 編成を置く。
編成が角・停留所に来たときと、一定の時間が過ぎた後の財務の窓を撮る。

    python -X utf8 tools/vehicle_check/tram_run.py --env <検証環境> --save flat_512_left_v64 --out <撮った絵の場所> --port 47880 [--cars 2]

ゲームの用意・起動・閉じ方は tools/game.py（docs/game-check.md）。pak は build/pak/ の物（先に tools/build.py）。--pak で別のフォルダの pak を使える。
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from game import Game, add_pak_argument  # noqa: E402


def places(ox, oy):
    """撮る場所: (名前, 中心のタイル, 近さ（タイル）)。"""
    mid, low, cx, ex = oy + 8, oy + 14, ox + 16, ox + 36
    return [
        ("road_straight", (ox + 12, oy), 1), ("road_corner", (cx, oy), 0), ("road_stop", (ox + 4, oy), 1),
        ("own_corner_w", (cx, low), 0), ("own_straight", (ox + 22, low), 1), ("own_stop", (ex, mid + 1), 1),
        ("own_corner_e", (ex, low), 0), ("road_to_own", (cx, mid), 0),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"))
    ap.add_argument("--save", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--origin", default="60,60")
    ap.add_argument("--cars", type=int, default=1, help="1 編成の両数")
    ap.add_argument("--no-cities", action="store_true")
    ap.add_argument("--timeout", type=float, default=300.0, help="曲がりを撮る全体の待ち（実時間の秒）")
    ap.add_argument("--run", type=float, default=0.0, help="撮り終えた後、速さ 64 で進める秒数（旅客とお金の確かめ）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    add_pak_argument(ap)
    args = ap.parse_args()
    if not args.env:
        sys.exit("検証環境を --env か PAK256_GAME_ENV で渡す")
    os.makedirs(args.out, exist_ok=True)
    ox, oy = (int(v) for v in args.origin.split(","))
    spots = places(ox, oy)
    # 角は向きの違う 2 回（行きと帰り）を撮る
    want = {name: (2 if "corner" in name else 1) for name, _, _ in spots}
    done = {}
    with Game(args.env, args.save, args.port, client=args.mcp_client, pak_dir=args.pak, simuconf_extra=["show_names = 0"]) as game:
        head = f'OX <- {ox}; OY <- {oy}; CARS <- {args.cars};\n'
        # 保存データの会社の残高は、置く前から大きくマイナスのことがある。置く前の残高を出しておく
        print("[cash before]", game.sq("return player_x(0).get_current_cash()"), flush=True)
        with open(os.path.join(HERE, "tram.nut"), encoding="utf-8") as f:
            result = game.sq(head + f.read(), timeout=90)
            print("[tram]", result, flush=True)
        if not result.rstrip().endswith("ok"):
            sys.exit(f"tram.nut が最後まで通らなかった: {result}")
        if not args.no_cities:
            with open(os.path.join(HERE, "tram_cities.nut"), encoding="utf-8") as f:
                print("[city]", game.sq(head + f.read(), timeout=90, player_nr=1), flush=True)
        game.settle(25)  # 停留所・車庫の建設中の絵が終わるまで
        game.sq("debug.set_game_speed(1); gui.set_zoom(3); return 1")
        query = ('local s=""; foreach (c in world.get_convoy_list()) { local p = c.get_pos();'
                 ' s += p.x + " " + p.y + " " + c.get_loading_level() + ";"; } return s')
        t0 = time.time()
        while time.time() - t0 < args.timeout and any(len(done.get(n, [])) < w for n, w in want.items()):
            info = game.sq(query)
            row = [r for r in info.split(";") if r]
            if row:
                x, y, load = (int(v) for v in row[0].split()[:3])
                for name, (sx, sy), near in spots:
                    got = done.setdefault(name, [])
                    # 2 枚めは、1 枚めと 20 秒以上あけて撮る（帰りに撮る）
                    if abs(x - sx) <= near and abs(y - sy) <= near and len(got) < want[name] and (not got or time.time() - got[-1] > 20):
                        game.sq(f"gui.close_all_windows(); gui.jump(coord3d({sx},{sy},0)); return 1")
                        time.sleep(0.2)
                        game.capture(os.path.join(args.out, f"{name}_{len(got)}.png"))
                        got.append(time.time())
                        print("[shot]", name, x, y, "load", load, flush=True)
            time.sleep(0.1)
        # 車両の無い停留所と車庫
        for name, (x, y) in (("empty_road_stop", (ox + 5, oy)), ("empty_own_stop", (ox + 36, oy + 10)), ("depot", (ox - 3, oy))):
            game.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
            time.sleep(0.3)
            game.capture(os.path.join(args.out, f"{name}.png"))
        if args.run:
            game.sq("debug.set_game_speed(64); return 1")
            time.sleep(args.run)
            game.sq("debug.set_game_speed(1); return 1")
        info = game.sq('local s=""; foreach (c in world.get_convoy_list()) { local t = c.get_transported_goods(); local p = c.get_profit();'
                       ' s += " transported=" + t[0] + "," + t[1] + " profit=" + p[0] + "," + p[1]; }'
                       ' foreach (st in halt_list_x()) { local h = st.get_happy(); local n = st.get_noroute(); local d = st.get_departed();'
                       ' s += " halt departed=" + d[0] + "," + d[1] + " happy=" + h[0] + "," + h[1] + " noroute=" + n[0] + "," + n[1]; } return s')
        print("[result]", info, flush=True)
        game.dialog("finances")
        time.sleep(0.5)
        game.capture(os.path.join(args.out, "finances.png"))
    if game.left_over:
        sys.exit(1)


if __name__ == "__main__":
    main()
