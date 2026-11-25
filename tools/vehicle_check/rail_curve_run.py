"""線路の曲がり・坂での列車の見え方の確かめ（docs/vehicles.md の「線路の車両」・#71）。MIT License。

用意したゲームの作業フォルダで本体を起動し、rail_curve.nut でコの字の線路（東の 2 つの角と、北の辺の丘）・駅・車庫・編成を置く。
編成が曲がり・坂のタイルの近くに来たときに、編成の先頭のタイルを真ん中にして撮る。

    python -X utf8 tools/vehicle_check/rail_curve_run.py --env <検証環境> --save flat_512_left_v64 --out <撮った絵の場所> --port 47880

ゲームの用意・起動・閉じ方は tools/game.py（docs/game-check.md）。pak は build/pak/ の物（先に tools/build.py）。
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from game import Game  # noqa: E402

W, H = 30, 10  # rail_curve.nut のコの字の大きさ


def places(ox, oy):
    """撮る場所: (名前, 中心のタイル, 近さ（タイル）)。編成がこの近さまで来たら撮る。"""
    return [
        ("hill", (ox + 21, oy), 4),
        ("corner_ne", (ox + W, oy), 1), ("corner_se", (ox + W, oy + H), 1),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"))
    ap.add_argument("--save", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--way", default="ami_rail_ballast")
    ap.add_argument("--origin", default="40,60")
    ap.add_argument("--trailer", type=int, default=1, help="付随車を 1 両つなぐか（0 か 1）")
    ap.add_argument("--rounds", type=int, default=2, help="コの字の往復の数（北→南と南→北で 1 往復）")
    ap.add_argument("--timeout", type=float, default=420.0, help="全体の待ち（実時間の秒）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    args = ap.parse_args()
    if not args.env:
        sys.exit("検証環境を --env か PAK256_GAME_ENV で渡す")
    os.makedirs(args.out, exist_ok=True)
    ox, oy = (int(v) for v in args.origin.split(","))
    spots = places(ox, oy)
    done = {}
    with Game(args.env, args.save, args.port, client=args.mcp_client) as game:
        head = f'OX <- {ox}; OY <- {oy}; WAY <- "{args.way}"; TRAILER <- {args.trailer};\n'
        with open(os.path.join(HERE, "rail_curve.nut"), encoding="utf-8") as f:
            result = game.sq(head + f.read(), timeout=90)
            print("[rail_curve]", result, flush=True)
        if not result.rstrip().endswith("ok"):
            sys.exit(f"rail_curve.nut が最後まで通らなかった: {result}")
        game.settle(25)  # 駅・車庫の建設中の絵が終わるまで
        game.sq("debug.set_game_speed(1); gui.set_zoom(3); return 1")
        query = ('local s=""; foreach (c in world.get_convoy_list()) { local p = c.get_pos();'
                 ' s += p.x + " " + p.y + ";"; } return s')
        t0 = time.time()
        while time.time() - t0 < args.timeout:
            info = game.sq(query)
            row = [r for r in info.split(";") if r]
            if not row:
                time.sleep(0.5)
                continue
            x, y = (int(v) for v in row[0].split()[:2])
            for name, (sx, sy), near in spots:
                if abs(x - sx) <= near and abs(y - sy) <= near:
                    n = done.get(name, 0)
                    if (x, y) != done.get(name + "_pos") and n < args.rounds * 2 * 3:
                        game.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
                        game.capture(os.path.join(args.out, f"{name}_{n:02d}_{x}_{y}.png"))
                        done[name] = n + 1
                        done[name + "_pos"] = (x, y)
                        print("[shot]", name, x, y, flush=True)
            if all(done.get(n, 0) >= args.rounds * 2 for n, _, _ in spots):
                break
            time.sleep(0.05)
        game.sq("gui.close_all_windows(); return 1")
    if game.left_over:
        sys.exit(1)


if __name__ == "__main__":
    main()
