"""Bolt's voice: Piper text-to-speech played through the headset.

Falls back to espeak-ng if Piper is missing or fails.
"""
import array
import logging
import os
import subprocess
import tempfile
import wave

from . import config

log = logging.getLogger("voice")


class Voice:
    def __init__(self):
        self.volume = config.VOLUME

    def set_volume(self, value):
        self.volume = max(0.1, min(1.0, value))
        return self.volume

    def _tts(self, text, path):
        if os.path.exists(config.PIPER_VOICE):
            try:
                subprocess.run(
                    ["piper", "-m", config.PIPER_VOICE, "-f", path],
                    input=text.encode(), check=True, capture_output=True, timeout=60,
                )
                return
            except Exception as e:
                log.warning("Piper failed (%s), using espeak-ng", e)
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "165", "-w", path, text], check=True, timeout=60)

    def _apply_volume(self, path):
        with wave.open(path, "rb") as w:
            params = w.getparams()
            frames = w.readframes(w.getnframes())
        if params.sampwidth != 2:
            return
        samples = array.array("h", frames)
        for i, s in enumerate(samples):
            samples[i] = int(s * self.volume)
        with wave.open(path, "wb") as w:
            w.setparams(params)
            w.writeframes(samples.tobytes())

    def say(self, text):
        if not text:
            return
        log.info("Bolt says: %s", text)
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            self._tts(text, path)
            self._apply_volume(path)
            subprocess.run(["aplay", "-q", "-D", config.SPEAKER_DEVICE, path], check=False, timeout=120)
        except Exception as e:
            log.error("Could not speak: %s", e)
        finally:
            os.remove(path)
