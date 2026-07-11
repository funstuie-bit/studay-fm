# Deep dive: writing the DJ scripts

Every word a host says is written fresh by an LLM, in that host's voice, against
a per-character brief, and then either passes a validation gate or is rejected and
rewritten. If no model is configured the same pipeline runs on built-in
deterministic lines, so the whole system works with zero keys and zero spend.

```
character sheet ─►  prompt  ─►  LLM (OpenAI-compatible)  ─►  validate  ─►  candidate script (.json)
 (identity, tone,     (one       or deterministic lines      pass? store.        review_status
  angles, forbidden,   flat        (fallback)                fail? feed reasons   = candidate
  handoffs)            turn)                                  back, retry x3)
```

This page is the script layer. The voice that speaks these words is covered in
[Voices](voices.md); how scripts get rendered and kept stocked is in
[the talk pipeline](talk-pipeline.md).

## 1. The character sheet

Each host is a static config entry. The fields are what turn a generic LLM into a
consistent, on-voice presenter:

| Field | What it does |
|---|---|
| `identity` | One or two sentences: who they are, what they love, what they notice. |
| `tone` | Energy rating, pace, sentence length, emotional register (e.g. "gentle, occasionally corny, never sarcastic"). |
| `story_style` | Long-form/comedy hosts only: a paragraph describing the storytelling voice, and for a comedy monologue host the entire structural engine of the joke. |
| `segments` | The break types this host can do (song intro, back-announce, hour marker, weather note, feature intro, rant, and so on). |
| `angles` | A pool of concrete one-line story premises. One is chosen per break. |
| `allowed` | Preferred vocabulary and subjects, injected as "allowed topics". |
| `forbidden` | A denylist of topics and literal phrases. It both steers the prompt and is enforced as a hard rejection (below). |
| `handoffs` | A few canned "into the music" closing lines. One is injected as the required sign-off and checked for. |
| render knobs | Optional per-host `exaggeration` / `cfg_weight` for the voice render. |

## 2. The prompt and the model

The generator speaks a **provider-agnostic OpenAI-compatible** chat API: set a
base URL, key, and model in config and it runs against any hosted provider or a
local model, unchanged. The prompt is **flat instruction text folded into a single
user turn** (no separate system message): the character brief is injected inline
(identity, tone, story style, the chosen segment type and angle, the allowed and
forbidden lists, and one random handoff as the required close), followed by an
explicit rules block. Typical settings: `temperature` around `0.9`, `max_tokens`
around `1200`.

Illustrative rules block (standard break):

```
- Output only the spoken words. No stage directions, no markdown, no labels.
- Write 50 to 90 spoken words. Never fewer than 25 or more than 120.
- Structure: observation, presenter reaction, then a clean music handoff.
- End with exactly this one music handoff: <handoff>. Do not stack or quote another.
- Mention the station name no more than once.
- Do not name real artists or real songs. None of the music on this station is real.
- Do not use any of these phrases: <global denylist>.
- Never use an em dash.
```

Long-form templates raise the word range and demand the personality land early;
the continuity announcer template caps at a handful of words and forbids
storytelling, opinion, and emotion; the comedy monologue template hard-codes its
satirical structure and an exact closing line.

## 3. Angles and anti-staleness

Segment type is chosen at random per break. The **angle** (the story premise) is
chosen to avoid repetition: the generator scans the host's existing non-rejected
scripts, counts how many used each angle, and picks at random among the
least-used ones. Never-used angles always win, so the host cycles its whole
premise pool instead of circling the same few.

## 4. The validation gate

A generated script returns a list of rejection reasons; any non-empty list fails
it. The concrete checks:

1. **Word-count bounds** per host (e.g. continuity `3 to 25`, a warm rambler
   `80 to 150`, long-form record hosts `120 to 240`, a comedy monologue
   `200 to 440`, default `25 to 120`).
2. **Global "poetry-drift" denylist**: a list of purple phrases the models reach
   for ("the pavement remembers", "the darkness whispered", and the like), matched
   as substrings in both straight and curly-quote forms.
3. **Per-host forbidden terms**: every entry in the host's `forbidden` list, matched
   as a lowercase substring. This is why some forbidden entries are literal phrases,
   for a comedy host who must never notice he has flipped his own argument, the
   trigger phrases are banned outright.
4. **Handoff presence** (non-continuity): exactly one of the host's handoffs must
   appear. Zero rejects as "missing music handoff"; more than one as "stacked
   handoffs".
5. **Balanced quotes** and a **complete final sentence** (ends in `. ! ?`).
6. **Station name normalized**: no un-normalized spelling of the station name may
   remain (see the pronunciation note below).

On failure the reasons are **appended to the prompt** ("The previous attempt was
rejected for: ...; rewrite it completely") and the model tries again, up to three
times. After three failures the item is skipped and the batch continues, so one
bad generation never kills a run. This retry-with-reasons loop is most of what
keeps hosts on voice.

## 5. The deterministic fallback

If no provider is configured, or the model returns nothing, or every attempt
fails, the generator falls back to **built-in per-host lines**. The scripts are
tagged `generation_source: "deterministic"` vs `"llm"`. This is what lets the
render and QA pipeline (and the whole demo) run with no API key and no spend, and
it guarantees a host is never left with an empty pool because the model was down.

## 6. Writing for the voice

The script layer enforces the rules the TTS needs (see [Voices](voices.md) for
why):

- **Em dashes are stripped** before storing (replaced with a comma). This is an
  absolute house rule, and an em dash renders as an unintended pause.
- **Spoken words only**, no stage directions, markdown, or labels, so the renderer
  never voices annotations.
- **No ultra-short lines** (word-count floors), and the continuity host is held to
  short plain factual sentences.
- **The station name is pinned to one spoken spelling** so the model pronounces the
  call sign correctly.
- The handoff must **end** the script, giving a clean musical out-point.

## 7. Output

Each accepted script is a JSON sidecar written to a per-show scripts directory,
tagged `review_status: "candidate"`, carrying:

```
station_id, show_id, show_name, host_id, host_name,
segment_type, angle, text, voice (reference clip path),
review_status: "candidate", generated_at, generator,
llm_model, generation_source
```

From here it enters [the talk pipeline](talk-pipeline.md): render to audio, QA,
and promote to `approved` before it can air.
