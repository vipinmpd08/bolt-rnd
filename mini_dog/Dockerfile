FROM python:3.12-slim-bookworm

# alsa-utils: arecord/aplay for the USB headset; espeak-ng: backup voice
RUN apt-get update \
 && apt-get install -y --no-install-recommends alsa-utils espeak-ng curl unzip ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Offline speech recogniser (about 40 MB) and Bolt's voice (about 60 MB)
RUN mkdir -p /models/piper \
 && curl -fsSL -o /tmp/vosk.zip https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip \
 && unzip -q /tmp/vosk.zip -d /models && mv /models/vosk-model-small-en-us-0.15 /models/vosk && rm /tmp/vosk.zip \
 && curl -fsSL -o /models/piper/voice.onnx https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/joe/medium/en_US-joe-medium.onnx \
 && curl -fsSL -o /models/piper/voice.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/joe/medium/en_US-joe-medium.onnx.json

# Vosk's library needs libatomic (a separate layer so earlier layers stay cached)
RUN apt-get update && apt-get install -y --no-install-recommends libatomic1 && rm -rf /var/lib/apt/lists/*

# Real bark recordings from SunFounder's PiDog project (GPL-2.0), fetched at build time
# rather than copied into this repo, and turned into WAV files
ARG PIDOG_SOUNDS=https://raw.githubusercontent.com/sunfounder/pidog/cee4bff0874641143c1dad101a40ba88897a4c20/sounds
RUN apt-get update && apt-get install -y --no-install-recommends mpg123 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /sounds && cd /sounds \
 && for f in single_bark_1 single_bark_2; do \
      curl -fsSL -o $f.mp3 $PIDOG_SOUNDS/$f.mp3 && mpg123 -q -m -w $f.wav $f.mp3 && rm $f.mp3; \
    done

COPY bolt /app/bolt
WORKDIR /app
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "bolt.main"]
