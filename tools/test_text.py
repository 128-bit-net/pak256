"""text/ の訳の表と街の名前の検査（docs/layout.md の「物の名前の訳と街の名前」）。

本体は壊れた表を警告なしで読み飛ばすので、ここで確かめる。
    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import glob
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "text")
LANGS = ("ja", "en")


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        s = f.read()
    assert s.startswith("§"), f"{path}: 先頭が § でない（UTF-8 の印）"
    assert "\r" not in s, f"{path}: 改行は LF だけにする"
    return s[1:].split("\n")


def pairs(lang):
    """名前と訳の行が交互に並ぶ表を {名前: 訳} にする。先頭の # の行は飛ばす。"""
    lines = read(os.path.join(TEXT, f"{lang}.tab"))
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    if lines and lines[-1] == "":
        lines.pop()
    assert len(lines) % 2 == 0, f"{lang}.tab: 名前と訳の行が交互にならない（行数が奇数）"
    return dict(zip(lines[0::2], lines[1::2])), lines[0::2]


def object_names():
    names = set()
    for p in glob.glob(os.path.join(ROOT, "objects", "**", "*.yaml"), recursive=True):
        with open(p, encoding="utf-8") as f:
            names.update(re.findall(r"^name:\s*(\S+)\s*$", f.read(), re.M))
    return names


class TextTest(unittest.TestCase):
    def test_tab_shape(self):
        for lang in LANGS:
            table, order = pairs(lang)
            self.assertEqual(len(table), len(order), f"{lang}.tab: 名前が重複している")
            for name, tr in table.items():
                self.assertTrue(tr.strip(), f"{lang}.tab: {name} の訳が空")
                self.assertNotEqual(name, tr, f"{lang}.tab: {name} の訳が名前と同じ（本体は黙って捨てる）")
                self.assertFalse(tr.startswith("#"), f"{lang}.tab: {name} の訳が # で始まる（注釈にならない）")

    def test_same_names_in_all_languages(self):
        sets = [set(pairs(lang)[0]) for lang in LANGS]
        self.assertEqual(sets[0], sets[1], "ja.tab と en.tab の名前の集合が違う")

    def test_object_names_translated(self):
        for lang in LANGS:
            missing = object_names() - set(pairs(lang)[0])
            self.assertFalse(missing, f"{lang}.tab に無い物の名前: {sorted(missing)}")

    def test_citylist(self):
        counts = []
        for lang in LANGS:
            names = [ln for ln in read(os.path.join(TEXT, f"citylist_{lang}.txt")) if ln and not ln.startswith("#")]
            self.assertEqual(len(names), len(set(names)), f"citylist_{lang}.txt: 名前が重複している")
            self.assertTrue(all(len(n.encode("utf-8")) < 255 for n in names))
            counts.append(len(names))
        self.assertEqual(counts[0], counts[1], "citylist の ja と en で数が違う")


if __name__ == "__main__":
    unittest.main()
