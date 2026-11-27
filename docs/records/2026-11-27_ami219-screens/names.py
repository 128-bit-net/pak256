"""AMI の物の名前の訳が日本語と英語で出ることを確かめる（#219）。MIT License。

使い方（リポジトリの直下で）:
    python -X utf8 docs/records/2026-11-27_ami219-screens/names.py <本体の検証環境> <MCP のポート> <配布の zip を展開した pak256/> <出力のフォルダ> <ja|en>
pak256/text/ の *.ami.tab の名前の全部を translate() で引き、訳が返ることを確かめる。道路の情報窓と名所の窓も撮る。
標識の情報窓は本体が「道路標識」とだけ出すので、標識の名前は translate() の結果（出力）で見る。
言語は起動の -lang を差し替える（game.py は ja に固定。検証環境の font/ には英語の選択に要る Prop-Latin1.bdf が無く、言語の窓では選べない）。
"""
import glob
import os
import sys
import time

sys.path.insert(0, os.path.abspath("tools"))
import game  # noqa: E402

env, port, pak_dir, out, lang = sys.argv[1], int(sys.argv[2]), os.path.abspath(sys.argv[3]), os.path.abspath(sys.argv[4]), sys.argv[5]
os.makedirs(out, exist_ok=True)
SIGNS = ("ami_sign_stop", "ami_sign_one_way", "ami_sign_speed_40", "ami_sign_speed_60", "ami_sign_speed_80", "ami_sign_min_50",
         "ami_sign_crosswalk", "ami_sign_crosswalk_one_way")

original = game.launch_command


def launch(*a, **k):
    cmd = original(*a, **k)
    cmd[cmd.index("-lang") + 1] = lang
    return cmd


game.launch_command = launch


def names_in_tabs():
    names = []
    for path in glob.glob(os.path.join(pak_dir, "text", "*.ami.tab")):
        if not os.path.basename(path).startswith(lang + "."):
            continue
        with open(path, encoding="utf-8") as f:
            lines = [ln for ln in f.read().split("\n")[1:] if ln]
        names += [(k, v) for k, v in zip(lines[::2], lines[1::2])]
    return names


pairs = names_in_tabs()
with game.Game(env, "flat_512_left_v64", port, pak_dir=pak_dir, simuconf_extra=["show_names = 0"]) as g:
    bad = []
    # 日本語の文字列は run_squirrel に渡すと化けるので、英字の名前だけを渡し、返りを Python で比べる
    for i in range(0, len(pairs), 40):
        chunk = pairs[i:i + 40]
        keys = ",".join(f'"{k}"' for k, _ in chunk)
        got = g.sq(f'local s = ""; foreach (k in [{keys}]) s += translate(k) + "|"; return s').split("|")[:-1]
        bad += [(k, v, r) for (k, v), r in zip(chunk, got) if r != v]
        if len(got) != len(chunk):
            bad.append(("(数)", len(chunk), len(got)))
    print(f"[names] {lang}: {len(pairs)} 件を translate() で引いた。訳と違う {len(bad)} 件", flush=True)
    for b in bad[:20]:
        print("   ", b, flush=True)
    for k in SIGNS:
        print(f"[names] {k} -> {g.sq(f'return translate({chr(34)}{k}{chr(34)})')}", flush=True)
    # 名前が画面に出る窓: 道路の情報窓と、盛土の建物を選ぶ名所の窓（公共のプレーヤー）
    g.road(40, 100, 44, 100, "ami_road_general")
    g.settle(5)
    g.sq("gui.close_all_windows(); gui.set_zoom(3); gui.jump(coord3d(42,100,0)); return 1")
    time.sleep(1)
    # 上の帯の問い合わせの道具（左から 3 つめ）を選んで、飛んだタイルの中心（game-check.md の「画面の中心」）を押す
    g.sq("gui.click(120, 24); return 1")
    time.sleep(1)
    g.sq("gui.click(896, 575); return 1")
    time.sleep(2)
    g.capture(os.path.join(out, f"{lang}_road_info.png"))
    g.sq("gui.close_all_windows(); gui.open_dialog_tool(21); return 1", player_nr=1)
    time.sleep(3)
    g.capture(os.path.join(out, f"{lang}_curiosity.png"))
if g.left_over:
    sys.exit(1)
