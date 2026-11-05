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

    def answer(self, text, audio=None, mode="wake"):
        """text: what Vosk heard; audio: raw PCM of it, which Whisper turns into better text.

        mode "follow" means no "Bolt" was said, so the router decides if it was meant for him.
        Returns the reply, or None when the router ignored it.
        """
        log.info("You said (%s): %s", mode, text)
        audio_id = ""
        if audio:
            audio_id = str(next(self.ids))
            self.audio[audio_id] = audio
        out = self.brain.invoke({"text": text, "audio_id": audio_id, "mode": mode}, THREAD)
        self.audio.pop(audio_id, None)
        self.turns += 1
        if self.turns % COMPACT_EVERY == 0:
            self._compact()
        if out.get("route") == "ignore":
            return None
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
    waiting_until = 0.0       # after a bare "Bolt", the next sentence is the question
    conversation_until = 0.0  # after he answers, you can keep talking without his name
    for heard, heard_name, audio in ears.sentences():
        now = time.time()
        woke, rest = split_wake_word(heard, heard_name)
        if woke:
            state = "name"
        elif now < waiting_until:
            state = "after Yes?"
        elif now < conversation_until:
            state = f"conversation, {conversation_until - now:.0f}s left"
        else:
            state = "not for Bolt"
        log.info("Heard: %s  [%s]", heard, state)
        if bolt.asleep:
            if woke and "wake" in rest:
                speak(bolt.answer(rest))
            continue
        if woke and not rest:
            speak("Yes?")
            waiting_until = time.time() + config.FOLLOW_UP_SECONDS
            continue
        if woke:
            reply = bolt.answer(rest, audio)
        elif now < waiting_until:
            reply = bolt.answer(heard, audio)
        elif now < conversation_until:
            reply = bolt.answer(heard, audio, mode="follow")
        else:
            continue
        waiting_until = 0.0
        if reply is None:
            continue  # the router decided it wasn't meant for him
        speak(reply)
        conversation_until = time.time() + config.CONVERSATION_SECONDS
        if bolt.asleep:
            conversation_until = 0.0


def type_forever():
    class Silent:
        volume = config.VOLUME

        def set_volume(self, v):
            self.volume = v

    bolt = Bolt(Silent())
    for line in sys.stdin:  # start a line with "~" to test it as speech without "Bolt"
        line = line.strip()
        if line:
            mode = "follow" if line.startswith("~") else "wake"
            reply = bolt.answer(line.lstrip("~ "), mode=mode)
            print("Bolt:", reply if reply is not None else "(ignored)", flush=True)


if __name__ == "__main__":
    type_forever() if "--type" in sys.argv else listen_forever()
