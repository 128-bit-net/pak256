"""保存データ（gzip）の設定にある街の道路・街どうしの道路の一覧を出す（#147）。MIT License。

使い方: python -X utf8 docs/records/2026-11-26_town-road/saved_roads.py <保存データ.sve> <街の道路の 1 つ目の名前>
本体の settings_t::rdwr の並び（数 int16 の後に、名前の長さ int16・名前・登場 int16・退役 int16）を、
1 つ目の名前の位置から読む（保存データの全体は解かない）。年は 月 / 12。
"""
import gzip
import struct
import sys


def main(path, first_name):
    data = gzip.open(path, "rb").read()
    print("先頭:", data.split(b"\n")[0].decode())
    pos = data.index(first_name.encode()) - 4  # 数(int16) と名前の長さ(int16) の分だけ戻る

    def short():
        nonlocal pos
        n = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        return n

    for label in ("city_road", "intercity_road"):
        for i in range(short()):
            n = short()
            name = data[pos:pos + n].decode()
            pos += n
            intro, retire = short(), short()
            print(f"{label}[{i}] {name} 登場 {intro / 12:.0f} 退役 {retire / 12:.0f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
