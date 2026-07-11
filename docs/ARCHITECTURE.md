# Architecture

Studay FM is built so that the always-on streaming box stays light while the heavy machine-learning work runs as independent services. The three expensive jobs, composing music, voicing the DJs, and writing the programming, are decoupled, so they can run on one machine or several.

## The three services

**Music**, a local text-to-music foundation model (ACE-Step) runs as an HTTP service. Given a positive-only style caption it returns a finished track. Generation is serialised behind a single lock (the model is single-flight; concurrent inference is unstable), and every result passes a quality gate (silence, clipping and length checks) before it can ever air.

**Voice**, a zero-shot TTS (Chatterbox) runs on a separate box with plenty of unified memory. Each presenter has one short reference clip that fixes their voice; every line they say is generated in that one consistent voice, a character of its own rather than an impersonation. Renders are loudness-matched to the music and pass a silence guard so a broken clip can never reach the air.

**Language**, an LLM writes every DJ break, the news bulletin, and the continuity diary, each in the right voice, against a per-character brief with allowed and forbidden topics and a validation pass that rejects off-voice output. It also drives a maintenance loop (below). The LLM layer is **provider-agnostic**: it speaks the plain OpenAI-compatible chat API, so the whole thing runs on a local model or a hosted one by changing a base URL, and different tasks can point at different models.

## The operator

The operator is the part that makes it feel like a real station rather than a shuffle. It builds a full schedule on a fixed clock, and for every slot it:

- **picks the show** for that hour (a full weekday clock, a weekend crew that swaps in on Saturday and Sunday, and weekly specials taking over their slots on the right days)
- **chooses each track** from the correct show's music lane, honouring three rules at once:
  - no song repeats too soon (a wide rotation gap)
  - no two tracks of the same style play back to back (genre spacing)
  - a show never reaches into another show's lane until its own and its compatible lanes are exhausted (so a pop show never drifts into country)
- **cues the DJ** at the show's natural cadence, choosing a break that hasn't aired recently
- **threads continuity** with the Signalman between programmes
- **writes the diary**, a short reflective note in the Signalman's voice on the state of the station

The schedule is validated before it goes live (no impossible gaps, no missing shows, no empty pools) and the live now-playing is driven by the *actual* file playing, not a wall-clock guess.

Separately, a lightweight **maintenance loop** keeps the station healthy hour to hour. It reads a brief of real state (the schedule, each show's talk-pool depth, the watchdog's health) and, if a talk pool is running thin, restocks it through the script -> render -> quality-gate pipeline. It is the same provider-agnostic LLM layer with a single shell tool and a hard denylist (never touch the stream, never delete, never spend money without a human), and every action is logged.

## Playout

The network runs several stations at once: show-scheduled stations like the flagship, and continuous "flow" stations (a lo-fi channel, a yacht/house channel, a jazz-hop channel, and a European-flavoured eclectic channel that also carries an hourly music-and-culture news bulletin). Each station is a continuous, gapless, loudness-normalised **MP3** stream produced by Liquidsoap and published to its own Icecast mount. This replaced an earlier per-track playout that produced timing discontinuities and didn't play in every browser. The real-time encoders run at interactive process priority so they are never starved by background work, the difference between a broadcast that holds and one that stutters.

## Public access and serving

A single Cloudflare named tunnel puts the website and every audio mount on one hostname with **no open inbound ports**, traffic is outbound-only from the stream host. The static single-page site is served with compression and edge caching, so the heavy assets are served from the CDN edge rather than round-tripping to the box on every request.

## Always-on

Every component runs as its own user-level service with automatic restart, plus health watchdogs that alert the moment a mount drops, a station goes silent, or a backend stops responding. The content libraries and the schedule self-heal: a thin pool tops itself up, and a rebuilt schedule re-syncs to the wall clock.

## Hard-won lessons

A 24/7 broadcast is mostly the unglamorous reliability work:

- **Real-time audio must be high priority.** Encoders left at a throttled QoS get starved under load and fall behind real time. Interactive priority fixes it.
- **Keep a fallback for every fancy backend** so a flaky model never takes a DJ off the air.
- **Single-flight ML scales with nodes, not concurrency.** One global lock; add machines to go faster.
- **Quality-gate everything generated**, a cheap automated check culls duds before they air, and a silence guard saves the dead-air clips.
- **Put the model where the memory is.** Moving heavy generation off the streaming box ends a whole class of crashes and frees its resources for the streams.
- **Don't wipe a library all at once**, regeneration is slow, and a show that rolls in empty plays silence. Backfill the current show first.

---

*This document is a high-level overview. For a step-by-step build guide, see [SETUP.md](../SETUP.md). For subsystem-by-subsystem technical write-ups (voices, DJ scripts, the talk pipeline, music generation, the newsreader, the station engine), see the [deep dives](deep-dive/).*
