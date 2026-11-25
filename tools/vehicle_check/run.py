"""車両の描画位置の試験（docs/vehicles.md の「試験」）。MIT License。

用意したゲームの作業フォルダで本体を起動し、tools/vehicle_check/course.nut で道路の輪と車庫と編成を置き、
編成が走る間に、編成ごとに画面の真ん中へ飛んで撮る（本体はスクリプトから止めると戻せないので、止めずに撮る）。向き（8 方向）ごとに 1 枚ずつ残す。

    python -X utf8 tools/vehicle_check/run.py --game <作業フォルダ> --save flat_512_left_v64 --out <撮った絵の場所> \
        --port 47800 --vehicle pak256_sample_bus

- 作業フォルダは、本体（sim-WinGDI64-OTRPv64.exe など）・DLL・themes/・font/・text/・script/（OTRP の物）と、
  pak/（組んだ pak と config/・text/）と save/（平らな保存データ）を写した物。settings.xml は写さない（送信用の記録を避ける）。
- 道路の車庫は、pak256 にも AMI の 256 版（ami-256-alpha.1）にもまだ無いので、試験のときだけ別の pak から借りて pak/ に置く
  （--depot で名前を渡す。借りた物はコミットしない）。
- MCP で動かすので、OTRP 本体（MCP のある版。-mcp-port）と、OTRP 本体のリポジトリの mcp_client.py が要る
  （--mcp-client か環境変数 MCP_CLIENT。既定は pak256 の本体の checkout と同じフォルダにある simutrans/ の中）。
- Windows で動かす前提（ゲームを taskkill で閉じる）。
- 通行の向きは保存データで決まる（本体の設定。スクリプトからは変えられない）。左側通行と右側通行の保存データを 1 つずつ流す。
- ゲームは起動したときの PID で閉じる。
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

from PIL import Image, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))


def default_client():
    """OTRP 本体のリポジトリ（pak256 の本体の checkout の隣の simutrans/）の mcp_client.py。

    worktree（.claude/worktrees/<名前>/）の中から動かしても届くように、git の共有のディレクトリから辿る。
    """
    try:
        common = subprocess.run(["git", "-C", HERE, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                capture_output=True, text=True, check=True).stdout.strip()
        repo = os.path.dirname(common)
    except (OSError, subprocess.CalledProcessError):
        repo = os.path.normpath(os.path.join(HERE, "..", ".."))
    return os.path.join(os.path.dirname(repo), "simutrans", ".agents", "skills", "simutrans-mcp-gui-debug",
                        "scripts", "mcp_client.py")
# gui.jump で飛んだタイルの中心が出る所の、画面の真ん中からのずれ（1600x900・拡大 3 で、停留所に止まった編成から測った）
JUMP_X, JUMP_Y = 106, 131
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


class Game:
    def __init__(self, client, port):
        self.client = client
        self.port = port

    def sq(self, code, timeout=30):
        out = subprocess.run(
            [sys.executable, "-I", self.client, "--port", str(self.port), "--run-squirrel", code, "--timeout", str(timeout)],
            capture_output=True, text=True, encoding="utf-8", timeout=timeout + 10)
        line = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "{}"
        data = json.loads(line)
        if "result" not in data:
            raise RuntimeError(f"run_squirrel failed: {line} {out.stderr[-300:]}")
        return str(data["result"])

    def capture(self, path, timeout=30):
        subprocess.run(
            [sys.executable, "-I", self.client, "--port", str(self.port), "--capture", path, "--timeout", str(timeout)],
            capture_output=True, text=True, timeout=timeout + 10, check=True)


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


def wait_ready(game, limit=120):
    if not os.path.isfile(game.client):
        raise RuntimeError(f"MCP のクライアントが無い: {game.client}（--mcp-client で渡す）")
    end = time.time() + limit
    last = None
    while time.time() < end:
        try:
            if game.sq("return 1", timeout=5) == "1":
                return
        except Exception as e:  # 起動中は答えない
            last = e
        time.sleep(3)
    raise RuntimeError(f"game did not answer MCP: {last}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", required=True, help="ゲームの作業フォルダ")
    ap.add_argument("--exe", default="sim-WinGDI64-OTRPv64.exe")
    ap.add_argument("--save", required=True, help="save/ の保存データの名前（拡張子なし）")
    ap.add_argument("--out", required=True, help="撮った絵の場所")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--vehicle", default="pak256_sample_bus")
    ap.add_argument("--depot", default="", help="道路の車庫の名前（空なら最初に見つかった物）")
    ap.add_argument("--way", default="ami_road_local", help="輪に敷く道路の名前（AMI の 256 版の道路）")
    ap.add_argument("--origin", default="40,40", help="輪の北西の角（温帯の x<256 に置く）")
    ap.add_argument("--rounds", type=int, default=90, help="撮る回数の上限（4 秒ごと）")
    ap.add_argument("--limit", type=int, default=480,
                    help="全体の秒数の上限。過ぎたら撮るのをやめてゲームを閉じる（外の timeout より短くする）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT") or default_client())
    ap.add_argument("--screensize", default="1600x900")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    game_dir = os.path.abspath(args.game)
    cmd = [os.path.join(game_dir, args.exe), "-singleuser", "-set_workdir", game_dir, "-objects", "pak/",
           "-load", args.save, "-freeplay", "-mute", "-lang", "ja", "-mcp-port", str(args.port), "-screensize", args.screensize]
    proc = subprocess.Popen(cmd, cwd=game_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[game] pid={proc.pid}", flush=True)
    game = Game(args.mcp_client, args.port)
    try:
        wait_ready(game)
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
    finally:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/F"], capture_output=True)
        print(f"[game] stopped pid={proc.pid}", flush=True)


if __name__ == "__main__":
    main()
