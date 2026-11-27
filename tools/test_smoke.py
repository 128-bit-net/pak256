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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMOKE = os.path.join(ROOT, "objects", "smoke")


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
        spec = importlib.util.spec_from_file_location("draw_smoke", os.path.join(SMOKE, "draw_smoke.py"))
        ds = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ds)
        self.assertEqual(read(os.path.join(SMOKE, "smoke.dat")), ds.dat_text())

    def test_chimney_smoke_place(self):
        table = read(os.path.join(ROOT, "objects", "industry", "coal_chain", "coal_power_plant.yaml"))
        self.assertIn('smoketile: {0: "1,0"}', table)
        self.assertIn('smokeoffset: {0: "2,-26"}', table)


if __name__ == "__main__":
    unittest.main()
