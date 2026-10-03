# Deep dive: music generation

Studay FM generates music with ACE-Step, but generation and playout are separated
by bounded batch workers, owner listening review, technical QA, and
atomic approved manifests.

```text
lane recipe -> serialized batch -> ACE-Step worker -> candidate audio
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

The primary bulk route is ACE-Step 1.5 XL Turbo with the 1.7B planner on an RTX
3090. It uses the native asynchronous task API: submit, checkpoint the returned
task ID, poll, retrieve and verify audio. The older authenticated server wrapper
is a separate API; its details below are reference design rather than the
current batch client's protocol.

The reviewed prompt library now covers vocals as well as instrumentals across
the flagship and flow stations. Distinct IDs, seeds or filenames do not make
repeated captions and lyrics distinct songs. Batch preflight checks creative
inputs as well as exact files, while listening establishes whether different
performances are worth keeping.

Current batch work can let the planner choose a duration rather than impose
one uniform length. Minimum-length checks and file-size/time budgets remain technical
controls, separate from musical structure.

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

## 3. Authenticated wrapper API (reference)

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

- the current batch runner starts one expensive job at a time;
- the API itself accepts one active inference and rejects overlap immediately.

Throughput scales by adding reviewed capacity or generation windows, not by
letting one model process accept an unbounded backlog.

Health checks need enough timeout to distinguish a busy server from an
unreachable one. They remain bounded and use the endpoint's configured access
contract, rather than assuming the native API and wrapper are interchangeable.

## 5. Generation queue v2 (historical)

This general worker is deliberately disabled. Current native-API batches use
their own persisted task checkpoints and review outputs. The lease design
below is historical reference, not a component monitoring should expect to
run just because its files remain present.

A queued music job records:

- a validated job schema and generated ID;
- type, owner-facing label, priority, and optional not-before time;
- argv array and approved project working directory;
- maximum attempts and overall timeout;
- lease identity, heartbeat, exit receipt, and terminal result.

The worker persists one supervisor per active job. If the worker restarts while
generation continues, it recognizes the leased process instead of launching
another GPU task.

The queue is a trusted local administrative interface. The public site and model
prompts can read only a summary; they cannot add, retry, reprioritize, or remove
work. Any owner-authorized queue action belongs behind a separate typed and
audited capability.

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

New music across all five stations requires explicit owner listening review.
Generation does not increase the approved pool or inherit the previous prompt
version's acceptance. Promotion requires that owner decision and current
technical QA.

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

Technical QA proves that the file is structurally usable; it does not prove that
the music remains coherent or pleasant from beginning to end. During the major
library rebuild, some candidates decoded cleanly and passed duration, silence,
loudness and peak checks but developed audible glitches, malformed transitions
or musical breakdowns later in the track. Other candidates were technically
fine but were rejected for taste or because large batches became too repetitive.

The owner therefore auditioned roughly two thousand candidates across the
project's generation routes while revising the prompt library. The major
replacement and replenishment batches used explicit human listening as their
acceptance gate. The project may test sampled review for recipes that sustain a
high acceptance yield, but that is a future operating policy rather than an
assumption that automated QA can hear the music.

For this project's ACE-Step workload, the single RTX 3090 backend was materially
faster than the M3 Max Apple backend and its batches produced fewer human
rejections. That is a project observation tied to the tested model,
configuration and prompts, not a general hardware benchmark.

Only policy-approved, technically current files can enter the atomic manifest.
Models and the operational query surface have no approval capability.

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

Generation masters, listening-review files and production assets have separate
roles. The private package registry binds decisions to exact content hashes
and portable relative locators; paths and folder suffixes carry no approval
authority. Imports retain receipts and do not resurrect owner-deleted rejects.
Approved package status must be reflected in the review index so already
completed listening work does not return as a new assignment.

Generated music belongs in a configurable external media root. During migration,
a compatibility link may keep older consumers working, but containment must be
checked against the canonical resolved root.

The scheduled retention pass is read-only. It can report old experiments,
rejects, retired tracks, and archives, while excluding approved, scheduled,
on-air, runtime, bulletin, continuity, and private reference material.
Quarantine is explicit and recoverable; deletion is not automatic.
