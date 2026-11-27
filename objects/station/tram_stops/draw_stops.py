"""路面電車の停留所の絵と表を書き出す（docs/stations.md の「路面電車の停留所」・#153）。pak256 の物。MIT License。絵は簡単な物。

- 道路の停留所（objects/station/road_stops/draw_stops.py）の作りに合わせる（#94・#115・#139）。タイルの座標・向きの 8 通り・
  後ろと前の 2 層・道具の絵・白線の外の帯は、そのスクリプトの関数と定数を読んで使う（写して増やさない）。
- 路面軌道は道路の上にも土の上にも敷けるので、設備はタイルの両脇（道路の白線の外）に置き、中央（軌道）は空ける。
- 道路の停留所と見分けられるように、屋根を緑にする。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/station/tram_stops/draw_stops.py
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_R = os.path.join(os.path.dirname(HERE), "road_stops", "draw_stops.py")
_spec = importlib.util.spec_from_file_location("road_draw_stops", _R)
rs = importlib.util.module_from_spec(_spec)
sys.modules["road_draw_stops"] = rs
_spec.loader.exec_module(rs)

ROOF_TRAM = (62, 128, 92)


# 屋根 2 つ（軸の向き a の範囲）。間は AMI の路面軌道の架線の柱が立つ所（#195。a = 0.5・c = 0.08）。
# 画面で柱に重ならないように、柱の太さより広く空ける（docs/stations.md の「路面電車の停留所」）
ROOFS = ((0.14, 0.39), (0.61, 0.86))


def tram_back(cv, axis, s, n):
    rs.platform(cv, axis, s, n, 0.15, rs.CONCRETE, rs.CONCRETE, rs.BUS_FAR)  # 奥の歩道（乗り場）
    c0, c1 = 0.030, 0.120
    for a0, a1 in ROOFS:  # 奥（a が小さい側）から描く
        for a in (a0 + 0.02, a1 - 0.02):  # 柱 4 本
            for c in (c0, c1 - 0.02):
                rs.box_a_c(cv, axis, a - 0.01, a + 0.01, c, c + 0.02, 0.15, 2.6, rs.POST, rs.POST)
        rs.box_a_c(cv, axis, a0 + 0.05, a1 - 0.05, c0 + 0.005, c0 + 0.035, 0.15, 0.6, (140, 100, 70), (150, 110, 80))  # ベンチ
        rs.box_a_c(cv, axis, a0, a1, c0 - 0.012, c1 + 0.012, 2.6, 2.9, ROOF_TRAM, ROOF_TRAM)  # 屋根
    rs.box_a_c(cv, axis, 0.10, 0.105, 0.125, 0.130, 0.15, 3.2, rs.POST, rs.SIGN)  # 停留所の標識


STOPS = {
    "tram_stop": dict(
        name="pak256_tram_stop", back=tram_back, front=rs.near_walk,
        dat={"waytype": "tram_track", "enables_pax": 1, "level": 2, "intro_year": 1900},
        note="路面電車の停留所。旅客。奥の側に緑の屋根の待合（高さ 2.9m）2 つのある乗り場（間は架線の柱の所）、手前の側に低い歩道",
    ),
}


def table(key, o):
    lines = rs.table(key, o).split("\n")
    assert lines[0].startswith("# 道路の停留所")
    lines[0] = "# 路面電車の停留所（絵は簡単な物。docs/stations.md）。この表と PNG は tram_stops/draw_stops.py が書き出す。"
    return "\n".join(lines)


def main():
    for key, o in STOPS.items():
        rs.sheet(o).save(os.path.join(HERE, f"{key}.png"))
        with open(os.path.join(HERE, f"{key}.yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(table(key, o))


if __name__ == "__main__":
    main()
