"""手元で組んだ pak（または配布の zip）を、テストプレイのフォルダの pak256/ に入れる道具（#38）。MIT License。

テストプレイのフォルダの形（本体の実行ファイルの横に pak256/ を置く）:
    <dest>/sim-WinGDI64-OTRPv64.exe
    <dest>/pak256/          この道具が入れる（*.pak・config/・text/）
    <dest>/play.bat         無ければ作る（-singleuser -objects pak256/ を付けて起動する）
    <dest>/save/ settings.xml ...   触らない

使い方:
    python -X utf8 tools/build.py                      # 先に組む
    python -X utf8 tools/install_local.py <dest>       # 手元で組んだ build/pak/ と config/・text/ を入れる
    python -X utf8 tools/install_local.py <dest> --zip pak256-v0.1.0.zip   # 配布の zip（Release の物を含む）を入れる

入れ替えのとき、pak256/ の中の古い *.pak・config/・text/ は消す（pak256/ のほかの物と、pak256/ の外は消さない）。
配布用の許諾の文の検査は通さない（ゲームで試すだけで、配るわけではないため）。ゲームは起動しない。
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import game  # noqa: E402

PAK_FOLDER = "pak256"
PLAY_BAT = "play.bat"


def play_bat_text(exe=game.EXE):
    return ("@echo off\r\n"
            'cd /d "%~dp0"\r\n'
            f'start "" "{exe}" -singleuser -objects {PAK_FOLDER}/\r\n')


def check_dest(dest, exe=game.EXE, root=game.ROOT):
    """dest がテストプレイのフォルダ（本体の実行ファイルがある）か、リポジトリの外かを確かめる。"""
    if not os.path.isdir(dest):
        raise RuntimeError(f"入れ先のフォルダが無い: {dest}")
    if not os.path.isfile(os.path.join(dest, exe)):
        raise RuntimeError(f"入れ先に {exe} が無い（本体のフォルダを渡す）: {dest}")
    d, r = os.path.normcase(os.path.realpath(dest)), os.path.normcase(os.path.realpath(root))
    if d == r or d.startswith(r + os.sep):
        raise RuntimeError(f"入れ先がこのリポジトリの中: {dest}")


def install_local(dest, zip_path=None, build=None, root=game.ROOT, exe=game.EXE, make_bat=True):
    """dest/pak256/ に入れて、入れた相対パスの一覧を返す。dest の save/・settings.xml などには触らない。"""
    check_dest(dest, exe, root)
    placed = game.install_pak(os.path.join(dest, PAK_FOLDER), root=root, build=build, zip_path=zip_path, clean=True)
    bat = os.path.join(dest, PLAY_BAT)
    if make_bat and not os.path.exists(bat):
        with open(bat, "w", encoding="ascii", newline="") as f:
            f.write(play_bat_text(exe))
        print(f"[install_local] {PLAY_BAT} を作った")
    elif os.path.isfile(bat):
        with open(bat, encoding="utf-8", errors="replace") as f:
            if f"-objects {PAK_FOLDER}/" not in f.read():
                print(f"[install_local] 注意: 既存の {PLAY_BAT} に -objects {PAK_FOLDER}/ が無い（触らない）")
    return placed


def main():
    ap = argparse.ArgumentParser(description="pak をテストプレイのフォルダの pak256/ に入れる（#38）")
    ap.add_argument("dest", help="本体の実行ファイルがあるフォルダ（テストプレイのフォルダ）")
    ap.add_argument("--zip", help="配布の zip（Release の物を含む）。無ければ手元で組んだ build/pak/ を入れる")
    ap.add_argument("--build-dir", help="手元で組んだ pak の置き場（既定は <リポジトリ>/build）")
    ap.add_argument("--no-play-bat", action="store_true", help="play.bat を作らない")
    a = ap.parse_args()
    try:
        placed = install_local(a.dest, a.zip, a.build_dir, make_bat=not a.no_play_bat)
    except RuntimeError as e:
        sys.exit(f"[install_local] {e}")
    print(f"[install_local] {os.path.join(a.dest, PAK_FOLDER)} に {len(placed)} ファイルを入れた")
    for rel in placed:
        print("    " + rel)


if __name__ == "__main__":
    main()
