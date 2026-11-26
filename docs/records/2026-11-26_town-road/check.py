"""街の道路がどの way になるか（#147）を 2 通りで確かめる。MIT License。

使い方（リポジトリの直下から。先に tools/build.py で組む）:
    python -X utf8 docs/records/2026-11-26_town-road/check.py <検証環境> <ポート>
環境変数 MCP_CLIENT に OTRP 本体の mcp_client.py を渡す。検証環境には書かない（作業フォルダは work/ の下）。

- old : 保存データ flat_512_left_v64 をそのまま読む（保存された街の道路の名前は pak128 の物）
- new_names : 同じ保存データの写しの、街の道路の名前 3 つを ami_road_local に書き換えて読む
"""
import gzip
import os
import struct
import sys

sys.path.insert(0, "tools")
import game  # noqa: E402

SAVE = "flat_512_left_v64"
OLD_NAMES = ("CityRoad_030", "Road_040", "Road_050")

LIST_WAYS = ('local s=""; foreach(w in way_desc_x.get_available_ways(wt_road, st_flat)) '
             '{ s += w.get_name() + "=" + w.get_topspeed() + "; " }; return s')
COUNT = ('local c={}; local n=world.get_size(); for(local x=0;x<n.x;x++) for(local y=0;y<n.y;y++) {'
         ' local t=square_x(x,y).get_ground_tile(); local w=t.find_object(mo_way);'
         ' if(w && w.get_waytype()==wt_road){ local k=w.get_desc().get_name()+"/sidewalk="+w.has_sidewalk();'
         ' c[k] <- (k in c ? c[k] : 0)+1 } };'
         ' local s=""; foreach(k,v in c) s+=k+":"+v+"; "; return s')


def say(*a):
    print(*a, flush=True)


def bag(name):
    """本体の stringhash_t（先頭 16 文字の和）を hashtable_tpl の 101 個の入れ物に分けた番号。"""
    return sum(name.encode()[:16]) % 101


def rename_city_roads(path):
    """保存データ（gzip）の街の道路の名前を ami_road_local にする（名前は int16 の長さ + 文字）。"""
    data = gzip.open(path, "rb").read()
    new = b"ami_road_local"
    for name in OLD_NAMES:
        old = struct.pack("<h", len(name)) + name.encode()
        assert data.count(old) >= 1, name
        data = data.replace(old, struct.pack("<h", len(new)) + new, 1)
    with gzip.open(path, "wb") as f:
        f.write(data)


def lay_city_road(g, x, y):
    """(x, y) から東へ 5 タイル、街の道路の道具で敷いて、敷けた way を返す。"""
    r = g.city_road(x, y, x + 4, y)
    z = g.sq(f"return square_x({x + 2},{y}).get_ground_tile().z")
    got = g.sq(f'local w=square_x({x + 2},{y}).get_ground_tile().find_object(mo_way); '
               'return w ? w.get_desc().get_name() + "/sidewalk=" + w.has_sidewalk() : "no way"')
    return f"戻り値={r} z={z} way={got}"


def run(env, port, case):
    original_prepare = game.prepare_workdir
    if case == "new_names":
        def prepare(*a, **k):
            placed = original_prepare(*a, **k)
            rename_city_roads(os.path.join(a[1], "save", a[2] + ".sve"))
            return placed
        game.prepare_workdir = prepare
    try:
        with game.Game(env, SAVE, port, work=os.path.abspath(f"work/town147/{port}")) as g:
            size = g.sq("local n=world.get_size(); return n.x + \"x\" + n.y")
            say(case, "地図", size, "年", g.sq("return world.get_time().year"))
            ways = g.sq(LIST_WAYS)
            say(case, "道路の way", ways)
            say(case, "地図の道（敷く前）", g.sq(COUNT, timeout=120) or "なし")
            say(case, "街の道路の道具", lay_city_road(g, 100, 100))
            g.sq("return command_x(tool_add_city).work(player_x(1), coord3d(160,160,0))", player_nr=1)
            say(case, "街を置いた後の地図の道（上の 5 タイルを含む）", g.sq(COUNT, timeout=120))
        if g.left_over:
            sys.exit(1)
    finally:
        game.prepare_workdir = original_prepare


if __name__ == "__main__":
    env, port = sys.argv[1], int(sys.argv[2])
    cases = sys.argv[3:] or ["old", "new_names"]
    for name in ("ami_road_local", "ami_road_local_base_single"):
        say("入れ物の番号", name, bag(name))
    for case in cases:
        run(env, port, case)
