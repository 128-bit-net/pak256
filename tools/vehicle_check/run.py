"""車両の描画位置の試験（docs/vehicles.md の「試験」）。MIT License。

用意したゲームの作業フォルダで本体を起動し、tools/vehicle_check/course.nut で道路の輪と車庫と編成を置き、
編成が走る間に、編成ごとに画面の真ん中へ飛んで撮る（本体はスクリプトから止めると戻せないので、止めずに撮る）。向き（8 方向）ごとに 1 枚ずつ残す。

    python -X utf8 tools/vehicle_check/run.py --env <検証環境> --save flat_512_left_v64 --out <撮った絵の場所> \n        --port 47880 --vehicle pak256_sample_bus

- ゲームの用意・起動・閉じ方・後片付けは tools/game.py（docs/game-check.md）。検証環境を写した作業フォルダで走らせ、pak256 の
  pak は build/pak/ の物（先に tools/build.py。--pak で別のフォルダ）を入れる。昼夜は止めてある。
- 道路の車庫は AMI の物（ami_road_depot。#64）を使う。別の車庫を試すときは --depot で名前を渡し、
  足りない物は --extra-pak で別の pak から借りる（借りた物はコミットしない）。
- MCP のクライアント（OTRP 本体のリポジトリの mcp_client.py）は --mcp-client か環境変数 MCP_CLIENT。
- Windows で動かす前提。
- 通行の向きは保存データで決まる（本体の設定。スクリプトからは変えられない）。左側通行と右側通行の保存データを 1 つずつ流す。
"""
import argparse
import os
import re
import sys
import time

from PIL import Image, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from game import Game, add_pak_argument  # noqa: E402

# gui.jump で飛んだタイルの中心が出る所の、画面の真ん中からのずれ（1600x900・拡大 3。測り方は docs/game-check.md の「画面の中心」）
JUMP_X, JUMP_Y = 96, 125
# 輪の寸法（course.nut と同じにする）
W, D, H = 10, 6, 8


def where(rx, ry, cw):
    """輪の北西の角からの場所 (rx, ry) と回る向きから、車両の向きの名前（dat の添字）。角は corner_nw・corner_sw。

    本体の向きはスクリプトから読めないので、コースの形から決める。
    """
    bottom = 2 * D + H
    if ry < 0:
        return "depot"
    if (rx, ry) == (0, 0):
        return "corner_nw"
    if (rx, ry) == (0, bottom):
        return "corner_sw"
    if ry == 0 and rx < W:
        return "e" if cw else "w"
    if ry == bottom and rx < W:
        return "w" if cw else "e"
    if rx == 0:
        return "n" if cw else "s"
    if rx == W + D and D < ry < D + H:
        return "s" if cw else "n"
    if ry <= D:
        return "se" if cw else "nw"
    return "sw" if cw else "ne"


def convoys(info):
    """編成の一覧の文字列から、編成の番号の順に (両数, x, y, 速さ) の並び。"""
    rows = []
    for row in filter(None, info.split(";")):
        nums, name = row.split("|", 1)
        m = re.match(r"\((\d+)\)", name)
        rows.append((int(m.group(1)) if m else 0, tuple(int(v) for v in nums.split())))
    return [r for _, r in sorted(rows)]


def keep_shot(path, dx=0, dy=0, threshold=60):
    """撮った画面が夜でなければ、編成のまわりを 2 倍（最近傍）にした切り抜き <名前>_zoom.png も書いて True。

    画面の真ん中は gui.jump で飛んだタイル。(dx, dy) は撮った後の編成のタイルのずれ（256px のタイルで画面へ直す）。
    """
    img = Image.open(path).convert("RGB")
    w, h = img.size
    cx = w // 2 + JUMP_X + 128 * (dx - dy)
    cy = h // 2 + JUMP_Y + 64 * (dx + dy)
    box = (cx - 256, cy - 160, cx + 256, cy + 160)
    crop = img.crop(box)
    mean = sum(ImageStat.Stat(crop).mean) / 3
    if mean < threshold:
        return False
    crop.resize((crop.width * 2, crop.height * 2), Image.NEAREST).save(path[:-4] + "_zoom.png")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"), help="検証環境（環境変数 PAK256_GAME_ENV）")
    ap.add_argument("--save", required=True, help="save/ の保存データの名前（拡張子なし）")
    ap.add_argument("--out", required=True, help="撮った絵の場所")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--vehicle", default="pak256_sample_bus")
    ap.add_argument("--depot", default="", help="道路の車庫の名前（空なら最初に見つかった物）")
    ap.add_argument("--extra-pak", action="append", default=[], help="借りる pak（別の車庫・停留所を試すときだけ）")
    ap.add_argument("--way", default="ami_road_local", help="輪に敷く道路の名前（AMI の 256 版の道路）")
    ap.add_argument("--origin", default="40,40", help="輪の北西の角（温帯の x<256 に置く）")
    ap.add_argument("--rounds", type=int, default=90, help="撮る回数の上限（4 秒ごと）")
    ap.add_argument("--limit", type=int, default=480,
                    help="全体の秒数の上限。過ぎたら撮るのをやめてゲームを閉じる（外の timeout より短くする）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    add_pak_argument(ap)
    args = ap.parse_args()
    if not args.env:
        sys.exit("検証環境を --env か環境変数 PAK256_GAME_ENV で渡す")

    os.makedirs(args.out, exist_ok=True)
    with Game(args.env, args.save, args.port, extra_paks=args.extra_pak, client=args.mcp_client, pak_dir=args.pak) as game:
        ox, oy = (int(v) for v in args.origin.split(","))
        with open(os.path.join(HERE, "course.nut"), encoding="utf-8") as f:
            nut = f.read()
        head = f'OX <- {ox}; OY <- {oy}; VEH <- "{args.vehicle}"; DEPOT <- "{args.depot}"; WAY <- "{args.way}";\n'
        print("[course]", game.sq(head + nut, timeout=60), flush=True)
        left = game.sq("return settings.get_drive_on_left() ? \"left\" : \"right\"")
        print("[drive]", left, flush=True)
        game.sq("debug.set_game_speed(1); gui.set_zoom(3); return 1")
        seen = {}
        query = ('local s=""; foreach (c in world.get_convoy_list()) { local p = c.get_pos();'
                 ' s += c.get_vehicles().len() + " " + p.x + " " + p.y + " " + c.get_speed() + "|" + c.get_name() + ";"; }'
                 ' return s')
        stop = (ox + W // 2, oy)
        deadline = time.time() + args.limit
        for i in range(args.rounds):
            if time.time() > deadline:
                print("[limit] 時間の上限で止めた", flush=True)
                break
            time.sleep(4)
            for k, (n, x, y, speed) in enumerate(convoys(game.sq(query))):
                cw = k < 2  # course.nut の編成の順: 時計回り 1 両・時計回り 2 両・反時計回り 1 両
                d = "stop" if (x, y) == stop and speed == 0 else where(x - ox, y - oy, cw)
                key = (n, d, cw)
                if key in seen:
                    continue
                game.sq(f"gui.close_all_windows(); gui.jump(coord3d({x},{y},0)); return 1")
                time.sleep(0.3)
                name = f"{left}_{d}_{n}car_{'cw' if cw else 'ccw'}_{x}_{y}"
                path = os.path.join(args.out, name + ".png")
                game.capture(path)
                # 撮る間に進んだ分だけ、切り抜きの真ん中を編成の今の場所へずらす
                _, x2, y2, _ = convoys(game.sq(query))[k]
                if not keep_shot(path, x2 - x, y2 - y):
                    print("[night] skip", path, flush=True)  # 夜は暗くて見えないので、昼に撮り直す
                    os.remove(path)
                    continue
                seen[key] = path
                print("[shot]", path, flush=True)
            dirs = {d for (_, d, _) in seen}
            if len(dirs) >= 11 and sum(1 for (n, _, _) in seen if n == 2) >= 5:
                break
        print("[done] directions:", sorted({d for (_, d, _) in seen}), flush=True)
    if game.left_over:
        sys.exit(1)


if __name__ == "__main__":
    main()
