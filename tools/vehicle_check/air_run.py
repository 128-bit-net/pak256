"""飛行機と空港の確かめ（docs/airport.md・#155）。MIT License。

air.nut で空港 2 つ・街・旅客機 1 機を置き、往復する間の編成の位置を読み、撮る。

    python -X utf8 tools/vehicle_check/air_run.py --env <検証環境> --save flat_512_left_v64 --out <撮った絵の場所> --port 47880

ゲームの用意・起動・閉じ方は tools/game.py（docs/game-check.md）。pak は build/pak/ の物（先に tools/build.py）。
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from game import Game  # noqa: E402

AX, AY, BX, BY, LEN = 60, 100, 150, 100, 18
QUERY = ('local s=""; foreach (c in world.get_convoy_list()) { local p = c.get_pos();'
         ' s += p.x + " " + p.y + " " + p.z + " " + c.get_speed() + " " + c.get_loading_level() + ";"; } return s')
# 収支と運んだ量（今月・先月）と、駅で待つ旅客
MONEY = ('local c = world.get_convoy_list(); local s = ""; foreach (v in c) { local t = v.get_transported_goods();'
         ' local r = v.get_revenue(); s += "transported=" + t[0] + "," + t[1] + " revenue=" + r[0] + "," + r[1]; }'
         ' s += " cash=" + player_x(0).get_cash()[0];'
         ' foreach (p in [[AX + 6, AY + 5], [BX + 6, BY + 5]]) s += " waiting=" + tile_x(p[0], p[1], 0).get_halt().get_waiting()[0];'
         ' return s')
HEAD = f"AX <- {AX}; AY <- {AY}; BX <- {BX}; BY <- {BY}; LEN <- {LEN};\n"
# 空港ごとに街を 1 つ置き、駅の範囲に街の建物を並べる（街が建てる建物は駅の近くに少なく、旅客がほとんど出ないため）。公共のプレーヤーで流す
HOUSES = ('local n = 0; foreach (a in [[AX, AY], [BX, BY]]) { local e = command_x(tool_add_city).work(player_x(1), coord3d(a[0] + 6, a[1] + 8, 0)); if (e != null) return "city: " + e; }'
          ' foreach (c in city_list_x()) c.change_size(3000);'
          ' foreach (a in [[AX, AY], [BX, BY]]) { for (local dx = 3; dx <= 9; dx++) { for (local dy = 6; dy <= 7; dy++) {'
          ' if (command_x(tool_build_house).work(player_x(1), coord3d(a[0] + dx, a[1] + dy, 0), "00pak256_apartment") == null) n++; } } } return n')


def setup(game):
    with open(os.path.join(HERE, "air.nut"), encoding="utf-8") as f:
        print("[air]", game.sq(HEAD + f.read(), timeout=90), flush=True)
    print("[cities]", game.sq(HEAD + HOUSES, player_nr=1, timeout=90), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"))
    ap.add_argument("--save", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--shots", type=int, default=30)
    ap.add_argument("--interval", type=float, default=2.0, help="撮る間隔（実時間の秒）")
    ap.add_argument("--speed", type=int, default=1, help="ゲームの速さ（1 が実時間）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    args = ap.parse_args()
    if not args.env:
        sys.exit("検証環境を --env か PAK256_GAME_ENV で渡す")
    os.makedirs(args.out, exist_ok=True)
    with Game(args.env, args.save, args.port, client=args.mcp_client) as game:
        setup(game)
        game.settle(20)  # 駅・格納庫の建設中の絵が終わるまで
        game.sq(f"debug.set_game_speed({args.speed}); gui.set_zoom(3); return 1")
        for i in range(args.shots):
            time.sleep(args.interval)
            row = [r for r in game.sq(QUERY).split(";") if r]
            print(f"[convoy] {i} {row}", flush=True)
            if i % 10 == 0 or i == args.shots - 1:
                print(f"[money] {i} {game.sq(HEAD + MONEY)}", flush=True)
            if not row:
                continue
            x, y = (int(v) for v in row[0].split()[:2])
            game.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
            time.sleep(0.2)
            game.capture(os.path.join(args.out, f"shot_{i:02d}_{x}_{y}.png"))
        for name, (x, y) in (("airport_a", (AX + 8, AY + 3)), ("airport_b", (BX + 8, BY + 3))):
            game.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
            time.sleep(0.5)
            game.capture(os.path.join(args.out, f"{name}.png"))
        game.dialog("finances")
        game.capture(os.path.join(args.out, "finances.png"))
    if game.left_over:
        sys.exit(1)


if __name__ == "__main__":
    main()
