"""線路の閉塞信号の絵と表を書き出す（docs/signals.md）。MIT License。絵は簡単（箱を数式で描いた物）。

- 縮尺・タイルの座標は objects/city/town_buildings/draw_buildings.py と同じ（1 タイル = 26.4m、高さ 1m = 5.94px）。
- 信号は列車が進む向きごとに 1 つの絵を持つ。dat の image[i] の i は 状態 × 4 + 向き。
  向きは 0 = n（北へ進む。-v）、1 = s（南へ進む。+v）、2 = w（西へ進む。-u）、3 = e（東へ進む。+u）。
  状態は 0 = 赤（止まれ）、1 = 青（進め）。本体の signal_t::calc_image の添字の順（n, s, w, e。数字の書き方のとき）。
- 日本の左側通行に合わせ、信号は進む向きの左に、タイルの手前の端（進む向きの出口の側）に立てる。
  南へ進む（+v）なら左は +u（見える側）、北へ進む（-v）なら -u、東へ進む（+u）なら -v、西へ進む（-u）なら +v。
- シートは 8 列 × 2 行。0 行 = 信号の絵（列 = 状態 × 4 + 向き）、1 行 = 道具の絵（0 列）とカーソル（1 列）。
  セルの名前は <名前>.<行>.<列>。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/signal/rail_signal/draw_signal.py
"""
import importlib.util
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OBJECTS = os.path.dirname(os.path.dirname(HERE))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(OBJECTS, *rel))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


db = _load("draw_buildings", ("city", "town_buildings", "draw_buildings.py"))
stops = _load("draw_stops", ("station", "rail_stops", "draw_stops.py"))

CELL = db.CELL
CLEAR = db.CLEAR
NAME = "pak256_rail_signal"
KEY = "rail_signal"

POST = (84, 88, 96)
HOOD = (40, 44, 52)
RED = (232, 40, 36)
GREEN = (40, 200, 90)
FOOT = (150, 148, 142)

# 向き（dat の順）: (名前, 線路の軸, 進む向きが + か, 手前（+c）の側に立てるか)
# 軸が NS のとき a = v・c = u、EW のとき a = u・c = v。
DIRS = [
    ("n", "NS", False, False),  # 北へ進む（-v）: 左は -u
    ("s", "NS", True, True),    # 南へ進む（+v）: 左は +u
    ("w", "EW", False, True),   # 西へ進む（-u）: 左は +v
    ("e", "EW", True, False),   # 東へ進む（+u）: 左は -v
]
STATES = 2  # 0 = 赤、1 = 青


def box(cv, axis, a0, a1, c0, c1, z0, z1, wall, roof):
    if axis == "NS":
        db.flat_box(cv, c0, c1, a0, a1, z0, z1, wall, roof)
    else:
        db.flat_box(cv, a0, a1, c0, c1, z0, z1, wall, roof)


def signal(cv, axis, plus, near, lamp):
    """柱と、灯りを 1 つ載せた頭。線路は c = 0.43〜0.57 を通る。柱は線路の脇（道床の外）に立てる。"""
    c = 0.68 if near else 0.30
    a = 0.86 if plus else 0.14
    w = 0.03  # 柱の太さ（タイル。見やすいよう実物より太く、高くした）
    box(cv, axis, a - 0.07, a + 0.07, c - 0.07, c + 0.07, 0, 0.4, FOOT, FOOT)  # 土台
    box(cv, axis, a - w, a + w, c - w, c + w, 0.4, 5.0, POST, POST)  # 柱
    box(cv, axis, a - 0.07, a + 0.07, c - 0.07, c + 0.07, 5.0, 6.6, lamp, HOOD)  # 頭（壁が灯りの色、上面は暗い）


def cell(direction, state):
    _, axis, plus, near = DIRS[direction]
    cv = db.Canvas()
    signal(cv, axis, plus, near, GREEN if state else RED)
    return cv.finish()


def sheet():
    out = Image.new("RGB", (CELL * STATES * len(DIRS), CELL * 2), CLEAR)
    for s in range(STATES):
        for d in range(len(DIRS)):
            out.paste(cell(d, s), ((s * len(DIRS) + d) * CELL, 0))
    # 道具の絵とカーソル: 南へ進む青の信号（1 列 = 5）
    art = out.crop((5 * CELL, 0, 6 * CELL, CELL))
    out.paste(stops.tool_icon(art, (84, 104, 134)), (0, CELL))
    out.paste(art, (CELL, CELL))
    return out


def table():
    lines = [
        "# 線路の閉塞信号（絵は簡単。docs/signals.md）。この表と PNG は draw_signal.py が書き出す。",
        "# 1 タイル = 26.4m の縮尺（docs/buildings.md）。",
        "obj: roadsign",
        f"name: {NAME}",
        "copyright: pak256.LongScale チーム",
        "# 閉塞信号。次の区間に列車がいると赤、いなければ青。image[状態 × 4 + 向き]。向きの順は n・s・w・e",
        "waytype: track",
        "is_signal: 1",
        "offset_left: 0",  # 絵は最初から進む向きの左に描いてあるので、信号を左に立てる地図でも、本体の左寄せ（既定 14）を使わない
        "intro_year: 1900",
        "cost: 500",
        f'icon: "> {KEY}.1.0"',
        f"cursor: {KEY}.1.1",
        "image:",
    ]
    for i in range(STATES * len(DIRS)):
        lines.append(f"  {i}: {KEY}.0.{i}")
    return "\n".join(lines) + "\n"


def main():
    sheet().save(os.path.join(HERE, f"{KEY}.png"))
    with open(os.path.join(HERE, f"{KEY}.yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(table())


if __name__ == "__main__":
    main()
