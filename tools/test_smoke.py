"""煙（obj=smoke）の検査（docs/smoke.md・#174）。

表が引く煙の名前が smoke.dat に無くても makeobj は組むときに気づかない（産業は必須の参照、車両は必須でない参照）。
つづりの違いは煙が出ないか読み込みの失敗になるので、ここで確かめる。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import importlib.util
import os
import re
import unittest

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMOKE = os.path.join(ROOT, "objects", "smoke")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def defined():
    return set(re.findall(r"^name=(\S+)$", read(os.path.join(SMOKE, "smoke.dat")), re.M))


def references():
    """表の `smoke:` の値（{表の相対パス: 名前}）。"""
    out = {}
    for p in glob.glob(os.path.join(ROOT, "objects", "**", "*.yaml"), recursive=True):
        m = re.search(r"^smoke:\s*([^\s#]+)", read(p), re.M)
        if m:
            out[os.path.relpath(p, ROOT).replace(os.sep, "/")] = m.group(1)
    return out


class SmokeTest(unittest.TestCase):
    def test_references_exist(self):
        for path, name in references().items():
            self.assertIn(name, defined(), f"{path}: 煙 {name} が objects/smoke/smoke.dat に無い")

    def test_expected_objects_smoke(self):
        got = {os.path.basename(p)[: -len(".yaml")]: n for p, n in references().items()}
        self.assertEqual(got, {
            "coal_power_plant": "pak256_smoke_chimney",
            "railcar": "pak256_smoke_diesel",
            "ferry": "pak256_smoke_ship",
            "cargo_ship": "pak256_smoke_ship",
        })

    def test_dat_matches_script(self):
        ds = load("draw_smoke", os.path.join(SMOKE, "draw_smoke.py"))
        self.assertEqual(read(os.path.join(SMOKE, "smoke.dat")), ds.dat_text())

    def test_chimney_smoke_place(self):
        # 表の位置が、今の煙突の寸法から出した値と同じこと（煙突を動かして流し直し忘れたら落ちる）
        folder = os.path.join(ROOT, "objects", "industry", "coal_chain")
        di = load("draw_industry", os.path.join(folder, "draw_industry.py"))
        tile, offset = di.smoke_place(di.CHIMNEY)
        table = read(os.path.join(folder, "coal_power_plant.yaml"))
        self.assertIn(f'smoketile: {{0: "{tile}"}}', table)
        self.assertIn(f'smokeoffset: {{0: "{offset}"}}', table)

    def test_png_frames_match_dat(self):
        # 絵の幅がコマ数と合うこと（image[N] の分だけ 256px のセルが並ぶ）
        ds = load("draw_smoke", os.path.join(SMOKE, "draw_smoke.py"))
        for spec in ds.SMOKES:
            with Image.open(os.path.join(SMOKE, spec["stem"] + ".png")) as im:
                self.assertEqual(im.size, (ds.CELL * len(spec["frames"]), ds.CELL), spec["name"])


if __name__ == "__main__":
    unittest.main()
