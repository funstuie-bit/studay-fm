# The DJ: writes short breaks, voices them via the TTS service, quality-gates
# them, and drops the approved clips into the shared talk pool.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && pip install --no-cache-dir pyyaml \
 && rm -rf /var/lib/apt/lists/*

COPY dj_stock.py /app/dj_stock.py
ENTRYPOINT ["python3", "/app/dj_stock.py"]
