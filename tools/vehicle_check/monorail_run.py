"""モノレールの確かめ（docs/vehicles.md の「モノレールの車両」・#156）。MIT License。

本体を起動し、monorail.nut で地上・高架・トンネル・曲がりの 4 本の線と編成を置く。地上の駅に停まった編成、高架の編成、
トンネルの口、南北の駅・角・斜め、ツールバーを撮り、早送りの後で、編成ごとの運んだ数と収支、財務の窓を出す。

    python -X utf8 tools/vehicle_check/monorail_run.py --env <検証環境> --save flat_512_left_v64 --out <撮った絵の場所> --port 47900

ゲームの用意・起動・閉じ方は tools/game.py（docs/game-check.md）。pak は build/pak/ の物（先に tools/build.py）。
ツールバーを押す位置は 1600x900 の画面（左から 7 つ目）。
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from game import Game  # noqa: E402

CONVOYS = ('local s=""; foreach (c in world.get_convoy_list()) { local p = c.get_pos();'
           ' s += p.x + " " + p.y + " " + p.z + " " + c.get_speed() + ";"; } return s')
RESULTS = ('local s=""; foreach (c in world.get_convoy_list()) { local g = 0, r = 0, m = 0;'
           ' foreach (v in c.get_transported_goods()) g += v; foreach (v in c.get_revenue()) r += v;'
           ' foreach (v in c.get_profit()) m += v;'
           ' s += "y=" + c.get_pos().y + " transported=" + g + " revenue=" + r + " profit=" + m + "; "; } return s')


def convoy_on(game, y):
    """y の線の編成の (x, z, 速さ)。車庫の口の升（y+1）も含める。無ければ None。"""
    for row in game.sq(CONVOYS).split(";"):
        if row:
            x, cy, z, v = (int(n) for n in row.split())
            if cy in (y, y + 1):
                return x, z, v
    return None


def shot(game, out, name, x, y, z=0):
    game.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},{z})); return 1")
    time.sleep(0.3)
    game.capture(os.path.join(out, name + ".png"))


def wait_for(game, y, cond, timeout=240):
    """y の線の編成が cond(x, z, 速さ) を満たすまで待つ。"""
    end = time.time() + timeout
    while time.time() < end:
        c = convoy_on(game, y)
        if c and cond(*c):
            return c
        time.sleep(0.2)
    print(f"[monorail] y={y} の編成が条件に合わなかった", flush=True)
    return convoy_on(game, y)


def positions(game):
    return [tuple(int(n) for n in row.split()) for row in game.sq(CONVOYS).split(";") if row]


def wait_on(game, x, y0, y1, stopped, timeout=240):
    """x の南北の線で、y0〜y1 に（stopped なら停まって）いる編成の y を返す。"""
    end = time.time() + timeout
    while time.time() < end:
        for cx, cy, _, v in positions(game):
            if cx == x and y0 <= cy <= y1 and (v == 0) == stopped:
                return cy
        time.sleep(0.1)
    print(f"[monorail] x={x} y={y0}〜{y1} に編成が来なかった", flush=True)
    return None


def wait_diagonal(game, x0, x1, timeout=240):
    """曲がりの線の斜めの区間（x が x0〜x1）にいる編成の x を返す。"""
    end = time.time() + timeout
    while time.time() < end:
        for cx, cy, _, v in positions(game):
            if x0 <= cx <= x1 and cy > 130 and v:
                return cx
        time.sleep(0.1)
    print("[monorail] 斜めの区間に編成が来なかった", flush=True)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"))
    ap.add_argument("--save", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--origin", default="40,60")
    ap.add_argument("--run", type=float, default=90.0, help="収支を見る前の早送りの秒（速さ 64）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    args = ap.parse_args()
    if not args.env:
        sys.exit("検証環境を --env か PAK256_GAME_ENV で渡す")
    os.makedirs(args.out, exist_ok=True)
    ox, oy = (int(v) for v in args.origin.split(","))
    elev, tun = oy + 20, oy + 40
    with Game(args.env, args.save, args.port, client=args.mcp_client) as game:
        head = f"OX <- {ox}; OY <- {oy};\n"
        # 街は線路を敷いた後に置く（先に置くと、街の建物が線の通り道をふさぐことがある）
        print("[monorail]", game.sq_file(os.path.join(HERE, "monorail.nut"), head=head), flush=True)
        print("[city]", game.sq_file(os.path.join(HERE, "monorail_city.nut"), head=head, player_nr=1), flush=True)
        game.settle(25)  # 駅・車庫の建設中の絵が終わるまで
        game.sq("debug.set_game_speed(1); gui.set_zoom(3); return 1")
        # 地上: 駅に停まった編成
        c = wait_for(game, oy, lambda x, z, v: v == 0 and (ox + 6 <= x <= ox + 8 or ox + 52 <= x <= ox + 54))
        shot(game, args.out, "ground_station", c[0], oy)
        # 高架: 線の中ほどを走る編成
        c = wait_for(game, elev, lambda x, z, v: ox + 8 <= x <= ox + 11)
        shot(game, args.out, "elevated", c[0], elev, 2)
        shot(game, args.out, "elevated_station", ox + 17, elev, 2)
        # トンネル: 東の口から出た編成
        wait_for(game, tun, lambda x, z, v: ox + 16 <= x <= ox + 17)
        shot(game, args.out, "tunnel", ox + 15, tun)
        shot(game, args.out, "tunnel_west", ox + 9, tun)
        # 曲がり・南北・斜め
        curve = oy + 60
        c = wait_on(game, ox + 14, curve + 8, curve + 10, stopped=True)
        shot(game, args.out, "ns_station", ox + 14, c or curve + 9)
        c = wait_on(game, ox + 14, curve, curve + 2, stopped=False)
        shot(game, args.out, "corner", ox + 14, curve + 1)
        c = wait_diagonal(game, ox + 17, ox + 20)
        shot(game, args.out, "diagonal", c or ox + 18, curve + (c - (ox + 14) if c else 4) + 14)
        # ツールバー（左から 7 つ目。1600x900）
        game.sq("gui.close_all_windows(); gui.click(312, 24); return 1")
        time.sleep(1)
        game.capture(os.path.join(args.out, "toolbar.png"))
        game.sq("gui.close_all_windows(); return 1")
        # お金が回る: 早送りの後で、編成ごとの運んだ数と収支、財務の窓
        game.sq("debug.set_game_speed(64); return 1")
        time.sleep(args.run)
        game.sq("debug.set_game_speed(1); return 1")
        print("[monorail]", game.sq(RESULTS), flush=True)
        game.dialog("finances")
        time.sleep(1)
        game.capture(os.path.join(args.out, "finances.png"))
    if game.left_over:
        sys.exit(1)


if __name__ == "__main__":
    main()
