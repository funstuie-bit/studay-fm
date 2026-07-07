# Minimal Icecast server. Built from Debian so there is no dependency on a
# third-party image, and so you can read exactly what it does.
FROM debian:stable-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends icecast2 gettext-base \
 && rm -rf /var/lib/apt/lists/*

COPY icecast.xml.tmpl /etc/icecast2/icecast.xml.tmpl
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
