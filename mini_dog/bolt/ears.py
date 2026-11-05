"""Bolt's ears: always listening to the mic, waiting for his name.

arecord streams raw 16 kHz audio from the USB mic into Vosk, an offline speech
recogniser. Every finished sentence is checked for the wake word "Bolt".
"""
import json
import logging
import subprocess
import threading
import time

from vosk import KaldiRecognizer, Model, SetLogLevel

from . import config

log = logging.getLogger("ears")

RATE = 16000
CHUNK = 4000  # bytes, about 1/8 second


class Ears:
    def __init__(self):
        SetLogLevel(-1)
        self.model = Model(config.VOSK_MODEL)
        self.rec = KaldiRecognizer(self.model, RATE)
        self.muted = threading.Event()  # set while Bolt is talking, so he doesn't hear himself
        self.proc = None

    def _start_mic(self):
        cmd = ["arecord", "-q", "-D", config.MIC_DEVICE, "-f", "S16_LE", "-r", str(RATE), "-c", "1", "-t", "raw"]
        log.info("Opening mic: %s", " ".join(cmd))
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def sentences(self):
        """Yield every sentence heard, forever. Restarts the mic if it is unplugged."""
        while True:
            self._start_mic()
            while True:
                data = self.proc.stdout.read(CHUNK)
                if not data:
                    break
                if self.muted.is_set():
                    continue
                if self.rec.AcceptWaveform(data):
                    text = json.loads(self.rec.Result()).get("text", "").strip()
                    if text:
                        yield text
            err = self.proc.stderr.read().decode(errors="ignore").strip()
            log.warning("Mic stopped (%s). Retrying in 5 s.", err or "no error text")
            time.sleep(5)

    def mute(self):
        self.muted.set()

    def unmute(self):
        # Drop anything half-heard while muted
        self.rec.Reset()
        self.muted.clear()


def split_wake_word(text):
    """Return (heard_wake_word, rest_of_sentence).

    "bolt what time is it" -> (True, "what time is it")
    "hey bolt"             -> (True, "")
    "what's for dinner"    -> (False, "")
    """
    words = text.lower().split()
    for i, w in enumerate(words):
        if w in config.WAKE_WORDS:
            return True, " ".join(words[i + 1:])
    return False, ""
