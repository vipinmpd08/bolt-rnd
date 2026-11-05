"""Bolt's voice: Piper text-to-speech played through the headset.

The voice is loaded once, and each sentence starts playing as soon as it is ready,
so Bolt begins talking while the rest of his answer is still being made.
Falls back to espeak-ng if Piper is missing or fails.
"""
import logging
import os
import subprocess

from . import config

log = logging.getLogger("voice")


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

    def _say_piper(self, text):
        from piper import SynthesisConfig

        player = None
        try:
            for chunk in self.piper.synthesize(text, syn_config=SynthesisConfig(volume=self.volume)):
                if player is None:
                    player = subprocess.Popen(
                        ["aplay", "-q", "-D", config.SPEAKER_DEVICE, "-t", "raw", "-f", "S16_LE",
                         "-r", str(chunk.sample_rate), "-c", str(chunk.sample_channels)],
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

    def say(self, text):
        if not text:
            return
        log.info("Bolt says: %s", text)
        try:
            if self.piper:
                try:
                    return self._say_piper(text)
                except Exception as e:
                    log.warning("Piper failed (%s), using espeak-ng", e)
            self._say_espeak(text)
        except Exception as e:
            log.error("Could not speak: %s", e)
