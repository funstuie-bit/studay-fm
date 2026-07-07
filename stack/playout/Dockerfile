# Playout: Liquidsoap reads the seed library and publishes one continuous,
# normalised MP3 to Icecast. Pinned to the version the script was checked against.
FROM savonet/liquidsoap:v2.4.5

USER root
# python3 + PyYAML so the entrypoint can turn config.yaml into the values the
# Liquidsoap script and the site read.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-yaml \
 && rm -rf /var/lib/apt/lists/*

COPY bootstrap.py /app/bootstrap.py
COPY radio.liq   /app/radio.liq
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
