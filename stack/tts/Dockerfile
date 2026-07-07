# The demo's built-in voice: espeak-ng behind a tiny HTTP server. No GPU, no
# model download. Robotic on purpose. Swap it for Chatterbox (same contract) to
# get cloned voices; see stack/tts/server.py for the contract.
FROM debian:stable-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends espeak-ng python3 \
 && rm -rf /var/lib/apt/lists/*

COPY server.py /app/server.py
EXPOSE 5002
ENTRYPOINT ["python3", "/app/server.py"]
