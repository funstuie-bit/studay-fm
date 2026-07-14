# Deep dive: the site (a custom single-page app)

The website is one static `index.html`, a single-page app built on a small in-repo
framework layered over React, wired entirely to live JSON the backend publishes. It
has a persistent player so audio survives navigation, and a now-playing card whose
progress bar tracks the real audio rather than a wall clock.

```
static index.html + a small framework (support.js over React)
        │  fetch, no-store, poll every 5s
        ▼
per-station now-playing JSON  ·  today's schedule JSON  ·  catalogue JSON  ·  diary JSON
        (written by the playout and publishers; the site is a pure static shell)
```

## 1. The component framework

The app is authored as a **Design Component**: an HTML template block plus a
`class Component extends DCLogic`. `DCLogic` is a small base class with React-style
lifecycle methods (`componentDidMount`, etc.), `this.state` / `this.setState`, and a
`renderVals()` that returns the value bag the template renders against. The runtime
wraps each component in an internal React class with an error boundary.

Templates are **compiled once**: the HTML is parsed into a `<template>`, walked once
to produce an array of builder functions, and each builder returns a
`React.createElement` tree from the current value bag. Re-render re-runs builders, it
never re-parses strings. Expressions in `{{ }}` are evaluated by a small hand-written
resolver (property paths, indexing, `===`/`!==`/`!`, literals), **not** `eval`.

## 2. Template directives

- **`{{ expr }}`** interpolation, in text nodes and in any attribute value.
- **`sc-for`** repeats an element: `list="{{ arr }}"`, `as="item"` (plus `$index`), and
  a placeholder count for skeletons while data streams.
- **`sc-if`** renders children only when `value="{{ expr }}"` is truthy.
- **Dynamic attributes on repeated elements**: a whole-value `{{ }}` returns the raw
  resolved value, so `onClick="{{ row.onPlay }}"` binds a real per-row function and
  `style="{{ row.style }}"` accepts a resolved object or a string (converted to a
  React style object).
- Attribute normalization handles `class`/`for`, `on*` handlers, `style-<pseudo>`
  (e.g. `style-hover`) compiled into a generated CSS class, and a `<helmet>` tag that
  mounts `<title>`/`<meta>`/`<link>` into `<head>`.

## 3. Routing

Hash routing: `#home`, `#schedule`, `#presenters`, `#catalogue`, `#diary` (anything
else falls back to home). A `hashchange` listener sets the view, closes any modal,
**refreshes route-specific data** (re-fetches the diary on `#diary`, the catalogue on
`#catalogue`), updates the document title, and scrolls to top. Each screen is an
`sc-if` block keyed off a boolean in `renderVals()`.

## 4. The persistent player

A `position: fixed; bottom: 0` player bar lives **outside** all the route blocks, so
it is always mounted and never unmounts on navigation; the body reserves space with
`padding-bottom`. Two hidden `<audio>` elements are held on refs, one for the **live
stream** and one for **catalogue track** playback. They are mutually exclusive
(starting one pauses the other) but both persist across route changes, so audio keeps
playing while you browse. Starting the live stream sets its `src` to the station's
stream path **plus a cache-buster** (`?_=<timestamp>`) so it always joins a fresh live
edge rather than resuming a stale buffer; pause clears `src` and calls `load()` to
fully disconnect.

## 5. The live now-playing card

- A poll runs every **5 s** (`fetch` with `cache: 'no-store'`) against a **per-station
  now-playing JSON**; a separate 1 s tick advances the progress bar smoothly between
  polls.
- **The progress bar is truthful**: elapsed is computed from the payload's real
  playback start and duration,
  `elapsed = (now - Date.parse(started_at)) / 1000`, clamped to
  `[0, duration_seconds]`. A continuous dial with no `started_at`/`duration_seconds`
  shows the live title with **no fabricated timing** rather than inventing a clock.
- Fields consumed: `show_id`, `track`, `artist`, `started_at`, `duration_seconds`,
  `type` (a `talk` type swaps the artist line for a host name). "Up next" comes from
  the real today's-schedule feed, so specials and weekend shows appear automatically.
- A station not yet broadcasting renders a truthful "online soon" placeholder, never
  fake now-playing.

## 6. Catalogue and diary views

- **Catalogue**: reads a catalogue JSON grouped into per-show lanes
  (`{ title, artist, genre, duration, src }`). Filter chips (dynamic
  `onClick`/`style`) narrow the list, each row has per-track play on the dedicated
  catalogue `<audio>` element, and a "surprise me" control plays a random track.
- **Diary**: reads a diary JSON of `{ time, mode, title, text }` entries, maps `mode`
  to a colored chip, and renders a timeline (see [Continuity and the diary](continuity.md)).

## 7. Self-hosted runtime, no CDN

React, ReactDOM, and Babel are served **locally from the site's own origin**
(`/assets/...`), loaded with Subresource Integrity hashes, not from a CDN. The whole
app boots from pinned, integrity-checked, offline-capable files with no third-party
runtime dependency.

## 8. Mobile

A single viewport meta, `overflow-x: hidden` guards, and **reflow-only** media
queries. Because the layout is authored with inline styles, the media queries match on
inline-style substrings (e.g. `[style*="repeat(4,"]`) to collapse multi-column grids
to one or two columns and hide secondary catalogue columns on narrow screens, leaving
the desktop layout untouched.

## 9. Wiring to live data

The SPA is a pure static shell; every piece of live content is a JSON file fetched at
runtime with `cache: 'no-store'`: a per-station now-playing JSON (polled every 5 s), a
today's-schedule JSON, a catalogue JSON, and a diary JSON. These are written by the
playout and its publishers (see [the station engine](station-engine.md) for how
now-playing is produced), completely decoupled from the frontend, so the site is just
a renderer of truth the backend already computed.
