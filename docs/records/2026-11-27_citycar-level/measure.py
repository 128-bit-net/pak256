"""街の車の台数とバスの走る距離を月ごとに測る（pak256#182）。MIT License。

    PAK256_GAME_ENV=<検証環境> python -X utf8 measure.py <citycar_level> <寿命> <ポート> <秒> <出力のフォルダ> [撮る月（例 24,72）]

環境変数 TOWN182 に保存データ（mksave.py の出力）を渡すと、同じ街から始める。渡さないと setup.nut で街を作る。
寿命は保存データの値を書き換える（settings.cc の rdwr で、numbered_stations の前の 4 バイト）。pak は先に tools/build.py で組む。
"""
import bz2, gzip, json, os, shutil, struct, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ENV = os.environ["PAK256_GAME_ENV"]  # 本体の検証環境（docs/game-check.md の --env）
sys.path.insert(0, os.path.join(ROOT, "tools"))
import game
from game import Game

HERE = os.path.dirname(os.path.abspath(__file__))
level, life, port, budget = [int(a) for a in sys.argv[1:5]]
out = sys.argv[5]
SHOTS = [int(a) for a in sys.argv[6].split(",")] if len(sys.argv) > 6 else [24, 60]
os.makedirs(out, exist_ok=True)
tag = f"L{level}_D{life}"
log = open(os.path.join(out, tag + ".jsonl"), "w", encoding="utf-8")


def emit(**kw):
    log.write(json.dumps(kw, ensure_ascii=False) + "\n")
    log.flush()
    print(json.dumps(kw, ensure_ascii=False), flush=True)


# 保存データの寿命（設定は保存データが持ち、pak の値より優先される）を書き換える
orig = game.rewrite_save_roads


TOWN = os.environ.get("TOWN182")


def patched(sve, simuconf):
    if TOWN:  # 同じ街の保存データ（mksave182.py）に差し替える
        shutil.copy(TOWN, sve)
        msg = None
    else:
        msg = orig(sve, simuconf)
    raw = open(sve, "rb").read()
    codec = bz2 if raw[:3] == b"BZh" else gzip
    data = codec.decompress(raw)
    found = game.find_road_block(data)
    assert len(found) == 1
    s = found[0][0]
    old = struct.unpack_from("<i", data, s - 5)[0]
    assert old == 120, old
    data = data[:s - 5] + struct.pack("<i", life) + data[s - 1:]
    open(sve, "wb").write(codec.compress(data))
    return msg


game.rewrite_save_roads = patched

COUNT = r"""
local res = "";
foreach (c in [[60,60,28],[160,160,60],[60,200,20]]) {
  local n = 0;
  for (local x = c[0] - c[2]; x <= c[0] + c[2]; x++) for (local y = c[1] - c[2]; y <= c[1] + c[2]; y++) {
    if (x < 0 || y < 0) continue;
    local sq = square_x(x, y);
    local t = sq.get_ground_tile();
    if (t == null) continue;
    foreach (o in t.get_objects()) if (o.get_type() == mo_city_car) n++;
  }
  res += n + " ";
}
return res;
"""
STATE = r"""
local s = "";
foreach (c in city_list_x()) {
  local p = c.get_pos();
  s += p.x + "," + p.y + ":" + c.get_citizens()[0] + ":" + c.get_citycars()[1] + " ";
}
local bus = "";
foreach (cnv in world.get_convoy_list()) bus += cnv.get_distance_traveled_total() + " ";
return s + "|" + world.get_citycars()[0] + "|" + bus;
"""

t0 = time.monotonic()
with Game(ENV, "flat_512_left_v64", port, simuconf_extra=["show_names = 0"]) as g:
    g.sq(f"settings.set_traffic_level({level}); return 1")
    time.sleep(1)
    msg = "town182" if TOWN else g.sq_file(os.path.join(HERE, "setup.nut"), timeout=200)
    time.sleep(1)
    emit(kind="setup", level=int(g.sq("return settings.get_traffic_level()")), life=life, msg=msg,
         convoys=int(g.sq("local n=0; foreach(c in world.get_convoy_list()) n++; return n")),
         citizens=g.sq('local s=""; foreach(c in city_list_x()) { local p=c.get_pos(); s+=p.x+","+p.y+":"+c.get_citizens()[0]+" "; } return s'))
    ym = lambda: int(g.sq("local t=world.get_time(); return t.year*12+t.month", timeout=120))
    g.sq("debug.set_game_speed(128); return 1")
    start = ym() + 1  # 式は前の月の人口を見るので 1 か月回してから数え始める
    spawned = {}
    last = ym()
    done_shots = set()
    prev_bus = None
    while time.monotonic() - t0 < budget:
        time.sleep(0.5)
        now = ym()
        if now == last:
            continue
        skipped = now - last - 1
        last = now
        k = now - start
        if k < 0:
            continue
        st = g.sq(STATE, timeout=120)
        towns, cars, bus = st.split("|")
        for item in towns.split():
            pos, cit, sp = item.split(":")
            if k >= 1:
                spawned[pos] = spawned.get(pos, 0) + int(sp)
        row = dict(kind="month", k=k, skipped=skipped, cars=int(cars), spawned=dict(spawned),
                   citizens={i.split(":")[0]: int(i.split(":")[1]) for i in towns.split()},
                   bus=[int(v) for v in bus.split()])
        checkpoint = k in (1, 6, 12, 24, 36, 48, 60, 72, 96, 120) or (k % 12 == 0)
        if checkpoint or k in SHOTS:
            g.sq("debug.set_game_speed(1); return 1")
            row["near"] = [int(v) for v in g.sq(COUNT, timeout=200).split()]
            if k in SHOTS and k not in done_shots:
                done_shots.add(k)
                for name, pos in (("big", (160, 160)), ("mid", (60, 60))):
                    g.sq(f"gui.close_all_windows(); gui.jump(coord3d({pos[0]},{pos[1]},0)); gui.set_zoom(3); return 1")
                    time.sleep(3)
                    g.capture(os.path.join(out, f"{tag}_m{k}_{name}.png"))
            g.sq("debug.set_game_speed(128); return 1")
        emit(**row)
        if k >= 120:
            break
    g.sq("debug.set_game_speed(1); return 1")
    emit(kind="end", seconds=time.monotonic() - t0, k=last - start)
