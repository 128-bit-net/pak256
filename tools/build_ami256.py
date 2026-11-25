"""AMI の 256 版の zip を、AMI のリポジトリの一時の worktree で組み、pak256 の置き場に上げる（docs/layout.md の「AMI の 256 版を組む」）。

AMI（128na/simutrans-addon-dev の addons/ami）は 128 用で、256 は pak256 で引き受ける（2026-11-25、ユーザー。roadmap の「進め方」）。
AMI の描く道具には 256 の倍率（SHEET_PAK_SIZE=256。AMI #261・#266）があるので、それをそのまま使う。AMI のリポジトリには何も書かない
（コミット・push・ブランチの切り替えをしない）。手元の clone に、組む間だけ detached の worktree を足し、終わったら消す。

build: vendor/ami/build.env の AMI_COMMIT（--ref で一度だけ別のコミット）から組む。
    1. git fetch origin → worktree を build/ami256/<SHA の頭 12 桁>/ に作る（AMI の道具は直さずに使う。256 だけのための直しも
       AMI の側で起票して直す。docs/layout.md の「AMI の側との分担」）
    2. dat    SHEET_PAK_SIZE=256 で blender/ami_dat.py（src256/ の dat。コミット済みの dat と違えば知らせる）
    3. render ../../tools/blender/render_parallel.py で catalog.SCALED_TARGETS を描く。先に描いた物の絵を読む物（踏切のシート・
              跨座式のトンネル）は、2 回目にまとめて描く（AMI README の「pak の大きさ」の描く順序）
    4. icons  blender/icons.py を全部のシートに（render.py は描いたシートの分しか書かない。試しでは飛ばす）
    5. check  AMI の check.sh の 256 の検査（check_scaled・check_icons・check_cells・check_crossing・check_depot・check_embankment・
              dat_lint_extra・dat_linter の src256）
    6. build  build.py（dist256/ に pak。makeobj の警告で止まる）
    7. release release.py --version <版> --paks <PAKS>（work/release/ami-256-<版>.zip）
    8. dist/ami-256-<版>.zip と、組んだ元を書いた dist/ami-256-<版>.json に写す
    --only <対象 ...> は試し: その対象だけを描き、絵のある物だけを組む（BUILD_SKIP_MISSING=1）。置き場には上げられない。
    止まったら worktree を残すので、直してから --resume --from <段> で続ける（済んだ段は worktree の隣の .steps.json に控える）。
    zip の隣の .json に、組んだ元のコミット・済んだ段・AMI の追跡ファイルの変更・Blender と makeobj の版を書く。
compare: 2 つの zip の pak の名前・大きさ・物（makeobj list）を比べる。
upload: dist/ami-256-<版>.zip を pak256 の非公開の Release（タグ vendor-ami-256-<版>、プレリリース）に上げ、vendor/ami/ami.env を書き換える。

使い方（リポジトリのどこからでも）:
    python -X utf8 tools/build_ami256.py build --version alpha.4
    python -X utf8 tools/build_ami256.py build --version try --only ami_road_local
    python -X utf8 tools/build_ami256.py compare dist/ami-256-alpha.4.zip build/cache/ami-256-alpha.3.zip
    python -X utf8 tools/build_ami256.py upload --version alpha.4 [--dry-run]
AMI の clone は --ami-repo か環境変数 AMI_REPO（既定は pak256 の本体の checkout の隣の simutrans-addon-dev）。
Blender は環境変数 SHEET_BLENDER か --blender（既定は AMI の sheet_settings と同じ D:\\bin\\blender\\blender.exe）。makeobj は PATH のもの。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_ami  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENDOR = os.path.join(ROOT, "vendor", "ami")
BUILD_ENV = os.path.join(VENDOR, "build.env")
WORK = os.path.join(ROOT, "build", "ami256")
DIST = os.path.join(ROOT, "dist")
RELEASE_REPO = "128-bit-net/pak256"
# 同梱する pak（alpha.2・alpha.3 と同じ 7 つ。旧描画位置の ami_rail_old と全部入りの ami は入れない）
PAKS = ("ami_rail", "ami_road", "ami_tram", "ami_extra", "ami_monorail", "ami_canal", "ami_scenery")
STEPS = ("dat", "render", "icons", "check", "build", "release")
# 子に渡さない環境変数（残っていると、絵の無い物を黙って飛ばしたり、別のモードで描いたりする）
SCRUB = ("BUILD_SKIP_MISSING", "CHECK_SKIP_MISSING", "CHECK_256_FULL", "SHEET_LAYOUT", "SHEET_ONLY", "AMI_ROUND", "AMI_FAMILY", "AMI_SURFACE")
# AMI の check.sh の 256 の検査（CHECK_256_FULL=1 の分）。アドオンのディレクトリからの相対で流す
CHECKS_FULL = (
    ("check_scaled.py",), ("check_icons.py",), ("check_cells.py", "--self-test"), ("check_cells.py",),
    ("check_crossing.py",), ("check_depot.py",), ("check_embankment.py",),
    ("../../tools/dat_lint_extra/dat_lint_extra.py", "--self-test"), ("../../tools/dat_lint_extra/dat_lint_extra.py", "src256"),
)
CHECKS_PARTIAL = (("check_icons.py",), ("check_cells.py",))
# dat_linter（AMI の check.sh が ci.env の版を TOOLS_DIR に取る）の場所。環境変数 DAT_LINTER_BIN → PATH → check.sh の既定の置き場
DAT_LINTER_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "simutrans-addon-dev", "ci-tools", "dat_linter")
VERSION_RE = re.compile(r"^[a-z0-9][a-z0-9.\-]*$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_BLENDER = r"D:\bin\blender\blender.exe"
TIMEOUT_GIT = 600
TIMEOUT_RENDER = 3 * 3600  # 全部で 15〜25 分ほど。ほかの作業者と描画の枠を分け合うと延びる
TIMEOUT_STEP = 3600


def log(msg):
    print(f"[build_ami256] {msg}", flush=True)


def die(msg):
    sys.exit(f"[build_ami256] {msg}")


def run(cmd, cwd=None, env=None, timeout=TIMEOUT_STEP, capture=False):
    """コマンドを流す。失敗・時間切れで止まる。capture なら標準出力を文字で返す。"""
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                           stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE if capture else None)
    except FileNotFoundError:
        die(f"コマンドが無い: {cmd[0]}")
    except subprocess.TimeoutExpired:
        die(f"{timeout} 秒で終わらない: {' '.join(cmd)}")
    if r.returncode != 0:
        detail = r.stderr.decode(errors="replace").strip() if capture else ""
        die(f"失敗（終了コード {r.returncode}）: {' '.join(cmd)}" + (f"\n{detail}" if detail else ""))
    return r.stdout.decode(errors="replace") if capture else None


def git(repo, *args, capture=True):
    return run(["git", "-C", repo, *args], timeout=TIMEOUT_GIT, capture=capture)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---- 設定 ----

def default_ami_repo():
    """pak256 の本体の checkout（worktree でも、その元）の隣の simutrans-addon-dev。"""
    common = git(ROOT, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    return os.path.join(os.path.dirname(os.path.dirname(os.path.normpath(common))), "simutrans-addon-dev")


def build_commit(path=None):
    env = fetch_ami.read_env(path or BUILD_ENV)
    sha = env.get("AMI_COMMIT", "")
    if not SHA_RE.match(sha):
        die(f"{fetch_ami._rel(path or BUILD_ENV)} の AMI_COMMIT が 40 桁の SHA でない: {sha!r}")
    return sha


def check_version(version):
    if not VERSION_RE.match(version):
        die(f"版の名前は英小文字・数字・. と - だけ（例 alpha.4）: {version!r}")
    return version


def child_env(blender):
    env = {k: v for k, v in os.environ.items() if k not in SCRUB}
    env["SHEET_PAK_SIZE"] = "256"
    env["PYTHONUTF8"] = "1"
    env["SHEET_BLENDER"] = blender
    return env


def split_stages(targets, later):
    """描く対象を 2 回に分ける。later（先に描いた物の絵を読む物）は 2 回目。並びは保つ。"""
    later = set(later)
    first = [t for t in targets if t not in later]
    second = [t for t in targets if t in later]
    return [s for s in (first, second) if s]


def read_catalog(ami, env):
    """worktree の catalog から、256 で描く対象と、2 回目に描く物を読む。"""
    code = ("import json, catalog; print(json.dumps({'targets': list(catalog.SCALED_TARGETS), "
            "'later': list(catalog.SCALED_CROSSING_SHEETS) + [catalog.MONORAIL_TUNNEL]}))")
    out = run([sys.executable, "-X", "utf8", "-c", code], cwd=os.path.join(ami, "blender"), env=env, capture=True)
    return json.loads(out)


# ---- build ----

def prepare_worktree(repo, commit, wt, resume):
    if os.path.isdir(wt):
        if not resume:
            die(f"worktree が既にある: {wt}（続けるなら --resume、やり直すなら git -C {repo} worktree remove --force {wt}）")
        head = git(wt, "rev-parse", "HEAD").strip()
        if head != commit:
            die(f"残っている worktree のコミット {head} が、組むコミット {commit} と違う")
        log(f"残っている worktree で続ける: {wt}")
        return
    if resume:
        die(f"--resume だが worktree が無い: {wt}")
    os.makedirs(os.path.dirname(wt), exist_ok=True)
    git(repo, "worktree", "add", "--detach", wt, commit, capture=False)


def step_dat(ami, env):
    run([sys.executable, "-X", "utf8", "blender/ami_dat.py"], cwd=ami, env=env)
    # ami_dat.py は LF で書き、checkout は CRLF（autocrlf）なので、行末の違いは数えない
    numstat = git(ami, "diff", "--ignore-cr-at-eol", "--numstat", "--", "src256").splitlines()
    changed = [line.split("\t")[-1] for line in numstat if not line.startswith("0\t0\t")]
    changed += git(ami, "ls-files", "--others", "--exclude-standard", "--", "src256").splitlines()
    changed = [c for c in changed if c.lower().endswith(".dat")]
    if changed:
        log(f"コミット済みの 256 の dat と違う物が {len(changed)} 個（AMI の dat の書き忘れ。組んだ pak はこの dat で作る）:")
        for c in changed[:20]:
            print("   ", c)


def step_render(ami, env, only, blender):
    cat = read_catalog(ami, env)
    if only:
        bad = [t for t in only if t not in cat["targets"]]
        if bad:
            die(f"256 で描けない対象（catalog.SCALED_TARGETS に無い）: {' '.join(bad)}")
        targets = list(only)
    else:
        targets = cat["targets"]
    return render_stages(ami, env, blender, targets, cat["later"], render_parallel)


def render_stages(ami, env, blender, targets, later, render):
    """段に分けて描き、落ちた対象を全部を描いた後に段の順で 1 回だけ描き直す。描き直した対象を返す（render は差し替えられる）。
    render.py が描いた後に書く自分のアイコン（--own）は、ほかのシートの絵（twin の壁の front など）を読むので、
    並べて描くと、そのシートがまだ無くて落ちることがある（シートは描けている。#83 の試しで 2 対象）。"""
    stages = split_stages(targets, later)
    failed = []
    for i, stage in enumerate(stages, 1):
        log(f"描く {i}/{len(stages)}: {len(stage)} 対象（ログは {os.path.join(ami, 'work', 'render_<対象>.log')}）")
        failed += render(ami, env, blender, stage)
    if not failed:
        return []
    log(f"描き直す: {len(failed)} 対象（{' '.join(failed)}。1 回目のログは work/render_<対象>.log を上書きする）")
    again = []
    for stage in split_stages(failed, later):  # 2 回目の段の物は、1 回目の段の物を描き直した後に描く
        again += render(ami, env, blender, stage)
    if again:
        die(f"描き直しても失敗: {' '.join(again)}（ログは {os.path.join(ami, 'work', 'render_<対象>.log')}）")
    return failed


def parse_render_failed(text):
    """render_parallel.py の最後の行（"[render] done in 12s, failed: a b"）から、失敗した対象を読む。"""
    for line in reversed(text.splitlines()):
        if line.startswith("[render] done in"):
            _, _, rest = line.partition(", failed: ")
            return rest.split()
    return None


def render_parallel(ami, env, blender, targets):
    """AMI の render_parallel.py で描き、失敗した対象を返す。出力はそのまま流す。最後の行が読めなければ止まる。"""
    cmd = [sys.executable, "-X", "utf8", "../../tools/blender/render_parallel.py", "--blender", blender, *targets]
    try:
        p = subprocess.Popen(cmd, cwd=ami, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        die(f"コマンドが無い: {cmd[0]}")
    timer = threading.Timer(TIMEOUT_RENDER, p.kill)  # 時間切れで止める（止めると最後の行が出ないので、下で止まる）
    timer.start()
    lines = []
    try:
        for raw in p.stdout:
            line = raw.decode(errors="replace").rstrip("\r\n")
            print(line, flush=True)
            lines.append(line)
        code = p.wait()
    finally:
        timer.cancel()
        if p.poll() is None:  # 出力の途中で止まった（Ctrl+C など）ときに子を残さない
            p.kill()
    failed = parse_render_failed("\n".join(lines))
    if failed is None or (code != 0 and not failed):
        die(f"render_parallel.py が失敗（終了コード {code}。{TIMEOUT_RENDER} 秒で時間切れのときも同じ）")
    return failed


def step_icons(ami, env, blender):
    """全部のシートのアイコン・カーソルを書き直す（render.py は描いたシートの分だけ --own で書く）。
    Blender は Python の例外でも終了コード 0 で終わるので、ログの Traceback でも止める（render_parallel と同じ）。"""
    path = os.path.join(ami, "work", "icons.log")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cmd = [blender, "-b", "--factory-startup", "--python", "blender/icons.py"]
    with open(path, "w", encoding="utf-8") as f:
        try:
            r = subprocess.run(cmd, cwd=ami, env=env, stdout=f, stderr=subprocess.STDOUT, timeout=TIMEOUT_STEP)
        except subprocess.TimeoutExpired:
            die(f"{TIMEOUT_STEP} 秒で終わらない: {' '.join(cmd)}")
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if r.returncode != 0 or "Traceback" in text:
        die(f"icons.py が失敗（ログ {path}）")


def find_dat_linter():
    for path in (os.environ.get("DAT_LINTER_BIN"), shutil.which("dat_linter"),
                 os.path.join(DAT_LINTER_CACHE, "dat_linter.exe"), os.path.join(DAT_LINTER_CACHE, "dat_linter")):
        if path and os.path.isfile(path):
            return path
    die("dat_linter が無い（AMI の clone で bash addons/ami/check.sh を一度流すと "
        f"{DAT_LINTER_CACHE} に入る。ほかの場所なら DAT_LINTER_BIN で渡す）")


def step_check(ami, env, partial):
    env = dict(env)
    if partial:
        env["CHECK_SKIP_MISSING"] = "1"
    for c in CHECKS_PARTIAL if partial else CHECKS_FULL:
        log(f"検査: {' '.join(c)}")
        run([sys.executable, "-X", "utf8", *c], cwd=ami, env=env)
    if not partial:
        log("検査: dat_linter lint --tile-size 512 src256")
        run([find_dat_linter(), "lint", "--tile-size", "512", "."], cwd=os.path.join(ami, "src256"), env=env)


def step_build(ami, env, partial):
    env = dict(env)
    if partial:
        env["BUILD_SKIP_MISSING"] = "1"
    run([sys.executable, "-X", "utf8", "build.py"], cwd=ami, env=env)


def step_release(ami, env, version, partial):
    paks = [p for p in PAKS if os.path.isfile(os.path.join(ami, "dist256", p + ".pak"))] if partial else list(PAKS)
    if not paks:
        die("dist256/ に同梱する pak が 1 つも無い")
    run([sys.executable, "-X", "utf8", "release.py", "--version", version, "--paks", *paks], cwd=ami, env=env)


def zip_paks(path):
    with zipfile.ZipFile(path) as z:
        return {os.path.basename(i.filename): i.file_size for i in z.infolist() if i.filename.lower().endswith(".pak")}


def steps_file(wt):
    """worktree で済んだ段の控え（worktree の外、隣に置く）。"""
    return wt + ".steps.json"


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def read_steps(wt):
    return read_json(steps_file(wt), [])


def resume_steps(done, from_step):
    """from_step から続けるときの、済んだ段の控え。前の段が済んでいなければ止まる。from_step から後は流し直すので外す。"""
    start = STEPS.index(from_step)
    missing = [s for s in STEPS[:start] if s not in done]
    if missing:
        die(f"--from {from_step} の前の段が済んでいない: {' '.join(missing)}（その段から続ける）")
    return [s for s in done if s in STEPS and STEPS.index(s) < start]


def write_steps(wt, steps):
    with open(steps_file(wt), "w", encoding="utf-8") as f:
        json.dump(steps, f)


def retried_file(wt):
    """描き直した対象の控え（マニフェストに写す）。"""
    return wt + ".retried.json"


def tree_changes(wt):
    """AMI のコミットからの変更のうち、組むと変わる物（src256/ の絵とその控え）以外。手で直した道具・dat、
    ami_dat.py の出力とコミット済みの dat の違い（AMI の書き忘れ）など。行末の違いは数えない。"""
    out = git(wt, "diff", "--ignore-cr-at-eol", "--numstat", "HEAD").splitlines()
    names = [line.split("\t")[-1] for line in out if not line.startswith("0\t0\t")]
    names += [n for n in git(wt, "ls-files", "--others", "--exclude-standard", "--", "addons/ami/src256").splitlines()
              if n.lower().endswith(".dat")]
    return [n for n in names if not (n.startswith("addons/ami/src256/") and not n.lower().endswith(".dat"))]


def tool_versions(blender):
    """組んだ道具の版（絵や pak が変わりうるので記録する）。"""
    def first(cmd, pat):
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=120)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ""
        text = r.stdout.decode(errors="replace") + r.stderr.decode(errors="replace")
        return next((line.strip() for line in text.splitlines() if pat in line), "")
    return {"blender": first([blender, "--version"], "Blender"),
            "makeobj": first([os.environ.get("MAKEOBJ", "makeobj")], "Makeobj version")}


def collect(ami, wt, version, commit, partial, blender):
    src = os.path.join(ami, "work", "release", f"ami-256-{version}.zip")
    if not os.path.isfile(src):
        die(f"zip が無い: {src}")
    paks = zip_paks(src)
    if not partial and sorted(paks) != sorted(p + ".pak" for p in PAKS):
        die(f"zip の pak が同梱する 7 つと違う: {sorted(paks)}")
    changes = tree_changes(wt)
    if changes:
        log(f"AMI の追跡しているファイルが {len(changes)} 個変わっている（この zip は置き場に上げられない）: {' '.join(changes[:10])}")
    os.makedirs(DIST, exist_ok=True)
    dst = os.path.join(DIST, f"ami-256-{version}.zip")
    shutil.copyfile(src, dst)
    manifest = {
        "version": f"ami-256-{version}",
        "ami_commit": commit,
        "partial": partial,
        "steps": read_steps(wt),
        "tree_changes": changes,
        "retried": read_json(retried_file(wt), []),
        "tools": tool_versions(blender),
        "zip_sha256": sha256_file(dst),
        "paks": paks,
    }
    with open(os.path.join(DIST, f"ami-256-{version}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log(f"{os.path.relpath(dst, ROOT)}  SHA-256 {manifest['zip_sha256']}")
    for name, size in sorted(paks.items()):
        print(f"    {name}  {size:,} B")
    return manifest


def cmd_build(a):
    version = check_version(a.version)
    partial = bool(a.only)
    repo = os.path.abspath(a.ami_repo or os.environ.get("AMI_REPO") or default_ami_repo())
    if not os.path.isdir(os.path.join(repo, "addons", "ami")):
        die(f"AMI の clone でない: {repo}（--ami-repo か AMI_REPO で渡す）")
    if not os.path.isfile(a.blender):
        die(f"Blender が無い: {a.blender}（--blender か SHEET_BLENDER で渡す）")
    if not partial:
        find_dat_linter()  # 描いた後の検査の段で無いと分かるのを避ける
    if not a.resume:
        git(repo, "fetch", "origin", capture=False)
    ref = a.ref or build_commit()
    commit = git(repo, "rev-parse", "--verify", ref + "^{commit}").strip()
    if commit != build_commit():
        log(f"build.env の AMI_COMMIT と違うコミットから組む: {commit}（この zip は置き場に上げられない）")
    wt = os.path.join(WORK, commit[:12] + ("-partial" if partial else ""))
    log(f"AMI {commit} を {wt} で組む" + ("（試し: " + " ".join(a.only) + "）" if partial else ""))
    prepare_worktree(repo, commit, wt, a.resume)
    ami = os.path.join(wt, "addons", "ami")
    env = child_env(a.blender)
    start = STEPS.index(a.from_step)
    done = resume_steps(read_steps(wt) if a.resume else [], a.from_step)
    write_steps(wt, done)
    if not a.resume and os.path.isfile(retried_file(wt)):
        os.remove(retried_file(wt))
    for step in STEPS[start:]:
        log(f"== {step}")
        if step == "dat":
            step_dat(ami, env)
        elif step == "render":
            with open(retried_file(wt), "w", encoding="utf-8") as f:
                json.dump(step_render(ami, env, a.only, a.blender), f)
        elif step == "icons":
            if partial:  # ほかのシートの絵から作る物（トンネルなど）が、描いていないシートを読んで落ちる
                log("試しなので飛ばす（描いたシートの分は render.py が書いた）")
            else:
                step_icons(ami, env, a.blender)
        elif step == "check":
            step_check(ami, env, partial)
        elif step == "build":
            step_build(ami, env, partial)
        elif step == "release":
            step_release(ami, env, version, partial)
        done.append(step)
        write_steps(wt, done)
    collect(ami, wt, version, commit, partial, a.blender)
    if a.keep:
        log(f"worktree を残した: {wt}")
    else:
        r = subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", wt], timeout=TIMEOUT_GIT)
        if r.returncode == 0:
            for path in (steps_file(wt), retried_file(wt)):
                if os.path.isfile(path):
                    os.remove(path)
            log("worktree を消した")
        else:  # zip はできているので止めない（中のファイルを開いているプロセスがあると消せない）
            log(f"worktree を消せなかった。後でフォルダ {wt} を消し、git -C {repo} worktree prune を流す")


# ---- compare ----

def pak_objects(pak_path):
    """makeobj list の表から (種類, 名前) の集合を読む。"""
    out = run([os.environ.get("MAKEOBJ", "makeobj"), "list", pak_path], timeout=600, capture=True)
    objs, table = set(), False
    for line in out.splitlines():
        if line.startswith("----"):
            table = True
            continue
        parts = line.split()
        if table and len(parts) >= 2:
            objs.add((parts[0], parts[1]))
    return objs


def zip_objects(path):
    with tempfile.TemporaryDirectory() as d, zipfile.ZipFile(path) as z:
        result = {}
        for i in z.infolist():
            if not i.filename.lower().endswith(".pak"):
                continue
            name = os.path.basename(i.filename)
            target = os.path.join(d, name)
            with z.open(i) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            result[name] = pak_objects(target)
        return result


def compare(a_paks, b_paks, a_objs, b_objs):
    """違いの行を返す。名前・数が違えば ok=False。大きさ・物の違いは知らせるだけ。"""
    lines, ok = [], sorted(a_paks) == sorted(b_paks)
    for name in sorted(set(a_paks) | set(b_paks)):
        if name not in a_paks or name not in b_paks:
            lines.append(f"{name}: 片方だけにある（A {'あり' if name in a_paks else 'なし'}、B {'あり' if name in b_paks else 'なし'}）")
            continue
        diff = a_paks[name] - b_paks[name]
        lines.append(f"{name}: A {a_paks[name]:,} B / B {b_paks[name]:,} B（差 {diff:+,}）")
        if a_objs is not None:
            only_a = sorted(a_objs[name] - b_objs[name])
            only_b = sorted(b_objs[name] - a_objs[name])
            lines.append(f"    物 A {len(a_objs[name])} / B {len(b_objs[name])}")
            for kind, obj in only_a:
                lines.append(f"    A だけ: {kind} {obj}")
            for kind, obj in only_b:
                lines.append(f"    B だけ: {kind} {obj}")
    return ok, lines


def cmd_compare(a):
    a_paks, b_paks = zip_paks(a.a), zip_paks(a.b)
    a_objs = b_objs = None
    if not a.no_objects:
        a_objs, b_objs = zip_objects(a.a), zip_objects(a.b)
    ok, lines = compare(a_paks, b_paks, a_objs, b_objs)
    print(f"A = {a.a}（{len(a_paks)} 個）\nB = {a.b}（{len(b_paks)} 個）")
    for line in lines:
        print(line)
    print("pak の名前と数: " + ("同じ" if ok else "違う"))
    sys.exit(0 if ok else 1)


# ---- upload ----

def rewrite_env(text, values):
    """KEY=値 の行を書き換える（コメント・並びは保つ）。無いキーは末尾に足す。"""
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    done = set()
    for i, line in enumerate(lines):
        key = line.partition("=")[0].strip()
        if not line.lstrip().startswith("#") and "=" in line and key in values:
            lines[i] = f"{key}={values[key]}"
            done.add(key)
    lines += [f"{k}={v}" for k, v in values.items() if k not in done]
    return nl.join(lines) + nl


def release_url(tag, name):
    return f"https://github.com/{RELEASE_REPO}/releases/download/{tag}/{name}"


def tag_exists(tag):
    r = subprocess.run(["gh", "release", "view", tag, "-R", RELEASE_REPO], capture_output=True, timeout=120)
    return r.returncode == 0


def cmd_upload(a):
    version = check_version(a.version)
    name = f"ami-256-{version}"
    zpath = os.path.join(DIST, name + ".zip")
    mpath = os.path.join(DIST, name + ".json")
    if not (os.path.isfile(zpath) and os.path.isfile(mpath)):
        die(f"{os.path.relpath(zpath, ROOT)} と .json が無い（先に build）")
    with open(mpath, encoding="utf-8") as f:
        m = json.load(f)
    if m.get("partial"):
        die("試し（--only）で組んだ zip は上げない")
    if m.get("ami_commit") != build_commit():
        die(f"zip の元のコミット {m.get('ami_commit')} が build.env の AMI_COMMIT と違う（build.env を直す PR を先に入れる）")
    if m.get("steps") != list(STEPS):
        die(f"全部の段を通して組んだ zip でない（済んだ段: {m.get('steps')}）。組み直す")
    tools = m.get("tools") or {}
    if not (tools.get("blender") and tools.get("makeobj")):
        die(f"組んだ道具の版が記録されていない（{tools}）。組み直す")
    if m.get("tree_changes") != []:
        die(f"AMI の道具などを変えて組んだ zip は上げない（{m.get('tree_changes')}）。AMI の側で直してもらう")
    sha = sha256_file(zpath)
    if sha != m.get("zip_sha256"):
        die("zip の SHA-256 が .json と違う。組み直す")
    tag = f"vendor-{name}"
    if tag_exists(tag):
        die(f"Release {tag} は既にある。版の名前を変える（上書きしない）")
    notes = (f"同梱用の AMI の 256 版（配布物ではない）。tools/build_ami256.py で組んだ。\n\n"
             f"- AMI: 128na/simutrans-addon-dev@{m['ami_commit']}\n"
             f"- 道具: {m.get('tools', {}).get('blender', '?')} / {m.get('tools', {}).get('makeobj', '?')}\n"
             f"- SHA-256: {sha}\n")
    values = {"AMI_VERSION": name, "AMI_ZIP_URL": release_url(tag, name + ".zip"), "AMI_ZIP_SHA256": sha,
              "AMI_COMMIT": m["ami_commit"]}
    cmd = ["gh", "release", "create", tag, zpath, "-R", RELEASE_REPO, "--prerelease", "--latest=false",
           "--title", f"vendor: AMI 256 {version}", "--notes", notes]
    if a.dry_run:
        log("（--dry-run）流すコマンド: " + " ".join(cmd[:8]) + " ...")
        log("（--dry-run）ami.env に書く値: " + json.dumps(values, ensure_ascii=False))
        return
    run(cmd, timeout=1800)
    with open(fetch_ami.ENV_FILE, encoding="utf-8", newline="") as f:
        text = f.read()
    with open(fetch_ami.ENV_FILE, "w", encoding="utf-8", newline="") as f:
        f.write(rewrite_env(text, values))
    log(f"{tag} に上げ、vendor/ami/ami.env を書き換えた。docs と合わせて PR にする")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="AMI の 256 版の zip を組む")
    b.add_argument("--version", required=True, help="版の名前（例 alpha.4。zip は ami-256-<版>.zip）")
    b.add_argument("--ref", help="組む AMI のコミット（既定は vendor/ami/build.env の AMI_COMMIT）")
    b.add_argument("--ami-repo", help="AMI の clone（既定は環境変数 AMI_REPO か、pak256 の隣の simutrans-addon-dev）")
    b.add_argument("--blender", default=os.environ.get("SHEET_BLENDER", DEFAULT_BLENDER))
    b.add_argument("--only", nargs="+", metavar="対象", help="試し: この対象だけを描いて、絵のある物だけを組む")
    b.add_argument("--resume", action="store_true", help="残っている worktree で続ける（fetch をしない）")
    b.add_argument("--from", dest="from_step", choices=STEPS, default=STEPS[0], help="この段から流す（--resume と使う）")
    b.add_argument("--keep", action="store_true", help="終わっても worktree を消さない")
    c = sub.add_parser("compare", help="2 つの zip の pak を比べる")
    c.add_argument("a")
    c.add_argument("b")
    c.add_argument("--no-objects", action="store_true", help="makeobj list で物を比べない")
    u = sub.add_parser("upload", help="組んだ zip を置き場に上げ、ami.env を書き換える")
    u.add_argument("--version", required=True)
    u.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "build" and a.from_step != STEPS[0] and not a.resume:
        ap.error("--from は --resume と使う")
    {"build": cmd_build, "compare": cmd_compare, "upload": cmd_upload}[a.cmd](a)


if __name__ == "__main__":
    main()
