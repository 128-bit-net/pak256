"""起動の窓（タイトルの画面）と、その後ろに映る地図を撮る道具（docs/game-check.md の「起動の画面を撮る」）。MIT License。

`-load` を付けない起動では、起動の窓が出ている間、本体は MCP に答えない（capture_screen が使えない）。
この道具は、保存データの無い作業フォルダ（実行ファイル・DLL・config/ などと pak256/ だけ）で MCP を付けずに起動し、
自分で起動した窓の中身を PrintWindow で読んで PNG にする。キーやクリックなどの入力は送らない。Windows だけ。Pillow が要る。

使い方:
    python -X utf8 tools/title_shot.py --env <検証環境> --out work/title.png              # build/pak/ などを入れる
    python -X utf8 tools/title_shot.py --env <検証環境> --out work/title.png --zip <配布の zip>

--env は環境変数 PAK256_GAME_ENV でも渡せる（個人の絶対パスはリポジトリに書かない）。
撮れたら、起動した PID を閉じて作業フォルダを消す（--keep で残す）。
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import game  # noqa: E402

PAK_FOLDER = "pak256"
FIRST_WAIT = 30  # 起動の窓が出るまで待つ秒
RETRIES = 12  # 黒い画面だったときに撮り直す回数
RETRY_WAIT = 5


def prepare(env, work, root=game.ROOT, build=None, zip_path=None, exe=game.EXE):
    """保存データの無い作業フォルダを作る。save/ と settings.xml は写さない（検証環境には書かない）。"""
    if not os.path.isfile(os.path.join(env, exe)):
        raise RuntimeError(f"検証環境に {exe} が無い: {env}")
    game.check_work(work, env, root)  # 他の物を消さない
    if os.path.exists(work):
        shutil.rmtree(work)
    os.makedirs(work)
    with open(os.path.join(work, game.MARK), "w", encoding="utf-8") as f:
        f.write("tools/title_shot.py\n")
    shutil.copyfile(os.path.join(env, exe), os.path.join(work, exe))
    for dll in glob.glob(os.path.join(env, "*.dll")):
        shutil.copyfile(dll, os.path.join(work, os.path.basename(dll)))
    for d in game.ENV_DIRS:
        if os.path.isdir(os.path.join(env, d)):
            shutil.copytree(os.path.join(env, d), os.path.join(work, d))
    return game.install_pak(os.path.join(work, PAK_FOLDER), root=root, build=build, zip_path=zip_path)


def command(work, exe=game.EXE, screensize=game.SCREENSIZE):
    """起動のコマンド。-load と -mcp-port を付けない（遊ぶ人の、保存データが無いときの起動と同じ道を通す）。"""
    return [os.path.join(work, exe), "-singleuser", "-set_workdir", work, "-objects", PAK_FOLDER + "/",
            "-lang", "ja", "-mute", "-screensize", screensize]


def shoot(proc, capture, log_path, out, wait=FIRST_WAIT, retries=RETRIES, sleep=time.sleep):
    """起動した proc の窓を capture(pid, out) で撮る。capture は黒くない絵が撮れたら True。

    描き直しの前に読むと真っ黒になることがあるので、黒でなくなるまで撮り直す。
    本体が終わった・FATAL ERROR や通知の窓で止まった場合は失敗にする（エラーの窓を成功の画面と取り違えない）。
    """
    sleep(wait)
    for _ in range(retries):
        with open(log_path, "rb") as f:
            log = f.read()
        marks = [i for i in (log.find(m) for m in game.FATAL_MARKS) if i >= 0]
        if marks:
            raise game.GameFatalError(log[min(marks):][:game.FATAL_CHARS].decode("utf-8", errors="replace"))
        if proc.poll() is not None:
            raise RuntimeError(f"ゲームが終わった（終了コード {proc.returncode}）")
        if capture(proc.pid, out):
            return
        print("[title_shot] 撮れない（窓が無い・読めない・黒一色）。撮り直す", flush=True)
        sleep(RETRY_WAIT)
    raise RuntimeError("撮れないまま（窓が無い・読めない・黒一色）")


def capture_window(pid, path):
    """PID の一番大きい窓の中身を PrintWindow で PNG にする（読むだけ）。黒一色なら False。"""
    import ctypes
    from ctypes import wintypes

    from PIL import Image

    class BitmapInfo(ctypes.Structure):
        _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                    ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                    ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                    ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                    ("biClrImportant", wintypes.DWORD), ("colors", wintypes.DWORD * 3)]

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
    user32.SetProcessDPIAware()
    user32.GetDC.restype = wintypes.HDC
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    gdi32.CreateCompatibleDC.restype = wintypes.HDC
    gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
    gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
    gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
    gdi32.SelectObject.restype = wintypes.HGDIOBJ
    gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
    gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p,
                                ctypes.c_void_p, wintypes.UINT]
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
    gdi32.DeleteDC.argtypes = [wintypes.HDC]

    def size(hwnd):
        r = wintypes.RECT()
        user32.GetClientRect(hwnd, ctypes.byref(r))
        return r.right - r.left, r.bottom - r.top

    found = []

    def each(hwnd, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(hwnd):
            w, h = size(hwnd)
            found.append((w * h, hwnd))
        return True

    user32.EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(each), 0)
    if not found or not max(found, key=lambda t: t[0])[0]:
        return False  # 窓がまだ無い
    hwnd = max(found, key=lambda t: t[0])[1]
    w, h = size(hwnd)
    screen = user32.GetDC(None)
    dc = gdi32.CreateCompatibleDC(screen)
    bmp = gdi32.CreateCompatibleBitmap(screen, w, h)
    try:
        old = gdi32.SelectObject(dc, bmp)
        ok = user32.PrintWindow(hwnd, dc, 3)  # PW_CLIENTONLY | PW_RENDERFULLCONTENT
        gdi32.SelectObject(dc, old)
        info = BitmapInfo(biSize=40, biWidth=w, biHeight=-h, biPlanes=1, biBitCount=32)
        buf = ctypes.create_string_buffer(w * h * 4)
        lines = gdi32.GetDIBits(dc, bmp, 0, h, buf, ctypes.byref(info), 0)
    finally:
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(dc)
        user32.ReleaseDC(None, screen)
    if not ok or lines != h:
        return False
    image = Image.frombuffer("RGB", (w, h), buf, "raw", "BGRX", 0, 1)
    if not image.getbbox():
        return False
    image.save(path)
    return True


def title_shot(env, out, work, root=game.ROOT, build=None, zip_path=None, exe=game.EXE, screensize=game.SCREENSIZE,
               wait=FIRST_WAIT, keep=False):
    """作業フォルダを作り、起動して撮り、起動した PID で閉じる。"""
    out, work = os.path.abspath(out), os.path.abspath(work)
    real = [os.path.normcase(os.path.realpath(p)) for p in (out, work)]  # 大文字小文字やリンクの違いでもすり抜けない
    if real[0].startswith(real[1] + os.sep):
        raise RuntimeError(f"出力が作業フォルダの中（撮った後に消える）: {out}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.isfile(out):
        os.remove(out)  # 古い物で成功と見誤らない
    prepare(os.path.abspath(env), work, root, build, zip_path, exe)
    job, proc, left = None, None, False
    log_path = os.path.join(work, "game.log")
    try:
        try:
            job = game.JobObject()  # この Python が強制終了されてもゲームを閉じる
        except OSError as e:
            print(f"[title_shot] Job Object を作れなかった（{e}）", flush=True)
        with open(log_path, "wb") as log:
            proc = subprocess.Popen(command(work, exe, screensize), cwd=work, stdout=log, stderr=subprocess.STDOUT)
        if job is not None:
            job.assign(proc)
        print(f"[title_shot] pid={proc.pid} work={work}", flush=True)
        shoot(proc, capture_window, log_path, out, wait)
        if not os.path.isfile(out):
            raise RuntimeError(f"撮った PNG が無い: {out}")
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.kill()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                pass
            left = game.alive(proc.pid)
            print(f"[title_shot] pid={proc.pid} が残っている" if left else f"[title_shot] stopped pid={proc.pid}", flush=True)
        if job is not None:
            job.close()
        if not keep and not left:
            shutil.rmtree(work, onerror=lambda f, p, e: print(f"[title_shot] 消せなかった: {p}", flush=True))
    if left:
        raise RuntimeError("ゲームのプロセスが残った")


def main():
    ap = argparse.ArgumentParser(description="起動の窓と後ろの地図を撮る（入力は送らない）")
    ap.add_argument("--env", default=os.environ.get("PAK256_GAME_ENV"), help="本体の検証環境（PAK256_GAME_ENV でも）")
    ap.add_argument("--out", required=True, help="撮る PNG")
    ap.add_argument("--zip", help="配布の zip を入れる。無ければ組み済みの build/pak/ と config/・text/・demo/")
    ap.add_argument("--work", default=os.path.join(game.ROOT, "work", "title_shot"), help="作業フォルダ")
    ap.add_argument("--screensize", default=game.SCREENSIZE)
    ap.add_argument("--wait", type=float, default=FIRST_WAIT, help="撮り始めるまでの秒")
    ap.add_argument("--keep", action="store_true", help="作業フォルダを残す")
    a = ap.parse_args()
    if not a.env:
        sys.exit("[title_shot] --env か PAK256_GAME_ENV で検証環境を渡す")
    try:
        title_shot(a.env, a.out, a.work, zip_path=a.zip, screensize=a.screensize, wait=a.wait, keep=a.keep)
    except (RuntimeError, OSError) as e:
        sys.exit(f"[title_shot] {e}")
    print(f"[title_shot] {a.out}")


if __name__ == "__main__":
    main()
