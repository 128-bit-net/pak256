"""#189 の新しい物が出るツールバー（線路・路面電車・リニア・編集）と、名所の窓を開いて撮る。MIT License。
使い方（リポジトリの直下で）: python -X utf8 docs/records/2026-11-27_ami189-screens/toolbar.py <検証環境> <ポート> <build のフォルダ> <出力フォルダ>
上の帯の位置は 1600x900 の画面（48px のアイコン）。編集のツールバー（x=696）は、特別のサブメニュー（x=552）のプレイヤーの切り替え（左端）を押して
公共のプレーヤーにしてから開く。サブメニューの位置は起動ごとに違うので、gui.get_windows() の位置から求める。
名所の窓は dialog_tool[21] を開いて、盛土の建物が一覧に出るかを見る。"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
from game import Game  # noqa: E402

env, port, build, out = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4])
os.makedirs(out, exist_ok=True)
WINDOWS = ('local s=""; foreach (w in gui.get_windows()) { s += w.id + ":"; '
           'foreach (k, v in w) if (k != "id") s += k + "=" + (typeof v == "table" ? v.x + "/" + v.y + "/" + v.w + "/" + v.h : v) + ","; s += ";" } return s')


def shot(g, name):
    time.sleep(2)
    g.capture(os.path.join(out, name + ".png"))


with Game(env, "flat_512_left_v64", port, build=build) as g:
    for name, x in (("rail", 216), ("tram", 312), ("maglev", 504)):
        g.sq(f"gui.close_all_windows(); gui.click({x}, 24); return 1")
        shot(g, "toolbar_" + name)
    g.sq("gui.close_all_windows(); gui.open_dialog_tool(21); return 1", player_nr=1)
    shot(g, "curiosity")
    g.sq("gui.close_all_windows(); gui.click(552, 24); return 1")
    shot(g, "special")
    windows = g.sq(WINDOWS)
    print("windows:", windows, flush=True)
    bounds = [part.split("client_bounds=")[1].split(",")[0] for part in windows.split(";") if "client_bounds=" in part]
    x, y, w, h = (int(v) for v in bounds[-1].split("/"))
    g.sq(f"gui.click({x + 24}, {y + 24}); return 1")  # プレイヤーの切り替え
    time.sleep(2)
    g.sq("gui.close_all_windows(); gui.click(696, 24); return 1")
    shot(g, "toolbar_edit")
    if g.left_over:
        sys.exit(1)
