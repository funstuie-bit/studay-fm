# Deep dive: producing and running a presenter voice

Every presenter on the network is a distinct, consistent AI voice. Each one is
produced by zero-shot voice cloning from a single short reference clip, then run
through a fixed post-production chain and a hard quality gate before a single
second of it is allowed on air. The voices are original characters inspired by
radio archetypes, not impersonations of real people (see
[CONTRIBUTING](../../CONTRIBUTING.md)); use only reference audio you have the
right to use.

This page is the end-to-end technical process: pick a voice, render text in it,
make it broadcast-ready, and keep bad renders off the air.

```
reference clip  ─┐
                 ├─►  TTS (zero-shot clone)  ─►  raw wav  ─►  QA + post chain  ─►  approved wav  ─►  playout
script text    ──┘        one-shot per render      (quiet,        (loudnorm, pad,      (review_status
  (per host)              exaggeration / cfg        candidate)      silence guard)       = approved)
```

## 1. The model

The voice engine is a **zero-shot voice-cloning TTS**. This build uses
[Chatterbox](https://github.com/resemble-ai/chatterbox) (about 0.5B parameters).
It has no named voices: you hand it text plus one reference clip and it renders
that text in the reference's voice.

- It runs on a box with a GPU or plenty of unified memory. The renderer selects
  CUDA, then Apple MPS, then CPU. Keep it **off the streaming box**: heavy
  inference next to the live encoder causes stream cutouts. In a multi-machine
  setup the voice service lives on its own node.
- Two render dials:
  - **exaggeration** (0.0 to 1.0): emotion intensity. About 0.5 is neutral.
  - **cfg_weight** (0.0 to 1.0): classifier-free guidance.

## 2. The reference clip

One short, clean, characterful clip per presenter.

- A few seconds up to roughly fifteen is plenty for zero-shot cloning. More is
  not better.
- Mono WAV. Capture the **timbre and cadence** you want the host to have. Avoid
  music beds, background noise, heavy reverb, and overlapping speakers, the model
  clones whatever is in the clip.
- The clip defines the voice: everything that presenter ever says is generated
  from it. Keep one canonical reference per host in a known location and point
  the host's render config at it.

## 3. Rendering text to speech

### Chunking

The model truncates long inputs, so long text is split into sentence-sized
chunks (about 250 characters), each chunk is rendered separately, and the pieces
are concatenated with a short (about 0.12 s) gap for a smooth join. An over-long
single sentence is split further on commas.

### Preparing the text (write for the model, not the page)

Transform pronunciation-hostile tokens **before** feeding the model, while
keeping the human-readable form in the stored script:

- **Spell out initialisms phonetically.** A bare `F M` renders as garble
  ("fm fm" and worse); feed the model `Eff Em`. Do the same for any acronym the
  model mangles.
- **No load-bearing first word.** The model can swallow the very first syllable,
  so do not open on a word the sentence depends on.
- **No ultra-short lines.** One or two word utterances render unreliably.

These are rules the script-writing layer enforces (covered in the DJ-scripts deep
dive); the renderer applies the pronunciation substitutions as a final pass.

### Render parameters, and the one lesson that matters

Practical starting points:

| Voice | exaggeration | cfg_weight |
|---|---|---|
| Conversational DJ | ~0.55 (a touch lower, ~0.48, for a fast/hot delivery) | ~0.45 |
| Calm newsreader | ~0.25 | ~0.40 |

**Do not raise exaggeration to add weight or gravitas.** Past a point it
destabilizes the accent (a calm reader pushed to ~0.35 started drifting into the
wrong accent entirely). Depth and body come from the **post chain** below, not
from overdriving the model. Treat exaggeration as "how animated", not "how big".

### One render per process (memory hygiene)

A long-lived TTS process leaks GPU / unified memory from one render to the next.
Run the renderer as a **one-shot CLI**: it loads the model, renders one clip,
writes the WAV, and exits. A controller feeds it jobs one at a time. Memory stays
flat across a batch of hundreds instead of climbing until the box swaps.

## 4. The post chain and the quality gate

Raw model output is quiet (around -34 dBFS) and untreated. It is tagged
`review_status = "candidate"`. **The playout only ever airs
`review_status = "approved"`.** A QA step bridges the two, and it is where a lot
of the "sounds like radio" comes from.

### Loudness and padding (do not trim)

```
loudnorm=I=-15:TP=-1.5:LRA=11,adelay=250:all=1,apad=pad_dur=0.6
```

- Normalize to a broadcast target (here -15 LUFS integrated, -1.5 dBTP true peak,
  loudness range 11), and resample to a consistent format (24 kHz mono).
- **Do not silence-trim the tails.** Clone tails decay below typical trim
  thresholds (around -45 dB), so an aggressive `silenceremove` eats the last word
  or syllable (hosts get "cut off mid sentence"). Instead pad a short lead
  (250 ms via `adelay`) and tail (0.6 s via `apad`) so the whole word survives and
  breathes.

### Optional per-voice timbre chain

For a voice the clone renders thin, insert a fixed timbre chain **before**
loudnorm, so normalization lands on the final tone rather than fighting it. A
worked example for a deeper, warmer newsreader:

```
aresample=24000,asetrate=24000*0.95,aresample=24000,atempo=1.0526,
bass=g=4:f=140:w=0.6,
acompressor=threshold=-18dB:ratio=2:attack=20:release=250:makeup=2dB
```

- `aresample` first pins the rate so the pitch math is stable whatever the model
  emits.
- `asetrate` * 0.95 drops the pitch about 5%; the matching `atempo=1.0526` puts
  the duration back so only the pitch moves.
- `bass` adds a low shelf (+4 dB at 140 Hz) to restore the chest resonance the
  clone loses.
- `acompressor` adds gentle broadcast weight.

Tune body **here**, not by cranking exaggeration.

### The silence guard

Reject botched renders. Run `silencedetect` and if any internal silence exceeds
about 4 seconds, mark the clip `review_status = "rejected"` and never air it:

```
silencedetect=noise=-38dB:d=4
```

On pass, overwrite the WAV in place and set `review_status = "approved"`,
recording the QA parameters in the sidecar.

## 5. Metadata and the approved-only contract

Every clip carries a JSON sidecar next to the WAV: the host, the voice reference
used, `review_status`, the render params (exaggeration / cfg), timings, and the
QA result. The playout selects **only** approved clips; candidate and rejected
clips sit inert on disk. That single property, approved-only playout, is what
guarantees a bad render cannot reach listeners.

## 6. Scaling and reliability

- **Batch and parallelize.** A controller can fan render jobs across several
  render boxes as a worker pool (one job at a time per box), skipping any clip
  that already exists so a run is resumable and idempotent. Rendering a full
  refresh of every host's talk pool is embarrassingly parallel.
- **Always keep a fallback.** The playout should fall back to music (or a short
  continuity bed) if a talk clip is missing, so a flaky render never becomes dead
  air.
- **Chatterbox gotcha.** Its watermarker imports `pkg_resources`, which
  setuptools 81+ removed. Pin `setuptools<81` or the model fails to initialize
  with a confusing `NoneType` error.

## 7. The swap-in contract

None of the station is bound to one TTS. The rest of the system only needs one
thing: **text in, a WAV in the host's voice out.** Wrap whatever engine you use
behind that contract, either a one-shot CLI as above or a small HTTP service with
a `POST /tts` endpoint taking `{ text, voice_ref, exaggeration, cfg }` and
returning audio. Keep the `candidate -> QA -> approved` lifecycle around it and
you can replace the voice engine without touching the rest of the station.

---

See also: [DJ scripts](dj-scripts.md) (how the words are written),
[the talk pipeline](talk-pipeline.md) (how renders are stocked and refreshed),
and [ARCHITECTURE](../ARCHITECTURE.md) for how the voice service sits in the whole
system.
