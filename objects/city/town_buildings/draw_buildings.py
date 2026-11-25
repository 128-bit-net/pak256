"""役場と住宅の絵と表を書き出す（docs/buildings.md）。MIT License。絵は仮（箱と屋根を数式で描いた物）で、見た目は後から描き直す。

- 縮尺（docs/concept.md の 3 章 C）: 1 タイル = 16 単位 × 1.65m = 26.4m。256px のタイルの菱形から、
  高さは 1m = 約 5.94px（docs/trees.md と同じ）。地面は、タイルの辺に沿って 1m = (4.85, 2.42)px。
- 建物は 1x1 タイル、向きは 1 通り（窓は見える 2 面に描き、戸は左下の面だけに描く。向きは 1 通りなので回しても同じ絵）。
- 絵は 256x256 のセル 1 枚。タイルの菱形はセルの下半分（上の頂点 (128,128)・左 (0,192)・右 (256,192)・下 (128,256)）。
  建物の足元の位置は、タイルの座標 (u, v)（0〜1）で決める。u は右下（南東）へ、v は左下（南西）へ。
  画面の x = 128 + (u - v) * 128、y = 128 + (u + v) * 64 - 高さ（m） * 5.94。

使い方（Pillow が要る。書き出した PNG と表は git に入れる）:
    python -X utf8 objects/city/town_buildings/draw_buildings.py
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
CELL = 256
SS = 3  # 描くときの拡大（縁をなめらかにしてから、半透明を切る）
PX_Z = 5.94  # 高さ 1m の px
TILE_M = 26.4  # 1 タイルの辺の長さ（m）
CLEAR = (231, 255, 255)  # makeobj の透明色

# makeobj が特別な色として読む色（描いた色がこれに当たると別の意味になるので、避ける）
_SPECIAL = {
    0x244B67, 0x395E7C, 0x4C7191, 0x6084A7, 0x7497BD, 0x88ABD3, 0x9CBEE9, 0xB0D2FF,
    0x7B5803, 0x8E6F04, 0xA18605, 0xB49D07, 0xC6B408, 0xD9CB0A, 0xECE20B, 0xFFF90D,
    0x57656F, 0x7F9BF1, 0xFFFF53, 0xFF211D, 0x01DD01, 0x6B6B6B, 0x9B9B9B, 0xB3B3B3,
    0xC9C9C9, 0xDFDFDF, 0xE3E3FF, 0xC1B1D1, 0x4D4D4D, 0xFF017F, 0x0101FF, 0xE7FFFF,
}


def safe(rgb):
    r, g, b = (max(0, min(255, int(round(v)))) for v in rgb)
    if (r << 16 | g << 8 | b) in _SPECIAL:
        b = b + 1 if b < 255 else b - 1
    return (r, g, b)


def shade(rgb, k):
    return tuple(c * k for c in rgb)


def m2t(m):
    """メートルをタイルの座標の長さ（0〜1）にする。"""
    return m / TILE_M


class Canvas:
    """SS 倍に拡大した 1 セル分の透明な画。座標は等倍の px。"""

    def __init__(self):
        self.im = Image.new("RGBA", (CELL * SS, CELL * SS), (0, 0, 0, 0))
        self.dr = ImageDraw.Draw(self.im)

    def poly(self, pts, rgb):
        self.dr.polygon([(x * SS, y * SS) for x, y in pts], fill=safe(rgb) + (255,))

    def finish(self):
        """縮めて、半透明を切り（α ≥ 128 を不透明）、透明色で埋めた RGB にする。"""
        small = self.im.resize((CELL, CELL), Image.LANCZOS)
        out = Image.new("RGB", (CELL, CELL), CLEAR)
        px, src = out.load(), small.load()
        for y in range(CELL):
            for x in range(CELL):
                r, g, b, a = src[x, y]
                if a >= 128:
                    px[x, y] = safe((r, g, b))
        return out


def P(u, v, zm):
    """タイルの座標 (u, v) と高さ zm（m）を、セルの画面の座標にする。"""
    return (128 + (u - v) * 128, 128 + (u + v) * 64 - zm * PX_Z)


# 面の明るさ: 光は左上から。南西の面（左下を向く）は明るく、南東の面（右下を向く）は暗く。
LIT_SW = 1.0
LIT_SE = 0.78
LIT_ROOF = 1.0


def face_sw(cv, u0, u1, v, z0, z1, rgb):
    """v = 一定の面（左下を向く）。u が u0〜u1、高さ z0〜z1（m）。"""
    cv.poly([P(u0, v, z0), P(u1, v, z0), P(u1, v, z1), P(u0, v, z1)], shade(rgb, LIT_SW))


def face_se(cv, u, v0, v1, z0, z1, rgb):
    """u = 一定の面（右下を向く）。"""
    cv.poly([P(u, v0, z0), P(u, v1, z0), P(u, v1, z1), P(u, v0, z1)], shade(rgb, LIT_SE))


def windows(cv, face, fixed, a0, a1, z0, floors, floor_h, wall, glass, door=None):
    """面に窓を並べる。a0〜a1 は面に沿った座標（u か v）、z0 は 1 階の床の高さ。
    窓の幅 1.4m、高さ 1.6m、間隔 3.2m ほど。door=(位置 0〜1, 幅 m, 高さ m, 色) で 1 階の中央付近に戸を置く。"""
    width_t = a1 - a0
    n = max(1, int(width_t * TILE_M / 3.2))
    step = width_t / n
    for fl in range(floors):
        zb = z0 + fl * floor_h + (floor_h - 1.6) / 2 + 0.2
        for i in range(n):
            if door and fl == 0 and i == int(door[0] * n):
                continue
            c = a0 + step * (i + 0.5)
            w = m2t(1.4) / 2
            if face == "sw":
                face_sw(cv, c - w, c + w, fixed, zb, zb + 1.6, glass)
            else:
                face_se(cv, fixed, c - w, c + w, zb, zb + 1.6, shade(glass, LIT_SE / LIT_SW))
    if door:
        c = a0 + step * (int(door[0] * n) + 0.5)
        w = m2t(door[1]) / 2
        if face == "sw":
            face_sw(cv, c - w, c + w, fixed, z0, z0 + door[2], door[3])
        else:
            face_se(cv, fixed, c - w, c + w, z0, z0 + door[2], shade(door[3], LIT_SE / LIT_SW))


def flat_box(cv, u0, u1, v0, v1, z0, z1, wall, roof):
    """平らな屋根の箱。壁（南西・南東の面）と屋根。"""
    face_sw(cv, u0, u1, v1, z0, z1, wall)
    face_se(cv, u1, v0, v1, z0, z1, wall)
    cv.poly([P(u0, v0, z1), P(u1, v0, z1), P(u1, v1, z1), P(u0, v1, z1)], shade(roof, LIT_ROOF))


def gable_box(cv, u0, u1, v0, v1, z0, z1, ridge_h, ridge_axis, wall, roof_a, roof_b):
    """切妻屋根の箱。壁は z0〜z1、棟は z1 + ridge_h。ridge_axis は棟の向き（"u" か "v"）。
    棟が u の向きなら、屋根の面は v の小さい側（奥）と大きい側（手前、左下を向く）に傾き、右下の面に三角の妻が出る。"""
    zr = z1 + ridge_h
    if ridge_axis == "u":
        vm = (v0 + v1) / 2
        face_sw(cv, u0, u1, v1, z0, z1, wall)
        face_se(cv, u1, v0, v1, z0, z1, wall)
        # 右下の妻（三角）
        cv.poly([P(u1, v0, z1), P(u1, v1, z1), P(u1, vm, zr)], shade(wall, LIT_SE))
        # 奥の屋根、手前の屋根
        cv.poly([P(u0, v0, z1), P(u1, v0, z1), P(u1, vm, zr), P(u0, vm, zr)], shade(roof_b, 0.85))
        cv.poly([P(u0, vm, zr), P(u1, vm, zr), P(u1, v1, z1), P(u0, v1, z1)], shade(roof_a, LIT_SW))
    else:
        um = (u0 + u1) / 2
        face_sw(cv, u0, u1, v1, z0, z1, wall)
        face_se(cv, u1, v0, v1, z0, z1, wall)
        # 左下の妻（三角）
        cv.poly([P(u0, v1, z1), P(u1, v1, z1), P(um, v1, zr)], shade(wall, LIT_SW))
        cv.poly([P(u0, v0, z1), P(um, v0, zr), P(um, v1, zr), P(u0, v1, z1)], shade(roof_b, 0.85))
        cv.poly([P(um, v0, zr), P(u1, v0, z1), P(u1, v1, z1), P(um, v1, zr)], shade(roof_a, LIT_SE))


def hip_roof(cv, u0, u1, v0, v1, z1, h, roof):
    """寄棟風の屋根（四角錐を平らにつぶした形）。頂点は中心。"""
    um, vm = (u0 + u1) / 2, (v0 + v1) / 2
    top = (um, vm, z1 + h)
    cv.poly([P(u0, v0, z1), P(u1, v0, z1), P(*top[:2], top[2])], shade(roof, 0.8))
    cv.poly([P(u0, v0, z1), P(u0, v1, z1), P(*top[:2], top[2])], shade(roof, 0.9))
    cv.poly([P(u0, v1, z1), P(u1, v1, z1), P(*top[:2], top[2])], shade(roof, LIT_SW))
    cv.poly([P(u1, v0, z1), P(u1, v1, z1), P(*top[:2], top[2])], shade(roof, LIT_SE))


def footprint(w_m, d_m, cu=0.5, cv_=0.5):
    """幅 w_m（u の向き）、奥行き d_m（v の向き）の足跡を、中心 (cu, cv_) に置いた (u0, u1, v0, v1)。"""
    return cu - m2t(w_m) / 2, cu + m2t(w_m) / 2, cv_ - m2t(d_m) / 2, cv_ + m2t(d_m) / 2


GLASS = (86, 120, 150)
GLASS_DARK = (58, 84, 108)


# ---- 建物ごとの絵 ----

def draw_townhall(cv):
    """役場。3 階建て（階高 4m）、幅 22m・奥行き 16m の鉄筋コンクリート造。平らな屋根に小さな時計塔。"""
    u0, u1, v0, v1 = footprint(22, 16)
    wall = (206, 198, 180)
    floor_h = 4.0
    H = 12.0
    # 基礎の段（0.6m）
    flat_box(cv, u0 - 0.01, u1 + 0.01, v0 - 0.01, v1 + 0.01, 0, 0.6, (150, 146, 138), (160, 156, 148))
    flat_box(cv, u0, u1, v0, v1, 0.6, H + 0.6, wall, (120, 118, 112))
    # 屋上の縁（胸壁）
    flat_box(cv, u0, u1, v0, v1, H + 0.6, H + 1.2, (186, 178, 162), (120, 118, 112))
    # 窓と正面玄関
    windows(cv, "sw", v1, u0, u1, 0.6, 3, floor_h, wall, GLASS, door=(0.5, 2.6, 2.4, (92, 62, 44)))
    windows(cv, "se", u1, v0, v1, 0.6, 3, floor_h, wall, GLASS)
    # 玄関の庇（1 階の上、2.4m 張り出す）
    ux0, ux1 = 0.5 - m2t(2.2), 0.5 + m2t(2.2)
    flat_box(cv, ux0, ux1, v1, v1 + m2t(2.4), 3.1, 3.4, (170, 164, 150), (140, 136, 128))
    # 時計塔: 屋上の左奥に 5m 角で 5m 立ち上げ、寄棟の屋根
    tu0, tu1, tv0, tv1 = footprint(5, 5, 0.40, 0.42)
    flat_box(cv, tu0, tu1, tv0, tv1, H + 1.2, H + 6.2, (196, 188, 170), (120, 118, 112))
    face_sw(cv, tu0 + 0.03, tu1 - 0.03, tv1, H + 3.6, H + 5.4, (236, 232, 218))  # 時計の文字盤
    face_se(cv, tu1, tv0 + 0.03, tv1 - 0.03, H + 3.6, H + 5.4, (236, 232, 218))
    hip_roof(cv, tu0 - 0.01, tu1 + 0.01, tv0 - 0.01, tv1 + 0.01, H + 6.2, 2.0, (64, 78, 88))


def draw_house_small(cv):
    """小さな戸建て（level 1）。2 階建て、幅 9m・奥行き 7m、切妻の瓦屋根（棟は u の向き）。"""
    u0, u1, v0, v1 = footprint(9, 7, 0.5, 0.52)
    wall = (232, 226, 208)
    floor_h = 3.0
    gable_box(cv, u0, u1, v0, v1, 0, 6.0, 2.6, "u", wall, (128, 78, 62), (112, 68, 54))
    windows(cv, "sw", v1, u0, u1, 0, 2, floor_h, wall, GLASS, door=(0.3, 1.0, 2.1, (96, 66, 48)))
    windows(cv, "se", u1, v0, v1, 0, 2, floor_h, wall, GLASS)


def draw_house_wide(cv):
    """やや大きな戸建て（level 1）。2 階建て、幅 12m・奥行き 9m、切妻の屋根（棟は v の向き）。"""
    u0, u1, v0, v1 = footprint(12, 9, 0.5, 0.5)
    wall = (214, 214, 200)
    floor_h = 3.0
    gable_box(cv, u0, u1, v0, v1, 0, 6.0, 3.0, "v", wall, (74, 88, 104), (62, 74, 88))
    windows(cv, "sw", v1, u0, u1, 0, 2, floor_h, wall, GLASS, door=(0.65, 1.0, 2.1, (80, 60, 46)))
    windows(cv, "se", u1, v0, v1, 0, 2, floor_h, wall, GLASS)


def draw_row_house(cv):
    """長屋・テラスハウス（level 2）。3 階建て、幅 20m・奥行き 9m、勾配の浅い切妻（棟は u の向き）。"""
    u0, u1, v0, v1 = footprint(20, 9, 0.5, 0.5)
    wall = (222, 196, 168)
    floor_h = 3.0
    gable_box(cv, u0, u1, v0, v1, 0, 9.0, 2.0, "u", wall, (96, 90, 96), (84, 78, 84))
    windows(cv, "sw", v1, u0, u1, 0, 3, floor_h, wall, GLASS, door=(0.15, 1.0, 2.1, (88, 62, 48)))
    windows(cv, "se", u1, v0, v1, 0, 3, floor_h, wall, GLASS)


def draw_apartment(cv):
    """集合住宅（level 3）。5 階建て（階高 3m）、幅 22m・奥行き 12m、平らな屋根。"""
    u0, u1, v0, v1 = footprint(22, 12, 0.5, 0.5)
    wall = (210, 206, 196)
    floor_h = 3.0
    flat_box(cv, u0, u1, v0, v1, 0, 15.0, wall, (128, 126, 120))
    flat_box(cv, u0, u1, v0, v1, 15.0, 15.6, (180, 176, 166), (128, 126, 120))  # 屋上の縁
    windows(cv, "sw", v1, u0, u1, 0, 5, floor_h, wall, GLASS, door=(0.5, 1.8, 2.3, (86, 90, 98)))
    windows(cv, "se", u1, v0, v1, 0, 5, floor_h, wall, GLASS)


# 物ごとの決め事: 描く関数、dat に書くもの
#   type: tow（役場）・res（住宅）
BUILDINGS = {
    "townhall": dict(
        name="pak256_townhall", draw=draw_townhall,
        dat={"type": "tow", "build_time": 0, "passengers": 12, "chance": 100},
        note="役場。街が最初に建てる（住民 0 のとき）。3 階建て、屋上 13.2m、時計塔まで約 20m",
    ),
    "house_small": dict(
        name="pak256_house_small", draw=draw_house_small,
        dat={"type": "res", "level": 1, "chance": 100},
        note="小さな戸建て。2 階建て、棟高 8.6m",
    ),
    "house_wide": dict(
        name="pak256_house_wide", draw=draw_house_wide,
        dat={"type": "res", "level": 1, "chance": 100},
        note="やや大きな戸建て。2 階建て、棟高 9m",
    ),
    "row_house": dict(
        name="pak256_row_house", draw=draw_row_house,
        dat={"type": "res", "level": 2, "chance": 100},
        note="長屋・テラスハウス。3 階建て、棟高 11m",
    ),
    "apartment": dict(
        name="pak256_apartment", draw=draw_apartment,
        dat={"type": "res", "level": 3, "chance": 100},
        note="集合住宅。5 階建て 15m",
    ),
}


def table(key):
    b = BUILDINGS[key]
    lines = [
        "obj: building",
        f"name: {b['name']}",
        "copyright: pak256.LongScale チーム",
        f"# {b['note']}",
    ]
    for k, v in b["dat"].items():
        lines.append(f"{k}: {v}")
    lines += [
        "dims: 1,1,1",
        "intro_year: 1900",
        "backimage:        # backimage[配置][y][x][高さ][コマ]。絵は draw_buildings.py が描く",
        f"  0: {{0: {{0: {{0: {{0: {key}.0.0}}}}}}}}",
    ]
    return "\n".join(lines) + "\n"


def main():
    header = (
        "# 役場と住宅（絵は仮）。この表と PNG は draw_buildings.py が書き出す。直すときはスクリプトを直して流し直す。\n"
        "# 1 タイル = 26.4m の縮尺（docs/buildings.md）。\n"
    )
    for key, b in BUILDINGS.items():
        cv = Canvas()
        b["draw"](cv)
        cv.finish().save(os.path.join(HERE, f"{key}.png"))
        with open(os.path.join(HERE, f"{key}.yaml"), "w", encoding="utf-8", newline="\n") as f:
            f.write(header + table(key))


if __name__ == "__main__":
    main()
