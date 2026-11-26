"""モノレールの駅の絵と表を書き出す（docs/stations.md の「モノレールの駅」・#156）。MIT License。絵は簡単な物（箱を数式で描いた物）。

向きの絵・シートの並び・道具の絵・表の形は、線路の駅の道具（objects/station/rail_stops/draw_stops.py）を読んで使う。
違うのは、ホームを跨座式の車両の床の高さ（地面から 2.4m）に、柱の上の台として置くこと。ホームは車両より手前にあるので、前の絵に描く。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/station/monorail_stops/draw_stops.py
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
_R = os.path.join(os.path.dirname(HERE), "rail_stops", "draw_stops.py")
_spec = importlib.util.spec_from_file_location("rail_draw_stops", _R)
rs = importlib.util.module_from_spec(_spec)
sys.modules["rail_draw_stops"] = rs
_spec.loader.exec_module(rs)

# ホームの上面の高さ（m）。車両の床（draw_monorail.py の FLOOR_M 2.0 × 高さの倍率 1.2）に合わせる
PLATFORM_Z = 2.4
DECK_M = 0.4  # ホームの床板の厚み
# 軸に直交する c の範囲。車両の車体は c = 0.42〜0.58
NEAR = (0.62, 0.96)
ROOF = (56, 128, 112)
DECK = (176, 174, 168)


def station_back(cv, axis, s, n):
    """後ろの絵: ホームの奥側の柱（車両の下と奥）。"""
    for a in (0.08, 0.5, 0.92):
        rs.box_a_c(cv, axis, a - 0.015, a + 0.015, NEAR[0] + 0.02, NEAR[0] + 0.05, 0, PLATFORM_Z - DECK_M, rs.POST, rs.POST)


def station_front(cv, axis, s, n):
    """前の絵: 手前の柱、ホームの床板、屋根。"""
    for a in (0.08, 0.5, 0.92):
        rs.box_a_c(cv, axis, a - 0.015, a + 0.015, NEAR[1] - 0.05, NEAR[1] - 0.02, 0, PLATFORM_Z - DECK_M, rs.POST, rs.POST)
    a0 = 0.05 if n else 0.0
    a1 = 0.95 if s else 1.0
    z0 = PLATFORM_Z - DECK_M
    rs.box_a_c(cv, axis, a0, a1, NEAR[0], NEAR[1], z0, PLATFORM_Z, DECK, rs.CONCRETE)
    if n:
        rs.box_a_c(cv, axis, 0.0, 0.05, NEAR[0], NEAR[1], z0, PLATFORM_Z + 0.2, rs.KERB, rs.KERB)
    if s:
        rs.box_a_c(cv, axis, 0.95, 1.0, NEAR[0], NEAR[1], z0, PLATFORM_Z + 0.2, rs.KERB, rs.KERB)
    c0, c1 = 0.76, 0.92
    top = PLATFORM_Z + 2.7
    for a in (0.2, 0.8):
        for c in (c0, c1 - 0.02):
            rs.box_a_c(cv, axis, a - 0.01, a + 0.01, c, c + 0.02, PLATFORM_Z, top, rs.POST, rs.POST)
    rs.box_a_c(cv, axis, 0.12, 0.88, c0 - 0.02, c1 + 0.02, top, top + 0.3, ROOF, ROOF)
    rs.box_a_c(cv, axis, 0.04, 0.045, c1 - 0.02, c1 - 0.015, PLATFORM_Z, PLATFORM_Z + 3.2, rs.POST, rs.SIGN)


STOPS = {
    "monorail_station": dict(
        name="pak256_monorail_station", back=station_back, front=station_front,
        dat={"waytype": "monorail_track", "enables_pax": 1, "level": 2, "intro_year": 1900},
        note="モノレールの駅（旅客）。跨座式の桁の脇の、高さ 2.4m の柱の上のホームと屋根",
    ),
}


def table(key, stop):
    """表の全文。線路の駅の道具の表の頭の説明を、この道具のものに替える。"""
    text = rs.table(key, stop)
    return text.replace("# 駅（絵は簡単な物。docs/stations.md）", "# モノレールの駅（絵は簡単な物。docs/stations.md）", 1)


def main():
    for key, stop in STOPS.items():
        rs.sheet(stop).save(os.path.join(HERE, f"{key}.png"))
        with open(os.path.join(HERE, f"{key}.yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(table(key, stop))


if __name__ == "__main__":
    main()
