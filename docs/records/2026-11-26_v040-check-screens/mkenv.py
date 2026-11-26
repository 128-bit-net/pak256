"""検証環境の写し（本体と保存データ 1 つ）を作る。検証環境には書かない。MIT License。
使い方: python -X utf8 docs/records/2026-11-26_v040-check-screens/mkenv.py <検証環境> <保存データ> <作る場所>"""
import glob
import os
import shutil
import sys

env, sve, out = sys.argv[1:4]
exe = "sim-WinGDI64-OTRPv64.exe"
os.makedirs(os.path.join(out, "save"), exist_ok=True)
shutil.copyfile(os.path.join(env, exe), os.path.join(out, exe))
for d in glob.glob(os.path.join(env, "*.dll")):
    shutil.copyfile(d, os.path.join(out, os.path.basename(d)))
for d in ("config", "font", "themes", "text", "script", "music"):
    if os.path.isdir(os.path.join(env, d)):
        shutil.copytree(os.path.join(env, d), os.path.join(out, d), dirs_exist_ok=True)
shutil.copyfile(sve, os.path.join(out, "save", os.path.basename(sve)))
print(os.listdir(os.path.join(out, "save")))
