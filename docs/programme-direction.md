# Deep dive: track-aware programme direction

Studay FM now separates two related jobs: a live, guarded presenter writer that
knows the exact record it is introducing, and a broader programme-director
experiment that still proposes decisions without changing playout.

```text
current show + recent history + approved shortlist
                         |
       +-----------------+-----------------+
       |                                   |
exact next record                   approved shortlist
       |                                   |
local presenter candidate           director proposal
       |                                   |
speech and technical QA             strict validation
       |                                   |
verified talk/track pair             review-only record
```

## Track-aware presenter links

The schedule selects music before a related script is written. The writer then
receives the exact adjacent track identifiers and a character brief. A presenter
can therefore tell an invented but character-consistent story about the record
that really follows, rather than producing a convincing link beside an unrelated
track.

The binding is mechanical. The validated script sidecar records the intended
track path plus hashes for the music and its metadata. Schedule assembly checks
both, places the talk and exact track as one pair, and live selection verifies
them again. A bulletin cannot split the pair. If the record changes, retires or
fails validation, the link is dropped and approved music continues.

This route is live for fourteen flagship presenters. It began with 52 approved
links, and the first naturally reached production pair was observed introducing
and then playing the exact named record. The Captain remains on the existing
Yacht Zone route until that independent flow scheduler can enforce the same
pairing rule.

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

## Programme-director shadow

The director shadow runs beside normal scheduling and records what it would have
chosen. It cannot enqueue media, edit manifests, restart services or change the
live schedule. Cloud and local models can be evaluated against the same contract
without changing their permissions.

Review asks practical radio questions: did it choose coherent records, avoid
repetition, respect the host's lane, use silence well and make the programme more
enjoyable? The first long shadow was mechanically stable but overwhelmingly
chose silence, so it did not earn a live canary. The next version needs stronger
show-aware creative behaviour before authority is reconsidered.

## Capability boundary

Programme direction is separate from operations. The director does not receive
a shell, filesystem access, approval authority or general station controls.
Likewise, owner-authorized operational actions do not let a presenter prompt or
public-facing character text administer the station.
