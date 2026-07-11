# Deep dives

Technical write-ups of how the network is actually built, subsystem by subsystem.
These describe the process and the practical technique (real parameters, recipes,
and the lessons behind them), not any one private deployment. For the high-level
shape first, read [ARCHITECTURE](../ARCHITECTURE.md); to run a small version of the
whole thing, see the [demo quickstart](../../README.md#run-your-own).

| Page | What it covers |
|---|---|
| [Voices](voices.md) | Producing a presenter voice: reference clips, zero-shot cloning, render params and the "don't overdrive" lesson, the timbre and loudness post chain, the silence guard, and the swap-in contract. |
| [DJ scripts](dj-scripts.md) | Writing what the hosts say: the per-character brief, the provider-agnostic LLM call, the validate-or-reject gate, anti-staleness, and the deterministic fallback. |
| [The talk pipeline](talk-pipeline.md) | The ongoing lifecycle: render, QA, approve, and the self-healing maintenance loop that keeps every host's pool stocked, with its single-tool, hard-denylist guardrails. |
| [Music generation](music.md) | Text-to-music: the locked recipe, positive-only captions, the single-flight lock, the quality gate, per-show lanes, and the "backfill, do not wipe" rule. |
| [The newsreader](newsreader.md) | The hourly music-and-culture bulletin: feeds, dedupe and rotation, the LLM write, the track-sensitive fallback that airs it, and the render-once fan-out across stations. |
| [The station engine](station-engine.md) | The scheduler and playout: the clock, the three simultaneous track-selection rules, schedule validation, one continuous normalized MP3, and truthful now-playing. |
| [The site](site.md) | The single-page app: a small template framework over React, hash routing, a persistent player, the truthful now-playing card, and the JSON feeds it reads. |
| [Continuity and the diary](continuity.md) | The non-DJ continuity voice: hour-boundary idents, the flow-station between-track weave, and the LLM-written public diary grounded in real state. |
| [Public access and serving](serving.md) | Reaching it from the internet: an outbound-only tunnel, one hostname path-routed to the site and each mount, the one-connector law, and edge caching. |
| [Reliability](reliability.md) | Staying up: the health watchdog and its checks, transition-only alerting, the always-on service model, and the hard-won lessons behind them. |

A few principles run through all of them:

- **Approved-only playout.** Everything generated (music and talk) is a `candidate`
  until it passes an automated quality gate and becomes `approved`. Only approved
  assets air, so a bad generation cannot reach listeners.
- **Provider-agnostic LLM.** Every text task (scripts, news, the maintenance loop)
  speaks the plain OpenAI-compatible chat API, so the same setup runs on a hosted
  model or a local one by changing a base URL.
- **Heavy work off the streaming box.** Music generation and voice rendering run on
  their own nodes; the streaming box only schedules, encodes, and serves.
- **Fail safe, never silent.** Fallbacks at every layer (a deterministic script line,
  a music fallback, an empty-safe news fallback) mean a flaky backend degrades
  gracefully instead of producing dead air.
