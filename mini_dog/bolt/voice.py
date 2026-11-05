"""Bolt's voice: Piper text-to-speech played through the headset.

To sound like a cartoon dog rather than a grown man, speech is made slower and
then played faster (VOICE_PITCH), which raises the pitch without speeding him up.
Every "woof" or "ruff" in a reply is played as a real bark sound instead.

The voice is loaded once, and each sentence starts playing as soon as it is ready,
so Bolt begins talking while the rest of his answer is still being made.
Falls back to espeak-ng if Piper is missing or fails.
"""
import logging
import os
import re
import subprocess

from . import config
from .bark import RATE as BARK_RATE, bark_pcm

log = logging.getLogger("voice")

# "woof", "woof woof", "ruff!", "arf arf" ... become barks
BARK_WORDS = r"\b(?:woo+f|ru+ff|arf)\b"
BARK_RE = re.compile(rf"({BARK_WORDS}(?:[\s,!.-]+{BARK_WORDS})*)[!.,]*", re.I)


class Voice:
    def __init__(self):
        self.volume = config.VOLUME
        self.piper = None
        if os.path.exists(config.PIPER_VOICE):
            try:
                from piper import PiperVoice

                self.piper = PiperVoice.load(config.PIPER_VOICE)
                log.info("Piper voice loaded")
            except Exception as e:
                log.warning("Could not load Piper (%s), using espeak-ng", e)

    def set_volume(self, value):
        self.volume = max(0.1, min(1.0, value))
        return self.volume

    def _play(self, pcm, rate):
        subprocess.run(["aplay", "-q", "-D", config.SPEAKER_DEVICE, "-t", "raw", "-f", "S16_LE",
                        "-r", str(rate), "-c", "1"], input=pcm, timeout=60)

    def bark(self, count=1):
        self._play(bark_pcm(count, self.volume), BARK_RATE)

    def _say_piper(self, text):
        from piper import SynthesisConfig

        pitch = config.VOICE_PITCH
        syn = SynthesisConfig(volume=self.volume, length_scale=pitch)
        player = None
        try:
            for chunk in self.piper.synthesize(text, syn_config=syn):
                if player is None:
                    player = subprocess.Popen(
                        ["aplay", "-q", "-D", config.SPEAKER_DEVICE, "-t", "raw", "-f", "S16_LE",
                         "-r", str(int(chunk.sample_rate * pitch)), "-c", str(chunk.sample_channels)],
                        stdin=subprocess.PIPE,
                    )
                player.stdin.write(chunk.audio_int16_bytes)
                player.stdin.flush()
        finally:
            if player:
                player.stdin.close()
                player.wait(timeout=120)

    def _say_espeak(self, text):
        amplitude = str(int(200 * self.volume))
        espeak = subprocess.Popen(["espeak-ng", "-v", "en-us", "-s", "165", "-a", amplitude, "--stdout", text],
                                  stdout=subprocess.PIPE)
        subprocess.run(["aplay", "-q", "-D", config.SPEAKER_DEVICE], stdin=espeak.stdout, timeout=120)
        espeak.wait()

    def _speak(self, text):
        if self.piper:
            try:
                return self._say_piper(text)
            except Exception as e:
                log.warning("Piper failed (%s), using espeak-ng", e)
        self._say_espeak(text)

    def say(self, text):
        if not text:
            return
        log.info("Bolt says: %s", text)
        try:
            # Split into speech and barks: "Woof! Hi there. Ruff ruff" -> bark, "Hi there.", 2 barks
            for i, part in enumerate(BARK_RE.split(text)):
                if i % 2:
                    self.bark(min(3, len(re.findall(BARK_WORDS, part, re.I))))
                elif re.search(r"\w", part):
                    self._speak(part.strip(" ,"))
        except Exception as e:
            log.error("Could not speak: %s", e)
