"""音の検査: sound/ の WAV の形式と、dat の sound= が指すファイルがあること。MIT License。"""
import glob
import os
import struct
import sys
import unittest
import wave

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_sounds  # noqa: E402

ROOT = make_sounds.ROOT
SOUND = make_sounds.SOUND_DIR
# 停留所から発車しない車両（先頭にならない付随車・街の車・歩行者）には音を付けない
NO_SOUND_VEHICLES = {"pak256_railcar_trailer"}


def tables():
    """objects/ の表の (パス, 物) を並べる。"""
    for path in sorted(glob.glob(os.path.join(ROOT, "objects", "**", "*.yaml"), recursive=True)):
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for obj in data if isinstance(data, list) else [data]:
            yield path, obj


class WavTest(unittest.TestCase):
    def test_files_match_the_generator(self):
        found = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SOUND, "*.wav")))
        self.assertEqual(found, sorted(make_sounds.SOUNDS))

    def test_format(self):
        for name in make_sounds.SOUNDS:
            path = os.path.join(SOUND, name)
            with wave.open(path, "rb") as w:
                self.assertEqual((w.getnchannels(), w.getsampwidth(), w.getframerate()), (1, 2, make_sounds.RATE), name)
                seconds = w.getnframes() / w.getframerate()
                data = w.readframes(w.getnframes())
            self.assertTrue(0.5 <= seconds <= 3.0, (name, seconds))
            peak = max(abs(v) for (v,) in struct.iter_unpack("<h", data))
            self.assertTrue(0.5 * 32767 <= peak <= 0.8 * 32767, (name, peak))
            # 本体の Windows 版の読み方に合わせ、fmt（16 バイト）と data だけにする
            with open(path, "rb") as f:
                head = f.read(44)
            self.assertEqual((head[12:16], struct.unpack("<I", head[16:20])[0], head[36:40]), (b"fmt ", 16, b"data"), name)
            self.assertEqual(os.path.getsize(path), 44 + len(data), name)

    def test_file_names(self):
        for name in make_sounds.SOUNDS:
            # 数字で始まる名前は makeobj が昔の番号と読む
            self.assertRegex(name, r"^pak256_[a-z_]+\.wav$")


class TableTest(unittest.TestCase):
    def test_vehicles_and_factories_have_existing_sounds(self):
        used = set()
        for path, obj in tables():
            kind, name = obj.get("obj"), obj.get("name")
            if kind == "factory" or (kind == "vehicle" and name not in NO_SOUND_VEHICLES):
                self.assertIn("sound", obj, f"{path}: {name}")
            if "sound" in obj:
                self.assertIn(obj["sound"], make_sounds.SOUNDS, f"{path}: {name}")
                used.add(obj["sound"])
                if kind == "factory":  # 省くと間隔が効かない（docs/sound.md）
                    self.assertGreater(obj.get("sound_interval", 0), 0, f"{path}: {name}")
        self.assertEqual(used, set(make_sounds.SOUNDS))  # 使われない音を残さない


if __name__ == "__main__":
    unittest.main()
