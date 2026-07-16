# Deep dive: the public site

The Studay FM website is a static single-page app backed by validated JSON
published by the station. It has five station selectors, a persistent live
player, truthful now-playing, schedule, presenters, catalogue, and diary views.

```text
validated private state
          |
   public-site builder
          |
 allowlisted static directory
          |
  Caddy on loopback
          |
 outbound tunnel and edge
```

The site is a renderer of station truth, not an operations console.

## 1. Public data boundary

The backend publishes only intended public fields:

- per-station ID, display name, current show, host, item type, track, artist,
  start time, and duration;
- today's flagship show windows;
- approved catalogue entries;
- public diary entries.

Every JSON writer validates its contract before durable atomic replacement.
Malformed or partial output never replaces the last complete feed.

The public build tool copies selected assets and feeds into a dedicated site
directory. It does not expose the repository, private media root, review pages,
queue, readiness internals, logs, prompts, references, or secrets.

## 2. Five-station navigation

The home view lets a listener switch among:

- Studay FM;
- StuLoFiDay;
- Yacht Zone;
- Tokyo Jazz Hop;
- C'est Magnifistu.

Switching a station changes the stream mount and now-playing feed but does not
turn the page into an admin interface. Internal service status and mutation
controls are absent.

## 3. Persistent player

The player bar remains mounted while the listener moves between app views.
Starting a live stream uses a fresh URL so the browser joins the current edge
rather than resuming a stale buffer. Pausing disconnects the audio element
cleanly.

Catalogue preview playback uses a separate audio element and is mutually
exclusive with the live stream. Both remain stable across route changes.

## 4. Truthful now-playing

The app polls the selected station's now-playing feed at a short interval with
cache disabled. A local one-second tick animates progress between server updates.

Progress is calculated from the payload's actual `started_at` and
`duration_seconds`, then clamped to the duration. These fields originate from
Liquidsoap's real track-change event.

If a flow item lacks reliable timing, the site shows the live title without
inventing progress. News, talk, and continuity use their explicit item types so
the presenter label changes correctly.

## 5. Schedule, catalogue, and diary

- **Schedule:** reads today's validated flagship windows, including weekend
  replacements and specials.
- **Catalogue:** renders only approved public catalogue entries and can play
  approved previews where present.
- **Diary:** displays the Signalman's grounded public entries and their modes.

The public catalogue is not a directory listing of the media root. It is a
separately generated allowlist.

## 6. Frontend framework

The current app is a small in-repository template layer over vendored React. It
supports interpolation, conditional blocks, repeated rows, hash routing, dynamic
attributes, and a persistent component state model.

Expression handling uses a restricted resolver rather than arbitrary application
data passed to `eval`. The browser compilation runtime is vendored and
integrity-pinned, so the site does not depend on a third-party CDN at runtime.

The remaining frontend debt is architectural: browser-side compilation and
inline styles require looser CSP allowances than a precompiled bundle would.

## 7. Security headers

The site is served with:

- self-origin Content Security Policy;
- framing denial;
- MIME sniffing protection;
- no-referrer policy;
- restrictive browser permissions;
- cross-origin opener isolation;
- HSTS at the public HTTPS boundary.

Private path patterns return `404`. The documentation tree is not served by
Caddy.

## 8. Privacy

The site currently has no PostHog embed, external font loader, analytics cookie,
or audience-tracking script. It works entirely from first-party static assets,
station JSON, and audio mounts.

Ordinary request and stream metadata may still be handled by the tunnel/CDN,
Caddy, Icecast, and the listener's network provider.

If analytics return, decide the minimum events, retention, disclosure, and
consent requirements before adding code.

## 9. Mobile behavior

The site uses one viewport, overflow guards, responsive grids, and reflow-focused
media queries. The player remains reachable without covering the current item,
and secondary catalogue columns collapse on narrow screens.

## 10. Failure behavior

- Missing one station feed shows an unavailable state for that dial.
- Invalid JSON never replaces the prior complete feed.
- Stale timing does not fabricate progress.
- A missing catalogue or diary feed does not stop live playback.
- Private operational data is not available through a hidden route because it
  is never copied into the public build.

## 11. Demo site

The Docker demo has a simpler one-station page and direct local ports. Its
quickstart remains unchanged. Production hardening can be adopted incrementally:

1. publish validated atomic JSON;
2. separate the public build from the repository;
3. put site and stream origins on loopback;
4. add an outbound tunnel or reviewed reverse proxy;
5. add headers and private-path tests;
6. keep operations out of the browser UI.
