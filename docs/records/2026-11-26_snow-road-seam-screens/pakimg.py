"""AMI の道の pak の画像を読んで調べる（#141）。MIT License。
使い方（リポジトリの直下から）:
  python -X utf8 docs/records/2026-11-26_snow-road-seam-screens/pakimg.py count <ami_road.pak>
      道（obj=way）ごとに、雪の画像（子 6 が平ら、子 7 が坂）のうち「列のいちばん下の画素だけが暗い」列が 30 以上ある枚数を出す
  python -X utf8 docs/records/2026-11-26_snow-road-seam-screens/pakimg.py figure <ami_road.pak> <出力の PNG>
      雪の直線の画像（子 6 の 8 番）を ami_road_local と ami_road_local_base_single で並べる
  python -X utf8 docs/records/2026-11-26_snow-road-seam-screens/pakimg.py patch <build のフォルダ> <出力の build のフォルダ>
      確かめ用（直しではない）: ami_road.pak の写しで、雪の画像の下端の暗い画素をすぐ上の色に置き換える
      （数えるときより条件が広い。すぐ上が明るく、下端がそれより 40 を超えて暗い画素）
  python -X utf8 docs/records/2026-11-26_snow-road-seam-screens/pakimg.py diff <今の pak の撮影> <置き換えた pak の撮影>
      2 つの撮影で大きく違う画素を数える
子の番号は、読んだ pak の WAY の子の並び（0・1 が名前と著作者の文字、2 が夏の平ら、3 が夏の坂、6 が雪の平ら、7 が雪の坂と見ている）。"""
import os
import shutil
import struct
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFont


def load(path):
    buf = bytearray(open(path, "rb").read())

    def node(pos):
        kind = bytes(buf[pos:pos + 4]).decode("latin1").rstrip("\0")
        nch, size = struct.unpack_from("<HH", buf, pos + 4)
        pos += 8
        if size == 0xFFFF:
            size = struct.unpack_from("<I", buf, pos)[0]
            pos += 4
        start, pos = pos, pos + size
        kids = []
        for _ in range(nch):
            kid, pos = node(pos)
            kids.append(kid)
        return (kind, start, size, kids), pos

    root, _ = node(buf.index(0x1A) + 5)  # 説明の文（0x1A まで）と版（4 バイト）の後が根
    return buf, root


def ways(buf, root):
    for obj in root[3]:
        if obj[0] == "WAY":
            _, start, size, _ = obj[3][0]
            yield bytes(buf[start:start + size]).split(b"\0")[0].decode(), obj


def images(n, path=()):
    if n[0] == "IMG" and n[2] > 10:
        yield path, n
    for k, kid in enumerate(n[3]):
        yield from images(kid, path + (k,))


def pixels(buf, start):
    """IMG（版 3）を {(x, y): (15bit の色, buf の中の位置)} にする。"""
    x0, y0, _, ver, h = struct.unpack_from("<hhhBh", buf, start)
    assert ver == 3, ver
    i, pix = start + 10, {}

    def word():
        nonlocal i
        v = struct.unpack_from("<H", buf, i)[0]
        i += 2
        return v

    for row in range(h):
        x, clear = x0, word()
        while True:
            x += clear
            for _ in range(word() & 0x7FFF):
                at = i
                pix[(x, y0 + row)] = (word(), at)
                x += 1
            clear = word()
            if clear == 0:
                break
    return pix


def rgb(c):
    return ((c >> 10) & 31) << 3, ((c >> 5) & 31) << 3, (c & 31) << 3


def bottoms(pix):
    low = {}
    for x, y in pix:
        low[x] = max(y, low.get(x, y))
    return low


def dark_bottom_columns(pix):
    """列のいちばん下の画素が暗く（RGB の和 300 未満）、すぐ上が明るい（和 500 超）列の数。"""
    return sum(1 for x, y in bottoms(pix).items()
               if (x, y - 1) in pix and sum(rgb(pix[(x, y)][0])) < 300 and sum(rgb(pix[(x, y - 1)][0])) > 500)


def count(path):
    buf, root = load(path)
    for name, obj in ways(buf, root):
        res = {}
        for p, n in images(obj):
            if p[0] in (6, 7):
                res.setdefault(p[0], []).append(dark_bottom_columns(pixels(buf, n[1])))
        line = ", ".join(f"子 {k}: {sum(1 for c in v if c >= 30)}/{len(v)} 枚（最大 {max(v)} 列）" for k, v in sorted(res.items()))
        print(name, line)


def figure(path, out):
    buf, root = load(path)
    objs = dict(ways(buf, root))
    names = ("ami_road_local", "ami_road_local_base_single")
    box, s = (30, 195, 80, 235), 8
    font = ImageFont.truetype("C:/Windows/Fonts/meiryo.ttc", 18)
    sheet = Image.new("RGB", (512 * 2 + 16, 30 + 512 + 10 + (box[3] - box[1]) * s), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        n = dict(images(objs[name]))[(6, 8)]
        im = Image.new("RGB", (256, 256), (255, 0, 255))
        for xy, (c, _) in pixels(buf, n[1]).items():
            im.putpixel(xy, rgb(c))
        ox = i * (512 + 16)
        d.text((ox, 2), f"{name} の雪の画像（子 6 の 8 番）", fill=(0, 0, 0), font=font)
        big = im.resize((512, 512), Image.NEAREST)
        ImageDraw.Draw(big).rectangle([v * 2 for v in box], outline=(255, 0, 0), width=2)
        sheet.paste(big, (ox, 30))
        sheet.paste(im.crop(box).resize(((box[2] - box[0]) * s, (box[3] - box[1]) * s), Image.NEAREST), (ox, 552))
    sheet.save(out)


def patch(build, out):
    buf, root = load(os.path.join(build, "pak", "ami_road.pak"))
    done, changed = set(), 0
    for _, obj in ways(buf, root):
        for p, n in images(obj):
            if p[0] not in (6, 7) or n[1] in done:
                continue
            done.add(n[1])
            pix = pixels(buf, n[1])
            for x, y in bottoms(pix).items():
                if (x, y - 1) not in pix:
                    continue
                (a, at), b = pix[(x, y)], pix[(x, y - 1)][0]
                if a < 0x8000 and b < 0x8000 and sum(rgb(b)) > 500 and sum(rgb(b)) - sum(rgb(a)) > 40:
                    struct.pack_into("<H", buf, at, b)
                    changed += 1
    if os.path.exists(out):
        sys.exit(f"出力が既にある: {out}")
    shutil.copytree(os.path.join(build, "pak"), os.path.join(out, "pak"))
    with open(os.path.join(out, "pak", "ami_road.pak"), "wb") as f:
        f.write(buf)
    print("置き換えた画素", changed)


def diff(before, after):
    """2 つの撮影のフォルダで、明るさの差が 40 を超える画素を数える（1600x900 の撮影から、上の道具の帯と下の状態の行を除く）。"""
    for name in ("snow_flat", "snow_hill", "temperate_flat", "temperate_hill"):
        a, b = (Image.open(os.path.join(d, name + ".png")).convert("RGB").crop((0, 48, 1600, 878)) for d in (before, after))
        gray = ImageChops.difference(a, b).convert("L")
        print(name, sum(gray.histogram()[41:]))


if __name__ == "__main__":
    {"count": count, "figure": figure, "patch": patch, "diff": diff}[sys.argv[1]](*sys.argv[2:])
