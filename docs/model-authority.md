# Model authority and the capability broker

The model is not the control plane. It can inspect a typed view of the station,
write candidate material and carry out a small owner-authorised action through a
separate broker. It does not get a shell and it cannot decide that it has earned
more access because the last job went well.

Studay FM is working towards fuller AI management. The current boundary is a
stage on that route, not the final claim.

## Three different things

The capability broker keeps observation, action and automatic repair separate.
Mixing them together would make a read-only status question far more dangerous
than it needs to be.

### Observation

The query side can return:

- overall status and computed health;
- current tracks and programmes;
- queue summary and worker availability;
- music-lane depth;
- presenter, continuity and bulletin stock;
- owner flags;
- bounded tails from named allowlisted logs.

These tools read the same validated state used by the owner and watchdog. They
do not launch arbitrary probes, reveal private paths or mutate anything.

### Owner-authorised action

An exact owner instruction can authorise one small reversible operation. The
broker validates typed arguments, binds the request to the exact target, applies
an expiry, enforces idempotency and records a receipt.

Retiring the exact track identified in a request is a useful example. Current,
recent and named-track resolution bind the operation to the intended asset;
a track change does not authorise retiring its replacement. Ambiguous names
need clarification. Changed file hashes fail rather than moving the action to
whatever happens to be playing later.

The owner's instruction approves that specific outcome. A later command
confirmation provides execution visibility. It does not invite the model to
reinterpret the request or quietly include more files.

### Policy repair

One repetitive repair class may run without a fresh owner message, but only
after repeated matching evidence. The action is chosen in advance, is
idempotent, has a cooldown and attempt limit, and must pass a postcondition
check.

The policy cannot invent a new repair, change the target type or widen its own
scope. This is fixed automation using model-readable evidence. It is not a
free-form agent deciding what seems sensible at 3am.

## What the model cannot do

The broker provides no general terminal, arbitrary filesystem access,
deployment path, unrestricted service controls or media approval tool. Queue
mutation is also excluded from general model access because
adding a queued job is local command authority in a nicer outfit.

Model endpoints, request size, response size, step count, tool output and
session duration are bounded. The local writing path uses fixed allowlisted
inference clients. Model pull, delete and administration routes are not
exposed as station capabilities.

A hosted provider can implement the same text-generation contract. Changing the
provider does not change the authority attached to the request.

## Candidate writing is not operational authority

Presenter writers receive one approved record and return candidate text. After
speech rendering and QA, an accepted link is bound to the hashes of that record
and its sidecar. The writer cannot approve media, change the schedule or control
playout.

Programme direction is separate again. The newer editorial sessions receive
the current show, recent history and an owner-reviewed shortlist, then propose
exact ordered records and presenter treatments. A narrow, expiring show-canary
path validates every asset and falls back to ordinary scheduling. It is not a
general service-control tool or permission to approve generated music.

## Why the receipts matter

A chat transcript saying the model intended to do the right thing is not proof
that the right target changed. The broker records the requested capability,
validated target, result and postcondition. That gives the owner something
specific to inspect when a job fails or a repair repeats.

The model can be useful without being treated as trustworthy by default. In
practice, that has been the less dramatic and much more useful design.

See [Operations agent](operations-agent.md),
[Reliability](reliability.md) and
[Programme direction](programme-direction.md).
