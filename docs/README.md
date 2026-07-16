# Studay FM deep dives

These pages describe the production design without publishing a private
deployment. The deep dives are flattened directly into `docs/` in this public
repository.

Start with [Architecture](ARCHITECTURE.md), then choose a subsystem:

| Page | What it covers |
|---|---|
| [Presenters](PRESENTERS.md) | Fictional roster, schedule, voice intent, provenance boundary |
| [Station engine](station-engine.md) | Five playouts, flagship clock, approved manifests, continuous MP3, truthful now-playing |
| [Music generation](music.md) | ACE-Step recipe, authenticated bounded API, queue v2, technical QA, lane rotation |
| [Voices](voices.md) | Reference-conditioned speech, one-shot creative intent, renderer containment, post-processing, QA |
| [DJ scripts](dj-scripts.md) | Character briefs, bounded LLM calls, validation, candidate metadata, deterministic fallback |
| [Talk pipeline](talk-pipeline.md) | Fixed producer workflow, review, QA, manifests, stocking, freshness, retirement |
| [Newsreader](newsreader.md) | Bounded feeds, structured source IDs, attribution gate, render-once fan-out |
| [Continuity and diary](continuity.md) | Hour markers, flow links, grounded diary, atomic publication |
| [Site](site.md) | Five-station SPA, validated live JSON, persistent player, privacy and frontend constraints |
| [Serving](serving.md) | Loopback origins, outbound tunnel, path allowlist, public build boundary, headers |
| [Reliability](reliability.md) | Watchdog, readiness, queue recovery, transition alerts, service isolation, retention |

## Principles shared by every subsystem

- **Studay is canonical.** Legacy names are historical upstream attribution, not
  current runtime identities.
- **Approved-only playout.** Review, current technical QA, and an atomic manifest
  are all required.
- **State is contracted and atomic.** Writers validate before durable replace;
  readers reject malformed or stale evidence.
- **Models do not administer the station.** The current operator and private ops
  bot share one typed read-only query surface.
- **Local self-governance is deferred.** The local coordinator and earlier
  local-model Hermes setup were unreliable; the current private Hermes gateway
  uses a bounded DeepSeek fallback while mutation remains owner-controlled.
- **Internal APIs are still security boundaries.** Authentication, size limits,
  path containment, symlink rejection, and single-flight behavior apply on the
  LAN too.
- **News is source-traceable and fail-closed.** Attribution and metadata are
  required, but human correction and source curation remain necessary.
- **Heavy work stays off the audio path.** Music and voice generation do not
  compete with real-time encoders.
- **Media lives outside Git-adjacent storage.** Retention is audit-first and does
  not delete approved or active material.
- **The public site is an allowlisted build.** The repository, private state,
  candidate review, references, and operations documents are not web roots.

For the small Docker-compatible demo, return to the
[README quickstart](../README.md#run-your-own) and [SETUP.md](../SETUP.md).
