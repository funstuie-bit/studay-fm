# Deep dive: public access and serving

Studay FM exposes one public hostname through an outbound-only named tunnel. The
origin services listen on loopback: Icecast serves the five stream mounts, and
Caddy serves an allowlisted public-site build.

```text
listeners -> HTTPS edge -> outbound tunnel connector
                                  |
                    +-------------+-------------+
                    |                           |
             five mount paths             public site paths
                    |                           |
            loopback Icecast              loopback Caddy
```

No router port-forward is required, and the repository is not a web root.

## 1. Loopback origins

Icecast and Caddy bind only to loopback. The tunnel connector reaches them
locally and dials outbound to the edge.

This prevents a service accidentally becoming reachable on every LAN interface.
The watchdog verifies expected listeners and flags unexpected wildcard binds.

The public guide uses the conventional local ports in examples, but a deployment
can choose different loopback ports as long as the station registry, tunnel
rules, health checks, and public build agree.

## 2. Route allowlist

Tunnel ingress is an ordered allowlist:

1. exact stream mount paths route to Icecast;
2. the intended public status resource can route to Icecast if required;
3. all approved site paths route to Caddy;
4. unmatched requests fail closed.

Mount patterns are end-anchored. Without an end anchor, a site path beginning
with a mount name could be misrouted to Icecast.

Adding a station requires coordinated changes to:

- station registry;
- Icecast mount;
- Liquidsoap output;
- tunnel mount allowlist;
- site station card and now-playing feed;
- watchdog expectations.

## 3. One connector per origin

The edge can load-balance among every connector registered to one tunnel. An old
machine left connected with stale ingress rules can therefore create
intermittent public failures while the current origin looks healthy.

Keep one intended connector for this origin and include connector count in
health checks. If a retired connector appears, disable and revoke that connector
through an owner-controlled incident process.

## 4. Public build boundary

Caddy serves a generated allowlist directory, not `docs/`, not the repository
root, and not private state.

The build copies only intended artifacts such as:

- app shell and vendored runtime;
- artwork and other approved static assets;
- validated now-playing, schedule, catalogue, and diary feeds;
- approved public audio samples, if explicitly included.

It must not copy:

- candidate review or audition pages;
- source voice references;
- private reports, logs, prompts, or queue records;
- service configuration or secrets;
- operational runbooks and migration evidence;
- raw generated-media directories.

Known private paths should return `404` even if a link is created accidentally.

## 5. Caching

Use different cache policies by artifact:

- fingerprinted vendored assets: long-lived immutable caching;
- artwork and slow-changing media: moderate caching;
- HTML shell and live JSON: no-cache or revalidation;
- streams: origin/edge behavior appropriate for live audio, not static-object
  caching.

Now-playing requests use no-store semantics so the UI does not resume stale
metadata.

## 6. Security headers

The Caddy origin and edge should provide:

- Content Security Policy restricted to the station origin;
- framing denial;
- MIME sniffing protection;
- `no-referrer`;
- restrictive browser permissions;
- cross-origin opener isolation;
- HSTS on the public HTTPS hostname.

The receiver shell uses first-party HTML, CSS and JavaScript with a
`script-src 'self'` policy. It does not require a browser compiler,
`unsafe-inline` or `unsafe-eval`.

## 7. Privacy

The public site does not need audience analytics to operate. The current design
loads no PostHog script, external font loader, analytics cookie, or similar
tracking code.

Cloudflare, Caddy, Icecast, and network providers may still process ordinary
connection metadata as infrastructure. If analytics are reintroduced, review
disclosure, retention, data minimization, and any applicable consent requirement
before deployment.

Historical analytics data can be deleted separately if it has no continuing
purpose.

## 8. TLS

Public TLS terminates at the edge. The tunnel connects to loopback HTTP origins,
so the origin does not need a publicly trusted certificate or open TLS port.

Keep tunnel credentials scoped. An account-wide credential is more powerful
than a single tunnel credential and should not be left on the origin merely for
convenience.

## 9. Failure diagnosis

Separate checks answer different questions:

- Caddy on loopback: is the site origin alive?
- Icecast on loopback: is the stream origin alive?
- Five source count: are the encoders connected?
- Public site request: is tunnel/edge routing healthy?
- Public mount request: does the mount route work?
- Connector count: is stale-origin split traffic possible?

Do not work around a tunnel problem by rebinding Icecast or Caddy to a wildcard
interface.

## 10. Demo compatibility

The public Docker demo intentionally binds host ports so a local user can open
the player and stream directly. That is a convenience for a development demo,
not the production ingress model.

Before exposing the demo, replace its example passwords and put it behind a
reviewed TLS/reverse-proxy boundary. The production loopback-and-tunnel guidance
does not require changing the demo quickstart.
