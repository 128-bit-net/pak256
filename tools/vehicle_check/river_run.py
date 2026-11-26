"""川の確かめ（#158）。開いたままのゲーム（tools/game.py --interactive）に、地形を作り、地図の拡大で川を引かせる。MIT License。

    python -X utf8 tools/vehicle_check/river_run.py --port <ポート> terrain      # 海と丘
    python -X utf8 tools/vehicle_check/river_run.py --port <ポート> enlarge      # 地図の拡大の窓を操作して 640x640 に。川が引かれる

pak はゲームを起動する側で選ぶ（tools/game.py --interactive --pak <フォルダ>）。この道具はゲームを起動しないので --pak は受けない。
拡大の窓の部品は gui.get_window_components で探して押す（窓の位置が変わっても押せる。詳しくは river_enlarge.nut）。
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import game  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def send(port, code, timeout=280):
    ok, body = game.send_command(os.path.join(game.default_work(port), game.INBOX), code, timeout)
    if not ok:
        raise SystemExit(body)
    return body


def script(port, head, timeout=280):
    with open(os.path.join(HERE, "river_terrain.nut"), encoding="utf-8") as f:
        return send(port, head + f.read(), timeout)


def terrain(port):
    for y0 in range(100, 320, 20):
        print(script(port, f"local STEP = 0, Y0 = {y0}, HILL = 0;\n"), flush=True)
    print(script(port, "local STEP = 2, Y0 = 0, HILL = 0;\n"), flush=True)
    for hill in range(12):
        print(script(port, f"local STEP = 1, Y0 = 0, HILL = {hill};\n"), flush=True)


def window(port, what, n=0, timeout=280):
    with open(os.path.join(HERE, "river_enlarge.nut"), encoding="utf-8") as f:
        out = send(port, f'local WHAT = "{what}", N = {n};\n' + f.read(), timeout)
    print(what, out, flush=True)
    if out.startswith("no "):
        raise SystemExit(out)


def enlarge(port, clicks, capture):
    """地図の拡大の窓: X・Y を 1 段ずつ増やし（512 → 640）、気候の窓で河川の数を増やして、拡大する。"""
    send(port, "gui.close_all_windows(); return gui.open_dialog_tool(24)")  # DIALOG_ENLARGE_MAP
    window(port, "size")
    window(port, "climate")
    window(port, "rivers", clicks)  # 数の入力欄は押すほど刻みが大きくなる
    if capture:
        send(port, "@capture " + os.path.abspath(capture))
    window(port, "start")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("step", choices=["terrain", "enlarge"])
    ap.add_argument("--clicks", type=int, default=9, help="河川の数の「増やす」を押す回数（enlarge）")
    ap.add_argument("--capture", help="拡大の前に窓を撮る PNG（enlarge）")
    a = ap.parse_args()
    if a.step == "terrain":
        terrain(a.port)
    else:
        enlarge(a.port, a.clicks, a.capture)


if __name__ == "__main__":
    main()
