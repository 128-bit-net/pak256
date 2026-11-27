"""手元で組んだ pak（または配布の zip）を、テストプレイのフォルダの pak256/ に入れる道具（#38）。MIT License。

テストプレイのフォルダの形（本体の実行ファイルの横に pak256/ を置く）:
    <dest>/sim-WinGDI64-OTRPv64.exe
    <dest>/pak256/          この道具が入れる（*.pak・config/・text/・sound/・demo.sve・VERSION。VERSION は入れた物の版の名前）
    <dest>/play.bat         無ければ作る（-singleuser -objects pak256/ -sound を付けて起動する）。既にあれば触らず、足りなければ注意を出す
    <dest>/save/ settings.xml ...   触らない

使い方:
    python -X utf8 tools/install_local.py <dest> --build   # build.py で組んでから、build/pak/ と config/・text/・sound/ を入れる
    python -X utf8 tools/install_local.py <dest>       # 組み済みの build/pak/ を入れる（--build が無いとき）
    python -X utf8 tools/install_local.py <dest> --zip pak256-v0.1.0.zip   # 配布の zip（Release の物を含む）を入れる

入れ替えのとき、pak256/ の中の古い *.pak・config/・text/・sound/・demo.sve・VERSION は消す（pak256/ のほかの物と、pak256/ の外は消さない）。
配布用の許諾の文の検査は通さない（ゲームで試すだけで、配るわけではないため）。ゲームは起動しない。
"""
import argparse
import os
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import game  # noqa: E402

PAK_FOLDER = "pak256"
PLAY_BAT = "play.bat"


def play_bat_text(exe=game.EXE):
    return ("@echo off\r\n"
            'cd /d "%~dp0"\r\n'
            f'start "" "{exe}" -singleuser -objects {PAK_FOLDER}/ -sound\r\n')  # -sound が無いと本体は効果音を消音で始める


def version_name(zip_path=None, root=game.ROOT):
    """入れた物の版の名前。zip は zip-<ファイル名>、手元で組んだ物は local-<短いコミット>（作業ツリーに変更があれば -dirty）。"""
    if zip_path:
        return "zip-" + os.path.splitext(os.path.basename(zip_path))[0]
    try:
        def git(*a):
            return subprocess.run(["git", "-C", root, *a], capture_output=True, check=True).stdout.decode().strip()
        rev = git("rev-parse", "--short", "HEAD")
        dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
        return "local-" + rev + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "local"


def check_dest(dest, exe=game.EXE, root=game.ROOT):
    """dest がテストプレイのフォルダ（本体の実行ファイルがある）か、リポジトリの外かを確かめる。"""
    if not os.path.isdir(dest):
        raise RuntimeError(f"入れ先のフォルダが無い: {dest}")
    if not os.path.isfile(os.path.join(dest, exe)):
        raise RuntimeError(f"入れ先に {exe} が無い（本体のフォルダを渡す）: {dest}")
    r = os.path.normcase(os.path.realpath(root))
    for target in (dest, os.path.join(dest, PAK_FOLDER)):
        t = os.path.normcase(os.path.realpath(target))  # pak256/ がリンクで、リポジトリの中を指していても止める
        if t == r or t.startswith(r + os.sep):
            raise RuntimeError(f"入れ先がこのリポジトリの中: {target}")


def install_local(dest, zip_path=None, build=None, root=game.ROOT, exe=game.EXE, make_bat=True):
    """dest/pak256/ に入れて、入れた相対パスの一覧を返す。dest の save/・settings.xml などには触らない。"""
    check_dest(dest, exe, root)
    placed = game.install_pak(os.path.join(dest, PAK_FOLDER), root=root, build=build, zip_path=zip_path, clean=True)
    version = version_name(zip_path, root)
    with open(os.path.join(dest, PAK_FOLDER, game.VERSION_FILE), "w", encoding="utf-8", newline="") as f:
        f.write(version + "\n")
    placed.append(game.VERSION_FILE)
    bat = os.path.join(dest, PLAY_BAT)
    if make_bat and not os.path.exists(bat):
        with open(bat, "w", encoding="ascii", newline="") as f:
            f.write(play_bat_text(exe))
        print(f"[install_local] {PLAY_BAT} を作った")
    elif os.path.isfile(bat):
        with open(bat, encoding="utf-8", errors="replace") as f:
            text = f.read()
        if f"-objects {PAK_FOLDER}/" not in text:
            print(f"[install_local] 注意: 既存の {PLAY_BAT} に -objects {PAK_FOLDER}/ が無い（触らない）")
        if "-sound" not in text.split():
            print(f"[install_local] 注意: 既存の {PLAY_BAT} に -sound が無く、効果音が消音で始まる（触らない）")
    return placed


def main():
    ap = argparse.ArgumentParser(description="pak をテストプレイのフォルダの pak256/ に入れる（#38）")
    ap.add_argument("dest", help="本体の実行ファイルがあるフォルダ（テストプレイのフォルダ）")
    ap.add_argument("--zip", help="配布の zip（Release の物を含む）。無ければ手元で組んだ build/pak/ を入れる")
    ap.add_argument("--build-dir", help="手元で組んだ pak の置き場（既定は <リポジトリ>/build）")
    ap.add_argument("--build", action="store_true", help="入れる前に tools/build.py を流す（zip のときは使えない）")
    ap.add_argument("--no-play-bat", action="store_true", help="play.bat を作らない")
    a = ap.parse_args()
    if a.build and (a.zip or a.build_dir):
        sys.exit("[install_local] --build は --zip・--build-dir と同時に使えない（build.py は <リポジトリ>/build に組む）")
    try:
        check_dest(a.dest)  # 時間のかかる build の前に、入れ先を確かめる
        if a.build:
            subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "build.py")], check=True)
        placed = install_local(a.dest, a.zip, a.build_dir, make_bat=not a.no_play_bat)
    except subprocess.CalledProcessError as e:
        sys.exit(f"[install_local] build.py が失敗した（終了コード {e.returncode}）")
    except (RuntimeError, OSError, zipfile.BadZipFile) as e:
        sys.exit(f"[install_local] {e}")
    print(f"[install_local] {os.path.join(a.dest, PAK_FOLDER)} に {len(placed)} ファイルを入れた")
    for rel in placed:
        print("    " + rel)


if __name__ == "__main__":
    main()
