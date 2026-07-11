# Deep dive: the talk pipeline (stocking and refreshing DJ talk)

Written scripts are not what airs. Between a script and the stream sits a pipeline
that renders it to audio, quality-gates it, promotes it to `approved`, and keeps
each host's pool deep enough that no one ever runs out of things to say. A small
self-healing maintenance loop drives the whole thing on a schedule.

```
scripts (candidate) ─► render (one-shot, on a GPU box) ─► QA + approve ─► approved pool ─► playout
        ▲                                                                      │
        └──────────────  maintenance loop: hourly, restock any thin pool  ◄────┘
```

The word-writing is covered in [DJ scripts](dj-scripts.md), the voice render and
QA recipe in [Voices](voices.md). This page is the lifecycle and the loop that
runs it.

## 1. Two review states, and approved-only playout

Every talk clip has a `review_status`:

- `candidate`, rendered, not yet checked.
- `approved`, passed QA, allowed on air.
- `rejected`, failed QA, never airs, kept for inspection.

**The scheduler only ever selects `approved` clips.** That single rule is the
safety property of the whole pipeline: a bad or unrendered clip physically cannot
reach listeners. New approvals are picked up automatically at the playout's next
schedule rebuild, so nothing needs restarting to put fresh talk on air.

## 2. Render

A controller fans render jobs across one or more render boxes as a worker pool
(one job at a time per box), skipping any script that already has audio so a run
is **resumable and idempotent**. Each render runs the TTS as a **one-shot process**
that exits afterward (keeps GPU memory flat), writes the WAV, and tags it
`candidate`. Rendering is confined to a dedicated render node; doing it on the
streaming box starves the live encoders and causes cutouts. Full detail in
[Voices](voices.md).

## 3. QA and approve

Only `candidate` clips are processed. The QA step:

- Normalizes to a broadcast target (`loudnorm I=-15:TP=-1.5:LRA=11`, 24 kHz mono)
  and **pads a lead and tail instead of trimming silence** (trimming ate soft word
  endings).
- Runs a **silence guard**: any clip with more than about `4 s` of internal silence
  is a botched render, marked `rejected`, and never airs.
- On pass, sets `approved` and records the QA parameters in the sidecar.

## 4. The maintenance loop

A long-running operator runs one pass per hour. It does not touch playback or the
stream; its only job is to keep the approved pools deep enough.

Each pass:

1. Takes a lock so two passes never overlap.
2. Assembles a **brief of real state** and hands it to an LLM agent.
3. The agent inspects the brief and, for any thin pool, drives the
   script -> render -> QA pipeline, then reports. Most passes there is nothing to
   do.

**The brief of real state** is assembled from live truth only:

- The **live schedule** (the current show, and which shows still air later today).
- **Per-show pool depth**: a count of `approved` clips in each show's talk
  directory (candidate and rejected do not count).
- **Watchdog health**: any failing health check surfaced as a red line.

Each show is tagged against a floor. A pool below the floor is marked thin, and
the brief ends with an explicit action line listing what to restock.

**Thresholds**: the floor is about `15` approved clips; a thin pool is restocked
up to about `30`, prioritising shows that air today, one show at a time. The
rationale is concrete: the scheduler enforces a multi-hour talk no-repeat, so a
short show with a thin pool cannot reuse a break and the host goes silent in the
back half of the show.

## 5. The guardrails: one tool, a hard denylist

The maintenance agent is a small ReAct-style loop on the same provider-agnostic
OpenAI-compatible layer as everything else (bounded: about `40` tool rounds, a
wall-clock session budget around `30 min`, per-command timeouts). It is given
**exactly one tool: a shell**, and every command is regex-screened against a hard
denylist before it runs. A match is refused and returned to the model as an error.

The denylist blocks, among others:

- recursive force delete (`rm -rf`), `kill -9`, killing a live process
- power or disk operations (`shutdown`, `reboot`, `diskutil`, `dd`, `mkfs`)
- touching a stream or service job (`launchctl bootout|kickstart|unload|...` against
  the stream, encoder, or the loop itself)
- `git push`, `git reset --hard`
- piping remote code into a shell (`curl ... | sh`), `sudo`, fork bombs

Prompt-level rules reinforce it and add policy a regex cannot express: **the stream
is sacred** (never restart a station, report problems rather than fix them),
**render voice only on the render box**, **do not generate music** (that is manual
and single-flight, see [Music](music.md)), **the taste gate is human** (the loop
only checks counts and render success, never judges quality), and **never delete,
push, change config, spend money, or take any irreversible action without a human.**
The net design property: an autonomous hourly pass can top up talk but can never
take the station down or spend money.

## 6. Observability and failure modes

Every pass logs its start, finish, and a heartbeat; the full agent transcript is
appended to a per-day session log; each pipeline stage prints per-item results and
a summary.

The two ways this silently fails, and the watchdog checks that catch them:

- **The maintenance loop stops running -> pools drain silently.** A watchdog check
  reads the service state and alerts if the loop is not running ("pools will
  drain"). This is a real incident: after the job was left disabled, long shows
  went silent in their back half before anyone noticed by ear.
- **A pool goes thin -> the host goes silent late in a show.** A second watchdog
  check independently recounts approved clips per show against the same floor and
  alerts on any thin pool.

The watchdog runs every 15 minutes, alerts only on state transitions (new problem
or resolved), and can push transitions to a chat webhook. These are the same
numbers the maintenance brief reads, giving two independent detectors of a drain.
