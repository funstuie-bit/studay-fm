# Deep dive: continuity and the diary

Continuity gives the network a voice between shows without giving that voice
operational authority. The Signalman marks flagship transitions and writes a
grounded public diary; Airelle provides sparse links on C'est Magnifistu.

```text
real station state -> bounded writing call or deterministic fallback
                                      |
                              candidate text
                                      |
                          speech render and QA
                                      |
                     fixed approval policy + manifest
                                      |
                                   playout

real station state -> diary entry -> append-only ledger -> atomic public feed
```

## 1. Continuity is not the operator

The Signalman is a fictional continuity character. It can describe the station
and appear between programmes, but it cannot restart a service, approve media,
enqueue work, or change the schedule.

The private operational model is separate. It receives a typed read-only station
query and can only observe and recommend.

Keeping these roles separate prevents public-facing character text from becoming
an administration channel.

## 2. Flagship hour markers

Flagship continuity lives in its own approved pool. The scheduler inserts a
short marker at an hour boundary when an eligible clip is available.

The selection is:

- bounded and rotation-aware;
- independent of per-show DJ cadence;
- subject to the shared station speech arbiter;
- empty-safe, falling through to music or the next scheduled event;
- validated as part of the schedule before publication.

An hour marker does not outrank the station's audio boundary. If a bulletin or
presenter link has just played, the marker defers until a full music track has
completed or is skipped under the fixed policy. This prevents an hourly event
from creating a voice-on-voice collision.

The script brief keeps the Signalman factual and sparse: short sentences,
restricted vocabulary, no grand storytelling, and no invented claims about the
station.

## 3. C'est flow continuity

Airelle's continuity is woven between tracks rather than placed on a flagship
clock. Lines are grouped by function, such as ident, mood, or moment, and
published through a separate approved manifest.

Liquidsoap uses a weighted, track-sensitive fallback. Roughly:

```text
continuity_or_music = fallback(track_sensitive=true, [continuity, music])
radio = rotate(weights=[music-heavy, continuity-sparse],
               [music, continuity_or_music])
```

If no approved line is ready, the fallback supplies music. Newly published
continuity becomes visible through the watched manifest without restarting the
station.

## 4. Writing continuity

The writing call is bounded and provider-agnostic. The current hosted fallback
does not gain tools merely because it writes a line.

The prompt enforces:

- spoken text only;
- short word range;
- factual station-safe language;
- no claims about listener counts or events unless supplied as facts;
- no stage directions or Markdown;
- no em dashes;
- no unsupported station pronunciation.

A deterministic line is available if the model is unavailable. Either result is
still a candidate.

## 5. Render, review, and manifest

Continuity uses the same speech safety chain as presenter talk:

1. private, path-confined reference-conditioned render;
2. loudness normalization and lead/tail padding;
3. silence, duration, format, channel, sample-rate, loudness, and peak checks;
4. the configured fixed approval policy;
5. technical-QA cache tied to the exact file;
6. atomic approved-manifest publication.

No sidecar-only edit can put a line on air.

The padded terminal margin remains part of the approved asset, and speech-aware
playout does not crossfade it away at the next transition.

## 6. The public diary

The diary is a short reflective summary grounded in real state. A writing pass
can receive:

- current and next flagship show;
- current audible track and artist;
- stream/readiness summary;
- approved library and catalogue counts;
- recent diary entries, with an instruction not to repeat them.

The model returns a small structured object containing mode, short title, and
text. The writer rejects malformed output and strips forbidden punctuation.

If no model is available, a deterministic entry is composed from the same facts.
The entry records its writer/source so a reader can distinguish fallback from a
model-generated note.

## 7. Append-only ledger

Diary entries are first appended to a private event ledger. Entry IDs are
derived from station and time bucket, making repeated runs idempotent.

A publisher:

1. reads and validates ledger entries;
2. sorts the public view;
3. writes the diary feed atomically;
4. validates station ID, timestamp, count, and entry list before replacement.

The public site receives only the intended diary fields. It does not receive
private health details, paths, prompts, or logs.

## 8. Freshness and retention

Continuity depth and freshness are separate checks. The watchdog can flag:

- too few approved lines;
- newest approved line too old;
- producer heartbeat stale;
- manifest stale or technically ineligible;
- diary feed older than expected.

Retirement moves old approved lines out of watched directories only after they
are no longer scheduled or on air. The scheduled retention audit excludes
continuity and private references entirely.

## 9. Failure behavior

- Missing continuity becomes normal music.
- A colliding hour marker defers or becomes music rather than stacking voices.
- Model failure uses a deterministic candidate or skips the cycle.
- Render/QA failure creates no manifest entry.
- Malformed diary output is rejected before publication.
- A failed public-feed write leaves the prior complete JSON in place.
- A red or stale watchdog state is visible to the typed operations query, not
  hidden by a cheerful continuity line.

Continuity makes the station coherent; it does not make the character an
autonomous controller.
