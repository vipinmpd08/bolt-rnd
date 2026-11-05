"""Settings, read from environment variables (the .env file next to docker-compose.yml)."""
import os


def _get(name, default=""):
    return os.environ.get(name, default).strip()


# Which AI service Bolt thinks with: grok, claude, or none (offline, no API key needed)
LLM_PROVIDER = _get("LLM_PROVIDER", "grok").lower()
XAI_API_KEY = _get("XAI_API_KEY")
XAI_MODEL = _get("XAI_MODEL", "grok-3-mini")
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = _get("CLAUDE_MODEL", "claude-haiku-5-5")

# Audio devices. Using the card name (not its number) keeps working if the number changes.
MIC_DEVICE = _get("MIC_DEVICE", "plughw:CARD=P3151,DEV=0")
SPEAKER_DEVICE = _get("SPEAKER_DEVICE", "plughw:CARD=P3151,DEV=0")
VOLUME = float(_get("VOLUME", "0.8"))

# Words the speech model may hear when you say "Bolt"
WAKE_WORDS = [w.strip().lower() for w in _get("WAKE_WORDS", "bolt,bold,volt,boult,bolts").split(",") if w.strip()]
# Seconds to wait for a question after you say just "Bolt"
FOLLOW_UP_SECONDS = float(_get("FOLLOW_UP_SECONDS", "8"))

VOSK_MODEL = _get("VOSK_MODEL", "/models/vosk")
PIPER_VOICE = _get("PIPER_VOICE", "/models/piper/voice.onnx")

DATA_DIR = _get("DATA_DIR", "/data")
