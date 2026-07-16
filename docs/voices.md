# Deep dive: presenter voices

Studay FM uses Chatterbox as a reference-conditioned speech synthesizer. The
technical model is often described as zero-shot voice cloning, but the station
workflow is designed around fictional presenter characters, private provenance,
bounded rendering, and approved-only playout.

```text
rights-cleared private reference + candidate script
                         |
              bounded Chatterbox render
                         |
                    candidate WAV
                         |
             post chain + technical QA
                         |
                  fixed review decision
                         |
              atomic approved manifest
                         |
                       playout
```

## 1. Creative intent

The production characters came from one accepted adaptation per role. There was
no iterative process aimed at increasing resemblance to a named inspiration.

Later pitch, EQ, timing, compression, and loudness work shaped distinct station
characters. The news voice processing, in particular, moved the result farther
from its inspiration. A historical filename containing words such as `clone`, or
an imprecise old code comment about timbre, is not evidence of impersonation or
soundalike intent.

That clarification does not erase source-rights obligations. A result can sound
different and still require permission, licence review, attribution, or
withdrawal handling.

## 2. Private provenance ledger

For every source and derived reference, a private ledger should record:

1. internal source ID and private location;
2. source description and acquisition date;
3. asserted permission, licence, or consent basis;
4. permitted use, territory, duration, attribution, and redistribution limits;
5. transformations and derived files;
6. presenter/show mapping and first use;
7. review date and unresolved questions;
8. withdrawal contact and removal procedure;
9. current status: candidate, active, rejected, retired, or deleted.

Do not infer permission from public availability, a short excerpt, one-shot use,
or lack of resemblance. Raw references must not enter Git, public site data,
queue logs, documentation, issue attachments, or chat.

## 3. Reference preparation

Use only audio you have the right to process.

A useful reference is:

- short, clean, and single-speaker;
- mono WAV;
- free of music, room noise, overlapping speech, and heavy reverb;
- long enough to carry stable timbre and cadence, but not needlessly large;
- stored as an owner-only regular file beneath an approved private root.

One canonical reference per presenter keeps output consistent and makes
withdrawal manageable.

For deployment smoke tests, prefer Chatterbox's generic no-reference voice. It
proves the model and audio path without involving private source material.

## 4. Renderer boundary

Production can use a one-shot CLI over a restricted remote account or an
authenticated internal HTTP service.

### CLI or SSH boundary

- fixed host/account and renderer entry point;
- argv-safe or strictly shell-quoted arguments;
- approved reference and output roots;
- no arbitrary remote shell exposure;
- one render at a time;
- bounded execution timeout;
- private temporary files removed after transfer.

### HTTP boundary

- startup fails without a strong private token;
- wildcard production binds are refused;
- health and synthesis both require authentication;
- JSON content type and body length are mandatory;
- text, reference, output, and audio sizes are bounded;
- unexpected fields and invalid numeric ranges are rejected;
- reference and output paths must stay under configured roots;
- symlinks and path escapes fail;
- concurrent synthesis returns `429` instead of building a backlog;
- generated output is written atomically with private permissions.

Internal network placement is not a substitute for these controls.

## 5. Text preparation

Write for speech rather than for a page:

- output spoken words only, no stage directions or Markdown;
- avoid one- or two-word utterances;
- do not put a load-bearing word at the very start;
- normalize station-name pronunciation before rendering;
- split long text at sentence boundaries, and then commas if necessary;
- join chunks with a small, consistent gap.

The stored script remains human-readable. Pronunciation substitutions belong in
the renderer input, not the editorial record.

## 6. Render parameters

Chatterbox exposes two important controls:

- `exaggeration`: how animated the delivery is;
- `cfg_weight`: how strongly the render follows conditioning.

Start conservatively. A conversational presenter can use a moderate
exaggeration; a newsreader should be calmer. Raising exaggeration to make a
voice sound “bigger” can destabilize accent and pacing.

Render parameters belong in the sidecar so a candidate can be reproduced and
compared.

## 7. Process lifetime

One-shot rendering is the safest baseline for a batch:

1. load the model;
2. render one candidate;
3. write the WAV;
4. exit.

This keeps memory behavior predictable. A long-lived service can be used if it
is demonstrably stable, serialized, bounded, and supervised, but it must not
run on the real-time streaming path.

## 8. Post-production

Raw speech is normalized and padded before technical review. A representative
chain:

```text
optional character EQ/pitch/compression
-> loudness normalization
-> short leading pad
-> short trailing pad
```

Do not aggressively silence-trim the tail. Quiet final consonants and word
decays can fall below a trim threshold and make the presenter sound cut off.

Optional pitch and EQ are character-shaping tools, not likeness-restoration
tools. Their purpose is consistency and intelligibility in the station mix. In
the news chain, the chosen processing moved the result farther from the original
inspiration.

## 9. Technical QA

The spoken-word profile validates:

- regular supported audio;
- allowed sample rate and channel count;
- duration inside the configured range;
- no excessive internal silence;
- loudness and true peak inside broad safety limits.

QA is fingerprint-bound. Replacing or modifying the file invalidates the cached
pass. A clip with a stale pass cannot enter the next manifest.

## 10. Review and approval policy

The recurring talk and continuity path can assign `approved` automatically after
the script validators and technical speech QA pass. The hourly news path adds its
structured source and editorial gate. This is fixed code under owner control, not
a decision delegated to the model through an operations tool.

Manual listening remains appropriate for:

- a new or replaced character reference;
- changed render parameters or post-processing;
- a new presenter or format;
- a suspicious candidate or watchdog alert;
- provenance, likeness, pronunciation, or editorial concerns.

The owner can reject or withdraw material and should audition representative
canaries before enabling a changed renderer. Only policy-approved, technically
current clips can enter the atomic manifest. Candidate and rejected files remain
inert.

## 11. Swap-in contract

The wider station does not depend on one speech model. A replacement renderer
only needs to preserve:

- text in;
- optional private character reference;
- WAV out;
- bounded, authenticated, path-confined execution;
- candidate metadata;
- technical QA and the applicable fixed approval policy before manifest
  publication.

Keeping that contract around the model makes speech engines replaceable without
weakening the airplay boundary.
