"""Bolt's ears: always listening to the mic, waiting for his name.

arecord streams raw 16 kHz audio from the USB mic into two Vosk recognisers:
- a "name" recogniser that only knows the word "bolt" (everything else is [unk]),
  so it picks out his name far better than free speech recognition, which
  often hears "but", "bald" or "boat";
- a full recogniser that writes down the whole sentence.
Both finish each sentence at the same moment, so we know if the name was in it.
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
MAX_AUDIO = RATE * 2 * 30  # keep at most 30 s of one sentence

# What the full recogniser writes when it mishears "Bolt" at the start of a sentence
SOUNDALIKES = {"bolt", "bolts", "bold", "volt", "boult", "but", "bart", "bald", "board", "boat", "born",
               "bob", "ball", "bowl", "bought", "both", "gold", "void", "vault", "boats", "bolton", "colt"}


class Ears:
    def __init__(self):
        SetLogLevel(-1)
        self.model = Model(config.VOSK_MODEL)
        self.rec = KaldiRecognizer(self.model, RATE)
        self.name_rec = KaldiRecognizer(self.model, RATE, json.dumps(["hey bolt", "bolt", "[unk]"]))
        self.muted = threading.Event()  # set while Bolt is talking, so he doesn't hear himself
        self.proc = None

    def _start_mic(self):
        cmd = ["arecord", "-q", "-D", config.MIC_DEVICE, "-f", "S16_LE", "-r", str(RATE), "-c", "1", "-t", "raw"]
        log.info("Opening mic: %s", " ".join(cmd))
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def sentences(self):
        """Yield (text, heard_name, audio) for every sentence, forever. Restarts the mic if it is unplugged.

        audio is the raw PCM of that sentence, for Whisper to transcribe properly.
        """
        while True:
            self._start_mic()
            audio = bytearray()
            while True:
                data = self.proc.stdout.read(CHUNK)
                if not data:
                    break
                if self.muted.is_set():
                    audio.clear()
                    continue
                audio += data
                del audio[:-MAX_AUDIO]
                self.name_rec.AcceptWaveform(data)
                if self.rec.AcceptWaveform(data):
                    text = json.loads(self.rec.Result()).get("text", "").strip()
                    name = json.loads(self.name_rec.FinalResult()).get("text", "")
                    if text:
                        yield text, "bolt" in name.split(), bytes(audio)
                    audio.clear()
                elif not json.loads(self.rec.PartialResult()).get("partial"):
                    del audio[:-RATE * 2]  # nothing said yet: keep just the last second
            err = self.proc.stderr.read().decode(errors="ignore").strip()
            log.warning("Mic stopped (%s). Retrying in 5 s.", err or "no error text")
            time.sleep(5)

    def mute(self):
        self.muted.set()

    def unmute(self):
        # Drop anything half-heard while muted
        self.rec.Reset()
        self.name_rec.Reset()
        self.muted.clear()


def split_wake_word(text, heard_name=False):
    """Return (heard_wake_word, rest_of_sentence).

    "bolt what time is it"            -> (True, "what time is it")
    "but what time is it" + name heard -> (True, "what time is it")
    "what's for dinner"               -> (False, "")
    """
    words = text.lower().split()
    for i, w in enumerate(words):
        if w in config.WAKE_WORDS:
            return True, " ".join(words[i + 1:])
    if heard_name:
        # The name recogniser heard "Bolt"; drop the misheard name from the start of the sentence
        for i, w in enumerate(words[:3]):
            if w in SOUNDALIKES:
                return True, " ".join(words[i + 1:])
        return True, " ".join(words)
    return False, ""
