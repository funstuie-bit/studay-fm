# Deep dive: track-aware programme direction

Studay FM is moving from isolated script generation toward an AI programme
director that understands the actual sequence around a presenter link. The
current stage is deliberately observable: it proposes decisions against real
approved media while deterministic playout remains authoritative.

```text
current show + recent history + approved shortlist
                         |
              bounded programme brief
                         |
             exact-asset structured proposal
                         |
       validate identifiers, order, speech and limits
                         |
                 reviewable shadow record
```

## Track-aware presenter links

The schedule selects music before a related script is written. The writer then
receives the exact adjacent track identifiers and a character brief. A presenter
can therefore tell an invented but character-consistent story about the record
that really follows, rather than producing a convincing link beside an unrelated
track.

The binding is mechanical. The validated script sidecar records the intended
track identity, and schedule assembly rejects a mismatch. If generation fails,
the station falls back to music or a safe generic link rather than inventing a
relationship.

## Programme-director contract

The director sees only bounded station context:

- current station and programme;
- a short recent-play history;
- a small approved, technically valid shortlist;
- current speech eligibility and remaining session limits;
- a bounded session note carried from the prior decision.

It returns a strict object containing one to three exact approved asset IDs, a
speech or silence decision, a reason code, and an optional short session note.
Unknown IDs, duplicates, invalid order, overlong notes and speech-policy
violations fail validation.

## Shadow before authority

The live shadow runs beside normal scheduling and records what it would have
chosen. It cannot enqueue media, edit manifests, restart services or change the
live schedule. Cloud and local models can be evaluated against the same contract
without changing their permissions.

Review asks practical radio questions: did it choose coherent records, avoid
repetition, respect the host's lane, use silence well and make the programme more
enjoyable? Only a consistently useful shadow should advance to a small queued
canary with an immediate deterministic fallback and owner stop.

## Capability boundary

Programme direction is separate from operations. The director does not receive
a shell, filesystem access, approval authority or general station controls.
Likewise, owner-authorized operational actions do not let a presenter prompt or
public-facing character text administer the station.
