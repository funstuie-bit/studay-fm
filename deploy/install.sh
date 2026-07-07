#!/usr/bin/env bash
# Studay FM installer for the STREAM HOST (the always-on box that runs Icecast,
# Liquidsoap, the site, and the DJ). It builds and starts the Docker stack, runs
# a health check, and can install an always-on service.
#
#   deploy/install.sh              build + run once
#   deploy/install.sh --service    also install a boot service (systemd/launchd)
#
# The heavy GPU services (music via ACE-Step, voices via Chatterbox) run on their
# own machines: install those from their own projects and point config.yaml at
# their URLs. See deploy/README.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

compose() {
  if docker compose version >/dev/null 2>&1; then docker compose "$@"
  else docker-compose "$@"; fi
}

preflight() {
  command -v docker >/dev/null 2>&1 || {
    echo "Docker is required. See https://docs.docker.com/get-docker/"; exit 1; }
  docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1 || {
    echo "docker compose (or docker-compose) is required."; exit 1; }
}

ensure_env() {
  [ -f .env ] && { echo ".env exists, leaving it as is."; return; }
  cp .env.example .env
  if command -v openssl >/dev/null 2>&1; then
    local src adm
    src="$(openssl rand -hex 12)"; adm="$(openssl rand -hex 12)"
    sed -i.bak \
      -e "s/^ICECAST_SOURCE_PASSWORD=.*/ICECAST_SOURCE_PASSWORD=${src}/" \
      -e "s/^ICECAST_ADMIN_PASSWORD=.*/ICECAST_ADMIN_PASSWORD=${adm}/" .env
    rm -f .env.bak
    echo "created .env with random Icecast passwords."
  else
    echo "created .env from .env.example. Edit the passwords before exposing it."
  fi
}

env_val() { grep -E "^$1=" .env 2>/dev/null | head -1 | cut -d= -f2- ; }

health_check() {
  local port web ok=0 i
  port="$(env_val ICECAST_PORT)"; port="${port:-8000}"
  web="$(env_val WEB_PORT)"; web="${web:-8080}"
  echo "waiting for the stream to come up..."
  for i in $(seq 1 90); do
    if curl -sf "http://localhost:${port}/status-json.xsl" 2>/dev/null | grep -q "radio.mp3"; then
      ok=1; break
    fi
    sleep 2
  done
  if [ "$ok" = 1 ]; then
    echo "OK. Stream: http://localhost:${port}/radio.mp3   Site: http://localhost:${web}"
  else
    echo "The stream did not report ready in time. Check: $(basename "$0") logs, or 'docker compose logs'."
  fi
}

install_systemd() {
  local unit="/etc/systemd/system/studayfm-demo.service"
  # systemd needs an absolute path in ExecStart.
  local dc
  if docker compose version >/dev/null 2>&1; then dc="$(command -v docker) compose"
  else dc="$(command -v docker-compose)"; fi
  echo "installing systemd unit at ${unit} (needs sudo)..."
  sed -e "s#__ROOT__#${ROOT}#g" -e "s#__DC__#${dc}#g" \
    deploy/studayfm-demo.service | sudo tee "$unit" >/dev/null
  sudo systemctl daemon-reload
  sudo systemctl enable --now studayfm-demo.service
  echo "installed. Manage with: sudo systemctl status studayfm-demo"
}

install_launchd() {
  local plist="$HOME/Library/LaunchAgents/com.studayfm.demo.plist"
  echo "installing launchd agent at ${plist}..."
  mkdir -p "$HOME/Library/LaunchAgents"
  sed -e "s#__ROOT__#${ROOT}#g" -e "s#__HOME__#${HOME}#g" deploy/com.studayfm.demo.plist > "$plist"
  launchctl unload "$plist" 2>/dev/null || true
  launchctl load "$plist"
  echo "installed. Manage with: launchctl list | grep studayfm"
}

install_service() {
  case "$(uname -s)" in
    Linux)  install_systemd ;;
    Darwin) install_launchd ;;
    *) echo "--service is only wired for Linux (systemd) and macOS (launchd)." ;;
  esac
}

main() {
  preflight
  ensure_env
  echo "building and starting the stack (first build pulls images, give it a few minutes)..."
  compose up -d --build
  health_check
  [ "${1:-}" = "--service" ] && install_service
  echo "done."
}

main "$@"
