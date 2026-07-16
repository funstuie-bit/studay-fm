# Deep dive: music generation

Studay FM generates music with ACE-Step, but generation and playout are separated
by authentication, a private queue, a fixed review policy, technical QA, and
atomic approved manifests.

```text
lane recipe -> typed queue job -> authenticated ACE-Step -> candidate audio
                                                        |
                                            configured review policy
                                                        |
                                              technical QA
                                                        |
                                         atomic approved manifest
                                                        |
                                                   playout
```

## 1. Versioned generation recipes

Each show or flow pool owns a lane recipe containing:

- positive descriptions of genre, mood, tempo, instrumentation, and production;
- optional fictional lyrics or an explicit instrumental marker;
- a coarse genre tag for scheduler spacing;
- fictional artist and title pools;
- model parameters recorded in metadata;
- an explicit recipe version and stable prompt ID.

The production generators pin their effective recipe rather than inheriting
client defaults. A typical ACE-Step profile uses strong caption guidance,
offline-quality inference steps, helper-caption rewriting disabled, lossless
output, and a requested duration suited to the station pool.

Exact settings are part of the candidate sidecar so a result can be reproduced
or compared later.

Schedulers select only prompts belonging to the current version for each lane.
When a version changes, its rotation cursor resets rather than mixing state from
the previous pool. This makes it possible to compare one coherent recipe
revision at a time.

## 2. Positive-only captions

Diffusion-style music models can react to a genre word even when it appears in a
negative instruction. The safe rule is:

- describe the wanted style in affirmative language;
- do not name the unwanted genre anywhere in caption or lyrics;
- enforce a trigger quarantine before sending the request.

For example, steer toward tight electronic drums, clipped guitar, bright synth,
and urban vocal delivery rather than writing “not [unwanted genre].”

The generator rejects a quarantined trigger before spending compute.

## 3. Authenticated internal API

The ACE-Step server is treated as a security boundary even when it is reachable
only on a private network.

The service should:

- require a private bearer token on health and generation routes;
- bind to one intended interface rather than a wildcard;
- disable interactive API documentation in production;
- cap request, upload, encoded response, and generated audio sizes;
- validate batch size, duration, inference settings, file count, and format;
- serialize model inference and return `429` with retry guidance when busy;
- use private temporary directories;
- avoid logging prompts, lyrics, or tokens.

The client should:

- allowlist the endpoint scheme, host, port, and empty base path;
- reject embedded credentials, redirects, and unexpected response shape;
- bound request timeout and response body;
- decode only supported audio formats;
- confine output to approved media roots;
- reject symlink targets and extension mismatches;
- write the file atomically with private permissions.

Authentication does not replace a host firewall or source-host restriction. A
deployment should layer both where the platform permits.

## 4. Single-flight generation

ACE-Step inference is single-flight. Parallel requests compete for the same
accelerator and can destabilize the service.

Two controls reinforce each other:

- the private generation queue starts one expensive job at a time;
- the API itself accepts one active inference and rejects overlap immediately.

Throughput scales by adding reviewed capacity or generation windows, not by
letting one model process accept an unbounded backlog.

Health checks need enough timeout to distinguish a busy server from an
unreachable one, but they still authenticate and remain bounded.

## 5. Generation queue v2

A queued music job records:

- a validated job schema and generated ID;
- type, owner-facing label, priority, and optional not-before time;
- argv array and approved project working directory;
- maximum attempts and overall timeout;
- lease identity, heartbeat, exit receipt, and terminal result.

The worker persists one supervisor per active job. If the worker restarts while
generation continues, it recognizes the leased process instead of launching
another GPU task.

The queue is a trusted local administrative interface. The scheduled operator,
private bot, public site, and model prompts can read only a summary; they cannot
add, retry, reprioritize, or remove work.

## 6. Vocal and instrumental requests

The request contract is explicit:

- an instrumental request uses `instrumental=true` and a non-null instrumental
  marker;
- a vocal request uses `instrumental=false` and non-empty lyrics;
- caption, lyrics, duration, seed, guidance, inference steps, and booleans are
  type- and range-checked;
- output extension must match the requested format.

Malformed requests fail before reaching the model.

## 7. Per-show lanes

The flagship has show-specific lanes, and flow stations have their own pools.
Examples include:

- bright morning soul/pop;
- lunchtime disco and electro-funk;
- drive-time dance-punk and electroclash;
- evening crate-digging styles;
- late-night and overnight lanes;
- lo-fi time-of-day pools;
- Yacht day/night pools;
- jazz-hop instrumental pool;
- C'est main and jazz pools.

Lane ownership lets the scheduler avoid genre bleed. It also makes stock and
freshness measurable per format rather than as one misleading total.

## 8. Candidate metadata

Each result is stored outside Git-adjacent storage with a same-stem sidecar. The
sidecar records:

- station and lane/show IDs;
- fictional artist, title, and genre;
- caption and lyrics/instrumental status;
- effective model recipe and timestamps;
- generator identity;
- `review_status`, initially `candidate`.

Generation success never sets live eligibility by itself.

## 9. Review policy and technical QA

Flagship music has an explicit owner taste-review path for candidates. A new or
changed prompt version on a flow station is also candidate-only: generation does
not increase the approved pool or inherit the previous version's acceptance.
Promotion requires the configured owner review and current technical QA.

Manual review is appropriate for a new lane, changed recipe, suspicious result,
vocal material, or any rights/provenance concern.

Technical QA then checks:

- readable supported audio;
- sample rate and channels within policy;
- duration within the music profile;
- internal silence below the safety limit;
- integrated loudness and true peak within broad bounds.

The cache stores a fingerprint of the exact file. Any later modification
invalidates the pass.

Only policy-approved, technically current files can enter the atomic manifest.
The model and read-only operator have no approval capability.

## 10. Candidate preview and owner feedback

Private previews are derived from the exact candidate through a contained,
no-symlink copy. The copy's digest must match the source before a bounded
transcode can begin. Preview filenames and metadata are display values, not path
authority.

An owner rating is accepted only with the SHA-256 digest of the asset that was
actually reviewed. The feedback tool verifies that the candidate or current
track still has that identity, then appends a bounded record to a private
append-only ledger. It refuses writes once the ledger reaches its configured
size ceiling.

Models may receive an aggregate of this history when drafting the next prompt
version. They cannot create owner ratings, alter earlier events, approve the
track, or directly replace the live prompt pool.

## 11. Rotation and backfill

The flagship selector combines rotation gap, artist/genre spacing, and lane
containment. Flow stations rotate approved pool manifests according to their
format clocks.

Never wipe a live lane before replacements are ready. Generation is slow,
single-flight, and probabilistic. The safe pattern is:

1. measure the exact thin lane;
2. enqueue a small bounded top-up;
3. review and QA candidates;
4. publish the approved manifest;
5. observe the next normal playlist/schedule refresh;
6. retire older material only after the replacement stock is live.

## 12. Storage and retention

Generated music belongs in a configurable external media root. During migration,
a compatibility link may keep older consumers working, but containment must be
checked against the canonical resolved root.

The scheduled retention pass is read-only. It can report old experiments,
rejects, retired tracks, and archives, while excluding approved, scheduled,
on-air, runtime, bulletin, continuity, and private reference material.
Quarantine is explicit and recoverable; deletion is not automatic.
