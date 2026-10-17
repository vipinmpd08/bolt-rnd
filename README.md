# Bolt 🐕⚡

Bolt is a voice-controlled AI robot dog built on the [SunFounder PiDog](https://docs.sunfounder.com/projects/pidog/en/latest/) kit and a Raspberry Pi 3B+.

The plan: you talk to Bolt, it turns your speech into text, an AI model decides what to say and do, and Bolt moves and talks back.

```
mic -> speech-to-text -> AI brain (Grok for now, swappable) -> PiDog actions + text-to-speech
```

## Hardware

- SunFounder PiDog kit (servos, Robot HAT, mic, speaker, camera, battery)
- Raspberry Pi 3 Model B+ running Raspberry Pi OS 64-bit

## Setup

1. Install SunFounder's libraries (robot-hat, vilib, pidog and the speaker script) by following their
   [Install All the Modules](https://docs.sunfounder.com/projects/pidog/en/latest/python/python_start/install_all_modules.html) guide.
2. Clone this repo on the Pi:
   ```
   git clone https://github.com/vipinmpd08/bolt-rnd.git ~/bolt-rnd
   cd ~/bolt-rnd
   ```
3. Copy the example settings and add your own API key (never commit `.env`):
   ```
   cp .env.example .env
   nano .env
   ```

## First test

With Bolt assembled and the battery on:

```
sudo python3 hello_bolt.py
```

Bolt should stand, wag his tail, bark once and lie down.

## Status

- [x] Pi OS and SunFounder libraries
- [ ] Servo zeroing and assembly (see [docs/assembly-plan.md](docs/assembly-plan.md))
- [ ] First moves (`hello_bolt.py`)
- [ ] Voice in and voice out
- [ ] AI brain picking actions and replies
