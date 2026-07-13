# Deep dive: reliability (the watchdog and always-on)

A 24/7 broadcast is mostly the unglamorous work of staying up. Three things carry it: a
health watchdog that catches faults the moment they happen, an always-on service model
that restarts every component automatically, and a set of hard-won lessons, each one the
scar of a past outage.

## 1. The watchdog

A stateless job runs **every 15 minutes**: it computes every check, diffs the results
against the previous run's state, emits an event for anything that flipped, rewrites a
state file, regenerates a status page, and exits. Every check exists because of a real
incident, this is failure-driven monitoring, not a generic template.

### The checks

- **Stream reachability**: each per-station mount must return `200` locally; the public
  URL must return `200` through the edge (catches tunnel breakage local checks miss); and
  the streaming server's connected-source count must equal the expected number of
  stations (catches an encoder that is alive but whose source silently dropped, a station
  dead while looking up).
- **Tunnel integrity**: exactly **one** connector is registered (more than one is
  split-brain, see [Serving](serving.md)). Exactly one is law.
- **Stream advancing**: each station's now-playing state file must have changed in the
  last `~20 min`; a frozen file means playout has stalled.
- **Site data freshness**: the now-playing feed is `< 5 min` old (published every few
  seconds), the schedule feed `< 15 min` old.
- **Content heartbeats**: the newest diary entry is `< 50 min` old, the hourly news loop
  shows recent activity, real feed supply has not been dry for more than a couple of
  hours, and no render/QA errors in the last runs.
- **Generation queue**: the dead-letter directory is empty (a dead-lettered job is one
  that exhausted its retries).
- **Talk stocking and freshness**: the stocking loop is running, and each show's approved
  talk pool is at or above the floor (`>= 15`). Because depth is not freshness, two further
  checks measure the **age of each show's newest approved clip** (red if a show has had
  nothing new in a day or two) and the **freshness generator's heartbeat** (red if the
  daily refresh has not run). See [the talk pipeline](talk-pipeline.md).
- **Music freshness (continuous stations)**: the same depth-and-freshness idea applied to
  the self-refreshing music pools, each pool must be at or above a depth floor **and**
  have a track newer than a set age, so a station whose daily music refresh has quietly
  stopped goes red instead of looping a stale library while its floor still reads green.
  One aired dir that plays a raw folder is watched directly rather than through its
  generator, because a fresh generator is no proof the stream is hearing it.
- **Host**: root filesystem usage is `< 90%`.

### Alerting

The watchdog alerts **only on state transitions**: an `ALERT` when a check goes green to
red, a `resolved` when it goes red to green. A standing problem is never re-alerted and a
still-green check is silent, so the log is one-to-one with real changes. Transitions are
appended to an **append-only JSONL alerts log** and, if a webhook is configured, pushed
to a chat channel (best-effort, a failed push never blocks the pass).

### The status page and state file

Each pass rewrites a `noindex` red/green status page (every check with OK/FAIL and
detail, plus the recent alerts, self-refreshing). It also maintains a **state file**
mapping each check to `{ ok, detail, at }`. That file is the source of truth for "what is
red right now", and other components read it rather than re-probing: the maintenance
loop's brief pulls the failing checks straight from it (see
[the talk pipeline](talk-pipeline.md)). The pattern is **compute health once, everyone
else reads the state**.

## 2. The always-on model

Every long-lived component runs as **its own user-level service** with the same
supervision pattern:

- **Start at boot** (`RunAtLoad`).
- **Restart on crash** (`KeepAlive`).
- **A throttle interval** (minimum seconds between restarts) so a crash-loop cannot
  hot-spin, roughly `10 s` for fast core services, `15 to 30 s` for supporting loops, and
  longer for the heavy generation worker.
- **Priority by workload**: real-time audio (the streaming server, every station's
  encoder, the scheduler) runs at **interactive** priority; non-realtime helpers (the
  data publisher, the stocking daemon, the queue worker, the watchdog) run in the
  **background**. This split matters (see the lessons).

Components run this way: the streaming server, one playout/encoder per station, the
scheduler, the site server, the tunnel connector, the now-playing/diary publisher, the
maintenance loop, and the watchdog itself (interval-driven rather than kept alive, since
each pass is short). Startup ordering is handled inside each service command (for
example the stream service waits for the streaming server to answer before starting), so
restart races self-heal. The single GPU generation worker guards itself with an OS lock
so an auto-restart can never race two workers onto one card. Some periodic jobs (the
hourly news bulletin) are calendar one-shots, not kept-alive daemons.

## 3. Hard-won lessons

Each of these is a rule with a reason:

- **Real-time audio must run at interactive priority.** Backgrounded, the encoders get
  throttled and you hear cutouts. Stray heavy work (renders, a headless browser, batch
  ffmpeg) on the streaming box starves the encoders. Keep heavy work off the box and the
  audio path at interactive priority.
- **Keep a fallback for every fancy backend.** Every generated slot degrades to plain
  music through an empty-safe fallback, and every premium model has a validated cheaper
  or local one behind it. A single flaky backend must never silence a host.
- **Single-flight ML scales with nodes, not concurrency.** The generation models saturate
  one accelerator and destabilize under parallel requests, so they are single-flight by
  construction. To go faster, add machines, not threads.
- **Quality-gate everything generated.** Music and talk are `candidate` until an automated
  gate passes them to `approved`, and only approved assets air. Generation is
  probabilistic; nothing reaches air unvetted.
- **Put the model where the memory is.** Music generation runs on the model server, voice
  rendering on the high-memory render box, and the streaming host only schedules,
  encodes, and serves. Co-locating heavy generation with real-time streaming starves the
  encoders.
- **Do not wipe a library all at once; backfill first.** Regeneration is slow and
  single-flight, so an idle-time top-up loop fills the thinnest lane incrementally rather
  than wiping and regenerating. A live station cannot go thin mid-refresh; grow the pool
  before draining anything.
- **Restart supervised services cleanly.** A config change needs a clean stop and start
  with a gap, not a racing reload, and renames must be boundary-aware (a careless global
  substitution once corrupted source and caused an outage).
- **Measure the work, not a threshold.** A check that a pool is above a floor, or a state
  file is under an age limit, stays green as long as the number is in range, even when the
  process that should be *doing the work* has quietly stopped. Two faults hid exactly this
  way: talk pools sat above their floor while every clip was days old, and a now-playing
  state file stayed under its staleness limit while skipping whole tracks. The fix is to
  monitor freshness and last-ran heartbeats (is new work actually appearing?), not just
  standing levels. A green dashboard should mean the work is happening, not merely that a
  level is in bounds.

Together these are what turn a pile of models into something that is actually on the air
at four in the morning.
