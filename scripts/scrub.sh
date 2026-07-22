#!/usr/bin/env bash
# Guard the public repo: fail if anything private or off-style sneaks in.
# Run before every push; CI runs it too. Add real paths/hosts here if they ever
# become a risk for your fork.
set -uo pipefail

cd "$(dirname "$0")/.."

# Patterns that must never appear in the public tree.
#  - private LAN IPs, absolute home paths, obvious secrets
#  - em dashes and en dashes (house style: never)
PATTERNS='192\.168\.[0-9]|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]|/Users/[a-z]|/home/[a-z]+/|BEGIN (RSA|OPENSSH) PRIVATE KEY|sk-[a-zA-Z0-9]{20}|—|–'

# Do not scan the repo plumbing, binaries, or this script's own pattern list.
HITS=$(grep -rInE "$PATTERNS" . \
  --exclude-dir=.git \
  --exclude='.git' \
  --exclude='*.mp3' --exclude='*.wav' --exclude='*.png' --exclude='*.webp' \
  --exclude='scrub.sh' 2>/dev/null || true)

if [ -n "$HITS" ]; then
  echo "scrub FAILED: private markers or em dashes found:"
  echo "$HITS"
  exit 1
fi

echo "scrub OK: no private markers or em dashes."
