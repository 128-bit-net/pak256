"""config/ の設定ファイルの書き方を検査する。MIT License。

本体は、menuconf.tab などの書き方の誤りを起動のログに出さずに黙って捨てる（#3 のレビューで見つかった）。
そのため、ログではなくこの道具で確かめる。誤りがあれば行番号つきで出して、終了コード 1 で終わる。

見るもの:
  menuconf.tab
    - ツールバーの行（toolbar[段][位置]=…）の `=` の後ろに空白が無い（前の空白は本体が捨てるが、そろえて禁じる）
    - toolbar[N] の参照が、本体が読む順（toolbar[0] から、位置の順）に 1, 2, 3… と 1 回ずつ出る
    - 位置が 0 から連番（抜け・重なりが無い）
    - ツールバーの行が使う toolbar[N]・general_tool[N]・simple_tool[N]・dialog_tool[N] の定義がある
      （道具の行が無くても、ツールバーの行がアイコンの番号を書いていれば使える）
    - toolbar[0] 以外の段は、どこかの行から使われている
    - 本家 125.0.1 と OTRP で番号が違う道具（general_tool 48〜・simple_tool 36〜・dialog_tool 36〜）を使っていない
  行頭が空白の行は、本体が読み飛ばすので誤りにする
  cityrules.tab
    - house_N・road_N が 1 から連番で、それぞれ .chance がある
    - 規則が正方形（1 辺 3・5・7）で、使える記号だけを使い、中央が n（空き地）
  menuconf.tab・cityrules.tab は、検査の前に本体と同じ読み方に直す
    - キーの大文字・小文字は区別されない（小文字にして読む）。値の道具の名前（general_tool[3] など）は小文字のまま比べられるので、大文字なら誤り
    - `toolbar[6][10-11]`・`[1,3]` のような範囲の書き方を 1 個ずつに展開して検査する（[n,s] のような ribi の名前は展開しない）
  cityrules.tab の .chance は、10 進か 0x の整数で -32768〜32767（本体は strtol で読み、読めなければ黙って 0）
  全部の .tab
    - 空行・# の注釈・`キー = 値` のどれでもない行が無い

使い方: python -X utf8 tools/lint_config.py [config のフォルダ]   （既定は config/）
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 本家 125.0.1 と OTRP で番号が同じ最大の番号 + 1。これ以上の番号は両方で別の道具になるので使わない
# （docs/config.md の「ツールの番号」）。本体のバージョンが変わったら見直す。
TOOL_ID_LIMITS = {"general_tool": 48, "simple_tool": 36, "dialog_tool": 36}

RULE_CHARS = set("nsShHtTuU.")  # 本体 simcity.cc の "SsnHhTtUu" と、何でもよい .
RULE_SIZES = (3, 5, 7)

TOOLBAR_LINE = re.compile(r"^toolbar\[(\d+)\]\[(\d+)\]")
TOOL_REF = re.compile(r"\b(toolbar|general_tool|simple_tool|dialog_tool)\[(\d+)\]")
TOOL_DEF = re.compile(r"^(general_tool|simple_tool|dialog_tool)\[(\d+)\]\s*=")
CHANCE_VALUE = re.compile(r"^[+-]?(0[xX][0-9a-fA-F]+|0|[1-9][0-9]*)$")
RULE_KEY = re.compile(r"^(house|road)_(\d+)(\.chance)?$")


def read_lines(path):
    """(行番号, 行) の並び。末尾の改行は除く。"""
    with open(path, encoding="utf-8-sig") as f:
        return [(i, line.rstrip("\r\n")) for i, line in enumerate(f, 1)]


def is_comment(line):
    """本体が読み飛ばす行（空行・# の注釈・行頭が空白の行）。"""
    s = line.strip()
    return s == "" or s.startswith("#") or line[:1] in (" ", "	")


RANGE_LIMIT = 256  # 本体は 1 つの [] の値が 256 個以上になる範囲で止まる（255 個まで。tabfile.cc）


def expand_key(key):
    """本体の tabfile_t::read が `キー` に対してすることを写す。戻り値: (展開したキーの並び, エラーの文 か None)

    - キーは小文字にし、右の空白と [] の中の空白を除く（format_key）
    - [] の中に `,` か `-` があれば展開する（`toolbar[6][10-11]` は [10] と [11]、`[1,3]` は 1 と 3、`[2-4]` は 2・3・4）。
      先頭の値は atoi と同じく数字の頭だけを読む。[] が複数あるときは全部の組み合わせ
    - [] の中が n・s・e・w で始まる名前の列（`[n,s]` など ribi の書き方）は展開しない。この 2 つの設定では使わない
    """
    key = key.rstrip(" ").lower()
    key = re.sub(r"\[[^\]]*\]", lambda m: m.group(0).replace(" ", ""), key)
    parts = re.split(r"(\[[^\]]*\])", key)
    choices = []  # 各 [] ごとの値の並び。展開しない [] は None
    for part in parts:
        if not (part.startswith("[") and part.endswith("]")):
            choices.append(None)
            continue
        body = part[1:-1]
        if not re.search(r".[,-]", body):
            choices.append(None)
            continue
        head = re.match(r"-?\d*", body).group(0)
        first = int(head) if re.fullmatch(r"-?\d+", head) else 0
        if first == 0 and body[:1] in "nsew" and body != "":
            choices.append(None)  # ribi の名前
            continue
        values = [first]
        for sep, tok in re.findall(r"([,-])([^,-]*)", body[len(head):] if head else body):
            num = re.match(r"-?\d*", tok).group(0)
            num = int(num) if re.fullmatch(r"-?\d+", num) else 0
            if sep == ",":
                values.append(num)
            else:
                values.extend(range(values[-1] + 1, num + 1))
            if len(values) >= RANGE_LIMIT:
                return [], f"[{body}] の値が {RANGE_LIMIT} 個以上になる（本体は止まる、または黙って捨てる）"
        choices.append(values)
    out = [""]
    for part, values in zip(parts, choices):
        if values is None:
            out = [o + part for o in out]
        else:
            out = [o + f"[{v}]" for o in out for v in values]
    return out, None


def normalize(lines):
    """本体が読むとおりの形に直す: キーを小文字にし、範囲の書き方を 1 個ずつの行に展開する。
    戻り値: (行の並び（行番号は元のまま）, エラーの並び)"""
    out, errors = [], []
    for n, line in lines:
        if is_comment(line) or "=" not in line:
            out.append((n, line))
            continue
        m = re.match(r"^([^=]*?)( *)=(.*)$", line)
        keys, err = expand_key(m.group(1))
        if err:
            errors.append(f"{n}: {err}")
            continue
        for k in keys:
            out.append((n, f"{k}{m.group(2)}={m.group(3)}"))
    return out, errors


def check_syntax(lines):
    errors = []
    for n, line in lines:
        s = line.strip()
        if s and not s.startswith("#") and line[0] in (" ", "	"):
            errors.append(f"{n}: 行頭が空白の行は本体が読み飛ばす（# の注釈にするか、行頭の空白を除く）: {s}")
        elif not is_comment(line) and "=" not in line:
            errors.append(f"{n}: `キー = 値` の形でない行: {line.strip()}")
    return errors


def check_menuconf(lines):
    errors = []
    defs = set()  # ("general_tool", 3) など
    bars = {}  # 段 -> [(行番号, 位置)]
    bar_refs = {}  # 段 -> [(行番号, 位置, 参照する toolbar の番号 か None)]
    refs = []  # (行番号, 種類, 番号)
    for n, line in lines:
        if is_comment(line):
            continue
        m = TOOL_DEF.match(line)
        if m:
            defs.add((m.group(1), int(m.group(2))))
            limit = TOOL_ID_LIMITS[m.group(1)]
            if int(m.group(2)) >= limit:
                errors.append(f"{n}: {m.group(1)}[{m.group(2)}] は本家 125.0.1 と OTRP で番号が違う道具（{limit} 以上。docs/config.md の「ツールの番号」）")
            continue
        m = TOOLBAR_LINE.match(line)
        if not m:
            continue
        bar, pos = int(m.group(1)), int(m.group(2))
        if bar not in bars:
            bars[bar] = []
        bars[bar].append((n, pos))
        # `=` の前後の空白。本体は空白があると道具名として読まない
        if not re.match(r"^toolbar\[\d+\]\[\d+\]=\S", line):
            errors.append(f"{n}: ツールバーの行は `=` の前後に空白を入れない（`toolbar[段][位置]=道具`）: {line.strip()}")
        value = line.split("=", 1)[1]
        r = TOOL_REF.match(value)
        # 値（道具の名前）は本体が小文字のまま比べる（キーと違って小文字にしない）
        if not r and re.match(r"(?i)(toolbar|general_tool|simple_tool|dialog_tool)\[", value):
            errors.append(f"{n}: 道具の名前は小文字で書く（本体は大文字・小文字を区別する）: {value.split(',')[0]}")
        bar_refs.setdefault(bar, []).append((pos, n, int(r.group(2)) if r and r.group(1) == "toolbar" else None))  # 値の先頭が道具。2 つ目の欄にアイコンの番号があれば、道具の行が無くても使える
        if r:
            if r.group(1) in TOOL_ID_LIMITS and int(r.group(2)) >= TOOL_ID_LIMITS[r.group(1)]:
                errors.append(f"{n}: {r.group(1)}[{r.group(2)}] は本家 125.0.1 と OTRP で番号が違う道具（{TOOL_ID_LIMITS[r.group(1)]} 以上。docs/config.md の「ツールの番号」）")
            fields = value.split(",")
            has_icon = len(fields) > 1 and fields[1].strip() != ""
            refs.append((n, r.group(1), int(r.group(2)), has_icon))

    # 位置は 0 からの連番（本体は位置を番号で読むので、行の順は問わない）
    for bar, items in bars.items():
        seen = [p for _, p in items]
        if sorted(seen) != list(range(len(seen))):
            dup = sorted({p for p in seen if seen.count(p) > 1})
            miss = sorted(set(range(max(seen) + 1)) - set(seen))
            detail = []
            if dup:
                detail.append(f"重なり {dup}")
            if miss:
                detail.append(f"抜け {miss}")
            errors.append(f"toolbar[{bar}] の位置が 0 からの連番でない（{', '.join(detail)}）")

    # 本体は toolbar[0] から順に位置の順で読み、toolbar[N] の参照を見たとき、
    # 今のツールバーの数が N に等しいときだけ新しい段を作る。違えば中身ごと黙って捨てる。
    if 0 in bars:
        count = 1
        i = 0
        while i < count:
            for pos, n, ref in sorted(bar_refs.get(i, [])):
                if ref is None:
                    continue
                if ref == count:
                    count += 1
                else:
                    errors.append(f"{n}: toolbar[{ref}] の参照が、読む順の {count} 番でない（本体は黙って捨てる。参照は 1, 2, 3… の順に、1 回ずつ）")
            i += 1
        for bar in bars:
            if bar >= count:
                errors.append(f"toolbar[{bar}] の行はあるが、読む順に作られる段にならない")

    used_bars = set()
    for n, kind, num, has_icon in refs:
        if kind == "toolbar":
            used_bars.add(num)
            if num not in bars:
                errors.append(f"{n}: toolbar[{num}] を使っているが、その段の行が無い")
        elif (kind, num) not in defs and not has_icon:
            errors.append(f"{n}: {kind}[{num}] を使っているが、道具の行（{kind}[{num}] = …）が無い")
    for bar in bars:
        if bar != 0 and bar not in used_bars:
            errors.append(f"toolbar[{bar}] の行はあるが、どこからも使われていない")
    if 0 not in bars:
        errors.append("toolbar[0]（一番上のツールバー）の行が無い")
    return errors


def parse_rules(lines):
    """house_N・road_N を集める。戻り値: (規則 {名前: (行番号, [行…])}, chance {名前: 行番号}, errors)"""
    rules, chances, errors = {}, {}, []
    for n, line in lines:
        if is_comment(line) or "=" not in line:
            continue
        key, value = (s.strip() for s in line.split("=", 1))
        m = RULE_KEY.match(key)
        if not m:
            continue
        name = f"{m.group(1)}_{m.group(2)}"
        if m.group(3):
            chances[name] = n
            if not CHANCE_VALUE.match(value) or not -32768 <= int(value, 0) <= 32767:
                errors.append(f"{n}: {name}.chance の値が 10 進か 0x の整数（-32768〜32767）でない（本体は strtol で読み、読めない値は黙って 0 にする。先頭が 0 の数は 8 進になる）: {value!r}")
        else:
            if name in rules:
                errors.append(f"{n}: {name} が重なっている")
            rules[name] = (n, value.split(" "))
    return rules, chances, errors


def check_cityrules(lines):
    rules, chances, errors = parse_rules(lines)
    for kind in ("house", "road"):
        nums = sorted(int(k.split("_")[1]) for k in rules if k.startswith(kind + "_"))
        if nums != list(range(1, len(nums) + 1)):
            errors.append(f"{kind}_N の番号が 1 からの連番でない: {nums}")
    for name in chances:
        if name not in rules:
            errors.append(f"{chances[name]}: {name}.chance があるが、{name} の規則が無い")
    for name, (n, rows) in rules.items():
        if name not in chances:
            errors.append(f"{n}: {name} に {name}.chance が無い")
        size = len(rows)
        if "" in rows:
            errors.append(f"{n}: {name} の行どうしは、空白 1 個で区切る（本体は 1 個として読む。空白が 2 個以上・タブ・前後の空白は誤り）")
            continue
        if size not in RULE_SIZES:
            errors.append(f"{n}: {name} の規則の大きさが 3・5・7 のどれでもない（{size} 行）")
            continue
        for row in rows:
            if len(row) != size:
                errors.append(f"{n}: {name} は正方形でない（{size} 行に対し、{len(row)} 文字の行がある）")
                break
        bad = sorted({c for row in rows for c in row} - RULE_CHARS)
        if bad:
            errors.append(f"{n}: {name} に使えない記号がある: {''.join(bad)}（使えるのは {''.join(sorted(RULE_CHARS))}）")
        mid = size // 2
        if len(rows[mid]) == size and rows[mid][mid] != "n":
            errors.append(f"{n}: {name} の中央が n（空き地）でない（{rows[mid][mid]}）")
    return errors


def lint(config_dir):
    """設定のフォルダを検査する。戻り値: エラーの文の並び（空なら通った）。"""
    errors = []
    checks = {"menuconf.tab": check_menuconf, "cityrules.tab": check_cityrules}
    names = sorted(f for f in os.listdir(config_dir) if f.endswith(".tab"))
    for need in checks:
        if need not in names:
            errors.append(f"{need}: ファイルが無い（無いと本体が起動しない物を含む）")
    for name in names:
        lines = read_lines(os.path.join(config_dir, name))
        found = check_syntax(lines)
        if name in checks:
            normalized, errs = normalize(lines)
            found += errs + checks[name](normalized)
        errors += [f"{name}: {e}" for e in found]
    return errors


def main(argv):
    config_dir = argv[1] if len(argv) > 1 else os.path.join(ROOT, "config")
    errors = lint(config_dir)
    for e in errors:
        print(f"ERROR {e}")
    if errors:
        print(f"{len(errors)} 件の誤りがある")
        return 1
    print(f"設定ファイルの検査: 誤りなし（{config_dir}）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
