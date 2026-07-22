# Deep dive: the station engine

Studay FM runs five independent Liquidsoap outputs. One is built from a
show-by-show clock; four are continuous flow stations. They share the same
approved-media boundary, state contracts, Icecast origin, and readiness model.

```text
station config
      |
      +-> flagship clock -> validated schedule -> flat approved playlist
      |
      +-> flow rules --------------------------> watched approved manifests
                                                   |
                                               Liquidsoap
                                                   |
                                     continuous normalized MP3
                                                   |
                                           Icecast mount
                                                   |
                                    actual track-change callback
                                                   |
                                      atomic now-playing state
```

## 1. The station registry

A canonical station registry defines exactly five station IDs, display names,
mount paths, and local service roles. Code that publishes state validates IDs
against that registry rather than accepting arbitrary station names.

The current dials are:

- Studay FM, schedule-driven;
- StuLoFiDay, time-of-day lo-fi flow;
- Yacht Zone, yacht-rock day and house night;
- Tokyo Jazz, continuous instrumental flow;
- C'est Magnifistu, eclectic flow with sparse continuity and news.

Separate playout processes allow a one-station restart and independent health
evidence. Icecast is shared, so origin health is checked separately from each
source connection.

## 2. The flagship clock

Each flagship show declares either a daily time window or day-restricted windows.
Resolution is ordered:

1. match a day-specific special or weekend replacement;
2. otherwise match the regular daily clock.

The scheduler walks forward from its start time. For each event it:

1. resolves the owning show;
2. decides music, talk, continuity, or an injected bulletin;
3. selects an eligible approved asset;
4. measures the real file duration;
5. appends a timestamped event;
6. advances the cursor by that duration.

This avoids pretending that every song is the same length. A show owns the
assets whose actual playback falls into its window.

## 3. Talk and continuity cadence

Talk cadence is configured per show as a song-count range. A music-forward show
talks less often than breakfast or drive; a talk special can alternate one
monologue with one song.

The scheduler selects from that show's approved talk inventory and avoids recent
repeats. If no fresh approved clip exists, it plays music. Missing speech should
degrade the format, not create dead air.

Continuity uses a separate pool. The Signalman can mark an hour boundary on the
flagship, while flow-station continuity is woven more sparsely through a watched
manifest. The C'est and Yacht voices do not share the flagship DJ pool.

Separate pools do not mean separate timing authority. Presenter links,
continuity, and bulletins feed one speech arbiter per station. After any voice
item is selected, the arbiter requires one complete music event before another
voice item becomes eligible. If an hour marker collides with a DJ link or
bulletin, one wins under deterministic policy and the others defer or become
music.

This invariant is validated in the published schedule and enforced again at
playout boundaries. It prevents back-to-back voices even if a producer or model
creates an unusually dense candidate pool.

## 4. Choosing music

The flagship selector tries to satisfy three rules at once:

1. **Rotation gap:** avoid replaying the same asset too soon.
2. **Style spacing:** avoid consecutive genre and artist repetition.
3. **Lane containment:** prefer the current show's own lane, then explicitly
   compatible lanes, before a general fallback.

The widening order is deliberate:

```text
for scope in [own lane, compatible lanes, general fallback]:
    for spacing in [avoid artist+genre, avoid artist, relax spacing]:
        if an eligible fresh choice exists:
            use it
use the least-recently-played eligible fallback as the final safe choice
```

Relaxing spacing before widening scope prevents a minor genre collision from
throwing a specialist show into an unrelated lane.

Flow stations use simpler manifests and time/weight rules:

- lo-fi chooses from time-of-day pools;
- Yacht changes between day and night manifests;
- Tokyo Jazz draws from one approved instrumental pool;
- C'est rotates its main and jazz pools with sparse continuity and a transient
  bulletin fallback.

## 5. Approved manifests

Liquidsoap does not scan arbitrary media directories for playable files. A
publisher creates manifests from files that satisfy the shared policy:

- regular audio and sidecar files, no leaf symlinks;
- explicit `approved` review status;
- current fingerprint-bound technical QA;
- approved media-root containment;
- additional editorial provenance for generated news.

The publisher holds one lock across the refresh and atomically replaces each
playlist. Non-transient station pools refuse to publish empty. Bulletin
manifests are allowed to be empty because silence there means normal music
continues.

For the flagship, schedule validation repeats the approved-only checks for every
event before publishing the schedule and playlist.

## 6. Schedule and state publication

The flagship writes its schedule and playlist through durable temporary-file
replacement. Public state uses small validated JSON contracts:

- station ID must be one of the five registry values;
- item type must be a known music/talk/continuity/news type;
- timestamps must parse;
- duration must be numeric and within a sane range;
- required display fields must be bounded strings.

The public schedule, diary, catalogue, and now-playing feeds follow the same
validate-then-replace pattern. A reader never needs to handle a half-written
JSON document.

## 7. Continuous audio

Each station emits one continuous MP3:

1. playlist or flow source;
2. optional track-sensitive bulletin/continuity fallback;
3. speech-aware transition handling that preserves padded voice tails;
4. slow loudness normalization with bounded gain;
5. limiter;
6. safe fallback source;
7. MP3 encoder;
8. Icecast output.

A continuous MP3 avoids the timestamp discontinuities and browser compatibility
problems of per-track chained streams.

Real-time playout should run at interactive priority. Batch generation, model
loading, large scans, and media processing belong on separate services or
machines so they cannot starve the encoder.

## 8. Truthful now-playing

Now-playing starts from the audio engine's real track-change callback.

- The callback records the exact file that became audible.
- The publisher resolves metadata from the matching schedule event or sidecar.
- `started_at` reflects the actual transition.
- Duration comes from the real asset.
- The website advances progress between polls but re-anchors to each new payload.

If timing is unavailable, the site shows a live title without inventing a
progress bar. For a transient bulletin, the sidecar remains long enough to label
the on-air item even after the watched audio path has been withdrawn to prevent
replay.

## 9. Health and readiness

Playout liveness is only one readiness input. The watchdog also checks:

- five expected Icecast sources and mount reachability;
- now-playing advancement;
- live JSON freshness and validity;
- approved-media manifests and current QA;
- queue cardinality, leases, receipts, and dead letters;
- scheduled producer heartbeats;
- news supply and render failures;
- local listener bindings;
- disk and log growth.

It writes an atomic readiness document. The flagship readiness endpoint fails
closed on missing, invalid, stale, or red evidence. The read-only operations CLI
and LLM tools read this computed state rather than launching their own probes.

## 10. Failure behavior

- Missing talk falls back to music.
- Missing bulletin falls through to the underlying station.
- Colliding speech requests select one item and defer or drop the rest.
- A padding or speech-boundary validation failure makes the candidate
  ineligible.
- A failed manifest build leaves the previous manifest untouched.
- A malformed state write is rejected before publication.
- A dead playout affects one mount, not all five.
- A model or renderer failure produces no candidate rather than bypassing review.

This separation is what makes the station engine safe to operate continuously:
audio can keep moving while generation, review, news, or model summaries are
temporarily unavailable.
