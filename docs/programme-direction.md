# Deep dive: track-aware programme direction

Studay FM separates live exact-track presenter writing from a newer editorial
session layer. The latter can shape an ordered musical run and give the
presenter a reason to make the next link, rather than attaching a convincing
story to a random record.

```text
current show + recent history + approved shortlist
                         |
       +-----------------+-----------------+
       |                                   |
exact next record                   approved shortlist
       |                                   |
local presenter candidate           editorial session
       |                                   |
speech and technical QA             strict validation
       |                                   |
verified talk/track pair             aircheck / bounded show canary
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

The route is live across the established flagship programmes and Big GT's new
Grove Pocket lane. The Captain's writing is now local too, but his Yacht Zone
continuity remains generic until that independent flow scheduler can enforce
the same pairing rule. Local prose and exact-track scheduling are different
milestones.

## Editorial session contract

The director sees only bounded station context:

- current station and programme;
- a short recent-play history;
- a small approved, technically valid shortlist;
- current speech eligibility and remaining session limits;
- a bounded session note carried from the prior decision.

It returns an ordered run of exact surfaced candidate IDs, a presenter
treatment and a bounded session note. Code maps those IDs back to reviewed
music hashes. Invented IDs, duplicate selections, wrong counts and invalid
adjacent-track references fail validation.

The model has useful creative freedom: an episode angle, a short musical
movement, a bridge or forward link, and character-consistent fictional stories
about supplied records. It cannot invent catalogue identity or turn a
fictional discovery story into verified release history.

Code owns speech cadence. Daytime shows generally talk after three or four
records, while quieter late-night programmes leave longer gaps. The model
cannot avoid every due break or start chatting after every song. Sessions
expire at the show boundary, retain bounded memory and record only material
actually aired, not every generation attempt.

## From aircheck to bounded canary

The original read-only shadow was mechanically stable but mostly chose silence.
It remains historical evaluation, not the current creative design. The newer
editorial sessions produced owner-accepted First Cup and Crate listening
editions with exact track joins and readable cue sheets.

A Crate-only canary path is implemented: a short hash-sealed run, its opening
and closing, an actual show window, expiry and a disable marker checked at
item boundaries. Outside that exact window, or if a binding fails, ordinary
approved scheduling wins. This is not a claim of permanent autonomous control
across every presenter.

Review still asks practical radio questions: does the run feel intentional,
avoid repetition, fit the host and name the record that really follows? A model
can reason about metadata but cannot establish that the music is pleasant or
glitch-free by listening. Editorial candidates therefore require explicit
owner-review evidence as well as technical eligibility.

## Capability boundary

Programme direction is separate from operations. The director does not receive
a shell, filesystem access, approval authority or general station controls.
Likewise, owner-authorized operational actions do not let a presenter prompt or
public-facing character text administer the station.
