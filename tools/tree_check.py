"""木を各気候・各季節でゲームに撮る道具（docs/trees.md、#102）。MIT License。

平らな保存データに、気候ごとの区画（tropic・desert・mediterran・temperate・tundra・arctic と、雪線の上の温帯）を作り、
`tool_forest` で林を置き、ゲームの月を進めて、同じ場所の夏・秋・冬・春を撮る。本体の季節は月で決まる
（OTRP の `simworld.cc` の `month_to_season`: 1 始まりの月で 12〜3 月 冬、4〜5 月 春、6〜9 月 夏、10〜11 月 秋）ので、月が目的になるまで
`debug.set_game_speed` で進める。

    python -X utf8 tools/tree_check.py --env <検証環境> --port 47841 --out work/tree_check

撮った画像は `<out>/<区画>_<季節>.png`。PR に付ける画像を作るのは `--out <撮った所> --montage <出す所>`（Pillow）。
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from game import Game  # noqa: E402

N = 14          # 区画の一辺（タイル）
STEP = 22       # 区画の間隔
X0, Y0 = 100, 100
# 区画の名前、気候の番号（本体の climate: 0 水・1 砂漠・2 熱帯・3 地中海・4 温帯・5 ツンドラ・6 岩・7 北極）、地面を上げる段数
PLOTS = [
    ("tropic", 2, 0), ("desert", 1, 0), ("mediterran", 3, 0), ("temperate", 4, 0),
    ("tundra", 5, 0), ("arctic", 7, 0), ("temperate_high", 4, 14),
]
# 季節ごとに撮る月（0 始まり）。本体の month_to_season に合う月
SEASONS = [("summer", 6), ("autumn", 9), ("winter", 0), ("spring", 3)]


def prepare_plot(g, idx, name, climate, lift):
    x, y = X0 + idx * STEP, Y0
    if lift:
        # 台地: 区画の格子点を lift 段上げる（雪線の上に木を置く）
        g.sq(f"local pl = player_x(0); for (local k = 0; k < {lift}; k++) for (local x = {x - 1}; x <= {x + N + 1}; x++) "
             f"for (local y = {y - 1}; y <= {y + N + 1}; y++) command_x.grid_raise(pl, coord3d(x, y, k)); return 1", timeout=240)
    z = lift
    g.sq(f"local pl = player_x(0); for (local x = {x}; x < {x + N}; x++) for (local y = {y}; y < {y + N}; y++) "
         f"command_x.change_climate_at(pl, coord3d(x, y, {z}), {climate}); return 1", timeout=120)
    r = g.sq(f'return command_x(tool_forest).work(player_x(0), coord3d({x}, {y}, {z}), coord3d({x + N - 1}, {y + N - 1}, {z}), "")')
    print(f"[tree_check] {name}: forest -> {r}")
    return x + N // 2, y + N // 2


def wait_month(g, target, timeout=420):
    """ゲームの月が target になるまで進める。"""
    end = time.time() + timeout
    g.sq("debug.set_game_speed(64); return 1")
    try:
        while time.time() < end:
            m = int(g.sq("return world.get_time().month"))
            if m == target:
                return
            time.sleep(0.4)
        raise RuntimeError(f"月 {target} にならなかった")
    finally:
        g.sq("debug.set_game_speed(1); return 1")


def montage(src, dst):
    """撮った画像から、PR に付ける画像を作る（Pillow）。区画の中央 640x360 を切り抜く。
    pair_<区画>.png: 夏と冬を並べる。seasons_temperate.png: 温帯の 4 季節。climates_summer.png: 各気候の夏。"""
    from PIL import Image, ImageDraw
    os.makedirs(dst, exist_ok=True)
    W, H = 640, 360

    def crop(name, season):
        im = Image.open(os.path.join(src, f"{name}_{season}.png")).convert("RGB")
        x, y = (im.width - W) // 2, (im.height - H) // 2
        return im.crop((x, y, x + W, y + H))

    def label(im, text):
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 8 * len(text) + 12, 18], fill=(0, 0, 0))
        d.text((6, 3), text, fill=(255, 255, 255))
        return im

    names = [p[0] for p in PLOTS]
    for name in names:
        out = Image.new("RGB", (W * 2 + 4, H), (255, 255, 255))
        out.paste(label(crop(name, "summer"), f"{name} summer"), (0, 0))
        out.paste(label(crop(name, "winter"), f"{name} winter"), (W + 4, 0))
        out.save(os.path.join(dst, f"pair_{name}.png"))
    out = Image.new("RGB", (W * 2 + 4, H * 2 + 4), (255, 255, 255))
    for i, (season, _) in enumerate(SEASONS):
        out.paste(label(crop("temperate", season), f"temperate {season}"), ((i % 2) * (W + 4), (i // 2) * (H + 4)))
    out.save(os.path.join(dst, "seasons_temperate.png"))
    out = Image.new("RGB", (W * 3 + 8, H * 2 + 4), (255, 255, 255))
    for i, name in enumerate(names[:6]):
        out.paste(label(crop(name, "summer"), f"{name} summer"), ((i % 3) * (W + 4), (i // 3) * (H + 4)))
    out.save(os.path.join(dst, "climates_summer.png"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"))
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--save", default="flat_512_left_v64")
    ap.add_argument("--out", default=os.path.join("work", "tree_check"))
    ap.add_argument("--zoom", type=int, default=3)
    ap.add_argument("--only", nargs="*", help="撮る区画の名前（既定は全部）")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--montage", metavar="OUT_DIR", help="ゲームを起動せず、--out の画像から PR に付ける画像を OUT_DIR に作る")
    args = ap.parse_args()
    if args.montage:
        montage(os.path.abspath(args.out), os.path.abspath(args.montage))
        return
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    with Game(args.env, args.save, args.port, keep=args.keep) as g:
        centers = {}
        for idx, (name, climate, lift) in enumerate(PLOTS):
            if args.only and name not in args.only:
                continue
            centers[name] = prepare_plot(g, idx, name, climate, lift)
        g.sq(f"gui.set_zoom({args.zoom}); return 1")
        for season, month in SEASONS:
            wait_month(g, month)
            time.sleep(8)  # 木の絵が季節に合わせて入れ替わるのを待つ
            for name, (cx, cy) in centers.items():
                g.sq(f"gui.jump(coord({cx}, {cy})); return 1")
                time.sleep(1.5)
                g.capture(os.path.join(out, f"{name}_{season}.png"))
                print(f"[tree_check] {name} {season} (月 {month})")


if __name__ == "__main__":
    main()
