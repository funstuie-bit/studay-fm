# Deep dive: reliability and readiness

A 24/7 radio network needs independent supervision, contracted state, and
failure-safe fallbacks more than it needs an all-powerful agent. Studay FM uses a
one-shot watchdog, atomic readiness, per-component services, a crash-aware queue,
and typed read-only operations.

## 1. Watchdog model

The watchdog runs on a schedule, computes a bounded snapshot, compares check
booleans with the previous pass, writes state and readiness atomically, emits
transition events, and exits.

It does not restart services during the health pass. Diagnosis and mutation stay
separate.

This one-shot design avoids a resident monitor becoming another fragile daemon.
The scheduler can restart a failed pass, while stale readiness makes the station
fail closed.

## 2. Stream checks

The stream layer verifies:

- Icecast responds on loopback;
- exactly five expected sources are connected;
- each mount is represented;
- public routing works independently of local routing;
- per-station now-playing advances;
- the playout service definition matches the intended station.

An alive process is not enough. A Liquidsoap encoder can exist while its Icecast
source is disconnected, and a public tunnel can fail while every local request
is green.

## 3. Decoder latency alerts

A decoder alert can report JSON decode failures and latency catch-ups for the
current session.

One catch-up with zero decode failures is a warning to inspect:

1. read the computed health view;
2. confirm the affected mount and metadata advance;
3. tail the bounded station and watchdog logs;
4. look for repetition, audio gaps, rising latency, or restarts.

Do not restart a station on the strength of one isolated catch-up. Repeated
events or audible degradation justify a targeted response.

## 4. State freshness and contracts

The watchdog checks the public and private artifacts the system depends on:

- per-station now-playing;
- flagship schedule;
- catalogue and diary;
- producer heartbeats;
- queue worker state and receipts;
- approved-media manifests;
- readiness itself.

State writers validate payload shape and timestamps before durable atomic
replacement. Readers reject malformed content. The readiness endpoint also
rejects evidence older than its allowed age.

The operating principle is: compute health once, then let the CLI, owner, and
bounded model tools read the same result.

## 5. Approved-media checks

For each station, reliability includes content eligibility:

- every manifest path is absolute, regular, contained, and non-symlinked;
- the sidecar is approved;
- technical QA is current for the exact file;
- generated news has valid source provenance and editorial verification;
- the manifest bytes match the current eligible set.

A station with a stale manifest or an on-air asset lacking current technical
evidence is red even if audio is still audible.

## 6. Queue v2 checks

Generation queue health includes:

- at most one running record;
- at most one active command child;
- fresh worker and job lease heartbeats;
- matching process identity, not PID alone;
- valid v2 job schemas;
- exit receipts consumed correctly;
- dead-letter count;
- no duplicate worker ownership.

If a worker restarts while a child is alive, recovery waits for the existing
supervisor. If the child is gone, the receipt or bounded retry policy decides the
next state.

## 7. Producer and freshness checks

The watchdog measures both level and activity:

- talk and continuity approved counts;
- newest approved item age;
- music pool depth and newest-track age;
- scheduled producer heartbeat;
- news feed supply, render attempts, and recent failures;
- diary generation age.

A full pool can still be stale. Measuring only the floor would miss a generator
that stopped days ago.

## 8. Host and network checks

Host checks include:

- filesystem capacity and free-space floor;
- media growth over time;
- log growth;
- expected loopback listeners;
- no unexpected wildcard listener for station services;
- optional service listeners treated as optional, not silently assumed.

Heavy generation belongs off the streaming host. Real-time audio processes need
interactive priority, while scans and publishers can run as background work.

## 9. Transition-only alerts

The watchdog emits:

- `ALERT` when a check moves green to red;
- `resolved` when it moves red to green.

Unchanged state is silent. Events go to an append-only private log and can be
delivered to a private alert channel. Delivery failure does not block state
publication.

Transition-only behavior avoids alert fatigue while preserving a one-to-one
record of changes.

## 10. Readiness document

Readiness is a small validated document:

```json
{
  "schema": "studayfm.readiness.v1",
  "ready": true,
  "generated_at": "ISO-8601 timestamp",
  "checks": {
    "check-id": {
      "ok": true,
      "detail": "bounded human-readable detail"
    }
  }
}
```

The flagship serves `200` only for fresh all-green evidence and `503` otherwise.
Liveness remains a separate endpoint.

## 11. Service supervision

Each long-lived component has its own user service:

- Icecast, Caddy, and tunnel connector;
- five playout graphs;
- site-data publisher;
- queue worker;
- optional model proxy and private bot gateway.

Calendar jobs cover news, content top-ups, watchdog, approved-media refresh, and
retention audit.

A calendar job can be healthy with no current PID. Evaluate its schedule, last
exit, heartbeat, log, and output time rather than assuming “not running” means
failed.

## 12. Read-only operations

The canonical CLI offers typed observation commands and bounded allowlisted log
tails. The scheduled operator and private ops bot receive the same
`station_query` capability.

They cannot:

- run shell commands;
- read arbitrary files;
- enqueue or retry work;
- generate or approve media;
- restart services;
- change configuration;
- deploy code.

The local coordinator and earlier local-model Hermes configuration were
unreliable, so the current private Hermes gateway uses DeepSeek only as an
observer and recommender. Owner control is a reliability feature as well as a
security feature.

## 13. Retention and storage

Media lives in a configurable external root so Git operations and repository
size do not govern the broadcast library.

The weekly retention job is audit-only. It can report old experiment, reject,
retired, and archive files while excluding runtime, approved, scheduled, on-air,
bulletin, continuity, and private references. Quarantine is explicit,
recoverable, and has no automatic deletion date.

## 14. Failure drills

Useful drills include:

- one mount missing while the other four remain live;
- local origin healthy but public route unavailable;
- stale readiness with all processes alive;
- queue worker restart during a long child job;
- failed approved-manifest refresh preserving prior bytes;
- invalid now-playing payload rejected before publication;
- news feed/model/render failure falling back to music;
- one isolated decoder catch-up versus repeated latency degradation.

The objective is a bounded response to the smallest affected component, not a
blanket restart.

## 15. Hard-won rules

- Real-time audio gets priority; heavy work goes elsewhere.
- A model failure must not become dead air.
- Internal APIs need authentication and limits.
- Candidate media is never live media.
- State must be valid, atomic, and fresh.
- Monitor new work, not only standing totals.
- Restart one component only after evidence.
- Never let a chat bot become the control plane by convenience.
