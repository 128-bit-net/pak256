"""build/ の pak と、config/・text/・許諾の文を、配布の zip にまとめる（docs/layout.md の「配布の zip」）。

zip の中身（先頭のフォルダ名は pak256。本体の pak のフォルダにそのまま置ける）:
    pak256/*.pak              build/pak/ の pak（自前の物と、あれば AMI）
    pak256/config/            config/ の中身（.gitkeep は除く）
    pak256/text/              text/ の中身（同上）
    pak256/demo.sve           demo/demo.sve（保存データが無いときに本体が読む初期マップ。docs/layout.md の「初期マップ」）
    pak256/LICENSE.md
    pak256/LICENSES/          許諾の本文（CC BY-SA 4.0・MIT）
    pak256/CREDITS.md
    pak256/ami_license.txt    AMI の pak を入れたときだけ（build/ami_license.txt）

先に tools/build.py を流しておく。pak が 1 つも無ければ止まる。
AMI の許諾の文は、fetch_ami.py が AMI の pak を置いたときだけ build/ に置く（置けなければそこで止まる）。

使い方:
    python -X utf8 tools/package.py <版の名前>     例: v0.1.0。dist/pak256-<版の名前>.zip を作る
"""
import glob
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")
TOP = "pak256"
SKIP = {".gitkeep"}
DEMO = "demo.sve"  # 本体が pak のフォルダから読む初期マップの名前。元はリポジトリの demo/demo.sve
FIXED_TIME = (2026, 1, 1, 0, 0, 0)  # 同じ中身なら同じ zip になるように


def collect_runtime(root=ROOT, build=BUILD):
    """(zip の中の名前, 元のファイル) のうち、ゲームが読む物（pak・config・text・初期マップ）だけ。許諾の文の検査はしない。

    配布の zip（collect）も、ゲームに入れる道具（game.install_pak・install_local.py。#38）も、ここから取る。
    pak が 1 つも無ければ止まる。
    """
    files = []
    paks = sorted(glob.glob(os.path.join(build, "pak", "*.pak")))
    if not paks:
        sys.exit("[package] build/pak/ に pak が無い（先に tools/build.py を流す）")
    for p in paks:
        files.append((f"{TOP}/{os.path.basename(p)}", p))
    files += collect_settings(root)
    demo = os.path.join(root, "demo", DEMO)
    if os.path.isfile(demo):
        files.append((f"{TOP}/{DEMO}", demo))
    return files


def collect_settings(root):
    """(zip の中の名前, 元のファイル) のうち、root の config/ と text/ の物。"""
    files = []
    for sub in ("config", "text"):
        base = os.path.join(root, sub)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames.sort()
            for name in sorted(filenames):
                if name in SKIP:
                    continue
                path = os.path.join(dirpath, name)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                files.append((f"{TOP}/{rel}", path))
    return files


def collect(root=ROOT, build=BUILD):
    """配布の zip に入れる (zip の中の名前, 元のファイル) の一覧を返す。許諾の文の検査を含む。"""
    files = collect_runtime(root, build)
    if f"{TOP}/{DEMO}" not in (arc for arc, _ in files):  # 配布物から黙って抜けないように
        sys.exit(f"[package] demo/{DEMO} が無い")
    for name in ("LICENSE.md", "CREDITS.md"):
        files.append((f"{TOP}/{name}", os.path.join(root, name)))
    # LICENSE.md が相対リンクで引く許諾の本文。zip の中でリンクが切れないように入れる
    for name in sorted(os.listdir(os.path.join(root, "LICENSES"))):
        files.append((f"{TOP}/LICENSES/{name}", os.path.join(root, "LICENSES", name)))
    # build.py が AMI の pak を入れたときだけ、fetch_ami.py がこの許諾の文を置く（build.py は毎回消してから組む）
    lic = os.path.join(build, "ami_license.txt")
    if os.path.isfile(lic):
        # AMI は CC BY 4.0。LICENSE.md の例外と CREDITS.md の行（#7）が先に要る
        for name, word in (("LICENSE.md", "CC BY 4.0"), ("CREDITS.md", "AMI")):
            with open(os.path.join(root, name), encoding="utf-8") as f:
                if word not in f.read():
                    sys.exit(f"[package] AMI を同梱するのに {name} に「{word}」が無い（#7 で書く）")
        files.append((f"{TOP}/ami_license.txt", lic))
    return files


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    version = sys.argv[1]
    if not re.fullmatch(r"[A-Za-z0-9._-]+", version):
        sys.exit(f"[package] 版の名前に使えない文字がある: {version}")
    files = collect()
    os.makedirs(DIST, exist_ok=True)
    out = os.path.join(DIST, f"pak256-{version}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, path in files:
            info = zipfile.ZipInfo(arc, FIXED_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            with open(path, "rb") as f:
                z.writestr(info, f.read())
    print(f"[package] {os.path.relpath(out, ROOT)}（{len(files)} ファイル）")
    for arc, _ in files:
        print("    " + arc)


if __name__ == "__main__":
    main()
