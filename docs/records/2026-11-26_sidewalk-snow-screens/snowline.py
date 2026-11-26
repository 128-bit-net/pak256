"""雪線をまたいで坂を登る街の道路（#136。Sidewalk の番号 + 2 を引く所）を撮る。MIT License。
使い方（リポジトリの直下から）: python -X utf8 docs/records/2026-11-26_sidewalk-snow-screens/snowline.py <検証環境> <ポート> <build のフォルダ> <出力フォルダ>
温帯に 1 段ずつ登る尾根（高さ 0〜9）を作り、尾根の上に街の道路を敷いて、冬（1 月）に撮る。"""
import json
import os
import sys
import time

sys.path.insert(0, "tools")
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
os.makedirs(out, exist_ok=True)
X0, CY, H = 60, 180, 9
END = X0 + 2 * H + 3


def say(*a):
    print(*a, flush=True)


def sq_public(g, code, timeout=60):
    r = g._client("--player-nr", "1", "--run-squirrel", code, timeout=timeout)
    return str(json.loads(r.stdout.strip().splitlines()[-1])["result"])


def probe(g, x):
    return g.sq(f"local t=square_x({x},{CY}).get_ground_tile(); local w=t.find_object(mo_way); "
                f'return t.z + ":" + t.get_slope() + ":" + (w ? "" + w.has_sidewalk() : "no way")')


with Game(env, "flat_512_left_v64", port, work=out + "/_w", build=build, simuconf_extra=["show_names = 0"]) as g:
    for k in range(1, H + 1):
        say("raise", k, sq_public(g, f"for (local x={X0 + 2 * k}; x<={END}; x++) for (local y={CY - 1}; y<={CY + 2}; y++) "
                                     "command_x.grid_raise(player_x(1), coord3d(x,y,square_x(x,y).get_ground_tile().z)); return 1",
                                  timeout=120))
    say("climate", g.climate(X0 - 20, CY - 30, END + 20, CY + 30, "temperate", timeout=180))
    # 端から端を 1 回で敷くと経路が見つからないので、1 段ずつ敷く（平らなタイル X0 + 2k の高さが k）
    for k in range(H):
        a = X0 + 2 * k
        say("road", k, sq_public(g, f'return command_x(tool_build_cityroad).work(player_x(1), coord3d({a},{CY},{k}), '
                                    f'coord3d({a + 2},{CY},{k + 1}), "")'))
    say("probe", {x: probe(g, x) for x in range(X0 - 2, END)})
    g.wait_month(0)
    time.sleep(8)
    for z in range(2, H + 1, 1):
        x = X0 + 2 * z
        g.sq(f"gui.set_zoom(3); gui.close_all_windows(); gui.jump(coord3d({x},{CY},{z})); return 1")
        time.sleep(3)
        g.capture(os.path.join(out, f"line_z{z}.png"))
    say("month", g.month())
    if g.left_over:
        sys.exit(1)
