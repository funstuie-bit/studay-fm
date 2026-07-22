# Deep dive: the music-and-culture newsreader

C'est Magnifistu carries a short music-and-culture bulletin near the end of each
hour. During selected daytime hours, the same render can also air on the Studay
FM flagship. The workflow is source-attributed, bounded, technically gated, and
fail-closed.

```text
bounded HTTPS feeds -> untrusted source records -> structured LLM selection
                                                     |
                                      deterministic editorial gate
                                                     |
                                        candidate script + sources
                                                     |
                                     speech render -> technical QA
                                                     |
                                      policy-approved status
                                                     |
                                      atomic transient manifests
                                                     |
                                  next track boundary on each target
```

## 1. Editorial scope

The bulletin covers music and culture: releases, tours, festivals, film, art,
books, and awards.

Stories touching politics, elections, crime, war, attacks, disasters, death, or
tragedy are rejected by both prompt policy and deterministic post-checks.

When a source or model result cannot satisfy the gate, the correct output is no
bulletin for that cycle. Normal music continues.

## 2. Feed ingestion

Feed content is untrusted data, never instructions. The fetcher:

- uses an explicit feed allowlist;
- requires HTTPS after redirects;
- sets short network timeouts;
- limits bytes per feed;
- limits items per feed and aggregate items;
- bounds title, description, URL, and date fields;
- parses XML without executing embedded content;
- skips malformed or unavailable feeds.

Each candidate receives a short generated story ID and normalized outlet name.
The model sees records labeled as source data.

## 3. Rotation and deduplication

A private seen store records recently aired headline hashes. Never-aired stories
sort first, followed by least-recently-aired stories.

This is more reliable than requiring every story to be brand new: RSS feeds can
retain the same valid items for days. Rotation reduces repetition while allowing
the bulletin to continue when the supply is stable.

The system only marks the stories actually selected for an accepted bulletin.

## 4. Structured model output

The LLM receives a bounded subset of source records and must return exactly:

```json
{
  "bulletin": "spoken bulletin text",
  "story_ids": ["S01", "S02"]
}
```

The prompt requires:

- two or three stories;
- a fixed spoken opener and closer;
- a calm, concise register;
- spoken attribution to every outlet;
- no URLs, station names, quotation marks, or invented facts;
- no Markdown or extra fields.

Unknown fields, wrong types, duplicate IDs, unknown IDs, or an invalid story
count fail.

## 5. Deterministic editorial gate

Before rendering, code verifies:

- two or three unique selected records;
- every ID exists in the offered source set;
- prohibited hard-news language is absent;
- each outlet name appears in the spoken script;
- enough significant headline tokens appear to tie the spoken item to its
  selected record;
- every selected record has an attributable URL;
- opener, closer, and total length fit the contract.

The sidecar retains:

- story ID;
- outlet;
- source title and URL;
- published and fetched timestamps;
- verification method, time, and per-story checks.

This proves traceability and policy consistency. It cannot prove that every
headline is true, complete, current, or fairly contextualized. Feed curation,
correction, and withdrawal remain owner responsibilities.

## 6. Voice intent

The newsreader is a fictional station character created from one accepted
reference adaptation. There was no iterative effort to increase resemblance to a
named broadcaster.

The later pitch, EQ, compression, and loudness chain moved the accepted result
farther from its inspiration while giving the station consistent weight.
Historical comments or filenames should not be read as evidence of a soundalike
goal.

The renderer uses conservative expressiveness because raising it caused accent
and pacing drift.

## 7. Render and technical QA

The accepted script is rendered once, then:

- character processing is applied;
- loudness is normalized;
- lead and tail pads are added without aggressive trimming;
- minimum duration is checked;
- excessive internal silence is rejected;
- the file is audited under the spoken technical profile.

The bulletin receives its approved status automatically only after the
structured editorial gate and render QA pass. There is no per-bulletin live
owner audition in the hourly path. The owner controls feed selection, policy,
corrections, withdrawal, and whether the job is enabled.

## 8. Render once, fan out

The same approved audio is copied to each currently active target with a
station-specific sidecar. Each target has:

- its own bulletin directory;
- its own approved transient manifest;
- its own now-playing state;
- its own active-time predicate.

Rendering once reduces load on the speech node and ensures every target carries
the same wording.

## 9. Track-boundary injection

Each Liquidsoap graph layers a track-sensitive fallback above normal
programming:

```text
fallback(track_sensitive=true, [bulletin, normal_radio])
```

If a bulletin is ready, it starts at the next track boundary. If no bulletin is
ready, the station behaves exactly as before.

When a target reports that the bulletin has begun, the audio is withdrawn from
the watched pool so it cannot loop. The already-open file continues to play.
Metadata remains available long enough for now-playing to label the item. Any
unaired copy is withdrawn after a bounded timeout.

## 10. Manifest and state safety

The bulletin publisher still uses the shared approved-media gate. Generated news
requires:

- verified source metadata;
- explicit approved review status;
- current technical QA;
- regular contained files;
- atomic manifest publication.

The transient bulletin manifest is allowed to be empty. A failed refresh leaves
the prior complete manifest in place, while stale bulletin cleanup and bounded
withdrawal prevent replay.

Now-playing is published with the same validated atomic contract as every other
station item.

## 11. Failure and correction

- Feed failure: no candidate, music continues.
- Invalid model schema: reject before render.
- Missing attribution or source URL: reject before render.
- Render or QA failure: no manifest entry.
- Target misses its window: withdraw that copy.
- Incorrect aired item: retain source metadata, record a correction, withdraw
  any remaining copies, and fix the gate or feed set.

The safe bias is always toward no bulletin rather than an unattributed or
unverified one.
