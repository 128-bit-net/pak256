"""線路の列車の確かめ（docs/vehicles.md の「線路の車両」・#46）。MIT License。

用意したゲームの作業フォルダで本体を起動し、rail.nut で線路・駅・車庫・街と編成を置く。編成が往復する間に、一定の間隔で編成のまわりを撮る。

    python -X utf8 tools/vehicle_check/rail_run.py --env <検証環境> --save flat_512_left_v64 --out <撮った絵の場所> --port 47880 [--cities]

ゲームの用意・起動・閉じ方は tools/game.py（docs/game-check.md）。pak は build/pak/ の物（先に tools/build.py）。--pak で別のフォルダの pak を使える。
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from game import Game, add_pak_argument  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"))
    ap.add_argument("--save", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--way", default="ami_rail_ballast")
    ap.add_argument("--origin", default="40,60")
    ap.add_argument("--cities", action="store_true", help="街を 2 つ置く（旅客を運ぶ確かめ）")
    ap.add_argument("--trailer", type=int, default=1, help="付随車を 1 両つなぐか（0 か 1）")
    ap.add_argument("--shots", type=int, default=12)
    ap.add_argument("--interval", type=float, default=5.0, help="撮る間隔（実時間の秒）")
    ap.add_argument("--speed", type=int, default=1, help="ゲームの速さ（1 が実時間）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    add_pak_argument(ap)
    args = ap.parse_args()
    if not args.env:
        sys.exit("検証環境を --env か PAK256_GAME_ENV で渡す")
    os.makedirs(args.out, exist_ok=True)
    ox, oy = (int(v) for v in args.origin.split(","))
    with Game(args.env, args.save, args.port, client=args.mcp_client, pak_dir=args.pak) as game:
        head = (f'OX <- {ox}; OY <- {oy}; WAY <- "{args.way}"; CITIES <- {1 if args.cities else 0}; '
                f'CARS <- 1; TRAILER <- {args.trailer};\n')
        with open(os.path.join(HERE, "rail.nut"), encoding="utf-8") as f:
            print("[rail]", game.sq(head + f.read(), timeout=90), flush=True)
        game.settle(25)  # 駅・車庫の建設中の絵が終わるまで
        game.sq(f"debug.set_game_speed({args.speed}); gui.set_zoom(3); return 1")
        query = ('local s=""; foreach (c in world.get_convoy_list()) { local p = c.get_pos();'
                 ' s += p.x + " " + p.y + " " + c.get_speed() + " " + c.get_loading_level() + ";"; } return s')
        for i in range(args.shots):
            time.sleep(args.interval)
            info = game.sq(query)
            print("[convoy]", info, flush=True)
            row = [r for r in info.split(";") if r]
            if not row:
                continue
            x, y = (int(v) for v in row[0].split()[:2])
            game.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
            time.sleep(0.3)
            game.capture(os.path.join(args.out, f"shot_{i:02d}_{x}_{y}.png"))
        game.sq("gui.close_all_windows(); return 1")
        game.sq("gui.click(216, 24); return 1")  # ツールバーの線路の道具（1600x900。左から 5 つ目）
        time.sleep(1)
        game.capture(os.path.join(args.out, "toolbar_rail.png"))
        game.sq("gui.close_all_windows(); return 1")
        if args.cities:
            game.dialog("finances")
            game.capture(os.path.join(args.out, "finances.png"))
    if game.left_over:
        sys.exit(1)


if __name__ == "__main__":
    main()
