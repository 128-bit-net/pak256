"""歩行者の絵と表を書き出す（docs/pedestrians.md・#172）。MIT License。
絵は仮（画素を直に置いた人形）で、見た目は後から描き直す。

大きさは大人の背丈の px（`ADULT_PX`）で決め、子どもは `height` の割合で小さくする。縮めて描くと細い脚が消えるので、拡大せず画素を直に置く。
足元の位置は、本体の歩行者の動き（vehicle/pedestrian.cc の get_screen_offset）に合わせる。本体は、道路の左側を歩くときだけ
絵を (256 − 2 × offset)/256 タイル左へずらすので、絵は進む向きの右側の、道路の端から offset/256 タイルの所に足元を描く
（道路の車両と違い、左側通行のずれは足されない）。

8 方向を 256px のセルに横に並べ、種類を縦に並べたシート（2048x768）を `walkers.png` に、表を `walkers.yaml` に書く。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/pedestrian/walkers/draw_pedestrians.py
大きさを比べる・位置を確かめる試験（別の場所に書く。git に入れない）:
    ... --adult 10 --out build/walkers_10       大人の背丈を 10px にする
    ... --marker --out build/walkers_marker     向きごとに違う色の人形にする
"""
import argparse
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "tools"))
import vehicles as V  # noqa: E402

# 大人の背丈（px）。実物の大きさ（約 10px）と手本の 2 倍（24px）の間。比べと理由は docs/pedestrians.md
ADULT_PX = 16

# makeobj の特別な色を避ける。当たれば 1 ずらす
SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}

# 向きごとの体の見え方: (横向きの度合い 0=正面か背面 / 1=斜め / 2=真横, 画面で進む左右 -1/0/+1, 顔が見えるか 1=前 / 0=横 / -1=後ろ)
VIEWS = {
    "s": (1, -1, 1), "w": (1, -1, -1), "sw": (2, -1, 0), "se": (0, 0, 1),
    "n": (1, 1, -1), "e": (1, 1, 1), "ne": (2, 1, 0), "nw": (0, 0, -1),
}
# 向きごとの試験の色（--marker）
MARKER_COLORS = {
    "s": (230, 0, 0), "w": (0, 200, 0), "sw": (0, 80, 255), "se": (255, 220, 0),
    "n": (230, 0, 230), "e": (0, 220, 220), "ne": (255, 140, 0), "nw": (150, 90, 20),
}

# 歩行者の表。offset は道路の端から歩く線までの距離（1/256 タイル）。AMI の生活道路の路肩は端から 0〜0.156 タイル（0〜40）。
# 種類ごとに offset を変え、同じ所に重ならないようにする。height は大人に対する背丈の割合。
WALKERS = [
    {
        "name": "pak256_pedestrian_man", "title": "男性", "offset": 18, "weight": 8, "height": 1.0,
        "hair": (40, 30, 26), "skin": (226, 178, 140), "coat": (112, 140, 186), "legs": (104, 100, 110), "shoes": (46, 34, 30),
    },
    {
        "name": "pak256_pedestrian_woman", "title": "女性", "offset": 24, "weight": 8, "height": 0.92, "skirt": True,
        "hair": (86, 48, 28), "skin": (234, 188, 152), "coat": (176, 52, 60), "legs": (96, 70, 64), "shoes": (60, 28, 28),
    },
    {
        "name": "pak256_pedestrian_child", "title": "子ども", "offset": 12, "weight": 4, "height": 0.75, "cap": True,
        "hair": (232, 190, 36), "skin": (232, 184, 146), "coat": (52, 128, 86), "legs": (60, 72, 104), "shoes": (36, 30, 30),
    },
]


def shade(color, k):
    c = tuple(max(0, min(255, int(v * k))) for v in color)
    if (c[0] << 16 | c[1] << 8 | c[2]) in SPECIAL:
        c = (c[0] + 1 if c[0] < 255 else c[0] - 1, c[1], c[2])
    return c


def foot_offset_px(direction, offset):
    """セルの基準点（タイルの中心）から足元までのずれ（px）。進む向きの右側、道路の端から offset/256 タイル。"""
    # 車線のずれ（道路の中心から 3/16 タイル = 48/256）を、道路の中心から (128 - offset)/256 タイルに引き伸ばす
    k = (128 - offset) / 48
    x, y = V.lane_offset_px(direction)
    return x * k, y * k


def foot_point(direction, offset):
    """足元の画素（靴の下の行の中央）。"""
    dx, dy = foot_offset_px(direction, offset)
    return int(round(V.ORIGIN[0] + dx)), int(round(V.ORIGIN[1] + dy))


class Figure:
    """足元を原点にした画素の人形。x は画面の右が正、y は上が正（靴の下の行が 0）。"""

    def __init__(self):
        self.px = {}

    def rect(self, x0, x1, y0, y1, color, lit=True):
        """[x0, x1) x [y0, y1) を塗る。光は左上からなので、左の列を明るく、右の列を暗くする。"""
        for x in range(x0, x1):
            k = 1.0
            if lit and x1 - x0 >= 2:
                k = 1.18 if x == x0 else (0.74 if x == x1 - 1 else 1.0)
            for y in range(y0, y1):
                self.px[(x, y)] = shade(color, k)


def span(width, shift=0):
    """中央にそろえた幅 width の区間。"""
    x0 = -(width // 2) + shift
    return x0, x0 + width


def draw_figure(spec, direction, adult_px):
    side, turn, face = VIEWS[direction]
    height = max(6, int(round(adult_px * spec["height"])))
    head_h = max(2, int(round(height * 0.22)))
    leg_h = max(2, int(round(height * 0.38)))
    body_h = max(2, height - head_h - leg_h)
    body_w = max(2, int(round(height * (0.34, 0.30, 0.24)[side])))
    head_w = max(2, int(round(height * 0.21)))
    leg_w = max(1, int(round(height * 0.12)))
    hip = leg_h
    neck = hip + body_h
    f = Figure()

    # 脚。横から見るほど前後に開き、上（腰）へ寄せる。正面と背面は 2 本を並べる
    stride = (0, int(round(height * 0.08)), int(round(height * 0.14)))[side]
    shoe_h = max(1, int(round(height * 0.07)))
    if side == 0:
        gap = 1 if leg_w >= 2 else 0
        for i, x0 in enumerate((-leg_w, gap)):
            lift = shoe_h // 2 if i == 1 else 0  # 片足を少し上げる
            f.rect(x0, x0 + leg_w, lift + shoe_h, hip, spec["legs"])
            f.rect(x0, x0 + leg_w, lift, lift + shoe_h, spec["shoes"], lit=False)
    else:
        for foot in (-1, 1):
            k = 1.0 if foot == turn else 0.75  # 後ろの脚を暗くする
            for y in range(hip):
                x = int(round(foot * stride * (1 - y / hip))) - leg_w // 2
                color = spec["shoes"] if y < shoe_h else spec["legs"]
                f.rect(x, x + leg_w, y, y + 1, shade(color, k), lit=False)

    # 胴。腕は左右の端の列（暗くする）と、手の画素
    x0, x1 = span(body_w)
    f.rect(x0, x1, hip, neck, spec["coat"])
    if spec.get("skirt"):
        hem = max(1, leg_h // 3)
        f.rect(x0 - (body_w >= 4), x1 + (body_w >= 4), hip - hem, hip + 1, spec["coat"])
    hand_y = hip + max(0, body_h // 5)
    if side == 2:
        f.rect(turn - 1 if turn > 0 else turn, turn + 1 if turn > 0 else turn + 2, hand_y, neck - 1, shade(spec["coat"], 0.7), lit=False)
        f.rect(turn * 1, turn * 1 + 1, hand_y - 1, hand_y + 1, spec["skin"], lit=False)
    elif body_w >= 4:
        for x in (x0, x1 - 1):
            f.rect(x, x + 1, hand_y, neck - 1, shade(spec["coat"], 0.68), lit=False)
            f.rect(x, x + 1, hand_y - 1, hand_y + 1, spec["skin"], lit=False)

    # 頭。顔は進む向きの側に寄せ、後ろ向きは髪（帽子）だけにする
    hx0, hx1 = span(head_w, turn if side == 2 else 0)
    top = neck + head_h
    f.rect(hx0, hx1, neck, top, spec["hair"])
    hair_h = max(1, int(round(head_h * 0.38)))
    if face >= 0:
        fx0, fx1 = hx0, hx1
        if turn:
            cut = max(1, head_w // (2 if face == 0 else 3))
            fx0, fx1 = (hx0, hx1 - cut) if turn < 0 else (hx0 + cut, hx1)
        f.rect(fx0, fx1, neck, top - hair_h, spec["skin"])
    elif turn:  # 斜め後ろ: 横顔の端だけ見える
        edge = hx0 if turn < 0 else hx1 - 1
        f.rect(edge, edge + 1, neck, top - hair_h - 1, spec["skin"], lit=False)
    if spec.get("cap") and turn:  # 帽子のつば
        brim = hx0 - 1 if turn < 0 else hx1
        f.rect(brim, brim + 1, top - hair_h, top - hair_h + 1, spec["hair"], lit=False)
    if spec.get("skirt"):  # 長い髪
        back = (hx0, hx1) if face < 0 else ((hx1 - 1, hx1) if turn <= 0 else (hx0, hx0 + 1))
        f.rect(back[0], back[1], neck - max(1, head_h // 2), neck + 1, spec["hair"], lit=False)
    return f


def draw_cell(spec, direction, adult_px=ADULT_PX, marker=False):
    """1 方向のセル（256x256、RGBA）。"""
    cell = Image.new("RGBA", (V.CELL, V.CELL), (0, 0, 0, 0))
    fx, fy = foot_point(direction, spec["offset"])
    put = cell.load()
    for (x, y), color in draw_figure(spec, direction, adult_px).px.items():
        put[fx + x, fy - y] = (MARKER_COLORS[direction] if marker else color) + (255,)
    return cell


def draw_sheet(adult_px=ADULT_PX, marker=False):
    """行 = WALKERS の順、列 = 向き（V.DIRECTIONS の順）。"""
    sheet = Image.new("RGBA", (V.CELL * len(V.DIRECTIONS), V.CELL * len(WALKERS)), (0, 0, 0, 0))
    for row, spec in enumerate(WALKERS):
        for col, direction in enumerate(V.DIRECTIONS):
            sheet.paste(draw_cell(spec, direction, adult_px, marker), (col * V.CELL, row * V.CELL))
    return sheet


def yaml_text():
    lines = [
        "# 歩行者（絵は仮）。この表と PNG は draw_pedestrians.py が書き出す。直すときはスクリプトを直して流し直す。",
        "# offset は道路の端から歩く線までの距離（1/256 タイル）で、絵の足元の位置と組になる（docs/pedestrians.md）。",
    ]
    for row, spec in enumerate(WALKERS):
        lines += [
            "- obj: pedestrian",
            f"  name: {spec['name']}   # {spec['title']}",
            "  copyright: pak256.LongScale チーム",
            f"  distributionweight: {spec['weight']}",
            f"  offset: {spec['offset']}",
            "  image:",
        ]
        for col, direction in enumerate(V.DIRECTIONS):
            lines.append(f"    {direction}: walkers.{row}.{col}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adult", type=int, default=ADULT_PX, help="大人の背丈 px（試験用）")
    ap.add_argument("--marker", action="store_true", help="向きごとに違う色にする（試験用）")
    ap.add_argument("--out", default=HERE, help="書き出す場所")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    draw_sheet(args.adult, args.marker).save(os.path.join(args.out, "walkers.png"))
    with open(os.path.join(args.out, "walkers.yaml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(yaml_text())
    print("wrote", os.path.join(args.out, "walkers.png"))


if __name__ == "__main__":
    main()
