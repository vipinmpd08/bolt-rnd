"""Synthetic dog barks, made in code so there are no sound files to download.

A bark is a short burst: a sharp attack, a pitch that jumps up and falls, a few
rough harmonics and some breathy noise, then a quick fade.
"""
import array
import math
import random

RATE = 22050


def _one_bark(start_hz, end_hz, length, rng):
    n = int(RATE * length)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / n
        # Pitch jumps up a little in the first 15%, then falls
        f = start_hz * (1 + 0.25 * t / 0.15) if t < 0.15 else start_hz * 1.25 + (end_hz - start_hz * 1.25) * (t - 0.15) / 0.85
        phase += 2 * math.pi * f / RATE
        tone = (math.sin(phase) + 0.6 * math.sin(2 * phase) + 0.35 * math.sin(3 * phase)
                + 0.2 * math.sin(4 * phase))
        tone = math.tanh(1.8 * tone)  # growl: clip the wave
        noise = rng.uniform(-1, 1)
        env = min(1.0, t / 0.03) * math.exp(-4.5 * t)  # fast attack, quick decay
        out.append(env * (0.8 * tone + 0.35 * noise))
    return out


def bark_pcm(count=1, volume=0.8, seed=None):
    """Raw 16-bit mono PCM at 22050 Hz: `count` barks with short gaps."""
    rng = random.Random(seed)
    samples = []
    for k in range(count):
        base = rng.uniform(420, 560)
        samples += _one_bark(base, base * 0.55, rng.uniform(0.16, 0.22), rng)
        samples += [0.0] * int(RATE * (0.12 if k < count - 1 else 0.08))
    peak = max(abs(s) for s in samples) or 1.0
    pcm = array.array("h", (int(32000 * volume * s / peak) for s in samples))
    return pcm.tobytes()
