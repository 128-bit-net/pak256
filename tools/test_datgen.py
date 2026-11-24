"""tools/datgen.py の検査。

    python -X utf8 -m unittest discover -s tools -p "test_*.py"
"""
import os
import tempfile
import unittest

import datgen

BASE = "obj: tree\nname: a\ncopyright: c\n"


def run(text):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "a.yaml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return datgen.yaml_to_dat(path)


class DatgenTest(unittest.TestCase):
    def test_nested(self):
        dat = run(BASE + "image:\n  0: {0: s.0.0}\n  1: {0: s.0.1}\nfreight: [x, y]\nflag: true\n")
        self.assertEqual(
            dat,
            "obj=tree\nname=a\ncopyright=c\nimage[0][0]=s.0.0\nimage[1][0]=s.0.1\n"
            "freight[0]=x\nfreight[1]=y\nflag=1\n-\n",
        )

    def test_several_objects(self):
        dat = run("- {obj: tree, name: a, copyright: c}\n- {obj: tree, name: b, copyright: c}\n")
        self.assertEqual(dat.count("\n-\n"), 2)

    def test_errors(self):
        for text in (
            "obj: tree\nname: a\n",                  # copyright が無い
            "obj: tree\nname: a\ncopyright: ''\n",   # copyright が空
            BASE + "x:\n",                           # 値が空
            BASE + "x: []\n",                        # 並びが空
            BASE + "on: 3\n",                        # キーが真偽になる
            BASE + "name: b\n",                      # 同じキーが 2 度
            BASE + "x: 'a\n\n  b'\n",                # 値に改行
            "",                                      # 中身が無い
            BASE + "image: {0: x, '0': y}\n",        # 数と文字のキーがぶつかる
            BASE + "[a]: 1\n",                       # 並びのキー
            BASE + "x: [\n",                         # YAML の文法の誤り
        ):
            with self.subTest(text=text), self.assertRaises(datgen.DatError):
                run(text)


if __name__ == "__main__":
    unittest.main()
