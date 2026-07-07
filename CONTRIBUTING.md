# Contributing

Thanks for your interest. This repo is a public demo and build guide for a
Studay-FM-style AI radio network: a one-command Docker demo you can run and then
grow into your own station.

## Ground rules

**No cloned real-person voices.** Do not commit, or add config that ships, voice
reference clips of real people (broadcasters, celebrities, anyone) without their
explicit permission. Presenters here are defined by persona; voices are something
each operator supplies for their own deployment. PRs that add such clips will be
closed.

**Nothing private.** No secrets, API keys, passwords, private IP addresses, or
absolute home paths. `scripts/scrub.sh` enforces this and runs in CI. Run it
before you push:

```sh
bash scripts/scrub.sh
```

**House style: no em dashes.** Use commas, colons or parentheses. The scrub
script also fails on em and en dashes.

## Developing

The whole thing is the Docker demo. To work on it:

```sh
cp .env.example .env
docker compose up --build
```

- Music-only or hosted talk is controlled by `config.yaml` (`talk.enabled`).
- The playout is Liquidsoap (`stack/playout/radio.liq`). If you change it, it is
  worth a local `liquidsoap --check`.
- The DJ pipeline is `stack/dj/dj_stock.py`; the voice contract is documented at
  the top of `stack/tts/server.py`.
- Keep the demo runnable with **no GPU, no LLM and no accounts**: built-in
  defaults (seed tracks, canned lines, espeak) must keep working, with the real
  services (ACE-Step, an LLM, Chatterbox) as opt-in swaps.

## Pull requests

- Keep the demo booting: CI runs `docker compose up` and checks the stream. Make
  sure `bash scripts/scrub.sh` passes.
- Describe what you changed and how you tested it.
- One focused change per PR where you can.
