# Setting up your own Studay FM

This is the build guide for a Studay-FM-style AI radio network: a self-hosted,
multi-presenter, always-on station. Read it two ways.

## The fast path (you have Docker)

1. **Run it.** `cp .env.example .env && docker compose up --build`, then open
   http://localhost:8080. One box, no GPU, no accounts: seed tracks, canned DJ
   lines and a basic robotic voice. Details in the [README](README.md).
2. **Make it yours.** Edit `config.yaml`: your `station`, your `shows`, and the
   `services` that write and voice the breaks. Drop your own tracks into
   `seed/music/`. Point `services.llm` at any OpenAI-compatible endpoint for real
   scripts, and `services.tts` at your own
   [Chatterbox](https://github.com/resemble-ai/chatterbox) (plus a reference clip
   in `voices/`) for real voices cloned from your own clips.
3. **Scale out and stay on.** Move the heavy GPU services onto their own machines
   and run the stream host always-on: `deploy/install.sh --service`. See
   [deploy/README.md](deploy/README.md).

## The deeper guide

The rest of this document is how the full live network is built, so you can grow
past the demo: multiple stations, a scheduled weekday clock, a news bulletin, a
self-healing operator loop, and the reliability work that keeps a 24/7 broadcast
up. It documents the setup and the process, not one private deployment, there are
no secrets, IPs, or host-specific paths here. Studay FM is built on the
open-source [writ-fm](https://github.com/keltokhy/writ-fm) stack.

---

## 1. What you are building

Four moving parts, deliberately decoupled so the always-on streaming box stays light:

1. **A music service** that turns a text style-caption into a finished track.
2. **A voice service** that holds a presenter's own voice, consistent, from one
   reference clip.
3. **An LLM** that writes DJ scripts, the news, and the diary, and drives an
   hourly maintenance loop.
4. **A stream host** that schedules, plays out, serves the site, and stays up.

Each of the first three is an HTTP service you can run on its own machine (put the
heavy ML where the GPU and the memory are) or collapse onto one box for a small
setup. The stream host talks to all of them over the network and never does
inference itself.

## 2. Hardware (roles, not specs)

You can run everything on one capable machine to start, but the intended shape is:

| Role | Needs | Runs |
|---|---|---|
| **Stream host** | Modest, always-on, reliable | Icecast, Liquidsoap, the operator, the site, the watchdog |
| **Voice box** | A GPU or lots of unified memory | Chatterbox TTS |
| **Music box** | A GPU | ACE-Step |
| **LLM** | Local model *or* a hosted API | The operator brain, scriptwriter, news, diary |

Keep heavy generation off the stream host. Real-time encoders get starved if a big
render or model load runs alongside them, and the stream stutters.

## 3. Prerequisites

On the stream host: [Icecast](https://icecast.org/), [Liquidsoap](https://www.liquidsoap.info/),
[Caddy](https://caddyserver.com/) (or any static server), [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
for public access, Python 3.12+ with [uv](https://github.com/astral-sh/uv), and a
per-service supervisor (launchd on macOS, systemd on Linux).

Elsewhere: an [ACE-Step](https://github.com/ace-step/ACE-Step) server, a
[Chatterbox](https://github.com/resemble-ai/chatterbox) server, and an
OpenAI-compatible LLM endpoint (a local runtime such as Ollama, or a hosted API).

## 4. The build, in order

### 4.1 Stand up the music service
Run ACE-Step as an HTTP service. Serialise requests behind a single lock, the model
is single-flight and concurrent inference is unstable. Wrap generation so every
result passes a quality gate (silence, clipping, and length checks) before it can
be filed as airable. Captions are positive-only style descriptions; front-load the
defining element of the sound.

### 4.2 Stand up the voice service
Run Chatterbox as an HTTP service. Record or source **one short reference clip per
presenter** (a clean, characterful few seconds). Every line that presenter ever
says is generated in that one consistent voice, a character of its own, not an
impersonation. Post-process each render: loudness-match it to the music and run a
silence guard so a broken clip can never reach air. Tune timbre in the post
chain, not by cranking the model's exaggeration (that bends the accent).

### 4.3 Define your stations and shows
This is the heart of the configuration. In a station/show config you declare, per
show: an id, a display name, a host, the hours and days it airs, its music lane(s),
a tone brief, the segment types the host can do, and the styles its music should be
drawn from. Weekday shows, a weekend crew, and day-restricted specials all live
here. The playout reads this to know who is on when and what they play.

Keep each show's music in its **own lane** and enforce separation: a show never
reaches into another show's lane until its own is exhausted, so a pop show never
drifts into country.

### 4.4 Generate the libraries
- **Music:** generate a starting library per lane through the music service. Do not
  wipe and regenerate all at once, regeneration is slow and an empty lane plays
  silence. Backfill the currently-airing show first.
- **Talk:** for each show, generate scripts with the LLM against the host's brief,
  render them on the voice box, then run an automated QA pass (loudness normalise,
  reject clips with long internal silence) that marks the good ones approved. Only
  approved clips air.

### 4.5 Wire the playout
Each station is a continuous, gapless, loudness-normalised MP3 produced by
Liquidsoap and published to an Icecast mount. The **operator** builds a schedule on
a fixed clock: it picks the show for each slot, chooses each track under three rules
at once (no song repeats too soon, no two same-style tracks back to back, no lane
bleed), cues the host at the show's cadence, and lets specials take their slots on
the right days. Drive the live now-playing from the *actual* file playing, not a
wall-clock guess. Validate every schedule before it airs (no gaps, no missing
shows, no empty pools).

A continuous "flow" station (no scheduled shows, just a mood with occasional
continuity and an hourly news bulletin) is a simpler Liquidsoap graph over a couple
of pools plus a timed insert, worth having as a second pattern alongside the
show-scheduled stations.

### 4.6 Serve the site and go public
Serve a single-page site (live now-playing per station, a catalogue, the operator
diary) behind Caddy with compression and edge-cache headers. Put the site and every
audio mount on one hostname with a single Cloudflare named tunnel, so there are
**no open inbound ports**, traffic is outbound-only from the stream host. Route by
path: the audio mounts to Icecast, everything else to the site.

### 4.7 The maintenance loop (the "operator agent")
Beyond scheduling, a small agent loop keeps the station healthy hour to hour: it
reads a brief of real state (the schedule, each show's talk-pool depth, the
watchdog's health), and if a talk pool is running thin it restocks it through the
script -> render -> QA pipeline. Keep it **provider-agnostic**: have it speak the
plain OpenAI-compatible chat API with a single shell tool, so it runs on a local
model or a hosted one by changing a base URL. Give it a hard denylist (never touch
the stream, never delete, never spend money without a human) and log every action.

### 4.8 Always-on and self-healing
Run every component as its own supervised service with automatic restart. Add a
**watchdog** that checks, on a short interval, that every mount serves, every
station is actually advancing, the backends respond, and no content pool has
drained, and that alerts you (a webhook to chat works well) on any transition into
a fault. Give the real-time encoders interactive/high priority so background work
never starves them.

## 5. Customising it into your own station

- **New presenter:** add a reference clip, a persona brief (tone, allowed and
  forbidden topics, segment types), a music lane, and a slot on the clock. Generate
  their scripts and music, and they are on air.
- **New station:** add its mount to Icecast, a Liquidsoap graph, a tunnel route, and
  a card on the site.
- **Different taste:** the whole character of the network is in the show briefs and
  the music captions. That is where you make it yours.

## 6. Hard-won lessons (read before you scale)

- **Real-time audio must be high priority.** Throttled encoders fall behind under
  load. Interactive priority fixes it.
- **Keep a fallback for every backend** so a flaky model never takes a DJ off air.
- **Single-flight ML scales with nodes, not concurrency.** One global lock; add
  machines to go faster.
- **Quality-gate everything generated.** A cheap automated check culls duds before
  they air; a silence guard saves the dead-air clips. Ears remain the final judge.
- **Put the model where the memory is.** Moving heavy generation off the stream host
  ends a whole class of crashes.
- **Do not wipe a library all at once.** Backfill the current show first.
- **Retire old services cleanly.** A stale, still-enabled stream or content job that
  resurfaces on a reboot is a classic self-inflicted outage. When you replace a
  component, remove the old one from the load path, do not just stop it.

---

*Studay FM is built on [writ-fm](https://github.com/keltokhy/writ-fm), with music by
[ACE-Step](https://github.com/ace-step/ACE-Step) and voices by
[Chatterbox](https://github.com/resemble-ai/chatterbox).*
