"""Mini dog Bolt: listens to the mic all the time and answers when you say "Bolt".

    python -m bolt.main          # listen to the mic
    python -m bolt.main --type   # type instead of talking (for testing)
"""
import itertools
import logging
import sys
import time

from . import config
from .graph import KEEP, build
from .llm import make_llm
from .stt import Whisper

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("bolt")

THREAD = {"configurable": {"thread_id": "home"}}
COMPACT_EVERY = 25  # turns; the checkpointer keeps every step, so old ones are dropped now and then


class Bolt:
    def __init__(self, voice):
        self.audio = {}
        self.brain = build(make_llm(), Whisper(), self.audio)
        self.voice = voice
        self.asleep = False
        self.turns = 0
        self.ids = itertools.count()

    def _compact(self):
        messages = self.brain.get_state(THREAD).values.get("messages", [])[-KEEP:]
        self.brain.checkpointer.delete_thread(THREAD["configurable"]["thread_id"])
        if messages:
            self.brain.update_state(THREAD, {"messages": messages}, as_node="command")

    def answer(self, text, audio=None):
        """text: what Vosk heard; audio: raw PCM of it, which Whisper turns into better text."""
        log.info("You said: %s", text)
        audio_id = ""
        if audio:
            audio_id = str(next(self.ids))
            self.audio[audio_id] = audio
        out = self.brain.invoke({"text": text, "audio_id": audio_id}, THREAD)
        self.audio.pop(audio_id, None)
        self.turns += 1
        if self.turns % COMPACT_EVERY == 0:
            self._compact()
        action = out.get("action", "")
        if action == "sleep":
            self.asleep = True
        elif action == "wake":
            self.asleep = False
        elif action == "volume_up":
            self.voice.set_volume(self.voice.volume + 0.2)
        elif action == "volume_down":
            self.voice.set_volume(self.voice.volume - 0.2)
        return out["reply"]


def listen_forever():
    from .ears import Ears, split_wake_word
    from .voice import Voice

    voice = Voice()
    ears = Ears()
    bolt = Bolt(voice)

    def speak(text):
        ears.mute()
        try:
            voice.say(text)
        finally:
            ears.unmute()

    speak("Woof! Bolt is listening.")
    waiting_until = 0.0  # after a bare "Bolt", the next sentence is the question
    for heard, heard_name, audio in ears.sentences():
        log.info("Heard: %s%s", heard, "  [name]" if heard_name else "")
        woke, rest = split_wake_word(heard, heard_name)
        if bolt.asleep:
            if woke and "wake" in rest:
                speak(bolt.answer(rest))
            continue
        if woke and not rest:
            speak("Yes?")
            waiting_until = time.time() + config.FOLLOW_UP_SECONDS
            continue
        if woke:
            question = rest
        elif time.time() < waiting_until:
            question = heard
        else:
            continue
        waiting_until = 0.0
        speak(bolt.answer(question, audio))


def type_forever():
    class Silent:
        volume = config.VOLUME

        def set_volume(self, v):
            self.volume = v

    bolt = Bolt(Silent())
    for line in sys.stdin:
        if line.strip():
            print("Bolt:", bolt.answer(line.strip()), flush=True)


if __name__ == "__main__":
    type_forever() if "--type" in sys.argv else listen_forever()
