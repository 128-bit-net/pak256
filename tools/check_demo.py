"""初期マップ demo/demo.sve が使う物の名前が、組んだ pak にあるかを調べる（docs/layout.md の「初期マップ」）。MIT License。

保存データは物を名前で引くので、pak の物を消す・名前を変えると、demo.sve の地図でその物が欠ける。
ゲームを起動せず、保存データの中の pak256_・ami_ で始まる名前を、build/pak/ の物の一覧（makeobj list）と突き合わせる。

見ないもの: pak256_・ami_ で始まらない名前（貨物 Passagiere など）、名前のほかの中身の変わり（駅の大きさなど）。
大きく変えたときは、ゲームで demo.sve を読んで確かめる。

使い方（先に tools/build.py を AMI も入れて流す）:
    python -X utf8 tools/check_demo.py
"""
import bz2
import glob
import gzip
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "demo", "demo.sve")
PAK_OUT = os.path.join(ROOT, "build", "pak")
MAKEOBJ = os.environ.get("MAKEOBJ", "makeobj")
PREFIX = re.compile(rb"pak256_|ami_")
LIST_ROW = re.compile(r"^(\S+)\s+(\S.*?)\s+(\d+)\s+(\d+)\s*$")


def read_save(path):
    """保存データを展開して返す。gzip・bzip2・無圧縮だけ扱う。"""
    with open(path, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\x1f\x8b"):
        return gzip.decompress(raw)
    if raw.startswith(b"BZh"):
        return bz2.decompress(raw)
    if raw.startswith(b"Simutrans "):
        return raw
    raise ValueError("読めない圧縮の形（gzip・bzip2・無圧縮だけ扱う）。保存の圧縮の設定を確かめる")


def save_names(data):
    """保存データの中の pak256_・ami_ で始まる名前の集まり。

    本体は名前を「長さ（16bit）と中身」で書くので、頭の位置の 2 バイト前を長さとして読む。
    その形でない所に名前の頭があれば ValueError（読み落としを黙って通さないため）。
    """
    names, end = set(), 0
    for m in PREFIX.finditer(data):
        start = m.start()
        if start < end:  # 前の名前の中（例: pak256_ami_…）
            continue
        length = struct.unpack_from("<H", data, start - 2)[0] if start >= 2 else 0
        name = data[start:start + length]
        if not (len(m.group()) < length <= 255 and len(name) == length and all(0x20 < c < 0x7f for c in name)):
            raise ValueError(f"名前の形を読めない（位置 {start}: {data[start:start + 40]!r}）")
        names.add(name.decode("ascii"))
        end = start + length
    return names


def list_names(text):
    """makeobj list の出力から、物の名前の集まり。"""
    names, table = set(), False
    for line in text.splitlines():
        if line.startswith("----"):
            table = True
            continue
        m = table and LIST_ROW.match(line)
        if m:
            names.add(m[2])
    return names


def pak_names(pak_dir=PAK_OUT, makeobj=MAKEOBJ):
    paks = sorted(glob.glob(os.path.join(pak_dir, "*.pak")))
    if not paks:
        raise ValueError("build/pak/ に pak が無い（先に tools/build.py を流す）")
    names = set()
    for pak in paks:
        r = subprocess.run([makeobj, "list", pak], capture_output=True, text=True, errors="replace")
        # 物の名前の無い pak（ground.Outside.pak）もあるので、1 つずつの空は誤りにしない。表の見出しが出ないのは読めていない
        if r.returncode != 0 or "\n----" not in r.stdout:
            raise ValueError(f"makeobj list で物を読めない: {os.path.basename(pak)}")
        names |= list_names(r.stdout)
    return names


def main():
    try:
        used = save_names(read_save(DEMO))
        have = pak_names()
    except (OSError, ValueError, EOFError) as e:
        sys.exit(f"[check_demo] {e}")
    if not used:
        sys.exit("[check_demo] demo.sve に物の名前が見つからない")
    missing = sorted(used - have)
    if missing:
        sys.exit("[check_demo] demo.sve が使う物が build/pak/ に無い: " + ", ".join(missing)
                 + "\n    （--no-ami で組んでいないか確かめる。物を消した・名前を変えたのなら demo.sve を作り直す。docs/layout.md の「初期マップ」）")
    print(f"[check_demo] demo.sve が使う {len(used)} 個の名前は、全部 build/pak/ にある")


if __name__ == "__main__":
    main()
