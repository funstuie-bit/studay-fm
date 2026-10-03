# Production flow and atomic publication

The live station never plays directly from a generator output folder. A file can
exist, decode and still be nowhere near ready for air. Studay FM puts a fixed
chain between generation and broadcast, then makes every publication step
replace a complete known-good state with another complete known-good state.

That sounds fussy. It is also why a failed refresh does not turn into dead air or
a half-written playlist.

## The full production shape

```text
                                  listeners
                                      |
                           HTTPS through a named tunnel
                                      |
                  +-------------------+-------------------+
                  |                                       |
             mount allowlist                         site allowlist
                  |                                       |
          loopback Icecast                         loopback Caddy
                  |                                       |
       five Liquidsoap playouts                 static app + live JSON
                  |
       speech-safe schedules and now-playing state
                  |
       approved-media manifests only
                  |
        +---------+----------+
        |                    |
   batch workers       scheduled producers
        |                    |
   ACE-Step music      Chatterbox speech
        +---------+----------+
                  |
       candidate -> fixed review policy -> technical QA -> approved

  watchdog -> atomic readiness -> typed station capability broker
                                      |
                  observe | owner-authorised action | policy repair

  exact approved record -> presenter text -> speech QA -> talk/track pair
  editorial sessions -> private airchecks / bounded expiring show canary
```

The five stations use separate Liquidsoap graphs and separate Icecast mounts.
Studay FM follows a full schedule. StuLoFiDay, Yacht Zone, Tokyo Jazz and C'est
Magnifistu use simpler flow rules and watched manifests. One failed dial should
not require the other four to restart.

## From candidate to air

Generated media moves through this chain:

```text
generate -> candidate -> review -> technical QA -> manifest -> playout
```

An `approved` value in a sidecar is not enough. A playable asset needs all of the
following:

1. A regular audio file below an approved media root.
2. A valid same-stem metadata sidecar.
3. Approval from the configured review path.
4. Current technical QA tied to the exact file identity.
5. Any extra subsystem gate, such as source records for generated news.
6. Inclusion in the complete manifest watched by Liquidsoap.

Music across all five stations uses owner listening review. Recurring speech,
continuity and news can use fixed owner-configured validators. The model does not
have a tool that can mark its own output approved.

Technical QA checks the appropriate music or spoken-word profile. That includes
format, sample rate, channel count, duration, internal silence, loudness and
peak. If the underlying file changes, its fingerprint no longer matches the QA
record. It becomes ineligible until checked again.

## Atomic manifest publication

The manifest publisher takes one lock for the whole refresh. It builds and
validates the next playlist away from the watched path, writes a private
temporary file in the same directory, flushes it, replaces the live manifest
and flushes the directory.

Liquidsoap therefore sees either the previous complete playlist or the next
complete playlist. It never sees the writer halfway through its work.

Normal music pools refuse to publish an empty manifest. Bulletin manifests are
allowed to be empty because an empty bulletin pool means normal music continues.
If any build fails, the previous manifest stays in place.

## Atomic state publication

Now-playing, schedules, catalogue, diary, watchdog state and readiness use the
same pattern. The complete JSON payload is validated before it can replace the
current file.

The contracts reject unknown station IDs, unknown item types, invalid
timestamps, impossible durations, oversized display strings and malformed
readiness checks. Readers also reject stale readiness evidence.

Now-playing begins with Liquidsoap's real track-change callback. It does not
guess from the schedule. The callback identifies the file that actually became
audible, and the publisher resolves its metadata and start time. If reliable
timing is missing, the site shows the title without making up a progress bar.

## Speech cannot pile up

Presenter links, continuity and bulletins share one speech arbiter on each
station. Only one voice item can win a boundary, and a complete music track must
play before another voice item becomes eligible. A late or colliding voice item
is deferred or dropped. Music carries on.

Track-aware presenter links add another check. The accepted talk file is bound
to one exact approved record and its metadata hashes. The scheduler verifies the
pair when building the schedule and the live selector verifies it again before
use. If the record changed or was retired, the talk is omitted.

## Failure is boring on purpose

A missing presenter link falls back to music. A missing bulletin falls back to
music. A failed manifest build leaves the old manifest alone. Invalid public
state is rejected before publication. A renderer or model failure creates no
candidate. One dead playout affects one mount.

The interesting AI work can fail without taking the transmitter with it. That
is the whole point.

More detail lives in [Architecture](ARCHITECTURE.md),
[Station engine](station-engine.md) and [Reliability](reliability.md).
