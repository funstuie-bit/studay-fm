# Deep dive: continuity and the diary

Threading the whole network together is a single continuity voice that is not a DJ. It
marks the hours on air, carries the mood between tracks on the flow stations, and
writes a short public diary about the state of the station. It is calm, precise, and
deliberately spare.

## 1. The continuity voice

A station-owned voice distinct from the host roster: a low-energy, public-information
register (calm, measured, quietly authoritative, only occasionally dryly amusing). It
never talks about itself and never does a "show". Its lines are short and factual, and
it plays two roles: an on-air ident between programmes, and the author of the public
diary.

The on-air register is enforced hard in its prompt: spoken words only, `5 to 15` words
(never more than `25`), short factual sentences, and an explicit "inform, do not tell a
story, review music, give an opinion, or react emotionally". It even ships an allowed
vocabulary (`station, programme, broadcast, signal, hour, next, shortly, continues`)
and a forbidden one (`amazing, incredible, emotional, beautiful, story, dreams,
philosophy, poetry`).

## 2. On-air idents at the hour boundary

Continuity clips live in their **own pool**, separate from per-show talk. The schedule
builder collects every approved continuity clip into one list, shuffles it once with
the build seed (a stable round-robin), and inserts one at the first event that crosses
into a new clock hour:

```
if hour_key != last_hour and continuity_pool:
    pick = continuity_pool[index % len(continuity_pool)]; index += 1
    kind = "signalman"        # tagged distinctly from "talk" and "music"
    last_hour = hour_key
```

So **at most one ident per clock hour**, chosen round-robin, and empty-safe (the
`and continuity_pool` guard means an empty pool simply falls through to normal
cadence). This is a different mechanism from DJ talk, which is inserted by a per-show
song-count cadence with its own no-repeat rule (see
[the station engine](station-engine.md)).

## 3. Producing continuity clips

The lines are written by the LLM and rendered in the continuity voice through the same
pipeline as DJ talk (see [Voices](voices.md) and [the talk pipeline](talk-pipeline.md)):
low exaggeration for a calm delivery, loudness-normalized with lead and tail padding
(no silence-trim), rejected if there is more than about `4 s` of internal silence, and
promoted to `approved` before it can air. Approved clips land in a continuity pool with
a sidecar tagged `role: "continuity"`. The generator is idempotent: on a re-run it
reads existing lines and only renders what is missing.

## 4. The flow-station continuity host

The genre-free flow stations carry a **sparser** continuity voice woven between tracks
rather than a scheduled ident. Its lines are short, station-safe sentences bucketed by
kind (`ident`, `eclectic`, `moment`), each rendered and QA'd the same way. Rather than a
fixed bank, they are **refreshed daily**: a scheduled pass writes new lines in the
continuity voice with the LLM, renders and approves them, and rotates the oldest beyond a
cap into a retired folder, with a freshness check watching the pool. (An early build
shipped a static bank and looped the same handful of lines for days before this was added,
the same depth-is-not-freshness lesson as the talk pools.) They are woven in with a
weighted rotation over an empty-safe fallback:

```
continuity = fallback(track_sensitive=true, [ playlist(watch, continuity_dir), music ])
radio      = rotate(weights=[10, 1], [ radio, continuity ])
```

That is roughly **one continuity slot per ten tracks**, and if no clip is ready the
inner fallback yields another track instead of stalling. The continuity directory is a
watched playlist, so newly approved lines air without a restart.

## 5. The public diary

On a schedule (about every `30 min`) the LLM writes a short reflective note on the
station's inner life, in the continuity voice.

- **Grounded in real state only.** Before writing, it gathers the current and next
  show, the current track and artist, stream up/down and listener count from the local
  streaming-server status, the approved music library depth, the catalogue size, a pass
  counter, and the **last several diary entries with an explicit instruction not to
  repeat their wording or focus**.
- **Register**: first person, calm, spare, warm but observant, two short paragraphs.
  The hard guardrail: ground everything in the given facts, **never invent listener
  numbers, songs, hosts, or events**. No em dashes.
- **Output contract**: the model must return compact JSON `{ mode, title, text }`, where
  `mode` is one of `maintenance` / `continuity` / `responsive` / `special` and `title`
  is at most seven words. A self-hosted model path enforces this with a response JSON
  schema (malformed output is structurally impossible); a hosted provider is the
  alternative, selected per task so the diary's model routing is independent of the
  rest.
- **Never goes dark**: if the model is unavailable, a deterministic note is composed
  purely from the facts (current host and track, next handoff, stream state), so the log
  always has an entry. Each entry records a `writer` field (deterministic or the model
  used) so "reads right" can be told apart from "came from where you think".

## 6. Storage and publishing

Entries are appended to a shared **append-only ledger** as `diary_entry` events. Writes
are idempotent: the entry id is derived from the station plus the 30-minute time bucket,
so a re-run inside the same window is skipped and the ledger refuses duplicate ids. A
separate publisher reads the ledger, sorts newest first, and writes two artifacts for
the site: a static diary page and the **diary JSON the SPA reads** (see [the site](site.md)).
A house-style pass strips any dashes at write time and again at publish time.

## 7. Guardrails

- **No em dashes anywhere**, enforced in the prompt, at write time, and at publish time.
- **Facts only** in the diary; no invented numbers, songs, hosts, or events.
- **Human taste gate**: on-air continuity, like all talk, only airs once its sidecar is
  `approved`. The automation tracks counts and render success, never judges quality.
