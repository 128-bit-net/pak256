"""同梱する AMI の 256 版の pak を取ってくる（docs/layout.md の「AMI の 256 版を同梱する」）。

取り方は 2 つ。上が優先。
1. 環境変数 AMI_DIST: 手元で組んだ AMI の pak のフォルダか、AMI の配る zip の場所。
   AMI が 256 版を Release に上げるまでは、これで渡す。
2. vendor/ami/ami.env の AMI_ZIP_URL: AMI の Release の zip。AMI_ZIP_SHA256 と合うときだけ使う。

どちらも無いときは何もしない（AMI 抜きで組む）。

取った pak は <出力>/ に、AMI の許諾の文（zip の ami_license.txt）は <出力>/../ami_license.txt に置く。

使い方:
    python -X utf8 tools/fetch_ami.py <出力のフォルダ>
"""
import hashlib
import io
import os
import shutil
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(ROOT, "vendor", "ami", "ami.env")
CACHE = os.path.join(ROOT, "build", "cache")
LICENSE_NAME = "ami_license.txt"


def read_env(path=ENV_FILE):
    env = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    return env


def _from_zip(data, out_dir):
    paks = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            base = os.path.basename(info.filename)
            if base.endswith(".pak"):
                target = os.path.join(out_dir, base)
            elif base == LICENSE_NAME:
                target = os.path.join(os.path.dirname(out_dir), LICENSE_NAME)
            else:
                continue
            with z.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            if base.endswith(".pak"):
                paks.append(target)
    return paks


def _from_dir(src, out_dir):
    paks = []
    for name in sorted(os.listdir(src)):
        if name.endswith(".pak"):
            target = os.path.join(out_dir, name)
            shutil.copyfile(os.path.join(src, name), target)
            paks.append(target)
    return paks


def _download(url, sha256, version):
    os.makedirs(CACHE, exist_ok=True)
    cached = os.path.join(CACHE, f"ami-{version or 'x'}.zip")
    if os.path.isfile(cached):
        with open(cached, "rb") as f:
            data = f.read()
    else:
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
    got = hashlib.sha256(data).hexdigest()
    if got.lower() != sha256.lower():
        sys.exit(f"[fetch_ami] SHA-256 が合わない: {url}（期待 {sha256}、実際 {got}）")
    if not os.path.isfile(cached):
        with open(cached, "wb") as f:
            f.write(data)
    return data


def fetch(out_dir):
    """AMI の pak を out_dir に置き、置いた pak の一覧を返す。取り方が無ければ空の一覧。"""
    os.makedirs(out_dir, exist_ok=True)
    local = os.environ.get("AMI_DIST")
    if local:
        if os.path.isdir(local):
            paks = _from_dir(local, out_dir)
        elif os.path.isfile(local) and local.endswith(".zip"):
            with open(local, "rb") as f:
                paks = _from_zip(f.read(), out_dir)
        else:
            sys.exit(f"[fetch_ami] AMI_DIST がフォルダでも zip でもない: {local}")
        if not paks:
            sys.exit(f"[fetch_ami] AMI_DIST に pak が無い: {local}")
        return paks
    env = read_env()
    url = env.get("AMI_ZIP_URL", "")
    if not url:
        return []
    sha = env.get("AMI_ZIP_SHA256", "")
    if not sha:
        sys.exit("[fetch_ami] ami.env に AMI_ZIP_SHA256 が無い")
    return _from_zip(_download(url, sha, env.get("AMI_VERSION", "")), out_dir)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    paks = fetch(sys.argv[1])
    print(f"[fetch_ami] {len(paks)} 個の pak を置いた" if paks else "[fetch_ami] AMI の取り方が無いので入れない")


if __name__ == "__main__":
    main()
