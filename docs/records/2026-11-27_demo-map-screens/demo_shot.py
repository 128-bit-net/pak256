"""保存データの無い環境を配布の zip から作り、-load を付けずに起動して、起動の窓の後ろの地図を撮る。MIT License。

検証環境からは実行ファイル・DLL・config/ などだけを写す（save/ と settings.xml は写さない）。MCP は使わない
（起動の窓が出ている間は答えない）。起動した PID は Job Object に入れ、撮ったら閉じる。

使い方（リポジトリの直下から）:
    python -X utf8 docs/records/2026-11-27_demo-map-screens/demo_shot.py <検証環境> <配布の zip> <作業フォルダ> <出力の PNG>
"""
import glob
import os
import shutil
import subprocess
import sys
import time

from PIL import Image

sys.path.insert(0, "tools")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import game  # noqa: E402
import wincap  # noqa: E402

env, zip_path, work, out = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3]), sys.argv[4]
if os.path.exists(work):
    sys.exit(f"作業フォルダが既にある: {work}")
os.makedirs(work)
shutil.copyfile(os.path.join(env, game.EXE), os.path.join(work, game.EXE))
for dll in glob.glob(os.path.join(env, "*.dll")):
    shutil.copyfile(dll, os.path.join(work, os.path.basename(dll)))
for d in game.ENV_DIRS:
    if os.path.isdir(os.path.join(env, d)):
        shutil.copytree(os.path.join(env, d), os.path.join(work, d))
game.install_pak(os.path.join(work, "pak256"), zip_path=zip_path)
cmd = [os.path.join(work, game.EXE), "-singleuser", "-set_workdir", work, "-objects", "pak256/", "-lang", "ja",
       "-mute", "-screensize", game.SCREENSIZE, "-log", "-debug", "3"]
job = game.JobObject()
with open(os.path.join(work, "game.log"), "wb") as log:
    proc = subprocess.Popen(cmd, cwd=work, stdout=log, stderr=subprocess.STDOUT)
job.assign(proc)
print("pid", proc.pid, flush=True)
try:
    time.sleep(30)
    # 描き直しの前に読むと真っ黒になることがあるので、黒でなくなるまで撮り直す
    for i in range(12):
        if proc.poll() is not None:
            sys.exit(f"ゲームが終わった（終了コード {proc.returncode}）")
        wincap.capture(proc.pid, out)
        with Image.open(out) as im:
            if im.getbbox():
                break
        print("黒い画面。撮り直す", flush=True)
        time.sleep(5)
    else:
        sys.exit("撮った画面が黒いまま")
finally:
    proc.kill()
    proc.wait(timeout=15)
    job.close()
    print("残り" if game.alive(proc.pid) else "閉じた", flush=True)
