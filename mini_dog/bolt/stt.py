"""Accurate speech-to-text: send what you said to Whisper on Groq.

Vosk (offline) is good enough to spot "Bolt", but Whisper understands whole
sentences much better. If there is no key or the call fails, the Vosk text is used.
"""
import io
import logging
import re
import wave

from . import config

log = logging.getLogger("stt")

# Helps Whisper spell the names it will hear
HINT = "Bolt is a dog. Vipindas is talking to Bolt."


class Whisper:
    def __init__(self):
        self.client = None
        if config.STT_PROVIDER == "groq" and config.GROQ_API_KEY:
            from openai import OpenAI

            self.client = OpenAI(api_key=config.GROQ_API_KEY, base_url="https://api.groq.com/openai/v1",
                                 timeout=15, max_retries=1)
            log.info("Speech-to-text: Whisper on Groq (%s)", config.STT_MODEL)
        else:
            log.info("Speech-to-text: Vosk only")

    def transcribe(self, audio, rate=16000):
        """audio: raw 16-bit mono PCM. Returns the text, or None if Whisper is not available."""
        if not self.client or not audio:
            return None
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(audio)
        buf.name = "speech.wav"
        buf.seek(0)
        try:
            r = self.client.audio.transcriptions.create(
                model=config.STT_MODEL, file=buf, language="en", prompt=HINT, temperature=0,
            )
            return r.text.strip()
        except Exception as e:
            log.warning("Whisper failed (%s), using Vosk text", e)
            return None


def strip_name(text):
    """'Hey Bolt, what time is it?' -> 'what time is it?'"""
    return re.sub(r"^\W*(hey\W+|okay\W+|ok\W+)?bolt\b\W*", "", text, flags=re.I).strip()
