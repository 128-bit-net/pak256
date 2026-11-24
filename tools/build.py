"""objects/ の物を dat にして、makeobj で pak に組む（docs/layout.md の「組み方」）。

物のフォルダ（objects/ の下で、.yaml か .dat を直に持つフォルダ）ごとに:
1. build/dat/<物のフォルダ>/ に、PNG を写し、.yaml を dat にし（tools/datgen.py）、手で書いた .dat を写す。
2. `makeobj pak256 build/pak/<種類>.<物>.pak build/dat/<物のフォルダ>/` で組む。
   256 より大きいセルに描いた物は、表に cell_size を書く（makeobj が物ごとに読む）。
3. makeobj が警告（Warning）か誤り（ERROR）を出したら、止める。

AMI の 256 版は tools/fetch_ami.py で build/pak/ に入れる（AMI_DIST か vendor/ami/ami.env。無ければ入れない）。

使い方（リポジトリのどこからでも）:
    python -X utf8 tools/build.py            全部の物を組む
    python -X utf8 tools/build.py --no-ami   AMI を入れない
"""
import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datgen  # noqa: E402
import fetch_ami  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBJECTS = os.path.join(ROOT, "objects")
BUILD = os.path.join(ROOT, "build")
DAT_OUT = os.path.join(BUILD, "dat")
PAK_OUT = os.path.join(BUILD, "pak")
CELL = 256  # 自前の物の既定のセル（1 タイル）。docs/layout.md の「セルの大きさ」
MAKEOBJ = os.environ.get("MAKEOBJ", "makeobj")


def object_dirs():
    """objects/ の下の、物のフォルダ（.yaml か .dat を直に持つ）を並べる。"""
    found = []
    for dirpath, dirnames, filenames in os.walk(OBJECTS):
        dirnames.sort()
        if any(f.endswith((".yaml", ".dat")) for f in filenames):
            found.append(dirpath)
    return found


def stage(src):
    """物のフォルダを build/dat/ に写し、写した先を返す。"""
    rel = os.path.relpath(src, OBJECTS)
    dst = os.path.join(DAT_OUT, rel)
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        path = os.path.join(src, name)
        if name.endswith((".png", ".dat")):
            shutil.copyfile(path, os.path.join(dst, name))
        elif name.endswith(".yaml"):
            text = datgen.yaml_to_dat(path)
            out = os.path.join(dst, name[: -len(".yaml")] + ".dat")
            if os.path.exists(out):
                raise datgen.DatError(f"{rel}: {name} と同じ名前の .dat がある")
            with open(out, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
    return rel, dst


def makeobj(rel, dat_dir):
    pak = os.path.join(PAK_OUT, rel.replace(os.sep, ".").replace("/", ".") + ".pak")
    # 相対のパスで渡す（makeobj の出力に手元の絶対パスを出さないため）
    args = [MAKEOBJ, f"pak{CELL}", os.path.relpath(pak, ROOT), os.path.relpath(dat_dir, ROOT).replace(os.sep, "/") + "/"]
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, errors="replace")
    out = (r.stdout + r.stderr).strip()
    bad = [ln for ln in out.splitlines() if ln.startswith(("Warning", "ERROR"))]
    print(f"[build] {rel} → {os.path.relpath(pak, ROOT)}")
    if out:
        print("\n".join("    " + ln for ln in out.splitlines()))
    if r.returncode != 0 or bad:
        sys.exit(f"[build] makeobj が警告か誤りを出した: {rel}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-ami", action="store_true", help="AMI を入れない")
    a = ap.parse_args()

    for d in (DAT_OUT, PAK_OUT):
        shutil.rmtree(d, ignore_errors=True)
    lic = os.path.join(BUILD, fetch_ami.LICENSE_NAME)
    if os.path.exists(lic):
        os.remove(lic)
    os.makedirs(PAK_OUT)
    dirs = object_dirs()
    try:
        staged = [stage(d) for d in dirs]
    except datgen.DatError as e:
        sys.exit(f"[build] {e}")
    for rel, dst in staged:
        makeobj(rel, dst)
    print(f"[build] 自前の物 {len(staged)} 個のフォルダを組んだ")

    if a.no_ami:
        return
    paks = fetch_ami.fetch(PAK_OUT)
    print(f"[build] AMI の pak を {len(paks)} 個入れた" if paks else "[build] AMI の取り方が無いので入れない（AMI_DIST か vendor/ami/ami.env）")


if __name__ == "__main__":
    main()
