"""ゲームの起動と後片付けを 1 つにした道具（docs/game-check.md）。MIT License。

本体の検証環境を一時の作業フォルダに写し、手元で組んだ pak を入れ、MCP 付きで起動して、Squirrel を流す・画面を撮る・
起動した PID で閉じる・作業フォルダを消す、までを 1 回の呼び出しで行う。

コマンドから使う:
    python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47880 \
        --script course.nut --capture out/shot.png

    --env は環境変数 PAK256_GAME_ENV でも渡せる（個人の絶対パスはリポジトリに書かない）。
    --build を付けると、起動の前に tools/build.py を流す。無ければ build/pak/ の物を使う。

開いたままのゲームへ命令を 1 つずつ流す（#85。docs/game-check.md の「開いたまま使う」）:
    python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47900 --interactive   # 起動して待つ（背景で動かす）
    python -X utf8 tools/game.py --port 47900 --send "return 1"            # Squirrel を流して結果を見る
    python -X utf8 tools/game.py --port 47900 --send "@capture out/a.png"  # 撮る（@dialog 名前・@settle 秒・@quit も）

別の道具（tools/vehicle_check/run.py など）から使う:
    from game import Game, prepare_workdir
    with Game(env, save, port) as g:
        g.sq("return 1")
        g.dialog("finances")   # 財務の窓（番号の表は DIALOGS・docs/game-check.md）
        g.settle(10)           # 建設中の絵が終わるまで進める
        g.capture("a.png")

決まり:
- 検証環境には書かない。写した作業フォルダ（既定は work/game/<ポート>/）だけを使う。
- settings.xml は写さない（本体が送信用の記録を持っていて、起動のたびに使用状況を外へ送るため）。
- config/simuconf.tab の末尾に day_night_shift = 0 を足して昼夜の切り替えを止める（夜の絵になって撮り直すのを防ぐ）。
  夜の灯りを見るときだけ --night。
- 起動に -singleuser・-set_workdir・-lang ja・-objects・-load・-mcp-port を付ける。
- ゲームは起動したときの PID で閉じる（実行ファイルの名前では止めない）。閉じた後に tasklist で残りを確かめ、残ったら知らせる。
- MCP のポートは、pak256 の作業者全体の範囲（PORT_MIN〜PORT_MAX = 47800〜47999）の中を必ず明示する。作業者ごとに進捗管理から割り当てられる範囲は、その中の一部。
- この道具を動かす Python が強制終了されても、ゲームは閉じる（Windows の Job Object。KILL_ON_JOB_CLOSE。#59）。
- Squirrel の文字列リテラルの中に改行を入れない（Python の通常の文字列のバックスラッシュ n が本物の改行になって、コンパイルが通らない）。入れたら流す前に止める。
- pak を入れる処理は install_pak（tools/install_local.py のテストプレイのフォルダへ入れる道具と共通。zip も渡せる。#38）。
"""
import argparse
import ctypes
import glob
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import zipfile

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
PORT_MIN, PORT_MAX = 47800, 47999  # pak256 の作業者全体の MCP のポートの範囲。作業者ごとの割り当てはこの中
# gui.open_dialog_tool(番号) の窓の番号（OTRP 本体の simmenu.h の DIALOG_*。順に 0 から）。使う物だけ。docs/game-check.md に表
DIALOGS = {
    "help": 0, "options": 1, "minimap": 2, "lineoverview": 3, "messages": 4, "finances": 5, "players": 6,
    "displayoptions": 7, "sound": 8, "language": 9, "playercolor": 10, "jump": 11, "load": 12, "save": 13,
    "list_halt": 14, "list_convoi": 15, "list_town": 16, "list_goods": 17, "list_factory": 18, "list_curiosity": 19,
}
SETTLE_SPEED = 64  # 建設中の絵が終わるまで進めるときの速さ（本体の set_game_speed）


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
    """配布の zip の pak256/ の中の相対パスのうち、ゲームが読む物（最上段の *.pak・config/・text/）か。"""
    return (rel.endswith(".pak") and "/" not in rel) or rel.split("/", 1)[0] in ("config", "text")


VERSION_FILE = "VERSION"  # install_local.py が書く版の名前のファイル（入れ替えのとき一緒に消す）


def clean_pak(dest):
    """dest の中の、入れる種類の物（最上段の *.pak・config/・text/・VERSION）だけを消す。下位のフォルダなどほかの物は残す。"""
    if not os.path.isdir(dest):
        return
    for name in os.listdir(dest):
        path = os.path.join(dest, name)
        if os.path.isfile(path) and (name.endswith(".pak") or name == VERSION_FILE):
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


def install_pak(dest, root=ROOT, build=None, extra=(), zip_path=None, clean=False):
    """pak と config/・text/ を dest（本体の pak のフォルダ）に入れる。

    dest の中身は配布の zip の pak256/ と同じ形（*.pak・config・text だけ。許諾の文は入れない）。
    zip_path があれば（root・build は使わない）、その zip（Release の物を含む配布の zip）から取る。無ければ手元で組んだ build/pak/ と config/・text/ から取る
    （配布用の許諾の検査は通さない。package.collect_runtime）。
    clean は、入れる前に dest の古い *.pak・config/・text/ を消す（テストプレイのフォルダの入れ替え。ほかの物は残す）。
    extra は、足りない物を別の pak から借りるときのファイル（試験のときだけ。コミットしない）。
    ゲームの作業フォルダ（Game）も、テストプレイのフォルダに入れる道具（tools/install_local.py。#38）も、これで入れる。
    入れた相対パスの一覧を返す。
    """
    if zip_path:
        members = _zip_members(zip_path)
        if not any(rel.endswith(".pak") and "/" not in rel for rel, _ in members):
            raise RuntimeError(f"zip に pak が無い: {zip_path}")
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


def prepare_workdir(env, work, save, exe=EXE, night=False, extra_paks=(), root=ROOT, build=None):
    """検証環境 env の一部を作業フォルダ work に写し、pak と保存データを入れる。work が既にあれば作り直す。

    写す物: 実行ファイル・DLL・ENV_DIRS（settings.xml は写さない）・指定の保存データ 1 つ。pak は work/pak/ に install_pak で入れる。
    """
    if not os.path.isfile(os.path.join(env, exe)):
        raise RuntimeError(f"検証環境に {exe} が無い: {env}")
    sve = os.path.join(env, "save", save + ".sve")
    if not os.path.isfile(sve):
        raise RuntimeError(f"保存データが無い: {sve}")
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
    placed = install_pak(os.path.join(work, PAK_DIR), root, build, extra_paks)
    if not night:
        # 本体の config/ と pak の config/ の両方に足す（どちらが後に読まれても止まる）
        append_day_night_off(os.path.join(work, "config", "simuconf.tab"))
        append_day_night_off(os.path.join(work, PAK_DIR, "config", "simuconf.tab"))
    return placed


def launch_command(work, save, port, exe=EXE, screensize=SCREENSIZE):
    """起動のコマンド。-singleuser が無いと本体が作業フォルダでなく別の場所を見る。-lang ja が無いと言語選びの画面で止まる。"""
    return [os.path.join(work, exe), "-singleuser", "-set_workdir", work, "-objects", PAK_DIR + "/",
            "-load", save, "-freeplay", "-mute", "-lang", "ja", "-mcp-port", str(port), "-screensize", screensize]


def check_port(port):
    if not PORT_MIN <= port <= PORT_MAX:
        raise RuntimeError(f"MCP のポートは {PORT_MIN}〜{PORT_MAX} の中で明示する: {port}")


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
                 screensize=SCREENSIZE, keep=False, root=ROOT, build=None):
        check_port(port)
        self.env, self.save, self.port = os.path.abspath(env), save, port
        self.work = os.path.abspath(work or os.path.join(root, "work", "game", str(port)))
        self.night, self.extra_paks, self.exe, self.screensize = night, extra_paks, exe, screensize
        self.client = client or os.environ.get("MCP_CLIENT") or default_client()
        self.keep, self.root, self.build = keep, root, build
        self.proc = None
        self.job = None  # 親が強制終了されてもゲームを閉じる Job Object（Windows）
        self.prepared = False  # この Game が作業フォルダを用意した（他人の物を消さない）
        self.left_over = False  # 閉じた後も PID が残ったか

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
        check_work(self.work, self.env, self.root)
        self.prepared = True
        prepare_workdir(self.env, self.work, self.save, self.exe, self.night, self.extra_paks, self.root, self.build)
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
            if self.proc.poll() is not None:
                raise RuntimeError(f"ゲームが終わった（終了コード {self.proc.returncode}）。ログの末尾: {self.log_tail()}")
            try:
                if self.sq("return 1", timeout=5) == "1":
                    return
            except Exception as e:  # 起動中は答えない
                last = e
            time.sleep(3)
        raise RuntimeError(f"ゲームが MCP に答えない: {last}。ログの末尾: {self.log_tail()}")

    def log_tail(self, n=600):
        """起動のログ（game.log）の末尾。作業フォルダは失敗の後に消えるので、メッセージに入れて残す。"""
        try:
            with open(os.path.join(self.work, "game.log"), "rb") as f:
                return f.read()[-n:].decode("utf-8", errors="replace").strip() or "（空）"
        except OSError:
            return "（無し）"

    def alive_mcp(self):
        try:
            return self.sq("return 1", timeout=3) == "1"
        except Exception:
            return False

    def _client(self, *args, timeout):
        return subprocess.run([sys.executable, "-X", "utf8", "-I", self.client, "--port", str(self.port), *args, "--timeout", str(timeout)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout + 10)

    def sq(self, code, timeout=30):
        """Squirrel を流して、戻り値の文字列を返す。"""
        check_squirrel(code)
        out = self._client("--run-squirrel", code, timeout=timeout)
        line = out.stdout.strip().splitlines()[-1] if out.stdout.strip() else "{}"
        data = json.loads(line)
        if "result" not in data:
            raise RuntimeError(f"run_squirrel failed: {line} {out.stderr[-300:]}")
        return str(data["result"])

    def sq_file(self, path, head="", timeout=60):
        """Squirrel のファイルを流す。head は先頭に足す変数の定義。"""
        with open(path, encoding="utf-8") as f:
            return self.sq(head + f.read(), timeout=timeout)

    def capture(self, path, timeout=30):
        """画面を PNG に撮る（capture_screen）。"""
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        if os.path.isfile(path):
            os.remove(path)  # 古い物で成功と見誤らない
        out = self._client("--capture", path, timeout=timeout)
        if out.returncode != 0 or not os.path.isfile(path):
            raise RuntimeError(f"撮れなかった: {out.stderr[-300:]}")

    def road(self, x1, y1, x2, y2, way="ami_road_local", z=0):
        """道路を敷く（command_x(tool_build_way)。道路の名前は AMI の物など）。Squirrel の戻り値を返す。"""
        return self.sq(f'return command_x(tool_build_way).work(player_x(0), coord3d({x1},{y1},{z}), coord3d({x2},{y2},{z}), "{way}")')

    def station(self, x, y, name, z=0):
        """停留所を置く（command_x(tool_build_station)。名前は物の name だけ。"1,<name>" の形は失敗する）。"""
        return self.sq(f'return command_x(tool_build_station).work(player_x(0), coord3d({x},{y},{z}), "{name}")')

    def dialog(self, which):
        """窓を開く（gui.open_dialog_tool）。which は番号か DIALOGS の名前（"finances" など。表は docs/game-check.md）。"""
        nr = DIALOGS.get(which) if isinstance(which, str) else which
        if not isinstance(nr, int) or isinstance(nr, bool) or nr < 0:
            raise ValueError(f"窓の番号か名前を渡す: {which!r}（名前: {', '.join(DIALOGS)}）")
        return self.sq(f"return gui.open_dialog_tool({nr})")

    def settle(self, seconds=15, speed=SETTLE_SPEED):
        """建設中の絵（黄と黒の縞）が終わるまでゲームを進めて、速さを 1 に戻す（速さ 1 のままだと終わらない。#58）。

        建物（車庫・停留所など）を置いた後、撮る前に呼ぶ。seconds は実時間の秒。
        """
        self.sq(f"debug.set_game_speed({int(speed)}); return 1")
        try:
            time.sleep(seconds)
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
# .out の 1 行目は ok か error、2 行目以降が結果。命令は Squirrel か、行頭が @ の指示（@capture <PNG>・@dialog <名前か番号>・@settle [秒]・@quit）。
INBOX = "inbox"
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
    raise ValueError(f"知らない指示: @{name}（@capture・@dialog・@settle・@quit）")


def serve_inbox(g, inbox, idle_limit=IDLE_LIMIT, poll=0.3, log=print):
    """inbox/ の .cmd を番号順に 1 つずつ流して .out に結果を書く。@quit か idle_limit 秒の無音か、ゲームが落ちたら戻る。"""
    os.makedirs(inbox, exist_ok=True)
    last = time.monotonic()
    while True:
        if g.proc is not None and g.proc.poll() is not None:
            log("[game] ゲームが終わった。見張りをやめる")
            return
        pending = sorted(n for n in os.listdir(inbox) if n.endswith(".cmd"))
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
        try:
            body = "ok\n" + ("bye" if quit_ else run_command(g, text))
        except Exception as e:  # 1 つの失敗で見張りを止めない
            body = f"error\n{type(e).__name__}: {e}"
        with open(out + ".tmp", "w", encoding="utf-8", newline="") as f:
            f.write(body)
        os.replace(out + ".tmp", out)  # 送る側が書きかけを読まない
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
        os.remove(cmd)  # 見張りが取らなかった命令は取り下げる
    except OSError:
        raise RuntimeError(f"{timeout} 秒、答えが無い。命令は見張りが取った後で、実行された可能性がある")
    raise RuntimeError(f"{timeout} 秒、答えが無い（見張りが止まっている？命令は取り下げた）")


def main():
    ap = argparse.ArgumentParser(description="ゲームを起動して Squirrel を流し、撮って、閉じる")
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"), help="検証環境（環境変数 PAK256_GAME_ENV）")
    ap.add_argument("--save", help="保存データの名前（拡張子なし）")
    ap.add_argument("--port", type=int, required=True, help=f"MCP のポート（{PORT_MIN}〜{PORT_MAX}。割り当てられた範囲の中）")
    ap.add_argument("--script", action="append", default=[], help="流す Squirrel のファイル（順に流す）")
    ap.add_argument("--capture", help="撮る PNG のパス（Squirrel の後）")
    ap.add_argument("--extra-pak", action="append", default=[], help="借りる pak のファイル（試験のときだけ）")
    ap.add_argument("--build", action="store_true", help="起動の前に tools/build.py を流す")
    ap.add_argument("--night", action="store_true", help="昼夜の切り替えを止めない（夜の灯りを見るとき）")
    ap.add_argument("--keep", action="store_true", help="閉じた後も作業フォルダを残す")
    ap.add_argument("--work", help="作業フォルダ（既定は work/game/<ポート>/）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    ap.add_argument("--interactive", action="store_true", help="起動して、命令を待つ（--send で流す）。@quit・無音・Ctrl+C で閉じる")
    ap.add_argument("--idle-limit", type=int, default=IDLE_LIMIT, help="--interactive で命令が来ない秒（超えたら閉じる）")
    ap.add_argument("--send", help="見張っているゲーム（--port）へ流す命令。Squirrel か @capture <PNG>・@dialog <名前>・@settle [秒]・@quit")
    ap.add_argument("--send-file", help="--send の代わりに、Squirrel のファイルを流す")
    ap.add_argument("--timeout", type=int, default=120, help="--send の答えを待つ秒")
    args = ap.parse_args()
    if (args.send is not None or args.send_file) and args.interactive:
        sys.exit("--interactive（起動）と --send（流す）は別の呼び出しで使う")
    if args.send is not None or args.send_file:
        text = args.send
        if args.send_file:
            with open(args.send_file, encoding="utf-8") as f:
                text = f.read()
        if text.lstrip().startswith("@capture "):  # 見張る側の作業フォルダでなく、ここからの相対で読む
            text = "@capture " + os.path.abspath(text.lstrip()[len("@capture "):].strip())
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
    with Game(args.env, args.save, args.port, work=args.work, night=args.night, extra_paks=args.extra_pak,
              client=args.mcp_client, keep=args.keep) as g:
        if args.interactive:
            print(f"[interactive] 待っている。別の窓から: python -X utf8 tools/game.py --port {args.port} --send \"return 1\"", flush=True)
            try:
                serve_inbox(g, os.path.join(g.work, INBOX), args.idle_limit)
            except KeyboardInterrupt:
                pass
        for s in args.script:
            print("[script]", g.sq_file(s), flush=True)
        if args.capture:
            g.capture(args.capture)
            print("[capture]", args.capture, flush=True)
    if g.left_over:
        sys.exit(1)


if __name__ == "__main__":
    main()
