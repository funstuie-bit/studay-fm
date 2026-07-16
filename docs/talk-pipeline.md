# Deep dive: the talk pipeline

Presenter scripts do not air directly. They move through a fixed, reviewable
pipeline that keeps writing, rendering, approval, technical QA, manifest
publication, and playout as separate stages.

```text
character brief -> script candidate -> speech render -> technical QA
                                                |
                                       fixed approval policy
                                                |
                                  approved-media refresh
                                                |
                                      atomic talk manifest
                                                |
                                           playout
```

The writing layer is covered in [DJ scripts](dj-scripts.md), and speech
generation in [Voices](voices.md).

## 1. Candidate is not approved

Talk metadata uses explicit review states:

- `candidate`: generated or rendered, not eligible;
- `approved`: accepted by the configured fixed review path and eligible for
  technical publication;
- `rejected`: retained for diagnosis, never eligible.

Playout still requires current technical QA and manifest inclusion. Editing a
sidecar to `approved` cannot put a clip on air by itself.

This split is useful because script validation and technical review answer
different questions:

- Does the line fit the character and station?
- Is the audio structurally safe and usable?

Both must pass.

## 2. Fixed producer entry points

Earlier designs gave an LLM a shell and asked it to keep talk pools stocked.
That surface has been removed from the operations model.

Current producers invoke fixed Python entry points with argv arrays. They can:

1. inspect a known show's stock;
2. write a bounded number of candidate scripts;
3. render those scripts through the configured voice boundary;
4. run technical QA;
5. publish manifests after explicit approvals already exist.

The read-only operator and private ops bot can report stock and freshness, but
cannot invoke these steps, enqueue a job, approve a clip, or restart a producer.

## 3. Rendering

Speech rendering is serialized per render node. A controller:

- validates the configured presenter and reference mapping;
- skips already completed outputs, making a batch resumable;
- sends text and paths through shell-safe argv or a bounded authenticated API;
- confines references and outputs to approved private roots;
- returns one candidate WAV plus metadata;
- exits or releases the model before the next job, depending on the renderer
  architecture.

Heavy speech inference stays away from the real-time streaming host. A render
failure leaves approved stock untouched.

## 4. Technical QA

Spoken-word QA checks:

- valid audio stream;
- allowed sample rate and channel count;
- duration within the spoken profile;
- no excessive internal silence;
- loudness and true peak within broad safety bounds;
- current file identity matching the cached result.

The post chain normalizes toward the station target and pads a short lead and
tail. It does not aggressively trim silence, because trimming can remove quiet
word endings.

If the audio file changes after QA, its device/inode/size/mtime fingerprint no
longer matches and it becomes ineligible until rescanned.

## 5. Review policy

Recurring presenter talk is approved by a fixed path: the script must pass its
character/text validators, the render must pass speech QA, and the sidecar is
then marked approved. The model cannot set status through a tool, and a technical
failure becomes rejected.

The owner controls the character brief, reference mapping, render settings,
validator code, schedule, and whether the producer is enabled. Manual audition
is the release gate for a new voice, changed renderer, changed post chain, or
other material policy change, and remains available for suspicious clips or
withdrawal.

Private audition pages and source references must stay local-only and outside
the public web root.

## 6. Manifest publication

The approved-media refresh audits changed files and then rebuilds the relevant
talk manifests under one lock. The publisher includes only regular, contained,
approved, technically current clips and replaces the manifest atomically.

Different consumers can share the same rule:

- the flagship schedule reads approved talk inventory;
- Yacht reads the Captain's approved manifest;
- C'est reads a separate approved continuity manifest.

Newly approved content becomes visible at the next normal schedule or watched
playlist refresh. No broad service restart is required.

## 7. Depth and freshness

Pool depth prevents a host from running out. Freshness prevents a full pool from
becoming repetitive. They are monitored independently.

A bounded floor-keeper can add material when a pool drops below its configured
minimum. A separate freshness pass can:

- add a small number of new candidates per presenter;
- leave them off air until reviewed and technically eligible;
- retire the oldest approved clips once a pool exceeds its cap.

Retirement is a move out of watched/selected directories, not an immediate
delete. A clip referenced by the current schedule is protected until it is no
longer live or scheduled.

## 8. Queue use

Large or scarce render batches can be submitted to generation queue v2. Jobs
store validated argv, working directory, attempts, timeout, priority, and
not-before time.

The queue runs one supervisor/command child at a time and records lease identity
plus an exit receipt. Restarting the worker does not duplicate a live render.

Because enqueueing is command authority, queue mutation stays local and trusted.
Models see only the bounded read-only summary.

## 9. Failure detection

The watchdog distinguishes:

- producer heartbeat stale;
- approved depth below floor;
- newest approved clip too old;
- technical-QA cache stale or failed;
- manifest different from the eligible set;
- queue worker stale, invalid record, multiple active children, or dead letter;
- renderer or approval refresh errors.

This catches both obvious failure and the quieter case where a pool still looks
full but no new work has appeared.

## 10. Retention

Approved, scheduled, on-air, continuity, bulletin, and private reference
material are excluded from automated retention selection.

Old rejected, retired, experiment, and archive material may appear in a
read-only retention report after age thresholds. Moving it to external
quarantine is a separate explicit owner action. The scheduled retention job does
not delete talk or references.
