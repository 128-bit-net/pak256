"""同じ街に街の車を置き足しながら、バスの走る距離を測る（pak256#182）。MIT License。

    PAK256_GAME_ENV=<検証環境> python -X utf8 stress.py <ポート> <秒> <出力のフォルダ>
"""
import json, os, sys, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ENV = os.environ["PAK256_GAME_ENV"]  # 本体の検証環境（docs/game-check.md の --env）
sys.path.insert(0, os.path.join(ROOT, "tools"))
from game import Game

HERE = os.path.dirname(os.path.abspath(__file__))
port, budget, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
os.makedirs(out, exist_ok=True)
log = open(os.path.join(out, "stress.jsonl"), "w", encoding="utf-8")


def emit(**kw):
    log.write(json.dumps(kw, ensure_ascii=False) + "\n")
    log.flush()
    print(json.dumps(kw, ensure_ascii=False), flush=True)


# 街の範囲（中心 x,y, 半径）と道のタイル数
ROADS = r"""
local res = "";
foreach (c in [[60,60,28],[160,160,60]]) {
  local n = 0;
  for (local x = c[0] - c[2]; x <= c[0] + c[2]; x++) for (local y = c[1] - c[2]; y <= c[1] + c[2]; y++) {
    local t = square_x(x, y).get_ground_tile();
    if (t != null && t.has_way(wt_road)) n++;
  }
  res += n + " ";
}
return res;
"""
# 各街の道のタイルに、目標の台数まで街の車を置く（置けないタイルは飛ばす）
ADD = r"""
local pl = player_x(1);
local res = "";
foreach (c in [[60,60,28,TARGET],[160,160,60,TARGET]]) {
  local tiles = [], have = 0;
  for (local x = c[0] - c[2]; x <= c[0] + c[2]; x++) for (local y = c[1] - c[2]; y <= c[1] + c[2]; y++) {
    local t = square_x(x, y).get_ground_tile();
    if (t == null || !t.has_way(wt_road)) continue;
    local car = false;
    foreach (o in t.get_objects()) if (o.get_type() == mo_city_car) { car = true; have++; }
    if (!car) tiles.append(coord3d(x, y, 0));
  }
  local need = c[3] - have;
  local step = 7919;
  local n = tiles.len();
  for (local i = 0; i < n && need > 0; i++) {
    local p = tiles[(i * step) % n];
    if (command_x(tool_add_citycar).work(pl, p, "pak256_citycar_sedan") == null) need--;
  }
  res += have + "+" + (c[3] - have - need) + " ";
}
return res;
"""
COUNT = r"""
local res = "";
foreach (c in [[60,60,28],[160,160,60]]) {
  local n = 0;
  for (local x = c[0] - c[2]; x <= c[0] + c[2]; x++) for (local y = c[1] - c[2]; y <= c[1] + c[2]; y++) {
    local t = square_x(x, y).get_ground_tile();
    if (t != null) foreach (o in t.get_objects()) if (o.get_type() == mo_city_car) n++;
  }
  res += n + " ";
}
return res;
"""
BUS = 'local s=""; foreach (c in world.get_convoy_list()) s += c.get_distance_traveled_total() + " "; return s'

t0 = time.monotonic()
with Game(ENV, "flat_512_left_v64", port, simuconf_extra=["show_names = 0"]) as g:
    g.sq("settings.set_traffic_level(0); return 1")
    time.sleep(1)
    msg = g.sq_file(os.path.join(HERE, "setup.nut"), timeout=200)
    time.sleep(1)
    emit(kind="setup", level=g.sq("return settings.get_traffic_level()"), msg=msg, roads=g.sq(ROADS, timeout=200))
    ym = lambda: int(g.sq("local t=world.get_time(); return t.year*12+t.month", timeout=120))

    def run_months(n):
        g.sq("debug.set_game_speed(128); return 1")
        a = ym()
        while ym() == a:
            time.sleep(0.3)
        a = ym()
        d0 = [int(v) for v in g.sq(BUS).split()]
        while ym() < a + n:
            time.sleep(0.5)
        d1 = [int(v) for v in g.sq(BUS).split()]
        m = ym() - a
        g.sq("debug.set_game_speed(1); return 1")
        return m, [round((y - x) / m, 1) for x, y in zip(d0, d1)]

    run_months(2)
    for target in (0, 25, 50, 100, 200, 300):
        if time.monotonic() - t0 > budget:
            break
        added = g.sq(ADD.replace("TARGET", str(target)), timeout=200, player_nr=1) if target else "0"
        run_months(2)  # 置いた直後の詰まりが落ち着くのを待つ
        m, per = run_months(6)
        near = g.sq(COUNT, timeout=200)
        emit(kind="stress", target=target, added=added, near=near, months=m, bus_per_month=per)
        g.sq("gui.close_all_windows(); gui.jump(coord3d(160,160,0)); gui.set_zoom(3); return 1")
        time.sleep(3)
        g.capture(os.path.join(out, f"stress_{target}_big.png"))
    emit(kind="end", seconds=time.monotonic() - t0)
