"""ゲームの起動と後片付けを 1 つにした道具（docs/game-check.md）。MIT License。

本体の検証環境を一時の作業フォルダに写し、手元で組んだ pak を入れ、MCP 付きで起動して、Squirrel を流す・画面を撮る・
起動した PID で閉じる・作業フォルダを消す、までを 1 回の呼び出しで行う。

コマンドから使う:
    python -X utf8 tools/game.py --env <検証環境> --save flat_512_left_v64 --port 47880 \
        --script course.nut --capture out/shot.png

    --env は環境変数 PAK256_GAME_ENV でも渡せる（個人の絶対パスはリポジトリに書かない）。
    --build を付けると、起動の前に tools/build.py を流す。無ければ build/pak/ の物を使う。

別の道具（tools/vehicle_check/run.py など）から使う:
    from game import Game, prepare_workdir
    with Game(env, save, port) as g:
        g.sq("return 1")
        g.capture("a.png")

決まり:
- 検証環境には書かない。写した作業フォルダ（既定は work/game/<ポート>/）だけを使う。
- settings.xml は写さない（本体が送信用の記録を持っていて、起動のたびに使用状況を外へ送るため）。
- config/simuconf.tab の末尾に day_night_shift = 0 を足して昼夜の切り替えを止める（夜の絵になって撮り直すのを防ぐ）。
  夜の灯りを見るときだけ --night。
- 起動に -singleuser・-set_workdir・-lang ja・-objects・-load・-mcp-port を付ける。
- ゲームは起動したときの PID で閉じる（実行ファイルの名前では止めない）。閉じた後に tasklist で残りを確かめ、残ったら知らせる。
- MCP のポートは、割り当てられた範囲（47880〜47899）の中を必ず明示する。
- pak を入れる処理は install_pak（#38 のテストプレイのフォルダへ入れる道具と共通）。
"""
import argparse
import glob
import json
import os
import shutil
import socket
import subprocess
import sys
import time

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

def install_pak(dest, root=ROOT, build=None, extra=()):
    """手元で組んだ pak と config/・text/ を dest（本体の pak のフォルダ）に入れる。

    dest の中身は配布の zip の pak256/ と同じ形（package.collect と同じ一覧から、pak・config・text だけを取る）。
    extra は、足りない物を別の pak から借りるときのファイル（試験のときだけ。コミットしない）。
    #38（テストプレイのフォルダへ入れる道具）も、この関数で入れる。入れた相対パスの一覧を返す。
    """
    build = build or os.path.join(root, "build")
    placed = []
    for arc, src in package.collect(root, build):
        rel = arc.split("/", 1)[1]
        if not (rel.endswith(".pak") and "/" not in rel) and rel.split("/", 1)[0] not in ("config", "text"):
            continue
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
    if not 47880 <= port <= 47899:
        raise RuntimeError(f"MCP のポートは 47880〜47899 の中で明示する: {port}")


def port_in_use(port):
    """そのポートに誰かがつながるか（他のゲームが使っている）。"""
    for host in ("127.0.0.1", "::1"):
        fam = socket.AF_INET6 if ":" in host else socket.AF_INET
        with socket.socket(fam, socket.SOCK_STREAM) as sk:
            sk.settimeout(1)
            if sk.connect_ex((host, port)) == 0:
                return True
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


def alive(pid):
    """tasklist で PID のプロセスが残っているか。"""
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True)
    return f'"{pid}"' in out.stdout.decode("utf-8", errors="replace")  # 日本語の Windows は cp932 で出す。PID の数字だけ見る


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
            self.proc = subprocess.Popen(cmd, cwd=self.work, stdout=log, stderr=subprocess.STDOUT)
        print(f"[game] pid={self.proc.pid} port={self.port} work={self.work}", flush=True)
        end, last = time.monotonic() + limit, None
        while time.monotonic() < end:
            if self.proc.poll() is not None:
                raise RuntimeError(f"ゲームが終わった（終了コード {self.proc.returncode}。ログは {self.work}/game.log）")
            try:
                if self.sq("return 1", timeout=5) == "1":
                    return
            except Exception as e:  # 起動中は答えない
                last = e
            time.sleep(3)
        raise RuntimeError(f"ゲームが MCP に答えない: {last}")

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
        if self.prepared and not self.keep and not self.left_over:
            shutil.rmtree(self.work, onerror=lambda f, p, e: print(f"[game] 消せなかった: {p}", flush=True))
            self.prepared = False


def main():
    ap = argparse.ArgumentParser(description="ゲームを起動して Squirrel を流し、撮って、閉じる")
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"), help="検証環境（環境変数 PAK256_GAME_ENV）")
    ap.add_argument("--save", required=True, help="保存データの名前（拡張子なし）")
    ap.add_argument("--port", type=int, required=True, help="MCP のポート（47880〜47899）")
    ap.add_argument("--script", action="append", default=[], help="流す Squirrel のファイル（順に流す）")
    ap.add_argument("--capture", help="撮る PNG のパス（Squirrel の後）")
    ap.add_argument("--extra-pak", action="append", default=[], help="借りる pak のファイル（試験のときだけ）")
    ap.add_argument("--build", action="store_true", help="起動の前に tools/build.py を流す")
    ap.add_argument("--night", action="store_true", help="昼夜の切り替えを止めない（夜の灯りを見るとき）")
    ap.add_argument("--keep", action="store_true", help="閉じた後も作業フォルダを残す")
    ap.add_argument("--work", help="作業フォルダ（既定は work/game/<ポート>/）")
    ap.add_argument("--mcp-client", default=os.environ.get("MCP_CLIENT"))
    args = ap.parse_args()
    if not args.env:
        sys.exit("検証環境を --env か環境変数 PAK256_GAME_ENV で渡す")
    if args.build:
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "build.py")], check=True)
    with Game(args.env, args.save, args.port, work=args.work, night=args.night, extra_paks=args.extra_pak,
              client=args.mcp_client, keep=args.keep) as g:
        for s in args.script:
            print("[script]", g.sq_file(s), flush=True)
        if args.capture:
            g.capture(args.capture)
            print("[capture]", args.capture, flush=True)
    if g.left_over:
        sys.exit(1)


if __name__ == "__main__":
    main()
