"""車両の長さと描画位置の決まり（docs/standards.md の 4 章）を計算にした物。MIT License。

車両を描くスクリプト（objects/vehicle/ の draw_*.py）と検査（tools/test_vehicles.py）が使う。
数はすべて docs/standards.md の決まりと同じにする。決まりを変えるときは、両方を一緒に直す。

座標: 地面はタイルの単位（1 タイル = 1）。x は東（画面の右下）、y は南（画面の左下）、原点はタイルの中心。
画面はセルの画素。256px のタイルで、タイルの中心はセルの (128, 192)（docs/ground.md）。
"""
import math

CELL = 256  # 1 タイルのセル
ORIGIN = (128, 192)  # セルの中のタイルの中心（地面の菱形の中心）
M_PER_UNIT = 1.65  # 長さ 1 単位の実物の m（docs/concept.md の C）
UNITS_PER_TILE = 16  # 本体の CARUNITS_PER_TILE
M_PER_TILE = M_PER_UNIT * UNITS_PER_TILE  # 26.4m
PX_PER_M_Z = CELL / (M_PER_TILE * math.sqrt(2)) * math.sqrt(3) / 2  # 高さ 1m の px（約 5.94）
PX_PER_UNIT_SIDE = CELL / 2 * math.sqrt(2) / UNITS_PER_TILE  # 横向き（画面で水平）の 1 単位の px（約 11.3）

# 車両の大きさ（2026-11-26、ユーザーの決定。docs/standards.md の 4 章「大きさ」）。画面の上の長さ・幅・高さを、
# 道路の車両は pak128 の同じ種類の手本の 2 倍、線路の車両は pak128.Japan の手本の 2 倍にする。
# 線路の車両は長さが実物の換算と同じなので、実物の幅・高さに次の倍率を掛けて描く。
RAIL_WIDTH_SCALE = 1.40
RAIL_HEIGHT_SCALE = 1.20

# 線路の車両（#46）の車輪の下端を、地面より何 px 下に描くか。AMI の線路は新描画位置で、レールが地面より下がる
# （way-addon.md の「線路の新描画位置」）。ゲームで走らせて決める（docs/vehicles.md の「線路の車両」）
RAIL_WHEEL_DROP_PX = 0

# 本体が左側通行のときに足すずれ（64px のタイルでの値。本家 125.0.1 の vehicle_base.cc の
# driveleft_base_offsets と、OTRP の settings.cc の既定値。どちらも同じ）。本体はこれを タイルの幅 / 64 倍する
DRIVELEFT_64 = {
    "s": (12, 6), "w": (-12, 6), "sw": (0, 6), "se": (12, 0),
    "n": (-12, -6), "e": (12, -6), "ne": (0, -6), "nw": (-12, 0),
}

# 向き（dat の emptyimage の添字）ごとの進む向き（地面の単位ベクトル）
_D = 1 / math.sqrt(2)
HEADING = {
    "s": (0.0, 1.0), "w": (-1.0, 0.0), "sw": (-_D, _D), "se": (_D, _D),
    "n": (0.0, -1.0), "e": (1.0, 0.0), "ne": (_D, -_D), "nw": (-_D, -_D),
}
DIRECTIONS = ("s", "w", "sw", "se", "n", "e", "ne", "nw")  # 本体の ribi_t::get_dir の順

# 基準点（本体の車両の位置。セルではタイルの中心 ORIGIN に当たる）から車体の前の端までの距離（単位。前が正）。
# 0 = 前の端を基準点に置き、車体は後ろへ length 伸ばす。止まると先頭の基準点がタイルの出口の辺の近くに来るので、
# 車体がタイルに収まる（docs/standards.md の 4 章「描画位置」と docs/vehicles.md の「前後の位置（細目）」）
FRONT_UNITS = 0


def length_from_px(px):
    """画面の横向きの長さ（px）から dat の length（道路の車両。手本の 2 倍の長さを単位にする）。"""
    return max(1, int(math.floor(px / PX_PER_UNIT_SIDE + 0.5)))


def length_units(metres):
    """実物の長さ（m）から dat の length。四捨五入（0.5 は切り上げ）で、1 より小さくしない。"""
    return max(1, int(math.floor(metres / M_PER_UNIT + 0.5)))


def to_screen(x, y, z_m=0.0):
    """地面の点（タイルの単位）と高さ（m）を、セルの画素 (sx, sy) にする。"""
    sx = ORIGIN[0] + CELL / 2 * (x - y)
    sy = ORIGIN[1] + CELL / 4 * (x + y) - z_m * PX_PER_M_Z
    return sx, sy


def from_screen(dx, dy):
    """画面のずれ（px）を、地面のずれ（タイルの単位）にする。"""
    a = dx / (CELL / 2)  # x - y
    b = dy / (CELL / 4)  # x + y
    return (a + b) / 2, (b - a) / 2


def lane_offset_px(direction):
    """右側の車線に描くずれ（セルの画素）。左側通行のずれのちょうど半分を、反対の向きに置く。

    本体は 1 組の絵を、右側通行ではそのまま、左側通行では DRIVELEFT_64 だけずらして描くので、
    半分に置くと、どちらの通行でも道路の中心から同じ距離になる。
    """
    lx, ly = DRIVELEFT_64[direction]
    scale = CELL / 64
    return -lx * scale / 2, -ly * scale / 2


def lane_point(direction):
    """右側の車線の基準点（地面、タイルの単位）。"""
    return from_screen(*lane_offset_px(direction))


def footprint(direction, length, width_m, front_units, centered=False):
    """車体の地面の四隅（タイルの単位）。前の右・前の左・後の左・後の右の順。

    length は dat の length（単位）。車体の長さは length × 1.65m に描く（実物の長さではない。連結のすき間を出さないため）。
    front_units は、基準点から車体の前の端までの距離（単位。前が正）。
    centered は線路の車両（#46）。本体は左側通行のずれを道路の車両（road_vehicle_t）にしか足さないので、
    線路の車両は車線のずれを付けず、線路の中心（基準点）に描く。
    """
    hx, hy = HEADING[direction]
    rx, ry = -hy, hx  # 右の向き
    px, py = (0.0, 0.0) if centered else lane_point(direction)
    front = front_units / UNITS_PER_TILE
    back = (front_units - length) / UNITS_PER_TILE
    half = width_m / M_PER_TILE / 2
    pts = []
    for along, side in ((front, half), (front, -half), (back, -half), (back, half)):
        pts.append((px + hx * along + rx * side, py + hy * along + ry * side))
    return pts
