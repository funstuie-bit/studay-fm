# Deep dive: public access and serving

The whole network is reachable on one public hostname with **no open inbound ports**.
An outbound-only tunnel connector dials the edge, one set of path rules routes the
hostname to a static-site server and to each per-station audio mount, TLS terminates at
the edge, and the static site is served with aggressive edge caching. There is exactly
one law that keeps it all working: **one connector**.

```
listeners ──HTTPS──►  CDN edge  ──(outbound tunnel)──►  connector  ─►  site server (site + data)
                       (TLS)      no inbound ports                  └►  streaming server (mounts)
```

## 1. Outbound-only tunnel

A named tunnel ([Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/) here)
fronts everything. A **connector daemon runs on the origin and dials outbound** to the
edge, which holds the persistent connection. Nothing listens for inbound connections:
**no open ports on the origin, no port-forwarding on the router**, and the origin is
never directly reachable from the internet. The connector runs as a supervised,
auto-restarting service (see [Reliability](reliability.md)).

## 2. Ingress: one hostname, a path per mount

The connector config is an **ordered list of ingress rules**, each matching a hostname
and path and forwarding to a **local plain-HTTP backend**. First match wins; the last
rule is a catch-all. There are two backends on the origin, both on loopback: the
streaming server (serving the per-station audio mounts) and the static-site server
(serving everything else).

```yaml
- hostname: <one-public-host>
  path: ^/(mount-a|mount-b|mount-c)$     # -> streaming backend (per-station mounts)
  service: http://localhost:8000
- hostname: <one-public-host>
  service: http://localhost:8090         # catch-all -> the static site
```

Two things to get right when you add a station:

- **A path per mount.** Each mount name must be whitelisted in the path pattern, or the
  request falls through to the site backend and 404s. Adding a station means: a
  streaming mount, an ingress path entry, and a site card.
- **End-anchor the path regex** (`...)$`). Without the `$`, a site path that merely
  begins with a mount name (for example `/<mount>-something`) would wrongly route to
  the streaming backend and 404. The same rules are duplicated for the apex and `www`
  hostnames, so a new mount goes in both.

After editing ingress, restart the connector and re-check the connector count (below).

## 3. The one-connector law

**Exactly one connector may be registered to the tunnel.** The edge **load-balances
across every connector currently dialed in**. If a second connector is running anywhere
(classically a retired box whose connector service was never stopped, still holding an
old ingress config), then roughly **half of all requests are routed to the stale
origin**. The symptom is intermittent public 404s and stream cutouts that flap, **while
the origin looks perfectly healthy locally** (a local request returns 200).

Tell-tale: an empty-body 404 carrying a `server: cloudflare` header is the connector's
own "no ingress matched" catch-all, not a CDN error page, meaning traffic reached a
connector whose config did not know the hostname.

This was a real outage (a decommissioned box still ran a connector against the same
tunnel with a config that only knew a legacy hostname; about half the traffic matched
no ingress and 404'd). So the **first diagnostic for any public flap** is the connector
count:

```
<tunnel-tool> tunnel info <tunnel-name>    # MUST show exactly one connector
```

If a second appears, stop the rogue connector on the other box and revoke its tunnel
credentials so it cannot re-register. The health watchdog enforces this automatically
(see [Reliability](reliability.md)).

## 4. Static site serving and edge caching

The static site is served by a local web server rooting the site directory, with
compression on and a **cache-tiering** policy so the edge does the heavy lifting:

- **Vendored libraries** (`/assets/*`): immutable, `Cache-Control: public,
  max-age=31536000, immutable`.
- **Slow-rotating media** (images, audio): about a day at the edge.
- **App shell and live data** (the HTML, the framework script, the now-playing and data
  JSON): `Cache-Control: no-cache`, so edits and fresh data go live immediately.

Net effect: the app shell and the now-playing / data JSON are always revalidated (so
changes are instant), while framework bundles and artwork are served from the CDN edge
rather than round-tripping the origin on every request.

## 5. TLS at the edge

TLS terminates at the CDN edge; public clients get HTTPS from the edge, and the
**origin speaks plain HTTP** to the connector over its loopback backends. No
certificates are managed on the origin.

## 6. The principle

Outbound-only, no port-forwarding, the origin never directly exposed. One hostname,
path-routed to a static-site backend and a per-mount streaming backend. Public
reachability depends entirely on **exactly one** connector being registered, so the
connector count is the first thing to check whenever public access misbehaves.
