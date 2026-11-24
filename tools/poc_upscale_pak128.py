"""pak128 のソースを 2 倍に拡大し、makeobj で pak256 として組む試しの道具（concept.md の 4 章の 1）。

絵は最近傍で 2 倍にする（特別な色を変えないため）。dat の絵の参照に付いた画素のずらし（`file.0.0,x,y`）も 2 倍にする。
煙の位置（SmokeOffset）と標識の offset_left は、本体が pak の大きさに合わせて縮尺するので変えない。

できた pak は pak128 の絵の写しなので、pak128 の許諾（Artistic License 2.0）に従い、リポジトリには入れない。

使い方:
    python tools/poc_upscale_pak128.py <pak128 のソース> <作業フォルダ>
作業フォルダに src/（拡大したソース）と pak256poc/（組んだ pak セット）ができる。
"""
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

SCALE = 2

# pak128 の Makefile の区分。値は元の大きさ。
DIRS = {
    64: ["base/misc_GUI_64"],
    128: [
        "base/misc_GUI", "base/pedestrians", "base/smokes", "citycars",
        "cityhouses/com", "cityhouses/com/no-winter", "cityhouses/ind", "cityhouses/ind/no-winter",
        "cityhouses/res", "cityhouses/res/blocks", "cityhouses/res/pioneer",
        "factories", "factories/powerplants",
        "infrastructure/airport_buildings_towers", "infrastructure/airport_depots",
        "infrastructure/airport_ways_items", "infrastructure/catenary_all",
        "infrastructure/depots_rail_road_tram", "infrastructure/headquarters",
        "infrastructure/rail_bridges", "infrastructure/rail_elevated", "infrastructure/rail_signals",
        "infrastructure/rail_stations", "infrastructure/rail_tracks", "infrastructure/rail_tunnels",
        "infrastructure/rail_water_crossings", "infrastructure/roads", "infrastructure/road_bridges",
        "infrastructure/road_elevated", "infrastructure/road_rail_crossings", "infrastructure/road_signs",
        "infrastructure/road_stops", "infrastructure/road_tunnels", "infrastructure/road_water_crossings",
        "infrastructure/schwebebahn_all", "infrastructure/station_buildings", "infrastructure/tram_tracks",
        "infrastructure/water_all",
        "landscape/groundobj_static", "landscape/grounds", "landscape/rivers", "landscape/trees",
        "special_buildings/city", "special_buildings/city/no-winter",
        "special_buildings/landscape", "special_buildings/landscape/no-winter",
        "special_buildings/monuments", "special_buildings/townhalls",
        "vehicles/monorail", "vehicles/rail-cargo", "vehicles/rail-engines", "vehicles/rail-psg+mail",
        "vehicles/road-cargo", "vehicles/road-horses", "vehicles/road-psg+mail", "vehicles/trams",
    ],
    176: ["infrastructure/powerlines", "vehicles/airplanes"],
    250: ["vehicles/ships-ferries", "vehicles/ships-cargo"],
}
OUTSIDE = "base/special"

# GUI の小さなアイコン（64）は拡大しない。ツールバーの大きさを変えないため。
NO_SCALE = set(DIRS[64])

# 絵の参照の後ろの画素のずらし: 「名前.行.列,x」または「名前.行.列,x,y」
OFFSET_RE = re.compile(rb"(\.\d+\.\d+)\s*,\s*(-?\d+)(?:\s*,\s*(-?\d+))?")


def scale_offsets(data):
    def repl(m):
        out = m.group(1) + b"," + str(int(m.group(2)) * SCALE).encode()
        if m.group(3) is not None:
            out += b"," + str(int(m.group(3)) * SCALE).encode()
        return out

    lines = data.split(b"\n")
    for i, line in enumerate(lines):
        if b"=" in line and not line.lstrip().startswith(b"#"):
            key, val = line.split(b"=", 1)
            lines[i] = key + b"=" + OFFSET_RE.sub(repl, val)
    return b"\n".join(lines)


def scale_png(src, dst):
    with Image.open(src) as im:
        im.load()
        big = im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)
        big.save(dst)


def copy_dir(src_root, dst_root, rel, scale, jobs):
    s = os.path.join(src_root, rel)
    d = os.path.join(dst_root, rel)
    os.makedirs(d, exist_ok=True)
    for name in os.listdir(s):
        sp = os.path.join(s, name)
        dp = os.path.join(d, name)
        if os.path.isdir(sp):
            continue  # 下のフォルダは DIRS で別に扱う
        low = name.lower()
        if scale and low.endswith(".png"):
            jobs.append((sp, dp))
        elif scale and low.endswith(".dat"):
            with open(sp, "rb") as f:
                data = f.read()
            with open(dp, "wb") as f:
                f.write(scale_offsets(data))
        else:
            shutil.copy2(sp, dp)


def makeobj(*args):
    r = subprocess.run(["makeobj", *args], capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-2000:] + r.stderr[-2000:])
        raise SystemExit("makeobj が失敗: " + " ".join(args))
    return r.stdout


def main():
    src_root, work = sys.argv[1], sys.argv[2]
    src_out = os.path.join(work, "src")
    pak_out = os.path.join(work, "pak256poc")
    shutil.rmtree(src_out, ignore_errors=True)
    shutil.rmtree(pak_out, ignore_errors=True)

    jobs = []
    for size, dirs in DIRS.items():
        for rel in dirs:
            copy_dir(src_root, src_out, rel, rel not in NO_SCALE, jobs)
    copy_dir(src_root, src_out, OUTSIDE, True, jobs)
    print(f"絵を拡大: {len(jobs)} 枚", flush=True)
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as ex:
        list(ex.map(lambda j: scale_png(*j), jobs))

    shutil.copytree(os.path.join(src_root, "pak128.prototype"), pak_out)
    os.makedirs(os.path.join(pak_out, "doc"), exist_ok=True)
    shutil.copy2(os.path.join(src_root, "LICENSE.txt"), os.path.join(pak_out, "doc"))

    def build(size, rel):
        out_size = size if rel in NO_SCALE else size * SCALE
        dest = os.path.join(pak_out, rel.replace("/", ".") + ".all.pak")
        makeobj("quiet", f"PAK{out_size}", dest, os.path.join(src_out, rel) + "/")
        return rel

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as ex:
        tasks = [ex.submit(build, size, rel) for size, dirs in DIRS.items() for rel in dirs]
        for t in tasks:
            print("組んだ:", t.result(), flush=True)

    outside = os.path.join(src_out, OUTSIDE)
    with open(os.path.join(outside, "outside.dat"), "w", encoding="ascii") as f:
        f.write("Obj=ground\nName=Outside\ncopyright=pak256 POC (pak128 x2)\nImage[0][0]=tile.1.1\n-\n")
    makeobj("quiet", f"PAK{128 * SCALE}", pak_out + "/", outside + "/")
    print("できた:", pak_out)


if __name__ == "__main__":
    main()
