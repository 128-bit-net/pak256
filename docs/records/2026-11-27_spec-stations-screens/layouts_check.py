"""#206: 向きの絵の数（dims の 3 つめ）で、停留所を建てられる升が変わることを確かめる。MIT License。

リポジトリの直下で、先に tools/build.py を流してから:
    python -X utf8 docs/records/2026-11-27_spec-stations-screens/layouts_check.py <検証環境> <ポート>
pak256 の線路の駅の dat の dims を 2・4・8 にした仮の物を makeobj で組み、直線・行き止まり・曲がりの升に置く。
最後に dims の 3 つめを省いた物を置く（本体が止まることがある）。
"""
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port = sys.argv[1], int(sys.argv[2])
src = os.path.abspath("build/dat/station/rail_stops")
tmp = tempfile.mkdtemp()
text = open(os.path.join(src, "train_station.dat"), encoding="utf-8").read()
png = os.path.abspath("objects/station/rail_stops/train_station.png")
paks = []
for key, dims, count in (("l2", "1,1,2", 2), ("l4", "1,1,4", 4), ("l8", "1,1,8", 8), ("l1", "1,1", 1)):
    out = re.sub(r"^name=.*$", "name=check_%s" % key, text, flags=re.M)
    out = re.sub(r"^dims=.*$", "dims=%s" % dims, out, flags=re.M)
    out = "".join(ln for ln in out.splitlines(True)
                  if not (m := re.match(r"(back|front)image\[(\d+)\]", ln)) or int(m.group(2)) < count)
    with open(os.path.join(tmp, key + ".dat"), "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    with open(png, "rb") as a, open(os.path.join(tmp, "train_station.png"), "wb") as b:
        b.write(a.read())
    pak = os.path.join(tmp, "check_%s.pak" % key)
    r = subprocess.run(["makeobj", "pak256", pak, key + ".dat"], cwd=tmp, capture_output=True)
    log = (r.stdout + r.stderr).decode(errors="replace")
    print(key, r.returncode, [ln for ln in log.splitlines() if "warning" in ln.lower() or "error" in ln.lower()], flush=True)
    paks.append(pak)

SETUP = """
local pl = player_x(0); local w = "ami_rail_ballast";
command_x(tool_build_way).work(pl, coord3d(40,60,0), coord3d(60,60,0), w);
command_x(tool_build_way).work(pl, coord3d(60,60,0), coord3d(60,70,0), w);
return "ok"
"""
# (置く物, x, y, 場所の説明)
# 同じ升に重ねると「置き換え」の判定になるので、置ける物は別々の升を使う（行き止まりは (40,60) と (60,70)）
PLACES = [("check_l2", 50, 60, "直線の中ほど"), ("check_l4", 52, 60, "直線の中ほど"), ("check_l8", 54, 60, "直線の中ほど"),
          ("check_l4", 60, 70, "行き止まり"), ("check_l8", 40, 60, "行き止まり"),
          ("check_l2", 60, 60, "曲がり"), ("check_l4", 60, 60, "曲がり"), ("check_l8", 60, 60, "曲がり"),
          ("check_l2", 54, 60, "直線の同じ升に重ねる（容量が同じ）")]

with Game(env, "flat_512_left_v64", port, extra_paks=paks, work=os.path.abspath("work/shots206/_l"),
          simuconf_extra=["show_names = 0"]) as g:
    print(g.sq(SETUP), flush=True)
    for k, x, y, where in PLACES:
        e = g.sq(f'local e = command_x(tool_build_station).work(player_x(0), coord3d({x},{y},0), "{k}"); return e == null ? "置けた" : e')
        print(k, where, "置けた" if "u7f6e" in e or e == "置けた" else e, flush=True)
    try:
        print("l1 直線", g.sq('local e = command_x(tool_build_station).work(player_x(0), coord3d(45,60,0), "check_l1"); '
                            'return e == null ? "ok" : e', timeout=20), flush=True)
    except Exception as ex:  # 本体が止まる想定
        print("l1 直線: 本体が答えない:", str(ex)[:300], flush=True)
    print("fatal:", g.fatal(), flush=True)
