# Deep dive: the newsreader

Once an hour a newsreader reads a short music-and-culture news bulletin. It is
built from live feeds, written by an LLM, rendered in a dedicated newsreader voice,
and slipped onto the stream at the next track boundary so it never lands mid-song.
Version 1 ran on one flow station; version 2 renders the bulletin once and airs it
on several stations, each on its own schedule.

```
RSS feeds ─► dedupe/rotate ─► LLM bulletin ─► render (newsreader voice) ─► stage wav+sidecar
                                                                                │
              per active station: track-sensitive fallback airs it at the next  ▼
              track boundary, then the wav self-deletes so it can never loop
```

## 1. Editorial scope (a hard rule)

Music and culture only: albums, tours, festivals, film, art, books, awards. If a
headline touches politics, crime, war, disaster, or any death or tragedy it is
skipped entirely. This is stated in the prompt and is the single editorial
constraint the whole feature is built around.

## 2. Version 1: the hourly loop

A job fires shortly before the top of the hour and runs one self-contained loop.

### Fetch and rotate
- Pull headlines from a set of music and culture RSS feeds (parsed with the
  standard library, no dependencies). A feed that times out is skipped.
- **Dedupe against a seen-store** (a hash per headline with a few-days TTL) so the
  same story is not read twice in a row.
- The feeds hold roughly the same couple hundred headlines for days, so "brand new"
  hits zero by mid-afternoon even when there is plenty to say. Rather than go
  silent, the loop **ranks least-recently-aired first** (never-aired stories at the
  front), builds from those, and re-stamps only the stories it actually used. Only a
  genuine feed failure (too few headlines fetched) yields no bulletin.

### Write
- An LLM writes a roughly 150-word bulletin in a calm newsreader register, picking
  the two or three most interesting stories with smooth verbal transitions.
- The **opener and closer are enforced in code**, not just the prompt (models
  occasionally truncate the sign-off): a fixed "here is the news..." open and a
  fixed "...and that is the news, now back to the music" close are checked and
  repaired. Em dashes are stripped. The bulletin names no stations and no URLs, and
  is length-checked (roughly 90 to 230 words) or rejected.

### Render and QA
- Rendered in a **dedicated newsreader voice**: calmer render params than a DJ, plus
  a timbre chain for gravitas (a slight pitch drop and a low shelf). See
  [Voices](voices.md); the key lesson is that gravitas comes from the post chain,
  not from cranking the model's expressiveness (which drifts the accent).
- Gentle QA (loudness normalize plus lead/tail padding, no silence-trim), then the
  WAV and a JSON sidecar are staged into a watched bulletin directory.

## 3. How it gets on air

The station's playout carries a **track-sensitive fallback** that watches the
bulletin directory:

```
fallback(track_sensitive=true, [bulletin, radio])
```

- With a WAV staged, the bulletin plays at the **next track boundary** (so around
  ten to the hour, never mid-song). Empty, the fallback falls straight through to
  normal programming, so it is safe at all times.
- The loop then **polls the station's now-playing state file**. The instant the
  bulletin starts airing it **deletes the WAV** (the open file handle plays out fine,
  and the emptied watched playlist means it can never loop). The **sidecar stays**
  until the bulletin finishes, because now-playing reads it every few seconds;
  deleting it mid-air would drop the newsreader label. Anything unaired after a
  timeout is withdrawn.

Now-playing shows the newsreader and "The News" for the duration, then returns to
normal.

## 4. Version 2: one render, many stations

The same loop now renders the bulletin **once** and airs it on every active target,
same audio on each. Targets are a small list, each entry carrying its own bulletin
directory, its own now-playing state file, and an **active predicate**:

```
TARGETS = [
  flow station : active 24/7,
  flagship     : active 06:00 to 20:00,   # airs ~:50, so 06:50 through 19:50
]
```

After one render and QA, the same WAV is copied into each **active** target's
bulletin directory with a per-station sidecar, and each target **airs and
self-deletes independently** at its own next track boundary. Rendering once means
no extra load on the voice box, and per-station dayparting is one predicate: a flow
station can carry news around the clock while a DJ-hosted flagship keeps it to
daytime, quiet in the evening like normal radio.

## 5. Two injection mechanisms

The stations do not all inject audio the same way, so the bulletin reaches them two
different ways:

- **A flow station** is a Liquidsoap graph; the bulletin fallback lives directly in
  its stream definition.
- **A schedule-driven station** pre-builds a flat playlist (see
  [the station engine](station-engine.md)). The bulletin fallback is layered **above**
  that playlist, so it interrupts cleanly without touching the schedule builder. One
  extra piece is needed there: because that station resolves now-playing by matching
  the playing file to its schedule (and a bulletin is not in the schedule), a small
  branch detects a bulletin path and reads the sidecar directly, **even after the WAV
  has self-deleted**, to report "The News".

## 6. Failure-safe by construction

- The fallback is **empty-safe**: no staged WAV means the station behaves exactly as
  if the feature were not there.
- A feed outage simply means **no bulletin that hour**, which is fine.
- Rendering once avoids doubling the voice-box load when several stations carry it.
- Every run **clears stale bulletins first** (crash recovery), so a previous run that
  died cannot leave a bulletin to loop.

See also [the station engine](station-engine.md) for how the schedule-driven
station builds and streams, and [Voices](voices.md) for the newsreader render.
