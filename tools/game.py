"""ゲームの起動と後片付けを 1 つにした道具（docs/game-check.md）。MIT License。

本体の検証環境を一時の作業フォルダに写し、手元で組んだ pak を入れ、MCP 付きで起動して、Squirrel を流す・画面を撮る・
起動した PID で閉じる・作業フォルダを消す、までを 1 回の呼び出しで行う。

コマンドから使う:
    python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47880 \
        --script course.nut --capture out/shot.png

    --env は環境変数 PAK256_GAME_ENV でも渡せる（個人の絶対パスはリポジトリに書かない）。
    --build を付けると、起動の前に tools/build.py を流す。無ければ build/pak/ の物を使う。
    --pak <フォルダ> を付けると、build/pak/ の代わりにそのフォルダの pak を使う（配布の zip を展開した pak256/ など。#170）。

開いたままのゲームへ命令を 1 つずつ流す（#85。docs/game-check.md の「開いたまま使う」）:
    python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47900 --interactive   # 起動して待つ（背景で動かす）
    python -X utf8 tools/game.py --port 47900 --send "return 1"            # Squirrel を流して結果を見る
    python -X utf8 tools/game.py --port 47900 --send "@capture out/a.png"  # 撮る（@dialog 名前・@settle 秒・@month 月・@quit も）
    python -X utf8 tools/game.py --port 47900 --player-nr 1 --send "return 1"  # 公共のプレーヤーで流す（#142）

別の道具（tools/vehicle_check/run.py など）から使う:
    from game import Game, prepare_workdir
    with Game(env, save, port) as g:
        g.sq("return 1")
        g.sq("return 1", player_nr=1)  # 公共のプレーヤーで流す（#142）
        g.city_road(40, 40, 48, 40)  # 歩道つきの街の道路（公共のプレーヤーで敷く）
        g.dialog("finances")   # 財務の窓（番号の表は DIALOGS・docs/game-check.md）
        g.settle(10)           # 建設中の絵が終わるまで進める
        g.climate(40, 40, 48, 48, "desert")  # 気候を塗る（地形を変えた後に）
        g.wait_month(0)        # 月を 1 月まで進める（0 始まり）
        g.capture("a.png")

決まり:
- 検証環境には書かない。写した作業フォルダ（既定は work/game/<ポート>/）だけを使う。
- settings.xml は写さない（本体が送信用の記録を持っていて、起動のたびに使用状況を外へ送るため）。
- config/simuconf.tab の末尾に day_night_shift = 0 を足して昼夜の切り替えを止める（夜の絵になって撮り直すのを防ぐ）。
  夜の灯りを見るときだけ --night。
- ほかの設定を足すときは Game(..., simuconf_extra=["show_names = 0"])（本体と pak の simuconf.tab の先頭に足す。#122）。
- 保存データの写しの街の道路・街どうしの道路の名前は、pak の config/simuconf.tab の指定に書き換える（新しい地図と同じ道路にする。#151）。
  保存された名前そのものを確かめるときは --keep-save-roads・Game(..., rewrite_roads=False)。
- 起動に -singleuser・-set_workdir・-lang ja・-objects・-load・-mcp-port を付ける。
- ゲームは起動したときの PID で閉じる（実行ファイルの名前では止めない）。閉じた後に tasklist で残りを確かめ、残ったら知らせる。
- MCP のポートは必ず明示する。範囲の既定は pak256 の作業者全体の範囲（PORT_MIN〜PORT_MAX = 47800〜47999）で、作業者ごとに進捗管理から割り当てられる範囲は、その中の一部。
  別の範囲を割り当てられた作業者は、--port-range・Game(port_range=…)・環境変数 PAK256_PORT_RANGE のどれかで範囲を渡す（"下限-上限"。#128）。
- この道具を動かす Python が強制終了されても、ゲームは閉じる（Windows の Job Object。KILL_ON_JOB_CLOSE。#59）。
- 本体が FATAL ERROR で止まると「PRESS ANY KEY」の画面のまま、起動の前の失敗では通知の窓（dr_fatal_notify）のまま残るので、
  起動のログ（game.log）を見て、どちらかの文が出ていたら待たずに閉じ、エラーの文を出して失敗する
  （GameFatalError。起動の待ち・Squirrel・撮影・settle・--interactive の見張り。#132・#142）。
- Squirrel は呼び出しの player_nr のプレーヤーで流れる（スクリプトの中の player_x(1) では変わらない）。公共は 1。
- Squirrel の文字列リテラルの中に改行を入れない（Python の通常の文字列のバックスラッシュ n が本物の改行になって、コンパイルが通らない）。入れたら流す前に止める。
- pak を入れる処理は install_pak（tools/install_local.py のテストプレイのフォルダへ入れる道具と共通。zip も渡せる。#38）。
"""
import argparse
import bz2
import ctypes
import glob
import gzip
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import time
import zipfile
import zlib

if os.name == "nt":
    from ctypes import wintypes

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import package  # noqa: E402

EXE = "sim-WinGDI64-OTRPv64.exe"
# 検証環境から写す物（フォルダ）。pak128 などの絵と addons/ は写さない。pak の側は install_pak で入れる
ENV_DIRS = ("config", "font", "themes", "text", "script", "music")
PAK_DIR = "pak"
DAY_NIGHT_OFF = "day_night_shift = 0"
MARK = ".game_py_workdir"  # この道具が作った作業フォルダの目印（他の物を rmtree しないため）
SCREENSIZE = "1600x900"
PORT_MIN, PORT_MAX = 47800, 47999  # MCP のポートの範囲の既定（pak256 の作業者全体の範囲。作業者ごとの割り当てはこの中）
PORT_RANGE_ENV = "PAK256_PORT_RANGE"  # 範囲を変える環境変数（"下限-上限"。別のリポジトリの作業者が使うとき。#128）
# gui.open_dialog_tool(番号) の窓の番号（OTRP 本体の simmenu.h の DIALOG_*。順に 0 から）。使う物だけ。docs/game-check.md に表
DIALOGS = {
    "help": 0, "options": 1, "minimap": 2, "lineoverview": 3, "messages": 4, "finances": 5, "players": 6,
    "displayoptions": 7, "sound": 8, "language": 9, "playercolor": 10, "jump": 11, "load": 12, "save": 13,
    "list_halt": 14, "list_convoi": 15, "list_town": 16, "list_goods": 17, "list_factory": 18, "list_curiosity": 19,
}
SETTLE_SPEED = 64  # 建設中の絵が終わるまで進めるときの速さ（本体の set_game_speed）
# 塗れる気候の番号（本体の climate）。0 は水で、塗ると地面が水になる・水の上を陸の気候で塗ると水位が下がるので、塗る手では扱わない
CLIMATES = {"desert": 1, "tropic": 2, "mediterran": 3, "temperate": 4, "tundra": 5, "rocky": 6, "arctic": 7}
# 本体の季節（0 夏・1 秋・2 冬・3 春。街の建物の絵 4 枚の添字と同じ）。添字は world.get_time().month（0 始まり）。
# OTRP の simworld.cc の recalc_season_snowline の month_to_season の写し
MONTH_TO_SEASON = (2, 2, 2, 3, 3, 0, 0, 0, 0, 1, 1, 2)
SEASON_MONTHS = {"summer": 6, "autumn": 9, "winter": 0, "spring": 3}  # 季節ごとの絵を撮るのに使う月（0 始まり）
MONTH_SPEED = 64  # 月を進めるときの速さ
# 本体が止まるときに出す文の印。"FATAL ERROR: …"（log.cc の fatal）と "FATAL ERROR during reading of …"（loadsave.cc）、
# FATAL ERROR を出さずに通知の窓で止まる "dr_fatal_notify: ERROR: …"（simsys.cc の dr_fatal_notify。pak やフォントが無いときなど。#142）
FATAL_MARKS = (b"FATAL ERROR", b"dr_fatal_notify: ERROR:")
PUBLIC_PLAYER = 1  # 公共のプレーヤーの player_nr（歩道つきの街の道路などはこのプレーヤーで敷く）
FATAL_CHARS = 1500  # エラーの文として持つ長さ（印から後ろ）
FATAL_FLUSH = 0.3  # 印を見つけてから、文の残りが書かれるのを待つ秒
FATAL_POLL = 0.5  # MCP の答えを待つ間に game.log を見る間隔（秒）
FATAL_SEND_WAIT = 2  # 致命の結果を .out に書いた後、送る側が読むのを待ってから閉じる秒


class GameFatalError(RuntimeError):
    """本体が FATAL ERROR で止まった。message は game.log の印から後ろ。"""

    def __init__(self, message):
        super().__init__(f"本体が FATAL ERROR・通知の窓で止まった:\n{message}")


def default_client():
    """OTRP 本体のリポジトリ（pak256 の本体の checkout の隣の simutrans/）の mcp_client.py。

    worktree（.claude/worktrees/<名前>/）の中から動かしても届くように、git の共有のディレクトリから辿る。
    """
    try:
        common = subprocess.run(["git", "-C", HERE, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                capture_output=True, text=True, check=True).stdout.strip()
        repo = os.path.dirname(common)
    except (OSError, subprocess.CalledProcessError):
        repo = ROOT
    return os.path.join(os.path.dirname(repo), "simutrans", ".agents", "skills", "simutrans-mcp-gui-debug",
                        "scripts", "mcp_client.py")


# --- 作業フォルダの用意（ゲームを使わない。検査できる） ---

def _is_runtime(rel):
    """配布の zip の pak256/ の中の相対パスのうち、ゲームが読む物（最上段の *.pak・demo.sve・config/・text/）か。"""
    return (rel.endswith(".pak") and "/" not in rel) or rel == package.DEMO or rel.split("/", 1)[0] in ("config", "text")


VERSION_FILE = "VERSION"  # install_local.py が書く版の名前のファイル（入れ替えのとき一緒に消す）


def clean_pak(dest):
    """dest の中の、入れる種類の物（最上段の *.pak・demo.sve・config/・text/・VERSION）だけを消す。下位のフォルダなどほかの物は残す。"""
    if not os.path.isdir(dest):
        return
    for name in os.listdir(dest):
        path = os.path.join(dest, name)
        if os.path.isfile(path) and (name.endswith(".pak") or name in (VERSION_FILE, package.DEMO)):
            os.remove(path)
        elif os.path.isdir(path) and name in ("config", "text"):
            shutil.rmtree(path)


def _zip_members(zip_path):
    """配布の zip（先頭のフォルダは pak256/）から、ゲームが読む物の (相対パス, 名前) を返す。危ない名前は止める。"""
    with zipfile.ZipFile(zip_path) as z:
        bad = z.testzip()  # 壊れたメンバーは、消す前に見つける
        if bad:
            raise RuntimeError(f"zip が壊れている: {bad}")
        names = [n for n in z.namelist() if not n.endswith("/")]
    out = []
    for n in names:
        if ".." in n.split("/") or n.startswith(("/", "\\")) or ":" in n or "\\" in n or any(c in n for c in '*?"<>|'):
            raise RuntimeError(f"zip の中の名前が危ない: {n}")
        parts = n.split("/")
        if parts[0] == package.TOP:
            parts = parts[1:]
        if not parts:
            continue
        rel = "/".join(parts)
        if _is_runtime(rel) and os.path.basename(rel) not in package.SKIP:
            out.append((rel, n))
    return out


def pak_dir_sources(pak_dir, root=ROOT):
    """pak のフォルダ pak_dir（--pak）から入れる (相対パス, 元のファイル) の一覧。入れられないときは RuntimeError。

    pak は pak_dir の直下の *.pak。pak_dir に config/ があれば（配布の zip を展開した pak256/ の形）、config/・text/・
    demo.sve も pak_dir の物を使う。無ければ（build/pak/ の形）root の物を使う。
    """
    if not os.path.isdir(pak_dir):
        raise RuntimeError(f"pak のフォルダが無い: {pak_dir}")
    paks = sorted(n for n in os.listdir(pak_dir) if n.endswith(".pak") and os.path.isfile(os.path.join(pak_dir, n)))
    if not paks:
        raise RuntimeError(f"pak のフォルダの直下に *.pak が無い: {pak_dir}")
    sources = [(n, os.path.join(pak_dir, n)) for n in paks]
    if os.path.isdir(os.path.join(pak_dir, "config")):
        if not os.path.isfile(os.path.join(pak_dir, "config", "simuconf.tab")):
            raise RuntimeError(f"pak のフォルダの config/ に simuconf.tab が無い: {pak_dir}")
        base, demo = pak_dir, os.path.join(pak_dir, package.DEMO)
    else:
        base, demo = root, os.path.join(root, "demo", package.DEMO)
    sources += [(arc.split("/", 1)[1], src) for arc, src in package.collect_settings(base)]
    if os.path.isfile(demo):
        sources.append((package.DEMO, demo))
    return sources


def add_pak_argument(ap):
    """ゲームを起動する道具に共通の --pak（Game(pak_dir=…) に渡す）。"""
    ap.add_argument("--pak", help="入れる pak のフォルダ（直下の *.pak。省くと build/pak/）。配布の zip を展開した pak256/ なら、"
                                  "その config/・text/・demo.sve を使う")


def install_pak(dest, root=ROOT, build=None, extra=(), zip_path=None, clean=False, pak_dir=None):
    """pak と config/・text/・demo.sve を dest（本体の pak のフォルダ）に入れる。

    dest の中身は配布の zip の pak256/ と同じ形（*.pak・config・text・demo.sve だけ。許諾の文は入れない）。
    zip_path があれば（root・build は使わない）、その zip（Release の物を含む配布の zip）から取る。無ければ手元で組んだ build/pak/ と config/・text/ から取る
    （配布用の許諾の検査は通さない。package.collect_runtime）。
    clean は、入れる前に dest の古い *.pak・demo.sve・config/・text/ を消す（テストプレイのフォルダの入れ替え。ほかの物は残す）。
    extra は、足りない物を別の pak から借りるときのファイル（試験のときだけ。コミットしない）。
    pak_dir があれば、build/pak/ の代わりにそのフォルダから取る（pak_dir_sources。zip_path とは一緒に渡せない）。
    ゲームの作業フォルダ（Game）も、テストプレイのフォルダに入れる道具（tools/install_local.py。#38）も、これで入れる。
    入れた相対パスの一覧を返す。
    """
    if zip_path and pak_dir is not None:
        raise ValueError("zip_path と pak_dir は一緒に渡せない")
    if zip_path:
        members = _zip_members(zip_path)
        if not any(rel.endswith(".pak") and "/" not in rel for rel, _ in members):
            raise RuntimeError(f"zip に pak が無い: {zip_path}")
    elif pak_dir is not None:
        members = None
        sources = pak_dir_sources(pak_dir, root)
    else:
        members = None
        build = build or os.path.join(root, "build")
        sources = [(arc.split("/", 1)[1], src) for arc, src in package.collect_runtime(root, build)]
    if clean:
        clean_pak(dest)
    placed = []
    if members is not None:
        with zipfile.ZipFile(zip_path) as z:
            for rel, name in members:
                out = os.path.join(dest, *rel.split("/"))
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with z.open(name) as fi, open(out, "wb") as fo:
                    shutil.copyfileobj(fi, fo)
                placed.append(rel)
    else:
        for rel, src in sources:
            out = os.path.join(dest, *rel.split("/"))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            shutil.copyfile(src, out)
            placed.append(rel)
    for src in extra:
        if not os.path.isfile(src):
            raise RuntimeError(f"借りる pak が無い: {src}")
        shutil.copyfile(src, os.path.join(dest, os.path.basename(src)))
        placed.append(os.path.basename(src))
    return placed


def append_day_night_off(simuconf):
    """simuconf.tab の末尾に day_night_shift = 0 を足す（無ければファイルを作る。既に足してあれば何もしない）。"""
    text = ""
    if os.path.isfile(simuconf):
        with open(simuconf, encoding="utf-8", newline="") as f:
            text = f.read()
    if any(line.strip() == DAY_NIGHT_OFF for line in text.splitlines()):
        return
    nl = "\r\n" if "\r\n" in text else "\n"
    if text and not text.endswith("\n"):
        text += nl
    os.makedirs(os.path.dirname(simuconf), exist_ok=True)
    with open(simuconf, "w", encoding="utf-8", newline="") as f:
        f.write(text + nl + DAY_NIGHT_OFF + nl)


def check_simuconf_lines(lines):
    """simuconf_extra が「キー = 値」の行の並びであることを確かめて、一覧にして返す。"""
    if isinstance(lines, str):
        raise ValueError(f"simuconf_extra は行の一覧で渡す（文字列 1 つではなく）: {lines!r}")
    lines = list(lines)
    for line in lines:
        s = line.strip() if isinstance(line, str) else ""
        if not s or "\n" in line or "\r" in line or s.startswith(("#", "-", "=")) or "=" not in s:
            raise ValueError(f"simuconf_extra の行は「キー = 値」の 1 行にする: {line!r}")
    return lines


def prepend_lines(simuconf, lines):
    """simuconf.tab の先頭に行を足す（無ければファイルを作る）。

    本体は 1 つのファイルの中の同じキーを先に書いた行から取る（tabfile.cc の tabfileobj_t::put）ので、
    末尾でなく先頭に足して、ファイルに元からある行より足した行を効かせる。
    """
    if not lines:
        return
    text = ""
    if os.path.isfile(simuconf):
        with open(simuconf, encoding="utf-8", newline="") as f:
            text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    os.makedirs(os.path.dirname(simuconf), exist_ok=True)
    with open(simuconf, "w", encoding="utf-8", newline="") as f:
        f.write("".join(line + nl for line in lines) + text)


# --- 保存データの写しの道路名（#151） ---
# 保存データは、街の道路・街どうしの道路の名前の一覧を自分で持つ（本体の settings_t::rdwr）。pak128 で作った地図を
# pak256 で読むと、名前の道路が無くて本体が代わりを選ぶので、新しい地図と違う絵になる（#147）。写しの一覧を pak の指定にする。
# 一覧の並び: 街の道路の数、(名前の長さ・名前・登場の月・退役の月) の繰り返し、街どうしの道路の数、同じ繰り返し。数はどれも 16bit。

ROAD_KEYS = ("city_road", "intercity_road")
ROAD_SEARCH = 16384  # 一覧を探す先頭の長さ（設定は保存データの初めの方にある）


def road_settings(simuconf):
    """simuconf.tab の city_road[n]・intercity_road[n] を {キー: [(名前, 登場の月, 退役の月), …]} で返す。

    本体の読み方に合わせる（settings_t::parse_simuconf）: [0] の行があるキーだけ、同じキーは先の行、年は 12 倍、
    省いた年は 0（本体が道路自身の年に置き換える）。
    """
    values = {}
    if os.path.isfile(simuconf):
        with open(simuconf, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = re.match(r"\s*((?:intercity|city)_road)\[(\d)\]\s*=(.*)", line)
                if m:
                    values.setdefault((m[1], int(m[2])), m[3].strip())

    def months(text):
        m = re.match(r"\s*(\d+)", text)
        return int(m[1]) * 12 if m else 0

    out = {}
    for key in ROAD_KEYS:
        if not values.get((key, 0)):
            continue
        roads = []
        for i in range(10):
            parts = values.get((key, i), "").split(",")
            if parts[0]:
                roads.append((parts[0].strip(), months("".join(parts[1:2])), months("".join(parts[2:3]))))
        out[key] = roads
    return out


def _parse_roads(data, pos):
    """data の pos から道路の一覧 1 つ（数と項目）を読んで ([(名前, 登場, 退役)], 次の位置) を返す。一覧の形でなければ None。"""
    if pos + 2 > len(data):
        return None
    count = struct.unpack_from("<H", data, pos)[0]
    pos += 2
    if not 1 <= count <= 9:  # 本体は 10 以上を FATAL にする
        return None
    roads = []
    for _ in range(count):
        if pos + 2 > len(data):
            return None
        n = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        if not 3 <= n <= 255 or pos + n + 4 > len(data):
            return None
        name = data[pos:pos + n]
        if any(c < 0x20 or c == 0x7f for c in name):
            return None
        try:
            name = name.decode("utf-8")
        except UnicodeDecodeError:
            return None
        intro, retire = struct.unpack_from("<HH", data, pos + n)
        if retire and intro > retire:
            return None
        roads.append((name, intro, retire))
        pos += n + 4
    return roads, pos


def find_road_block(data):
    """保存データ（展開した中身）の中の道路の 2 つの一覧を探し、(始まり, 終わり, {キー: 一覧}) の一覧を返す。"""
    found = []
    for start in range(min(len(data), ROAD_SEARCH)):
        city = _parse_roads(data, start)
        inter = city and _parse_roads(data, city[1])
        if inter:
            found.append((start, inter[1], {"city_road": city[0], "intercity_road": inter[0]}))
    return found


def _pack_roads(roads):
    out = struct.pack("<H", len(roads))
    for name, intro, retire in roads:
        raw = name.encode("utf-8")
        out += struct.pack("<H", len(raw)) + raw + struct.pack("<HH", intro, retire)
    return out


def rewrite_save_roads(sve, simuconf):
    """保存データ sve（作業フォルダの写し）の道路の一覧を、simuconf の指定に書き換える。結果の説明を返す。

    simuconf に指定の無い方の一覧は残す。指定が無い・同じ中身なら何もせず None。
    読めない形（zstd など）・一覧が見つからない・2 か所以上に見えるときは、ファイルに触らずに理由を返す。
    """
    wanted = road_settings(simuconf)
    if not wanted:
        return None
    with open(sve, "rb") as f:
        raw = f.read()
    if raw.startswith(b"\x1f\x8b"):
        codec = gzip
    elif raw.startswith(b"BZh"):
        codec = bz2
    elif raw.startswith(b"Simutrans "):
        codec = None
    else:
        return "保存データの道路名は書き換えていない（読めない圧縮の形。gzip・bzip2・無圧縮だけ扱う）"
    try:
        data = codec.decompress(raw) if codec else raw
    except (OSError, EOFError, ValueError, zlib.error) as e:
        return f"保存データの道路名は書き換えていない（展開できない: {e}）"
    if any(len(roads) > 9 for roads in wanted.values()):
        return "保存データの道路名は書き換えていない（指定が 10 本以上。本体は読み込みで止まる）"
    found = find_road_block(data)
    if len(found) != 1:
        return f"保存データの道路名は書き換えていない（道路の一覧が {len(found)} か所）"
    start, end, old = found[0]
    new = {key: wanted.get(key, old[key]) for key in ROAD_KEYS}
    if new == old:
        return None
    data = data[:start] + b"".join(_pack_roads(new[key]) for key in ROAD_KEYS) + data[end:]
    with open(sve, "wb") as f:
        f.write(codec.compress(data) if codec else data)

    def names(roads):
        return " / ".join(f"{k}: {', '.join(r[0] for r in roads[k])}" for k in ROAD_KEYS)

    return f"保存データの写しの道路名を書き換えた（{names(old)} → {names(new)}）"


def prepare_workdir(env, work, save, exe=EXE, night=False, extra_paks=(), root=ROOT, build=None, simuconf_extra=(),
                    rewrite_roads=True, pak_dir=None):
    """検証環境 env の一部を作業フォルダ work に写し、pak と保存データを入れる。work が既にあれば作り直す。

    写す物: 実行ファイル・DLL・ENV_DIRS（settings.xml は写さない）・指定の保存データ 1 つ。pak は work/pak/ に install_pak で入れる。
    simuconf_extra は、本体と pak の config/simuconf.tab の両方に足す行の一覧（例: ["show_names = 0"]。night でも足す）。
    rewrite_roads なら、保存データの写しの街の道路・街どうしの道路の名前を pak の config/simuconf.tab の指定にする（#151）。
    pak_dir は、build/pak/ の代わりに入れる pak のフォルダ（pak_dir_sources）。
    """
    simuconf_extra = check_simuconf_lines(simuconf_extra)  # 作業フォルダを消す前に止める
    if not os.path.isfile(os.path.join(env, exe)):
        raise RuntimeError(f"検証環境に {exe} が無い: {env}")
    sve = os.path.join(env, "save", save + ".sve")
    if not os.path.isfile(sve):
        raise RuntimeError(f"保存データが無い: {sve}")
    if pak_dir is not None:  # 作業フォルダを消す前に止める（空文字も止める。黙って build/pak/ にしない）
        pak_dir_sources(pak_dir, root)
        p, w = (os.path.normcase(os.path.realpath(d)) for d in (pak_dir, work))
        if p == w or p.startswith(w + os.sep):
            raise RuntimeError(f"pak のフォルダが作業フォルダの中にある（作り直すと消える）: {pak_dir}")
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(os.path.join(work, "save"))
    with open(os.path.join(work, MARK), "w", encoding="utf-8") as f:
        f.write("tools/game.py\n")
    shutil.copyfile(os.path.join(env, exe), os.path.join(work, exe))
    for dll in glob.glob(os.path.join(env, "*.dll")):
        shutil.copyfile(dll, os.path.join(work, os.path.basename(dll)))
    for d in ENV_DIRS:
        if os.path.isdir(os.path.join(env, d)):
            shutil.copytree(os.path.join(env, d), os.path.join(work, d))
    shutil.copyfile(sve, os.path.join(work, "save", save + ".sve"))
    placed = install_pak(os.path.join(work, PAK_DIR), root, build, extra_paks, pak_dir=pak_dir)
    # 本体の config/ と pak の config/ の両方に足す（pak の物が後に読まれる）
    for simuconf in (os.path.join(work, "config", "simuconf.tab"), os.path.join(work, PAK_DIR, "config", "simuconf.tab")):
        if not night:
            append_day_night_off(simuconf)
        prepend_lines(simuconf, simuconf_extra)
    if rewrite_roads:
        message = rewrite_save_roads(os.path.join(work, "save", save + ".sve"),
                                     os.path.join(work, PAK_DIR, "config", "simuconf.tab"))
        if message:
            print(f"[game] {message}", flush=True)
    return placed


def launch_command(work, save, port, exe=EXE, screensize=SCREENSIZE):
    """起動のコマンド。-singleuser が無いと本体が作業フォルダでなく別の場所を見る。-lang ja が無いと言語選びの画面で止まる。"""
    return [os.path.join(work, exe), "-singleuser", "-set_workdir", work, "-objects", PAK_DIR + "/",
            "-load", save, "-freeplay", "-mute", "-lang", "ja", "-mcp-port", str(port), "-screensize", screensize]


def resolve_port_range(port_range=None):
    """MCP のポートの範囲 (下限, 上限) を決める。引数（組か "下限-上限"）、環境変数 PORT_RANGE_ENV、PORT_MIN〜PORT_MAX の順。"""
    where = "port_range"
    if port_range is None:
        where, port_range = PORT_RANGE_ENV, os.environ.get(PORT_RANGE_ENV) or (PORT_MIN, PORT_MAX)
    try:
        parts = port_range.split("-") if isinstance(port_range, str) else port_range
        lo, hi = (int(str(p)) for p in parts)
    except (TypeError, ValueError):
        raise RuntimeError(f"{where} は「下限-上限」（例 47200-47299）で渡す: {port_range!r}") from None
    if not 1 <= lo <= hi <= 65535:
        raise RuntimeError(f"{where} の範囲が正しくない（1 ≦ 下限 ≦ 上限 ≦ 65535）: {port_range!r}")
    return lo, hi


def check_port(port, port_range=None):
    lo, hi = resolve_port_range(port_range)
    if not lo <= port <= hi:
        raise RuntimeError(f"MCP のポートは {lo}〜{hi} の中で明示する（範囲は --port-range か環境変数 {PORT_RANGE_ENV} で変えられる）: {port}")


def port_in_use(port):
    """そのポートに誰かがつながるか（他のゲームが使っている）。"""
    for host in ("127.0.0.1", "::1"):
        fam = socket.AF_INET6 if ":" in host else socket.AF_INET
        try:
            with socket.socket(fam, socket.SOCK_STREAM) as sk:
                sk.settimeout(1)
                if sk.connect_ex((host, port)) == 0:
                    return True
        except OSError:  # IPv6 が使えない環境
            continue
    return False


def check_work(work, env, root):
    """作業フォルダが、検証環境・その中・その親・リポジトリそのものでないこと。空でなければ、この道具の物（目印あり）であること（rmtree で消すため）。"""
    w = os.path.normcase(os.path.realpath(work))
    e = os.path.normcase(os.path.realpath(env))
    r = os.path.normcase(os.path.realpath(root))
    if w == r or w == e or e.startswith(w + os.sep) or r.startswith(w + os.sep) or w.startswith(e + os.sep):
        raise RuntimeError(f"作業フォルダが検証環境かリポジトリと重なる: {work}")
    if os.path.exists(work) and os.listdir(work) and not os.path.isfile(os.path.join(work, MARK)):
        raise RuntimeError(f"作業フォルダが空でなく、この道具の物でもない: {work}")


def check_squirrel(code):
    """Squirrel の文字列リテラル（"…"）の中に改行があれば、流す前に止める（#59）。

    Python の "\\n" は本物の改行になり、本体の run_squirrel でコンパイルが通らない（"…" の中の改行は Squirrel の誤り）。
    文字列の外の改行（複数行のコード・// # /* */ の注釈・'"' の文字リテラル）は構わない。@"…" の逐語の文字列は改行を許すので見ない。
    """
    i, n, line = 0, len(code), 1
    while i < n:
        c = code[i]
        if c == "\n":
            line += 1
        elif code.startswith("//", i) or c == "#":
            while i < n and code[i] != "\n":
                i += 1
            continue
        elif code.startswith("/*", i):
            end = code.find("*/", i + 2)
            end = n if end < 0 else end + 2
            line += code.count("\n", i, end)
            i = end
            continue
        elif code.startswith('@"', i):  # 逐語の文字列。"" で引用符、改行は可
            i += 2
            while i < n:
                if code[i] == '"':
                    if code.startswith('""', i):
                        i += 2
                        continue
                    break
                line += code[i] == "\n"
                i += 1
        elif c == "'":  # 文字リテラル（'"' など）。1 文字か、エスケープ 1 つ
            i += 3 if code[i + 1:i + 2] != "\\" else 4
            continue
        elif c == '"':
            start = line
            i += 1
            while i < n and code[i] != '"':
                if code[i] == "\\":
                    i += 1
                elif code[i] in "\r\n":
                    raise ValueError(
                        f"Squirrel の文字列の中に改行がある（{start} 行目の文字列）。Python の通常の文字列に \\n と書くと本物の改行になる。"
                        "区切りに改行を使わないか、raw 文字列で渡す")
                i += 1
        i += 1


def check_player_nr(player_nr):
    """本体の player_nr（0〜15 の整数）であることを確かめる。"""
    if not isinstance(player_nr, int) or isinstance(player_nr, bool) or not 0 <= player_nr <= 15:
        raise ValueError(f"player_nr は 0〜15 の整数で渡す（公共は {PUBLIC_PLAYER}）: {player_nr!r}")
    return player_nr


def alive(pid):
    """tasklist で PID のプロセスが残っているか。"""
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True)
    return f'"{pid}"' in out.stdout.decode("utf-8", errors="replace")  # 日本語の Windows は cp932 で出す。PID の数字だけ見る


class JobObject:
    """親が終わったら子も終わらせる Windows の Job Object（JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE。#59）。

    この道具を動かす Python を TaskStop などで強制終了すると、with を抜けず、ゲームが閉じられずにポートを握ったまま残った（#30）。
    ゲームのプロセスをこの Job に入れておくと、Python が終わってハンドルが閉じた時に、OS がゲームも終わらせる。
    Windows 以外では何もしない（assign は False を返す）。
    """

    KILL_ON_JOB_CLOSE = 0x2000
    EXTENDED_LIMIT_INFORMATION = 9  # JobObjectExtendedLimitInformation

    def __init__(self):
        self.handle = None
        if os.name != "nt":
            return
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.k32 = k32

        class BasicLimits(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

        class IoCounters(ctypes.Structure):
            _fields_ = [(n, ctypes.c_uint64) for n in ("ReadOps", "WriteOps", "OtherOps", "ReadBytes", "WriteBytes", "OtherBytes")]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("Basic", BasicLimits), ("Io", IoCounters), ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        handle = k32.CreateJobObjectW(None, None)
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        info = ExtendedLimits()
        info.Basic.LimitFlags = self.KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(handle, self.EXTENDED_LIMIT_INFORMATION, ctypes.byref(info), ctypes.sizeof(info)):
            err = ctypes.get_last_error()
            k32.CloseHandle(handle)
            raise ctypes.WinError(err)
        self.handle = handle

    def assign(self, proc):
        """subprocess.Popen のプロセスを Job に入れる。入れられたら True（既に別の Job にいて入れられないときは False）。"""
        if self.handle is None:
            return False
        return bool(self.k32.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(proc._handle))))

    def close(self):
        """ハンドルを閉じる。Job に残っているプロセスは OS が終わらせる。"""
        if self.handle is not None:
            self.k32.CloseHandle(self.handle)
            self.handle = None


# --- ゲームの起動と操作 ---

class Game:
    """作業フォルダを用意して本体を起動し、MCP で操作し、with を抜けるときに PID で閉じて作業フォルダを消す。"""

    def __init__(self, env, save, port, work=None, night=False, extra_paks=(), client=None, exe=EXE,
                 screensize=SCREENSIZE, keep=False, root=ROOT, build=None, simuconf_extra=(), port_range=None,
                 rewrite_roads=True, pak_dir=None):
        check_port(port, port_range)
        self.pak_dir = os.path.abspath(pak_dir) if pak_dir else pak_dir  # 空文字は abspath しない（今の場所になる）
        self.rewrite_roads = rewrite_roads
        self.simuconf_extra = check_simuconf_lines(simuconf_extra)
        self.env, self.save, self.port = os.path.abspath(env), save, port
        self.work = os.path.abspath(work or os.path.join(root, "work", "game", str(port)))
        self.night, self.extra_paks, self.exe, self.screensize = night, extra_paks, exe, screensize
        self.client = client or os.environ.get("MCP_CLIENT") or default_client()
        self.keep, self.root, self.build = keep, root, build
        self.proc = None
        self.job = None  # 親が強制終了されてもゲームを閉じる Job Object（Windows）
        self.prepared = False  # この Game が作業フォルダを用意した（他人の物を消さない）
        self.left_over = False  # 閉じた後も PID が残ったか
        self.fatal_message = None  # 見つけた FATAL ERROR の文
        self._log_pos = 0  # game.log を見終えた位置

    def __enter__(self):
        try:
            self.start()
        except BaseException:  # 起動の途中の失敗・Ctrl+C でも、起動した物を閉じて片付ける（with は __enter__ の失敗で __exit__ を呼ばない）
            self.stop()
            raise
        return self

    def __exit__(self, *exc):
        self.stop()

    def start(self, limit=120):
        if not os.path.isfile(self.client):
            raise RuntimeError(f"MCP のクライアントが無い: {self.client}（--mcp-client か環境変数 MCP_CLIENT で渡す）")
        if port_in_use(self.port) or self.alive_mcp():
            raise RuntimeError(f"ポート {self.port} は他で使われている（他のゲームが動いている）")
        self.fatal_message, self._log_pos = None, 0
        check_work(self.work, self.env, self.root)
        self.prepared = True
        prepare_workdir(self.env, self.work, self.save, self.exe, self.night, self.extra_paks, self.root, self.build,
                        simuconf_extra=self.simuconf_extra, rewrite_roads=self.rewrite_roads, pak_dir=self.pak_dir)
        cmd = launch_command(self.work, self.save, self.port, self.exe, self.screensize)
        with open(os.path.join(self.work, "game.log"), "wb") as log:
            try:
                self.job = JobObject()
            except OSError as e:  # 保険の仕組みの失敗で起動を止めない
                self.job = None
                print(f"[game] Job Object を作れなかった（{e}）。この Python を強制終了するとゲームが残る", flush=True)
            self.proc = subprocess.Popen(cmd, cwd=self.work, stdout=log, stderr=subprocess.STDOUT)
        if self.job is not None and not self.job.assign(self.proc):
            print("[game] Job Object に入れられなかった（この Python を強制終了するとゲームが残る）", flush=True)
        print(f"[game] pid={self.proc.pid} port={self.port} work={self.work}", flush=True)
        end, last = time.monotonic() + limit, None
        while time.monotonic() < end:
            self.check_fatal()
            if self.proc.poll() is not None:
                self.check_fatal()  # 見た後に書いて終わった場合
                raise RuntimeError(f"ゲームが終わった（終了コード {self.proc.returncode}）。ログの末尾: {self.log_tail()}")
            try:
                if self.sq("return 1", timeout=5) == "1":
                    return
            except GameFatalError:
                raise
            except Exception as e:  # 起動中は答えない
                last = e
            time.sleep(3)
        self.check_fatal()
        raise RuntimeError(f"ゲームが MCP に答えない: {last}。ログの末尾: {self.log_tail()}")

    def log_tail(self, n=600):
        """起動のログ（game.log）の末尾。作業フォルダは失敗の後に消えるので、メッセージに入れて残す。"""
        try:
            with open(os.path.join(self.work, "game.log"), "rb") as f:
                return f.read()[-n:].decode("utf-8", errors="replace").strip() or "（空）"
        except OSError:
            return "（無し）"

    def fatal(self):
        """game.log に FATAL_MARKS のどれかが出ていれば、その文を返す（無ければ None）。起動していないときは見ない。

        前に見た所から先だけを読む（-log -debug 3 を足すとログが大きい）。一度見つけたら覚えておく。
        """
        if self.fatal_message is not None or self.proc is None:
            return self.fatal_message
        path = os.path.join(self.work, "game.log")
        try:
            with open(path, "rb") as f:
                f.seek(self._log_pos)
                data = f.read()
            i = min((n for n in (data.find(m) for m in FATAL_MARKS) if n >= 0), default=-1)  # 先に出た印
            if i < 0:  # 印が読みの境目で割れないよう、少し手前から次を読む
                self._log_pos += max(0, len(data) - max(map(len, FATAL_MARKS)) + 1)
                return None
            time.sleep(FATAL_FLUSH)
            with open(path, "rb") as f:
                f.seek(self._log_pos + i)
                data = f.read(FATAL_CHARS)
        except OSError:
            return None
        self.fatal_message = data.decode("utf-8", errors="replace").strip()
        return self.fatal_message

    def check_fatal(self):
        """本体が FATAL ERROR・通知の窓で止まっていたら GameFatalError。"""
        message = self.fatal()
        if message is not None:
            raise GameFatalError(message)

    def alive_mcp(self):
        try:
            return self.sq("return 1", timeout=3) == "1"
        except Exception:
            return False

    def _client(self, *args, timeout):
        """MCP のクライアントを流す。止まった本体は答えないので、待つ間も game.log を見て、FATAL ERROR ならすぐ失敗する。"""
        self.check_fatal()
        cmd = [sys.executable, "-X", "utf8", "-I", self.client, "--port", str(self.port), *args, "--timeout", str(timeout)]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        end = time.monotonic() + timeout + 10
        try:
            while True:
                try:
                    out, err = p.communicate(timeout=FATAL_POLL)
                    break
                except subprocess.TimeoutExpired:
                    self.check_fatal()
                    if time.monotonic() >= end:
                        raise subprocess.TimeoutExpired(cmd, timeout + 10) from None
        finally:
            if p.poll() is None:
                p.kill()
                p.communicate()
        self.check_fatal()
        return subprocess.CompletedProcess(cmd, p.returncode, out, err)

    def sq(self, code, timeout=30, player_nr=0):
        """Squirrel を流して、戻り値の文字列を返す。

        player_nr のプレーヤーで道具を使う（公共は 1）。スクリプトの中の player_x(1) では変わらないので、ここで渡す（#142）。
        """
        check_squirrel(code)
        out = self._client("--player-nr", str(check_player_nr(player_nr)), "--run-squirrel", code, timeout=timeout)
        line = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "{}"
        data = json.loads(line)
        if "result" not in data:
            raise RuntimeError(f"run_squirrel failed: {line} {out.stderr[-300:]}")
        return str(data["result"])

    def sq_file(self, path, head="", timeout=60, player_nr=0):
        """Squirrel のファイルを流す。head は先頭に足す変数の定義。"""
        with open(path, encoding="utf-8") as f:
            return self.sq(head + f.read(), timeout=timeout, player_nr=player_nr)

    def capture(self, path, timeout=30):
        """画面を PNG に撮る（capture_screen）。"""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        if os.path.isfile(path):
            os.remove(path)  # 古い物で成功と見誤らない
        out = self._client("--capture", path, timeout=timeout)
        if out.returncode != 0 or not os.path.isfile(path):
            raise RuntimeError(f"撮れなかった: {out.stderr[-300:]}")

    def road(self, x1, y1, x2, y2, way="ami_road_local", z=0, player_nr=0):
        """道路を敷く（command_x(tool_build_way)。道路の名前は AMI の物など）。Squirrel の戻り値を返す。"""
        return self.sq(f'return command_x(tool_build_way).work(player_x({player_nr}), coord3d({x1},{y1},{z}), '
                       f'coord3d({x2},{y2},{z}), "{way}")', player_nr=player_nr)

    def city_road(self, x1, y1, x2, y2, way="", z=0):
        """歩道つきの街の道路を敷く（公共のプレーヤーで command_x(tool_build_cityroad)。#142）。

        way を省くと本体の街の道路。歩道は公共のプレーヤーがこの道具で敷いたときに付く（road に player_nr=1 を渡すだけでは付かない）。
        """
        return self.sq(f'return command_x(tool_build_cityroad).work(player_x({PUBLIC_PLAYER}), coord3d({x1},{y1},{z}), '
                       f'coord3d({x2},{y2},{z}), "{way}")', player_nr=PUBLIC_PLAYER)

    def station(self, x, y, name, z=0, player_nr=0):
        """停留所を置く（command_x(tool_build_station)。名前は物の name だけ。"1,<name>" の形は失敗する）。"""
        return self.sq(f'return command_x(tool_build_station).work(player_x({player_nr}), coord3d({x},{y},{z}), "{name}")',
                       player_nr=player_nr)

    def dialog(self, which):
        """窓を開く（gui.open_dialog_tool）。which は番号か DIALOGS の名前（"finances" など。表は docs/game-check.md）。"""
        nr = DIALOGS.get(which) if isinstance(which, str) else which
        if not isinstance(nr, int) or isinstance(nr, bool) or nr < 0:
            raise ValueError(f"窓の番号か名前を渡す: {which!r}（名前: {', '.join(DIALOGS)}）")
        return self.sq(f"return gui.open_dialog_tool({nr})")

    def climate(self, x1, y1, x2, y2, climate, z=0, timeout=60, player_nr=0):
        """(x1, y1)〜(x2, y2) の矩形の気候を塗る（tool_set_climate）。climate は 1〜7 の番号か CLIMATES の名前。

        地形（grid_raise・grid_lower・水位）を変えると気候が高さで決まり直すので、塗るのは地形の後。
        戻り値は Squirrel の戻り値の文字列。本体は 1 タイルも変わらなくても成功を返すので、塗れたかは画面で見る。
        """
        nr = CLIMATES.get(climate) if isinstance(climate, str) else climate
        if not isinstance(nr, int) or isinstance(nr, bool) or nr not in CLIMATES.values():
            raise ValueError(f"気候は 1〜7 か名前を渡す: {climate!r}（名前: {', '.join(CLIMATES)}）")
        return self.sq(f'return command_x(tool_set_climate).work(player_x({player_nr}), coord3d({x1},{y1},{z}), '
                       f'coord3d({x2},{y2},{z}), "{nr}")', timeout=timeout, player_nr=player_nr)

    def month(self):
        """今の月（0 始まり。0 = 1 月）。"""
        return int(self.sq("return world.get_time().month"))

    def wait_month(self, target, timeout=420, speed=MONTH_SPEED, poll=0.4):
        """ゲームを進めて、月が target（0〜11。0 = 1 月）になったら速さを 1 に戻す。既にその月なら何もしない。

        季節の絵の確認に使う（季節と月は MONTH_TO_SEASON・SEASON_MONTHS）。同じ月の中の日付はそろえられない。
        木などの絵は月が変わってから少し遅れて入れ替わるので、撮る前に数秒待つ。timeout は実時間の秒。
        """
        if not isinstance(target, int) or isinstance(target, bool) or not 0 <= target <= 11:
            raise ValueError(f"月は 0〜11（0 = 1 月）を渡す: {target!r}")
        if self.month() == target:
            return
        end = time.monotonic() + timeout
        self.sq(f"debug.set_game_speed({int(speed)}); return 1")
        try:
            while time.monotonic() < end:
                if self.month() == target:
                    return
                time.sleep(poll)
            raise RuntimeError(f"{timeout} 秒たっても月 {target} にならなかった")
        finally:
            self.sq("debug.set_game_speed(1); return 1")

    def settle(self, seconds=15, speed=SETTLE_SPEED):
        """建設中の絵（黄と黒の縞）が終わるまでゲームを進めて、速さを 1 に戻す（速さ 1 のままだと終わらない。#58）。

        建物（車庫・停留所など）を置いた後、撮る前に呼ぶ。seconds は実時間の秒。
        待つ間も game.log を FATAL_POLL 秒ごとに見て、本体が止まったら秒数を待ち切らずに GameFatalError（#142）。
        """
        self.sq(f"debug.set_game_speed({int(speed)}); return 1")
        try:
            end = time.monotonic() + seconds
            while (rest := end - time.monotonic()) > 0:
                time.sleep(min(FATAL_POLL, rest))
                self.check_fatal()
        finally:
            self.sq("debug.set_game_speed(1); return 1")

    def stop(self):
        """起動した PID で閉じ、残りを確かめ、作業フォルダを消す（keep なら残す）。残ったら知らせる。"""
        if self.proc is not None:
            pid = self.proc.pid
            if self.proc.poll() is None:  # 終わった PID は別のプロセスに再利用されうるので撃たない
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
                try:
                    self.proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
            self.left_over = alive(pid)
            print(f"[game] stopped pid={pid}" if not self.left_over else
                  f"[game] pid={pid} が残っている（Windows を再起動するまで消えないことがある。{self.work} は消せない）", flush=True)
            self.proc = None
        if self.job is not None:
            self.job.close()
            self.job = None
        if self.prepared and not self.keep and not self.left_over:
            shutil.rmtree(self.work, onerror=lambda f, p, e: print(f"[game] 消せなかった: {p}", flush=True))
            self.prepared = False


# --- 開いたままのゲームへ命令を流す（#85） ---
# 作業フォルダの inbox/ に <番号>.cmd を置くと、見張っている側（--interactive）が流して <番号>.out に結果を書く。
# .out の 1 行目は ok か error、2 行目以降が結果。命令は Squirrel か、行頭が @ の指示（@capture <PNG>・@dialog <名前か番号>・@settle [秒]・@month <月>・
# @player <番号> <Squirrel>・@quit）。命令を流している間は inbox/busy にその 1 行目を置き、順番が来なかった送りがそれを理由にする（#142）。
INBOX = "inbox"
BUSY = "busy"
CMD_TIMEOUT = 300  # 1 つの Squirrel の待ち秒（AMI の game.sh の RUN と同じ。長い見本のため）
IDLE_LIMIT = 3600  # 命令が来ないまま続いたら閉じる秒（閉じ忘れの保険）


def default_work(port, root=ROOT):
    return os.path.abspath(os.path.join(root, "work", "game", str(port)))


def run_command(g, text):
    """命令 1 つを Game で実行して、結果の文字列を返す（@quit は呼び出し側で扱う）。"""
    text = text.strip()
    if not text.startswith("@"):
        return g.sq(text, timeout=CMD_TIMEOUT)
    name, _, arg = text[1:].partition(" ")
    arg = arg.strip()
    if name == "player":
        parts = arg.split(None, 1)
        if len(parts) != 2 or not (parts[0].isascii() and parts[0].isdigit()) or parts[1].startswith("@"):
            raise ValueError("@player には番号（公共は 1）と Squirrel を渡す")
        return g.sq(parts[1], timeout=CMD_TIMEOUT, player_nr=int(parts[0]))
    if name == "capture":
        if not arg:
            raise ValueError("@capture には PNG のパスを渡す")
        g.capture(arg)
        return arg
    if name == "dialog":
        return g.dialog(int(arg) if arg.isdigit() else arg)
    if name == "settle":
        g.settle(float(arg) if arg else 15)
        return "settled"
    if name == "month":
        if not arg.isdigit():
            raise ValueError("@month には月（0〜11。0 = 1 月）を渡す")
        g.wait_month(int(arg))
        return str(int(arg))
    raise ValueError(f"知らない指示: @{name}（@capture・@dialog・@settle・@month・@player・@quit）")


def write_result(out, body):
    """送る側が書きかけを読まないように、別の名前で書いてから置く。"""
    with open(out + ".tmp", "w", encoding="utf-8", newline="") as f:
        f.write(body)
    os.replace(out + ".tmp", out)


def set_busy(inbox, line):
    """実行中の命令の 1 行目を inbox/busy に置く（line が None なら消す）。

    送る側が読んでいる間の Windows は置き換えも削除も PermissionError になるので、少し待ってやり直す。
    理由を伝えるためだけのファイルなので、できなくても命令は続ける。
    """
    path = os.path.join(inbox, BUSY)
    for _ in range(10):
        try:
            if line is not None:
                write_result(path, line)
            elif os.path.exists(path):
                os.remove(path)
            return
        except OSError:
            time.sleep(0.05)


def reject_pending(inbox, reason):
    """順番を待っている命令を流さずに取り下げて、理由を .out に返す（#142）。"""
    for name in sorted(n for n in os.listdir(inbox) if n.endswith(".cmd")):
        try:
            os.remove(os.path.join(inbox, name))
        except OSError:  # 送る側が取り下げた
            continue
        write_result(os.path.join(inbox, name[:-4] + ".out"), f"error\nこの命令は流さなかった。{reason}")


def serve_inbox(g, inbox, idle_limit=IDLE_LIMIT, poll=0.3, log=print):
    """inbox/ の .cmd を番号順に 1 つずつ流して .out に結果を書く。@quit か idle_limit 秒の無音か、ゲームが落ちたら戻る。

    本体が FATAL ERROR・通知の窓で止まったら GameFatalError（命令の途中なら、その命令の .out に error を書いてから。
    順番を待っている命令にも、流さなかった理由を .out に返す）。
    """
    os.makedirs(inbox, exist_ok=True)
    try:
        _serve(g, inbox, idle_limit, poll, log)
    except GameFatalError as e:
        reject_pending(inbox, str(e))
        if any(n.endswith(".out") for n in os.listdir(inbox)):
            time.sleep(FATAL_SEND_WAIT)  # 閉じると inbox が消えるので、送る側が結果を読むのを待つ
        raise


def _serve(g, inbox, idle_limit, poll, log):
    last = time.monotonic()
    while True:
        pending = sorted(n for n in os.listdir(inbox) if n.endswith(".cmd"))
        if not pending:
            g.check_fatal()  # 待っている命令があるときは、流して .out に理由を返してから抜ける
        if g.proc is not None and g.proc.poll() is not None:
            g.check_fatal()
            log("[game] ゲームが終わった。見張りをやめる")
            return
        if not pending:
            if time.monotonic() - last > idle_limit:
                log(f"[game] {idle_limit} 秒、命令が無い。閉じる")
                return
            time.sleep(poll)
            continue
        cmd = os.path.join(inbox, pending[0])
        try:
            with open(cmd, encoding="utf-8") as f:
                text = f.read()
            os.remove(cmd)
        except OSError:  # 送る側が取り下げた（競合）。次へ
            continue
        out = os.path.join(inbox, pending[0][:-4] + ".out")
        quit_ = text.strip() == "@quit"
        set_busy(inbox, (text.strip().splitlines() or [""])[0][:100])
        try:
            body = "ok\n" + ("bye" if quit_ else run_command(g, text))
        except Exception as e:  # 1 つの失敗で見張りを止めない
            body = f"error\n{type(e).__name__}: {e}"
        finally:
            set_busy(inbox, None)
        write_result(out, body)
        if g.fatal() is not None:
            g.check_fatal()
        last = time.monotonic()  # 長い命令の後すぐに「無音」と見なさない
        if quit_:
            return


def send_command(inbox, text, timeout=120, poll=0.2):
    """見張っているゲームへ命令を 1 つ送り、(成功か, 結果) を返す。"""
    if not os.path.isdir(inbox):
        raise RuntimeError(f"見張っているゲームが無い（{inbox} が無い。--interactive で起動する）")
    stamp = f"{time.time_ns()}_{os.getpid()}"  # 同時の送りでも名前が重ならない
    tmp, cmd, out = (os.path.join(inbox, stamp + ext) for ext in (".tmp", ".cmd", ".out"))
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    os.replace(tmp, cmd)
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if not os.path.isdir(inbox):
            raise RuntimeError("見張っているゲームが閉じた（inbox が消えた）")
        if os.path.isfile(out):
            with open(out, encoding="utf-8") as f:
                head, _, body = f.read().partition("\n")
            os.remove(out)
            return head == "ok", body
        time.sleep(poll)
    try:
        with open(os.path.join(inbox, BUSY), encoding="utf-8") as f:
            running = f.read()
    except OSError:
        running = None
    try:
        os.remove(cmd)  # 見張りが取らなかった命令は取り下げる
    except OSError:
        raise RuntimeError(f"{timeout} 秒、答えが無い。命令は見張りが取った後で、実行された可能性がある")
    if running is not None:
        raise RuntimeError(f"{timeout} 秒、答えが無い。見張りが前の命令を実行中で、順番が来なかった（命令は取り下げた。"
                           f"実行中の命令: {running}）。終わってから送り直すか、--timeout を長くする")
    raise RuntimeError(f"{timeout} 秒、答えが無い（見張りが止まっている？命令は取り下げた）")


def main():
    ap = argparse.ArgumentParser(description="ゲームを起動して Squirrel を流し、撮って、閉じる")
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"), help="検証環境（環境変数 PAK256_GAME_ENV）")
    ap.add_argument("--save", help="保存データの名前（拡張子なし）")
    ap.add_argument("--port", type=int, required=True, help=f"MCP のポート（既定の範囲は {PORT_MIN}〜{PORT_MAX}。割り当てられた範囲の中）")
    ap.add_argument("--port-range", help=f"ポートの範囲を変える「下限-上限」（環境変数 {PORT_RANGE_ENV} でも渡せる）")
    ap.add_argument("--script", action="append", default=[], help="流す Squirrel のファイル（順に流す）")
    ap.add_argument("--capture", help="撮る PNG のパス（Squirrel の後）")
    ap.add_argument("--extra-pak", action="append", default=[], help="借りる pak のファイル（試験のときだけ）")
    ap.add_argument("--build", action="store_true", help="起動の前に tools/build.py を流す")
    add_pak_argument(ap)
    ap.add_argument("--night", action="store_true", help="昼夜の切り替えを止めない（夜の灯りを見るとき）")
    ap.add_argument("--keep", action="store_true", help="閉じた後も作業フォルダを残す")
    ap.add_argument("--keep-save-roads", action="store_true",
                    help="保存データの写しの道路名を pak の指定に書き換えない（保存された名前を確かめるとき）")
    ap.add_argument("--work", help="作業フォルダ（既定は work/game/<ポート>/）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    ap.add_argument("--interactive", action="store_true", help="起動して、命令を待つ（--send で流す）。@quit・無音・Ctrl+C で閉じる")
    ap.add_argument("--idle-limit", type=int, default=IDLE_LIMIT, help="--interactive で命令が来ない秒（超えたら閉じる）")
    ap.add_argument("--send", help="見張っているゲーム（--port）へ流す命令。Squirrel か @capture <PNG>・@dialog <名前>・@settle [秒]・@month <月>・@player <番号> <Squirrel>・@quit")
    ap.add_argument("--player-nr", type=int, help=f"Squirrel（--script・--send・--send-file）を流すプレーヤー（公共は {PUBLIC_PLAYER}。省くと 0）")
    ap.add_argument("--send-file", help="--send の代わりに、Squirrel のファイルを流す")
    ap.add_argument("--timeout", type=int, default=120, help="--send の答えを待つ秒")
    args = ap.parse_args()
    if (args.send is not None or args.send_file) and args.interactive:
        sys.exit("--interactive（起動）と --send（流す）は別の呼び出しで使う")
    if args.player_nr is not None:
        try:
            check_player_nr(args.player_nr)
        except ValueError as e:
            sys.exit(f"--player-nr: {e}")
        if args.interactive:
            sys.exit("--player-nr は --interactive でなく、--send・--send-file の呼び出しに付ける")
    if args.pak is not None and (args.send is not None or args.send_file):
        sys.exit("--pak は起動する呼び出し（--interactive など）に付ける")
    if args.pak is not None and args.build:
        sys.exit("--build（build/pak/ を組む）と --pak は一緒に使わない")
    if args.send is not None or args.send_file:
        text = args.send
        if args.send_file:
            with open(args.send_file, encoding="utf-8") as f:
                text = f.read()
        if text.lstrip().startswith("@capture "):  # 見張る側の作業フォルダでなく、ここからの相対で読む
            text = "@capture " + os.path.abspath(text.lstrip()[len("@capture "):].strip())
        if args.player_nr is not None:
            if text.lstrip().startswith("@"):
                sys.exit("--player-nr は Squirrel を流すときだけ（@capture などの指示には付けない）")
            text = f"@player {args.player_nr} {text}"
        ok, body = send_command(os.path.join(os.path.abspath(args.work) if args.work else default_work(args.port), INBOX),
                                text, args.timeout)
        print(body)
        sys.exit(0 if ok else 1)
    if not args.save:
        sys.exit("--save（保存データの名前）を渡す")
    if not args.env:
        sys.exit("検証環境を --env か環境変数 PAK256_GAME_ENV で渡す")
    if args.build:
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "build.py")], check=True)
    try:
        with Game(args.env, args.save, args.port, work=args.work, night=args.night, extra_paks=args.extra_pak,
                  client=args.mcp_client, keep=args.keep, port_range=args.port_range,
                  rewrite_roads=not args.keep_save_roads, pak_dir=args.pak) as g:
            if args.interactive:
                print(f"[interactive] 待っている。別の窓から: python -X utf8 tools/game.py --port {args.port} --send \"return 1\"", flush=True)
                try:
                    serve_inbox(g, os.path.join(g.work, INBOX), args.idle_limit)
                except KeyboardInterrupt:
                    pass
            for s in args.script:
                print("[script]", g.sq_file(s, player_nr=args.player_nr or 0), flush=True)
            if args.capture:
                g.capture(args.capture)
                print("[capture]", args.capture, flush=True)
            g.check_fatal()  # 最後の命令の後に止まっていても、成功にしない
    except GameFatalError as e:  # with を抜けるときに閉じてある
        sys.exit(f"[game] {e}")
    if g.left_over:
        sys.exit(1)


if __name__ == "__main__":
    main()
