#!/bin/sh
# Substitute the passwords from the environment into the config, then run Icecast.
# Passwords come from .env via docker-compose, so none live in the image.
set -eu

: "${ICECAST_SOURCE_PASSWORD:?ICECAST_SOURCE_PASSWORD is required}"
: "${ICECAST_ADMIN_PASSWORD:?ICECAST_ADMIN_PASSWORD is required}"

envsubst '${ICECAST_SOURCE_PASSWORD} ${ICECAST_ADMIN_PASSWORD}' \
  < /etc/icecast2/icecast.xml.tmpl > /etc/icecast2/icecast.xml

exec icecast2 -c /etc/icecast2/icecast.xml
