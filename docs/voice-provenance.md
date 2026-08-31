# Voice provenance and reference handling

Studay FM's presenters are fictional characters built with
reference-conditioned speech synthesis. The production process accepted one
adaptation for each role, then used pitch, EQ, timing, compression and loudness
work to shape the station character.

Creative intent and source rights are separate questions. A voice sounding
different does not prove the source was cleared. A source being publicly
available does not grant permission to use it. Both facts need their own record.

## What the station did

The character workflow was not an iterative attempt to get closer to a named
person. One adaptation was accepted for each role. Later processing shaped the
result for the programme. The news workflow moved its accepted voice farther
from the original inspiration.

Historical filenames containing words such as `clone`, or an old code comment
about timbre, do not establish the creative goal. They also do not settle the
rights question. That requires evidence about the actual source and permitted
use.

## The private provenance ledger

Every source and derived reference should have one private record containing:

1. Internal source ID and private file location.
2. Description of the source and acquisition date.
3. Permission, licence or consent basis being relied upon.
4. Permitted use, territory, duration, attribution and redistribution limits.
5. Transformations and derived reference files.
6. Presenter or show mapping and first use.
7. Review date and unresolved questions.
8. Withdrawal contact and removal procedure.
9. Current status: candidate, active, rejected, retired or deleted.

The ledger is private because it points to private reference material and may
contain rights records or contact details. The public docs can describe the
process without publishing the evidence itself.

## What does not count as permission

The project does not infer permission from:

- a clip being easy to find online;
- a source being short;
- using the reference only once;
- processing the output until it sounds different;
- nobody complaining yet.

Those may describe what happened. They do not answer whether the use was
permitted.

This page records the station's internal handling process. It does not claim one
set of rights rules applies in every territory.

## Reference preparation

Only audio the operator has the right to process should enter the reference
store. A usable reference is short, clean, single-speaker, mono and free of
music, overlapping speech, heavy room noise and reverb.

Each presenter uses one canonical reference so the output remains consistent and
withdrawal remains manageable. Files are regular owner-only files beneath an
approved private root. Symlinks and path escapes fail.

Deployment smoke tests use the renderer's generic no-reference voice. A service
check does not need The Duke's private source clip attached to it.

## Where reference material must not appear

Raw sources and derived references do not belong in:

- Git or repository history;
- the public site build;
- public documentation or issue attachments;
- model prompts or ordinary chat transcripts;
- queue labels and general logs;
- candidate audition pages shared outside the private review path.

The renderer receives the approved private path it needs. Other parts of the
station receive a character ID or bounded result, not the source file.

## Rendering, review and airplay

Chatterbox runs through a bounded path with authentication where applicable,
path containment, request limits, serialised rendering and private temporary
files. The output is still a candidate.

Spoken-word QA checks the audio format, sample rate, channels, duration,
internal silence, loudness and peak. QA is tied to the exact file fingerprint.
Changing the file invalidates the cached pass.

Recurring presenter links and continuity can receive approval from fixed
owner-configured validators after script and technical checks. News adds its
source and editorial gate. The model cannot assign approval through an
operations tool.

Manual listening remains appropriate for a new or replaced character reference,
changed render parameters, a new presenter, a suspicious candidate, a watchdog
alert, a pronunciation problem or a provenance concern.

## Withdrawal

Withdrawing a source means identifying every active and derived file through the
ledger, removing it from future rendering, retiring affected candidates and live
assets, rebuilding manifests and recording what changed.

Do not delete first and work out the dependencies later. The point of the ledger
is to make the removal specific and provable.

See [Presenter voices](voices.md), [Presenters](PRESENTERS.md) and
[Generation boundaries](generation-boundaries.md).
