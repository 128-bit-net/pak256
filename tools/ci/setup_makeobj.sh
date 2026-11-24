#!/usr/bin/env bash
# CI の Linux に makeobj を用意する（本家のリリースの配布物を取る）。
#   bash tools/ci/setup_makeobj.sh <本家のリリースのタグ> <置き場所>
# <置き場所>/makeobj があれば何もしない（キャッシュから戻したとき）。gh を使う。CI では GH_TOKEN が要る。
set -euo pipefail

tag="${1:?本家のリリースのタグが要る}"
dest="${2:?置き場所が要る}"

if [ -x "$dest/makeobj" ]; then
  echo "[setup_makeobj] $tag: 用意済みのものを使う（$dest/makeobj）"
  exit 0
fi
mkdir -p "$dest"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

gh release download "$tag" -R simutrans/simutrans -p 'makeobj_linux-x64*.zip' -D "$work"
unzip -q "$work"/makeobj_linux-x64*.zip -d "$work/unzip"
bin="$(find "$work/unzip" -type f -name makeobj | head -1)"
[ -n "$bin" ] || { echo "[setup_makeobj] zip に makeobj が無い" >&2; exit 1; }
install -m 755 "$bin" "$dest/makeobj"
echo "[setup_makeobj] $tag: $dest/makeobj"
"$dest/makeobj" 2>&1 | head -1 || true
