"""Real dog barks: recordings from SunFounder's PiDog project, fetched when the image is built.

The WAV files live in /sounds (see the Dockerfile). Each bark picks one of them at random.
"""
import array
import glob
import logging
import random
import wave

log = logging.getLogger("bark")

SOUNDS_DIR = "/sounds"


def _load():
    clips = []
    for path in sorted(glob.glob(f"{SOUNDS_DIR}/*bark*.wav")):
        with wave.open(path) as w:
            if w.getsampwidth() == 2 and w.getnchannels() == 1:
                clips.append((w.getframerate(), w.readframes(w.getnframes())))
    if clips:
        log.info("Loaded %d bark sounds", len(clips))
    else:
        log.warning("No bark sounds found in %s", SOUNDS_DIR)
    return clips


CLIPS = _load()


def bark_pcm(count=1, volume=0.8):
    """(raw 16-bit mono PCM, sample rate) for `count` barks with short gaps, or (b"", 0) if none."""
    if not CLIPS:
        return b"", 0
    rate = CLIPS[0][0]
    clips = [pcm for r, pcm in CLIPS if r == rate]
    gap = b"\0\0" * int(rate * 0.08)
    out = array.array("h")
    for _ in range(count):
        out.frombytes(random.choice(clips) + gap)
    for i, s in enumerate(out):
        out[i] = int(s * volume)
    return out.tobytes(), rate
