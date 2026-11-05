"""Long-term memory: a small JSON list of facts kept in the data volume."""
import json
import os
import threading

from . import config

_PATH = os.path.join(config.DATA_DIR, "memory.json")
_lock = threading.Lock()


def load_facts():
    try:
        with open(_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def add_fact(fact):
    with _lock:
        facts = load_facts()
        if fact not in facts:
            facts.append(fact)
        os.makedirs(config.DATA_DIR, exist_ok=True)
        with open(_PATH, "w") as f:
            json.dump(facts[-100:], f, indent=1)


def forget_all():
    with _lock:
        if os.path.exists(_PATH):
            os.remove(_PATH)
