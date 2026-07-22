# Deep dive: writing DJ scripts

Each presenter has a static character brief. A bounded language-model call or a
deterministic fallback produces a candidate script, and validators either accept
the candidate for rendering or reject it with reasons.

```text
character brief -> bounded prompt -> LLM or deterministic fallback
                                      |
                                validate text
                              pass / reject+retry
                                      |
                            candidate script sidecar
```

The script layer does not approve audio, control playout, or administer the
station.

## 1. Character brief

A presenter configuration can include:

| Field | Purpose |
|---|---|
| `identity` | Who the fictional host is and what they notice |
| `tone` | Energy, pace, sentence length, emotional register |
| `story_style` | Long-form structure or comedy mechanism |
| `segments` | Intro, back-announce, hour marker, feature, monologue, and so on |
| `angles` | Concrete premises to rotate across |
| `allowed` | Preferred topics and vocabulary |
| `forbidden` | Topics and literal phrases that must be rejected |
| `handoffs` | Approved clean endings into music |
| render settings | Presenter-specific speech parameters |

The brief is versioned station configuration, not model memory. A stateless call
can therefore be audited and reproduced.

## 2. Model boundary

Writing tasks use an OpenAI-compatible chat API. The configured endpoint can be
local or hosted, but the call is still bounded:

- endpoint and model identifier allowlists;
- scoped credential available only to the writing process;
- request, response, timeout, and token limits;
- no redirects to arbitrary hosts;
- no tool access;
- no station mutation authority.

The earlier local coordinator and local-model Hermes configuration were not
reliable enough to run operational tools safely. The current private Hermes
gateway uses DeepSeek within fixed workflows, while the separate operator
surface remains read-only.

Changing provider does not change these capability limits.

## 3. Prompt construction

The prompt contains:

- fictional identity and tone;
- chosen segment type and least-used angle;
- allowed and forbidden topics;
- target word range;
- required handoff;
- station pronunciation rule;
- output-only-spoken-words rule;
- no real-artist or real-song invention where the format requires fictional
  catalogue references;
- no em dashes or stage directions.

Feed stories and other external text are not mixed into ordinary DJ prompts.
The news workflow has its own untrusted-data boundary.

## 4. Anti-staleness

The generator scans existing non-rejected scripts and counts angle use. It
chooses among the least-used angles, so never-used premises win before familiar
ones.

Freshness still needs operational monitoring. A large pool can remain full while
its newest script becomes old. The watchdog therefore tracks both approved depth
and newest approved age.

## 5. Validation

A candidate can be rejected for:

1. word count outside the presenter's range;
2. global stale or purple phrases;
3. presenter-specific forbidden terms;
4. missing or stacked handoffs;
5. unbalanced quotes;
6. incomplete final sentence;
7. malformed station-name pronunciation;
8. stage directions, Markdown, or labels;
9. unsupported output shape.

The generator can append bounded rejection reasons and retry a small fixed
number of times. It does not loop indefinitely. A failed item is skipped so one
bad completion cannot stop a batch.

## 6. Deterministic fallback

If no provider is configured, the endpoint is unavailable, or all bounded
attempts fail, the producer can choose from built-in presenter lines.

Fallback scripts are marked with their generation source. This keeps the public
demo account-free and lets production degrade without inventing a successful
model call.

The fallback is not a bypass: it still becomes a candidate and follows the same
render, review, technical QA, and manifest path.

## 7. Writing for speech

The script validator enforces renderer-friendly text:

- spoken words only;
- no ultra-short lines;
- punctuation suitable for chunking;
- pronunciation-safe station name;
- no em dash pause artifacts;
- a clean final handoff.

Long-form characters get wider word ranges and explicit structure. Continuity is
short, factual, and non-performative. The satirical talk character has a fixed
argument mechanism and rejects abuse or accidental self-awareness that breaks
the joke.

## 8. Candidate metadata

An accepted script sidecar records:

```text
station_id, show_id, show_name,
host_id, host_name,
segment_type, angle, text,
private voice mapping identifier,
review_status: candidate,
generated_at, generator,
model, generation_source,
brief/config revision
```

Avoid copying raw reference paths into public logs or feeds. Production sidecars
remain private.

## 9. Operations separation

The typed station operator is not the scriptwriter's shell. It can inspect
health, now-playing, queue summary, lanes, talk stock, and flags through one
validated read-only tool.

Script production is invoked by fixed scheduled jobs or trusted local queue
commands. Approval, retries, configuration changes, and service control remain
owner actions.

From the accepted script sidecar, continue to the
[talk pipeline](talk-pipeline.md) and [voice renderer](voices.md).
