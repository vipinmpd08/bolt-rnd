# Mini dog Bolt 🐕🎤

Bolt without the robot body: a voice dog that lives in a Docker container on the Pi 4,
listens to the USB headset all the time, and answers when you say **"Bolt"**.

```
mic (always on) -> Vosk speech-to-text (offline) -> "Bolt" heard?
   -> LangGraph agents -> Piper voice -> headset
```

## The agents (LangGraph)

| Agent | What it does | Needs AI key |
|---|---|---|
| supervisor | Decides who answers (quick rules first, then the AI) | optional |
| chat | Talks in character as a cheeky dog, remembers the conversation | yes |
| helper | Uses tools: time, date, maths, the Pi's temperature and uptime | for maths |
| news | Live headlines from Google News for any country or topic ("Bolt, what's happening in the US?") | to summarise |
| memory | "Bolt, remember that...", "my name is...", "what do you remember", "forget everything" | no |
| command | "go to sleep", "wake up", "louder", "quieter", "stop" | no |

Without an API key Bolt still runs offline: time, date, memory and commands work, chat says he needs his brain.

## Talking to him

- "Bolt, what time is it?" (all in one go), or
- "Bolt" ... he says "Yes?" ... then ask within 8 seconds.

## Run on the Pi

```
cd ~/projects/bolt
nano .env                 # GROQ_API_KEY (default), or LLM_PROVIDER=grok/claude with its key
docker compose up -d --build
docker logs -f app-bolt   # watch what he hears and says
```

The container is limited to 2 CPU cores and 700 MB of memory so the websites on the Pi stay fast.
Memories are kept in `data/memory.json`.

Test the brain by typing instead of talking:

```
docker compose run --rm bolt python -m bolt.main --type
```
