"""Settings, read from environment variables (the .env file next to docker-compose.yml)."""
import os


def _get(name, default=""):
    return os.environ.get(name, default).strip()


# Which AI service Bolt thinks with: groq, grok, claude, or none (offline, no API key needed)
LLM_PROVIDER = _get("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = _get("GROQ_API_KEY")
GROQ_MODEL = _get("GROQ_MODEL", "qwen/qwen3.8-27b")
XAI_API_KEY = _get("XAI_API_KEY")
XAI_MODEL = _get("XAI_MODEL", "grok-3-mini")
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")
CLAUDE_MODEL = _get("CLAUDE_MODEL", "claude-haiku-5-5")

# Accurate speech-to-text for your question: groq (Whisper, uses GROQ_API_KEY) or vosk (offline only)
STT_PROVIDER = _get("STT_PROVIDER", "groq").lower()
STT_MODEL = _get("STT_MODEL", "whisper-large-v3-turbo")

# Audio devices. Using the card name (not its number) keeps working if the number changes.
MIC_DEVICE = _get("MIC_DEVICE", "plughw:CARD=P3151,DEV=0")
SPEAKER_DEVICE = _get("SPEAKER_DEVICE", "plughw:CARD=P3151,DEV=0")
VOLUME = float(_get("VOLUME", "0.8"))
# Above 1 makes his voice higher, like a cartoon dog (1 = the normal Piper voice)
VOICE_PITCH = float(_get("VOICE_PITCH", "1.3"))

# Words the speech model may hear when you say "Bolt"
WAKE_WORDS = [w.strip().lower() for w in _get("WAKE_WORDS", "bolt,bold,volt,boult,bolts").split(",") if w.strip()]
# Seconds to wait for a question after you say just "Bolt"
FOLLOW_UP_SECONDS = float(_get("FOLLOW_UP_SECONDS", "8"))
# After Bolt answers, how long you can keep talking without saying his name
CONVERSATION_SECONDS = float(_get("CONVERSATION_SECONDS", "30"))

VOSK_MODEL = _get("VOSK_MODEL", "/models/vosk")
PIPER_VOICE = _get("PIPER_VOICE", "/models/piper/voice.onnx")

DATA_DIR = _get("DATA_DIR", "/data")
