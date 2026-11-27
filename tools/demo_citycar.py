"""初期マップ demo/demo.sve の街の車の値を、config/simuconf.tab に合わせる道具（docs/layout.md の「初期マップ」。#194）。MIT License。

保存データは citycar_level（交通量）と default_citycar_life（寿命）を自分で持ち、pak の simuconf.tab より優先される。
地図を作り直さず、展開した中身のこの 2 つの整数（各 4 バイト）だけを書き換えて、元と同じ圧縮の形で詰め直す。

場所（OTRP の fork の settings.cc の settings_t::rdwr。保存の版 0.122.0.64 で確かめた）:
  交通量: 版の行の直後から 8 つ目の 32bit の整数
  寿命:   街の道路の一覧の 5 バイト前からの 32bit の整数（間の 1 バイトは numbered_stations）

使い方:
    python -X utf8 tools/demo_citycar.py           # 今の値と simuconf.tab の値を表示する。違えば終了コード 1
    python -X utf8 tools/demo_citycar.py --write   # 違うときだけ demo.sve を書き換える
"""
import argparse
import bz2
import gzip
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_demo  # noqa: E402
import game  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "demo", "demo.sve")
SIMUCONF = os.path.join(ROOT, "config", "simuconf.tab")
KEYS = ("citycar_level", "default_citycar_life")
RANGES = {"citycar_level": (0, 16), "default_citycar_life": (0, 1200)}  # 本体の get_int_clamped の範囲


def wanted_values(simuconf=SIMUCONF):
    """simuconf.tab の 2 つの値。本体と同じく、同じキーは先の行を使う。"""
    values = {}
    with open(simuconf, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\s*(citycar_level|default_citycar_life)\s*=\s*(\d+)", line)
            if m:
                values.setdefault(m[1], int(m[2]))
    missing = [k for k in KEYS if k not in values]
    if missing:
        raise ValueError(f"simuconf.tab に指定が無い: {', '.join(missing)}")
    return values


def offsets(data):
    """展開した保存データの中の、2 つの値の位置。読める形でなければ ValueError。"""
    if not data.startswith(b"Simutrans 0.122."):
        raise ValueError(f"確かめた版（0.122）の保存データではない: {data[:40]!r}。settings.cc の rdwr で場所を確かめ直す")
    found = game.find_road_block(data)
    if len(found) != 1:
        raise ValueError(f"街の道路の一覧が {len(found)} か所")
    pos = {"citycar_level": data.index(b"\n") + 1 + 7 * 4, "default_citycar_life": found[0][0] - 5}
    if data[pos["default_citycar_life"] + 4] not in b"01":  # numbered_stations（真偽値は文字の 0・1）
        raise ValueError("寿命の後ろが想定の形でない")
    for key, at in pos.items():
        value = struct.unpack_from("<i", data, at)[0]
        low, high = RANGES[key]
        if not low <= value <= high:
            raise ValueError(f"{key} の位置の値が範囲の外: {value}")
    return pos


def read_values(data):
    return {key: struct.unpack_from("<i", data, at)[0] for key, at in offsets(data).items()}


def patch(data, values):
    """data の 2 つの値を values にした中身を返す。"""
    out = bytearray(data)
    for key, at in offsets(data).items():
        struct.pack_into("<i", out, at, values[key])
    return bytes(out)


def write_save(path, data):
    """data を、今の path と同じ圧縮の形（gzip・bzip2・無圧縮）で書く。"""
    with open(path, "rb") as f:
        head = f.read(3)
    if head.startswith(b"\x1f\x8b"):
        data = gzip.compress(data, mtime=0)
    elif head == b"BZh":
        data = bz2.compress(data)
    with open(path, "wb") as f:
        f.write(data)


def main(argv=None):
    ap = argparse.ArgumentParser(description="demo.sve の街の車の値を simuconf.tab に合わせる")
    ap.add_argument("--write", action="store_true", help="違うときに demo.sve を書き換える")
    args = ap.parse_args(argv)
    try:
        data = check_demo.read_save(DEMO)
        now, want = read_values(data), wanted_values()
        for key in KEYS:
            print(f"[demo_citycar] {key}: demo.sve {now[key]} / simuconf.tab {want[key]}")
        if now == want:
            return
        if not args.write:
            sys.exit("[demo_citycar] 値が違う（--write で書き換える）")
        write_save(DEMO, patch(data, want))
        print("[demo_citycar] demo.sve を書き換えた")
    except (OSError, ValueError, EOFError) as e:
        sys.exit(f"[demo_citycar] {e}")


if __name__ == "__main__":
    main()
