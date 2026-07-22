# Phase 5: playout quality and bounded automation

Phase 5 closes the gap between “the station is technically streaming” and “the
station sounds deliberate while its automation remains containable.” It adds
deterministic speech boundaries, protects spoken-word endings, makes music
experimentation reviewable, narrows the local-model surface, binds owner
feedback to exact media, and verifies changes in isolated CI.

This page is a public design summary. It intentionally omits private hosts,
accounts, credentials, service labels, review identifiers, and recovery
commands.

## One voice at a time

Presenter links, continuity, and bulletins used to have independent scheduling
reasons to play. Near an hour boundary, individually reasonable decisions could
therefore produce an unreasonable sequence of voices.

Phase 5 makes the rule global within each station:

```text
music -> one eligible voice item -> one complete music track -> next voice item
```

All speech categories use the same deterministic arbiter. If several requests
meet at one boundary, the station selects one according to fixed priority and
rotation policy; the others defer or fall through to music. A voice event cannot
be followed immediately by another voice event, even when the second event came
from a different subsystem.

The arbiter belongs in schedule and playout code, not in an LLM prompt. It must
continue to work when every model endpoint is unavailable.

## Protecting the last word

Spoken assets receive conservative lead and tail padding after rendering and
normalization. The padding step validates input containment, file type, size,
duration, and output identity, then publishes atomically. A padding or probe
failure is a failed candidate; it is not silently treated as success.

The playout graph recognizes speech items and preserves their terminal tail
instead of crossfading it into the following track. Verification compares a
captured broadcast transition with the approved source and checks that the
source's final spoken region is present before declaring the boundary fixed.

## Versioned music prompt pools

Lo-fi, jazz-hop, and Yacht day/night generation use structured prompt records
rather than a loose list of strings. Each record identifies its station, lane,
recipe version, musical intent, and effective model settings.

Only the current prompt version is scheduled. A version change resets rotation
state and generates review candidates without increasing the approved pool.
Candidate previews are private, bounded, symlink-safe, and digest-checked.
Promotion still requires the applicable owner review and current technical QA.

This makes experimentation reversible:

1. define a new prompt version;
2. generate a small candidate batch across the affected lanes;
3. audition and record feedback;
4. revise or approve;
5. publish only the accepted, technically current assets;
6. retain the previous live pool until replacements are ready.

## Digest-bound owner feedback

A review action includes the SHA-256 identity of the exact asset the owner
heard. Before appending the action, the tool confirms that identity still
matches the expected candidate or current track.

Feedback is written to a size-bounded, append-only private ledger. The model can
read an aggregated summary for future prompt work, but it cannot fabricate an
owner rating, rewrite history, or turn a rating into media approval.

## Authenticated inference-only local models

The local-model daemon is not exposed as a general-purpose API to station
automation. A loopback gateway:

- requires a private bearer credential;
- forwards only the bounded generation route the station needs;
- allowlists the model and request shape;
- caps request, response, message, and timeout sizes;
- rejects browser-origin requests and administrative model routes;
- keeps the underlying transport private.

The operator and private bot still receive only the typed read-only station
query. Local inference improves availability and cost; it does not expand
authority.

## Verification and CI

The change gate combines:

- focused schedule, speech-tail, prompt-version, preview, and feedback tests;
- the complete frozen test suite;
- critical lint and canonical naming checks;
- secret-history scanning;
- dependency vulnerability review with expiring exceptions;
- deterministic SBOM verification;
- runtime capture and health evidence for playout changes.

Runtime monitoring also keeps cadence separate from content provenance. The
hourly diary writer receives a 75-minute liveness allowance, while two
consecutive deterministic-fallback entries trigger their own provenance alarm.
This avoids both false freshness alerts and silent degradation of the preferred
writing path.

CI runs under a dedicated unprivileged identity without production secrets.
Protected-branch status is tied to the exact quality/security job for the
reviewed revision.

## What remains owner-controlled

Phase 5 does not make the station a self-governing administrator. The following
remain explicit privileged actions:

- creating or changing service accounts;
- host firewall and outbound-network policy;
- deployment-key and runner scope;
- installing or replacing system services;
- retiring legacy credentials;
- removing a final compatibility storage link;
- granting any model a new mutation capability.

Those controls require a separate owner-approved change, audit evidence, and a
rollback path. The station can observe and recommend; it cannot silently grant
itself more authority.
