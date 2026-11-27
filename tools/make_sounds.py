"""車両と産業の効果音を合成して、sound/ に WAV で書く（docs/sound.md）。

標準ライブラリだけで作る。録音や他人の素材は使わない。乱数の種は音ごとに決めてあるので、流し直しても同じ音になる。
形式は PCM 16bit・モノラル・22050Hz で、チャンクは fmt と data だけ（本体の Windows 版の WAV の読み方が簡単なため）。
長さ（バイト数）は偶数にする。

使い方（リポジトリのどこからでも）:
    python -X utf8 tools/make_sounds.py            sound/ に書く
    python -X utf8 tools/make_sounds.py --out DIR  別のフォルダに書く
"""
import argparse
import array
import math
import os
import random
import sys
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOUND_DIR = os.path.join(ROOT, "sound")
RATE = 22050
PEAK = 0.7  # 書き出すときの最大の振幅（1.0 が 16bit の上限）
TAU = 2 * math.pi


# ---------------------------------------------------------------- 部品

def silence(seconds):
    return [0.0] * int(RATE * seconds)


def envelope(n, attack, release):
    """長さ n の音の、立ち上がり attack 秒・消え際 release 秒の掛け率。両端は 0 になる。"""
    a = max(1, int(RATE * attack))
    r = max(1, int(RATE * release))
    return [min(1.0, i / a, (n - 1 - i) / r) for i in range(n)]


def tone(seconds, freq, harmonics=(1.0,), attack=0.02, release=0.05, vibrato=0.0, vibrato_hz=5.0):
    """倍音を重ねた音。freq は数か、時刻（0..1）から周波数を返す関数。harmonics は基音から順の強さ。"""
    n = int(RATE * seconds)
    f = freq if callable(freq) else (lambda _t: freq)
    out = []
    phase = 0.0
    for i in range(n):
        hz = f(i / n) * (1.0 + vibrato * math.sin(TAU * vibrato_hz * i / RATE))
        phase += TAU * hz / RATE
        out.append(sum(g * math.sin(phase * (k + 1)) for k, g in enumerate(harmonics)))
    return [s * e for s, e in zip(out, envelope(n, attack, release))]


def noise(seconds, seed, low=1.0, high=0.0, attack=0.01, release=0.05):
    """雑音。low は低域通過の係数（0..1。小さいほどこもる）、high は低域を引く係数（大きいほど高い音だけになる）。"""
    rng = random.Random(seed)
    n = int(RATE * seconds)
    out = []
    lp = base = 0.0
    for _ in range(n):
        lp += low * (rng.uniform(-1.0, 1.0) - lp)
        base += high * (lp - base)
        out.append(lp - base)
    return [s * e for s, e in zip(out, envelope(n, attack, release))]


def engine(seconds, seed, rpm, roughness, attack=0.15, release=0.4):
    """内燃機関の音。rpm は時刻（0..1）から 1 秒あたりの爆発の回数を返す関数。爆発ごとの短い脈と排気の雑音を重ねる。"""
    rng = random.Random(seed)
    n = int(RATE * seconds)
    out = []
    phase = 0.0
    lp = 0.0
    level = 1.0
    for i in range(n):
        phase += rpm(i / n) / RATE
        if phase >= 1.0:
            phase -= 1.0
            level = 1.0 + rng.uniform(-roughness, roughness)
        pulse = math.exp(-5.0 * phase)
        lp += 0.18 * (rng.uniform(-1.0, 1.0) - lp)
        body = math.sin(TAU * phase) + 0.5 * math.sin(TAU * 2 * phase) + 0.25 * math.sin(TAU * 3 * phase)
        out.append(level * (0.6 * body * (0.4 + pulse) + 1.6 * lp * pulse))
    return [s * e for s, e in zip(out, envelope(n, attack, release))]


def strike(seconds, partials, decay, attack=0.002):
    """打った金物の音。partials は (周波数, 強さ) の並び。"""
    n = int(RATE * seconds)
    env = envelope(n, attack, 0.02)
    return [env[i] * math.exp(-decay * i / RATE) * sum(g * math.sin(TAU * f * i / RATE) for f, g in partials)
            for i in range(n)]


def mix(*layers):
    """(始まる秒, 強さ, 音) を重ねる。"""
    total = max(int(RATE * at) + len(s) for at, _, s in layers)
    out = [0.0] * total
    for at, gain, s in layers:
        start = int(RATE * at)
        top = max((abs(v) for v in s), default=0.0) or 1.0  # 部品の大きさをそろえてから gain を掛ける
        for i, v in enumerate(s):
            out[start + i] += gain * v / top
    return out


def ramp(a, b):
    return lambda t: a + (b - a) * t


# ---------------------------------------------------------------- 音（車両は停留所から発車するとき、産業は生産するとき）

def bus():
    """ディーゼルのバスの発車。空気ブレーキを抜く音のあと、回転が上がる。"""
    return mix((0.0, 0.5, noise(0.35, 11, low=0.9, high=0.4, attack=0.01, release=0.25)),
               (0.2, 1.0, engine(1.5, 12, ramp(24, 52), 0.25)))


def truck():
    """トラックの発車。バスより低く重い回転。"""
    return mix((0.0, 1.0, engine(1.7, 21, ramp(17, 36), 0.35)),
               (1.1, 0.25, noise(0.4, 22, low=0.9, high=0.5, release=0.3)))


def railcar():
    """気動車の発車。短い汽笛（2 音）のあとに低い機関の音。"""
    horn = mix((0.0, 1.0, tone(0.6, 370, (1.0, 0.6, 0.4, 0.25, 0.15), attack=0.03, release=0.12)),
               (0.0, 0.8, tone(0.6, 466, (1.0, 0.6, 0.35, 0.2), attack=0.03, release=0.12)))
    return mix((0.0, 0.9, horn), (0.5, 0.7, engine(1.4, 31, ramp(20, 34), 0.2, attack=0.3)))


def tram():
    """路面電車の発車の鐘（2 回打つ）。"""
    bell = strike(0.9, ((880, 1.0), (1318, 0.6), (2217, 0.45), (3136, 0.2)), decay=5.0)
    return mix((0.0, 1.0, bell), (0.28, 1.0, bell))


def monorail():
    """モノレールの発車。モーターの唸りが上がっていく。"""
    return mix((0.0, 0.8, tone(1.8, ramp(180, 760), (1.0, 0.35, 0.15), attack=0.2, release=0.5)),
               (0.0, 0.45, tone(1.8, ramp(540, 1500), (1.0, 0.2), attack=0.4, release=0.5, vibrato=0.01, vibrato_hz=11)),
               (0.0, 0.3, noise(1.8, 51, low=0.2, attack=0.4, release=0.6)))


def ship():
    """船の汽笛。低い 1 声を長く鳴らす。"""
    return mix((0.0, 1.0, tone(1.8, 146, (1.0, 0.8, 0.55, 0.4, 0.25, 0.15), attack=0.15, release=0.35,
                               vibrato=0.004)),
               (0.0, 0.7, tone(1.8, 185, (1.0, 0.7, 0.45, 0.25), attack=0.18, release=0.35, vibrato=0.004)),
               (0.0, 0.12, noise(1.8, 61, low=0.25, attack=0.2, release=0.4)))


def airplane():
    """プロペラ機の発進。回転が上がるうなり。"""
    return mix((0.0, 1.0, engine(2.4, 71, ramp(38, 86), 0.12, attack=0.5, release=0.6)),
               (0.0, 0.35, tone(2.4, ramp(76, 172), (1.0, 0.5, 0.25), attack=0.6, release=0.6)),
               (0.3, 0.25, noise(2.1, 72, low=0.35, high=0.05, attack=0.8, release=0.7)))


def coal_mine():
    """炭鉱。巻上げ機の唸りと、炭車の金物が当たる音。"""
    clank = strike(0.35, ((410, 1.0), (1093, 0.7), (1740, 0.4)), decay=14.0)
    return mix((0.0, 0.55, tone(1.8, ramp(92, 118), (1.0, 0.6, 0.35, 0.2), attack=0.3, release=0.5,
                                vibrato=0.02, vibrato_hz=9)),
               (0.35, 0.8, clank), (0.85, 0.6, clank), (1.05, 0.45, clank),
               (1.3, 0.35, noise(0.6, 81, low=0.3, attack=0.05, release=0.45)))


def power_plant():
    """発電所。タービンの低い唸りと、蒸気を逃がす音。"""
    return mix((0.0, 0.8, tone(2.2, 100, (1.0, 0.7, 0.3, 0.2), attack=0.5, release=0.7)),
               (0.0, 0.3, tone(2.2, 301, (1.0, 0.3), attack=0.5, release=0.7, vibrato=0.006)),
               (0.5, 0.55, noise(1.4, 91, low=0.8, high=0.35, attack=0.25, release=0.8)))


# ファイル名 → 作り方。名前は英字の小文字で始める（makeobj は数字で始まる sound= を昔の番号と読む）
SOUNDS = {
    "pak256_bus.wav": bus,
    "pak256_truck.wav": truck,
    "pak256_railcar.wav": railcar,
    "pak256_tram.wav": tram,
    "pak256_monorail.wav": monorail,
    "pak256_ship.wav": ship,
    "pak256_airplane.wav": airplane,
    "pak256_coal_mine.wav": coal_mine,
    "pak256_power_plant.wav": power_plant,
}


def write_wav(path, samples):
    top = max(abs(v) for v in samples)
    data = array.array("h", (int(round(v / top * PEAK * 32767)) for v in samples))
    if sys.byteorder == "big":
        data.byteswap()
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=SOUND_DIR, help="書き先（省くと sound/）")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for name, make in SOUNDS.items():
        samples = make()
        write_wav(os.path.join(a.out, name), samples)
        print(f"[make_sounds] {name}: {len(samples) / RATE:.2f} 秒")


if __name__ == "__main__":
    main()
