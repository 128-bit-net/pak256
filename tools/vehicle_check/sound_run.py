"""音を耳で確かめる場面を 1 つ作って、閉じるまで待つ（docs/sound.md の「耳で確かめる」・#175）。MIT License。

場面の置き方は、ほかの確かめ（*.nut・*_run.py）の物をそのまま使う。置いた後、停留所を画面の中央に出して実時間の速さにする。
音はマウスのカーソルに近いほど大きいので、画面の中央の近くの停留所（産業を聞くときは炭鉱・発電所）の上にカーソルを置いて聞く。Enter を押すと閉じる。

使い方:
    python -X utf8 tools/vehicle_check/sound_run.py --env <検証環境> --port 47920 --scene bus
場面: bus（バスと郵便のトラック）・coal（石炭のトラックと炭鉱）・plant（石炭のトラックと発電所）・
rail（気動車）・tram・monorail・air（旅客機）・ship（船 2 種）

plant の発電所の音は、トラックが石炭を届けて生産が始まってから鳴るので、しばらく待つ。Enter を待つので、端末で流す。

--check は耳を使わない確かめ: 鳴らさずに起動し、画面の中央の近くの停留所から編成が出たことを読んで、画面を撮って閉じる。
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from game import Game, add_pak_argument  # noqa: E402
import air_run  # noqa: E402

SAVE = "flat_512_left_v64"
# 場面 → 画面の中央に出す所（停留所）
SPOTS = {
    "bus": (60, 60, 0),
    "coal": (63, 63, 0),
    "plant": (83, 63, 0),  # coal と同じ置き方で、発電所の側を出す
    "rail": (47, 60, 0),
    "tram": (65, 60, 0),
    "monorail": (47, 60, 0),
    "air": (air_run.AX + 6, air_run.AY + 5, 0),
    "ship": (49, 93, -1),
}
# 停留所の上の編成と、その場所を読む
CONVOYS = ('local s=""; foreach (c in world.get_convoy_list()) { local p = c.get_pos(); local t = tile_x(p.x, p.y, p.z);'
           ' s += p.x + " " + p.y + " " + (t.get_halt() == null ? 0 : 1) + ";"; } return s')


def nut(game, name, head="", player_nr=0, must_end_ok=True):
    result = game.sq_file(os.path.join(HERE, name), head=head, player_nr=player_nr)
    print(f"[{name}] {result}", flush=True)
    if must_end_ok and not str(result).rstrip().endswith("ok"):  # 置けなかった場面で無音を待たせない
        sys.exit(f"[sound] {name} が最後まで通らなかった")


def setup(game, scene):
    if scene == "bus":
        nut(game, "road_stop_bus.nut")
    elif scene in ("coal", "plant"):
        nut(game, "road_stop_coal.nut")
    elif scene == "rail":
        nut(game, "rail.nut", head='OX <- 40; OY <- 60; WAY <- "ami_rail_ballast"; CITIES <- 1; CARS <- 1; TRAILER <- 1;\n')
    elif scene == "tram":
        head = "OX <- 60; OY <- 60; CARS <- 1;\n"
        nut(game, "tram.nut", head=head)
        nut(game, "tram_cities.nut", head=head, player_nr=1, must_end_ok=False)
    elif scene == "monorail":
        head = "OX <- 40; OY <- 60;\n"
        nut(game, "monorail.nut", head=head)
        nut(game, "monorail_city.nut", head=head, player_nr=1, must_end_ok=False)
    elif scene == "air":
        air_run.setup(game)
    elif scene == "ship":
        nut(game, "ship.nut")


def jump(game, spot):
    game.sq("gui.close_all_windows(); gui.jump(coord3d(%d,%d,%d)); gui.set_zoom(3); return 1" % spot)


NEAR = 6  # 画面の中央の停留所と見なす距離（縦と横のタイル数の和）


def departed(game, spot, limit, water=False):
    """spot の近くの停留所の上にいた編成が、そこから動くのを limit 秒まで待つ。動いた編成の番号を返す（無ければ None）。

    船は停留所の升でなく隣の水の升に停まるので、water なら spot の隣の升も停留所の上と数える。
    """
    on_halt = {}
    end = time.monotonic() + limit
    while time.monotonic() < end:
        rows = [tuple(int(v) for v in r.split()) for r in game.sq(CONVOYS).split(";") if r]
        for i, (x, y, halt) in enumerate(rows):
            d = abs(x - spot[0]) + abs(y - spot[1])
            if (halt and d <= NEAR) or (water and d <= 1):
                on_halt[i] = (x, y)
            elif i in on_halt:
                return i
        time.sleep(1.0)  # 短い間隔で読み続けると run_squirrel が失敗することがある
        game.check_fatal()
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"))
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--scene", required=True, choices=sorted(SPOTS))
    ap.add_argument("--check", action="store_true", help="鳴らさずに発車を確かめて閉じる")
    ap.add_argument("--capture", help="停留所の画面を撮る PNG のパス")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    add_pak_argument(ap)
    args = ap.parse_args()
    if not args.env:
        sys.exit("検証環境を --env か PAK256_GAME_ENV で渡す")
    spot = SPOTS[args.scene]
    ok = True
    with Game(args.env, SAVE, args.port, client=args.mcp_client, pak_dir=args.pak,
              sound="load" if args.check else "on", simuconf_extra=["show_names = 0"]) as game:
        setup(game, args.scene)
        game.settle(25)  # 停留所の建設中の絵が終わるまで
        game.sq("debug.set_game_speed(%d); return 1" % (4 if args.check else 1))
        jump(game, spot)
        if args.check:
            i = departed(game, spot, 400, water=args.scene == "ship")
            print(f"[check] {args.scene}: " + ("停留所から発車した" if i is not None else "発車を見なかった"), flush=True)
            ok = i is not None
        if args.capture:
            jump(game, spot)
            time.sleep(0.5)
            os.makedirs(os.path.dirname(os.path.abspath(args.capture)), exist_ok=True)
            game.capture(args.capture)
        if not args.check:
            print("[sound] 画面の中央の近くの停留所や産業の上にマウスのカーソルを置いて聞く。早送りは使わない。Enter で閉じる", flush=True)
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                pass
    if game.left_over or not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
