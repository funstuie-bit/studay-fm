# Deep dive: the station engine (scheduler and playout)

What makes it feel like a station rather than a shuffle is a single supervisor that
builds a full broadcast day on a clock, picks every track by rule, renders the day
to a flat playlist, and hands playout to a streaming engine that emits one
continuous normalized stream and reports exactly what is audible.

```
config (the clock) ─► build 24h schedule ─► playlist.m3u ─► Liquidsoap ─► one continuous MP3
   shows + hours        (per-slot: show,      (flat file,     (normalize,      to the mount
   + lanes + cadence     kind, track by rule)   watched)        limit, encode)
                                                     │
                              on_track writes the actually-playing file ─► truthful now-playing
```

## 1. The clock

A `show_at(when)` function maps any instant to the show that owns it. Each show
declares either an everyday `hours` window (`"HH:MM-HH:MM"`, wrap past midnight
allowed) or a day-restricted `windows` list. Resolution is two-pass, **specials
win**:

1. Any show with a day or window restriction whose day and time match now.
2. Otherwise the first everyday show whose window contains now.

That is how a weekday clock (breakfast `06-10`, midday `10-14`, drive `14-18`,
evening `18-22`, late `22-02`, overnight `02-06`) gets overridden: a Friday-night
special displaces the evening show, a weekend crew swaps in on Saturday and Sunday
daytime, and a weekly special takes a single slot on its days. A special fully
displaces whichever regular show it overlaps.

## 2. Walk-the-clock construction

The builder starts at "now", and appends events until it has covered 24 hours. Each
step: ask the clock for the show, decide the event **kind** (station ident, talk,
or music), pick the concrete asset, measure its real duration, append an event
(`start`, `end`, `duration_seconds`, `show`, `host`, `kind`, `path`, ...), and
advance the cursor by that duration. Because the cursor advances by real file
length, slots are not fixed blocks: a show simply owns whatever tracks fall inside
its hours. The build is seeded from the timestamp, so it is deterministic but
distinct each rebuild. The supervisor rebuilds the whole day roughly every 24 hours,
hot-swapping it (below).

## 3. Kinds and talk cadence

- A **station ident** is dropped at each hour boundary (round-robin over a continuity
  pool).
- **Talk cadence** is per show: `(low, high)` songs between breaks, drawn each time.
  Personality and daytime shows talk often (about `3 to 4` songs apart), music-forward
  evening and late shows less (`5 to 8`), and a talk-dominant special is `(1, 1)`, one
  monologue, one song, repeat.
- A break is drawn from **that show's approved talk pool** only, scanning from a
  rotating index and taking the first clip that belongs to the show and is **fresh
  under a multi-hour no-repeat** (about `8 h`), so recently-aired breaks are skipped.
  If nothing fresh exists it defers talk and plays music.

## 4. Choosing music: three rules at once

Every music pick runs through one selector that honors three constraints
simultaneously.

**Rule 1, no repeat too soon.** Each candidate must satisfy
`now - last_played >= gap`. The target gap is about `16 h`; small special-show
libraries override it tighter (a Friday special `2 h`, a talk special `1 h`, weekend
mellow shows `2 to 3 h`).

**Rule 2, genre and artist spacing.** The builder tracks the last genre and the last
couple of artists and avoids them, so no two same-style tracks and no same artist
land back to back. Both use tags written at generation time (see [Music](music.md)).

**Rule 3, no lane bleed.** A show must exhaust its **own** lane, then a short
whitelist of **compatible** lanes, before reaching a general fallback. A compatibility
map lists, per show, the musically adjacent lanes it may borrow from; genre-locked
specials borrow from no one and are excluded from regular shows' fallback, so an
arena-rock hour never leaks into a pop show.

The algorithm widens scope and relaxes spacing in a fixed order:

```
for lanes in [ own lane, compatible lanes, general fallback ]:   # widen scope
    for spacing in [ avoid artist+genre, avoid artist, avoid nothing ]:  # relax
        candidates = fresh tracks in `lanes` matching `spacing`
        if candidates: return random choice
return least-recently-played across fallback lanes   # last resort, never stalls
```

Order matters: it fully exhausts the show's own lane (relaxing genre, then artist)
before widening, so a mere genre clash never throws a show onto a neighbour's shelf
when staying home would have worked. The absolute last resort is a
least-recently-played pick, so the stream never stalls even when everything is "too
recent".

## 5. Schedule validation

Before any schedule goes live it must pass a validator (a failure aborts the
rebuild):

- **Every file exists** on disk.
- **Approved-only**: every asset's sidecar is `review_status: "approved"`.
- **No empty kinds**: there is at least one music, one talk, and one ident event.
- **Repeat-gap floor**: consecutive plays of an asset are spaced at least a floor
  apart (a looser `7 h` floor than the selector's `16 h` target, so intended
  thin-lane fallbacks pass but true too-soon repeats are rejected).
- **No missing shows**: every regular show appears (skipped on days a special
  legitimately displaces one).

## 6. The playlist model

The builder writes two runtime files: `schedule.json` (the full event list, the
truth for now-playing) and `playlist.m3u` (a flat list of audio paths in play
order). **Python owns sequencing; the streaming engine just plays the file list.**
Liquidsoap loads it with `playlist(mode="normal", reload_mode="watch")`, so it plays
in order and **hot-reloads when the file changes**, letting a 24-hour rebuild swap
the day seamlessly with no restart. The `:50` news bulletin is layered on top as a
track-sensitive fallback over a second watched playlist (see
[the newsreader](newsreader.md)).

## 7. Playout and encoding

One continuous, gapless, loudness-normalized MP3 per station. The chain:

1. `playlist(...)` (plus the optional bulletin fallback).
2. `normalize(target=-15., window=4., gain_min=-6., gain_max=6.)`, a slow `4 s`
   window so it levels track to track without chasing intra-track dynamics (a short
   window pumps quiet-loud-quiet on anything that breathes), gain clamped to plus or
   minus `6 dB`.
3. `limit(...)`, a brickwall limiter so normalize cannot overshoot into clipping.
4. `mksafe(...)`, makes the source infallible so the output never dies on a gap.
5. `output.icecast(%ffmpeg(format="mp3", %audio(codec="libmp3lame", b="128k",
   ar=44100, channels=2)), ...)`, continuous MP3 at `128 kbit/s`, `44.1 kHz`, stereo.

**Why one continuous MP3.** An earlier per-track pipeline re-encoded every track as
a separate stream (chained Ogg). The per-track timestamp discontinuities made
browsers stall or cut out between tracks, and Ogg locks out Safari and iOS entirely.
One continuous MP3 is smooth in every browser.

## 8. Truthful now-playing

Now-playing is driven by what is **actually audible**, never a wall-clock guess.

- **Ground truth.** Liquidsoap's `on_track` fires on every real track change and
  writes the playing filename to a state file. Because it fires on the real audio
  boundary, the state file's mtime is when playback actually started.
- **Match.** The API reads that file, finds the scheduled event with that exact path
  (disambiguating a repeated track by the event whose start is nearest to now), and
  takes show, host, title, and kind from the matched event.
- **Progress.** The progress bar starts from the state file's mtime and runs for the
  track's real duration, so it tracks the audible track, not the planned clock, and
  never drifts from the audio.
- **Publish.** The current object is written every few seconds to a public JSON file
  and served from a small HTTP endpoint. An audit mode cross-checks the wall-clock
  show, the scheduled event, and the published now-playing, and fails on any
  disagreement.

See also [Music](music.md) for how the tracks are made and tagged, and
[the talk pipeline](talk-pipeline.md) for how the approved talk pool is kept stocked.
