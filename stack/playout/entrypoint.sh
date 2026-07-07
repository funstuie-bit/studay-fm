#!/bin/sh
# Turn config.yaml into the small files the rest of the stack reads, then start
# Liquidsoap. Liquidsoap reconnects on its own if Icecast is not ready yet, so a
# short head start is enough.
set -eu

echo "[playout] generating station files from config.yaml"
python3 /app/bootstrap.py /config.yaml /shared

echo "[playout] giving Icecast a head start"
sleep 3

# If talk is enabled, wait briefly for the DJ to stock the pool so the breaks are
# present when Liquidsoap builds its graph. New clips are still picked up live.
TALK_EVERY="$(grep -oE 'station_talk_every = [0-9]+' /shared/station.liq | grep -oE '[0-9]+$' || echo 0)"
if [ "${TALK_EVERY:-0}" -gt 0 ]; then
  echo "[playout] waiting up to 120s for the DJ to stock the talk pool"
  i=0
  while [ "$i" -lt 60 ]; do
    if ls /talk/*.wav >/dev/null 2>&1; then echo "[playout] talk pool ready"; break; fi
    i=$((i + 1)); sleep 2
  done
fi

echo "[playout] starting Liquidsoap"
exec liquidsoap /app/radio.liq
