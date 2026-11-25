"""同梱する AMI の 256 版の pak を取ってくる（docs/layout.md の「AMI の 256 版を同梱する」）。

取り方は 2 つ。上が優先。
1. 環境変数 AMI_DIST: 手元で組んだ AMI の pak のフォルダか、AMI の配る zip の場所。
   手元で組んだ pak を試すときに使う（ami.env より優先）。
2. vendor/ami/ami.env の AMI_ZIP_URL: Release の zip。AMI_ZIP_SHA256 と合うときだけ使う。
   GitHub の Release の URL（https://github.com/<owner>/<repo>/releases/download/<タグ>/<ファイル>）は
   gh で取る（pak256 の非公開の Release に置いた zip も取れる。CI は GH_TOKEN に GITHUB_TOKEN、手元は gh のログイン）。
   それ以外の URL は urllib で取る。

どちらも無いときは何もしない（AMI 抜きで組む）。

取った pak は <出力>/ に置く。pak を 1 つでも置いたら、AMI の許諾の文 vendor/ami/ami_license.txt を
<出力>/../ami_license.txt に写す（CC BY 4.0 の表示。配布の zip に入れる）。

使い方:
    python -X utf8 tools/fetch_ami.py <出力のフォルダ>
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "vendor", "ami")
ENV_FILE = os.path.join(VENDOR, "ami.env")
LICENSE_NAME = "ami_license.txt"
LICENSE_FILE = os.path.join(VENDOR, LICENSE_NAME)
CACHE = os.path.join(ROOT, "build", "cache")
RELEASE_URL_RE = re.compile(r"^https://github\.com/([^/\s]+/[^/\s]+)/releases/download/([^/\s]+)/([^/\s]+)$")


def read_env(path=None):
    """ami.env を読む。path を省くと、呼ぶ時点の ENV_FILE を読む。"""
    if path is None:
        path = ENV_FILE
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def _rel(path):
    """ROOT からの相対パス。別のドライブなどで出せないときは、そのパスのまま返す。"""
    try:
        return os.path.relpath(path, ROOT)
    except ValueError:
        return path


def _is_pak(name):
    return name.lower().endswith(".pak")


def _from_zip(data, out_dir):
    paks = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            base = os.path.basename(info.filename)
            if not _is_pak(base):
                continue
            target = os.path.join(out_dir, base)
            with z.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            paks.append(target)
    return paks


def _from_dir(src, out_dir):
    paks = []
    for name in sorted(os.listdir(src)):
        if _is_pak(name):
            target = os.path.join(out_dir, name)
            shutil.copyfile(os.path.join(src, name), target)
            paks.append(target)
    return paks


def _gh_download(repo, tag, name):
    """gh で Release の asset を取る（非公開のリポジトリでも、gh のログインか GH_TOKEN で取れる）。"""
    with tempfile.TemporaryDirectory() as d:
        cmd = ["gh", "release", "download", tag, "-R", repo, "-p", name, "-D", d]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=600)
        except FileNotFoundError:
            sys.exit("[fetch_ami] gh が無い（GitHub CLI を入れて gh auth login する。CI は GH_TOKEN を渡す）")
        except subprocess.TimeoutExpired:
            sys.exit(f"[fetch_ami] gh release download が 600 秒で終わらない: {repo} {tag}")
        if r.returncode != 0:
            sys.exit(f"[fetch_ami] gh release download が失敗（{repo} {tag} {name}）: {r.stderr.decode(errors='replace').strip()}")
        path = os.path.join(d, name)
        if not os.path.isfile(path):
            sys.exit(f"[fetch_ami] gh release download の後に {name} が無い")
        with open(path, "rb") as f:
            return f.read()


def _fetch_bytes(url):
    m = RELEASE_URL_RE.match(url)
    if m:
        return _gh_download(*m.groups())
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read()


def _download(url, sha256, version):
    os.makedirs(CACHE, exist_ok=True)
    cached = os.path.join(CACHE, f"{version or 'ami'}.zip")  # version は Release のタグ（ami-256-alpha.1 など）
    if os.path.isfile(cached):
        with open(cached, "rb") as f:
            data = f.read()
    else:
        data = _fetch_bytes(url)
    got = hashlib.sha256(data).hexdigest()
    if got.lower() != sha256.lower():
        if os.path.isfile(cached):
            os.remove(cached)  # 次は取り直す
        sys.exit(f"[fetch_ami] SHA-256 が合わない: {url}（期待 {sha256}、実際 {got}）")
    if not os.path.isfile(cached):
        with open(cached, "wb") as f:
            f.write(data)
    return data


def fetch(out_dir):
    """AMI の pak を out_dir に置き、置いた pak の一覧を返す。取り方が無ければ空の一覧。"""
    out_dir = os.path.normpath(os.path.abspath(out_dir))
    os.makedirs(out_dir, exist_ok=True)
    local = os.environ.get("AMI_DIST")
    if local:
        where = f"AMI_DIST（{local}）"
        if os.path.isdir(local):
            paks = _from_dir(local, out_dir)
        elif os.path.isfile(local) and local.lower().endswith(".zip"):
            with open(local, "rb") as f:
                paks = _from_zip(f.read(), out_dir)
        else:
            sys.exit(f"[fetch_ami] AMI_DIST がフォルダでも zip でもない: {local}")
    else:
        env = read_env()
        url = env.get("AMI_ZIP_URL", "")
        if not url:
            return []
        sha = env.get("AMI_ZIP_SHA256", "")
        if not sha:
            sys.exit("[fetch_ami] ami.env に AMI_ZIP_SHA256 が無い")
        where = url
        paks = _from_zip(_download(url, sha, env.get("AMI_VERSION", "")), out_dir)
    if not paks:
        sys.exit(f"[fetch_ami] {where} に pak が無い")
    if not os.path.isfile(LICENSE_FILE):
        sys.exit(f"[fetch_ami] AMI の許諾の文 {_rel(LICENSE_FILE)} が無い")
    shutil.copyfile(LICENSE_FILE, os.path.join(os.path.dirname(out_dir), LICENSE_NAME))
    return paks


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    paks = fetch(sys.argv[1])
    print(f"[fetch_ami] {len(paks)} 個の pak を置いた" if paks else "[fetch_ami] AMI の取り方が無いので入れない")


if __name__ == "__main__":
    main()
