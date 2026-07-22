# Studay FM architecture

Studay FM is a five-station radio network built around a small stream origin,
independent playout graphs, bounded generation services, approved-only media,
validated runtime state, and owner-controlled operations.

This is a public reference architecture. Paths, hosts, credentials, private
voice material, deployment recovery details, and the live media library are
intentionally omitted.

## System shape

```text
                                public listeners
                                       |
                             HTTPS at the edge
                                       |
                         outbound-only named tunnel
                                       |
                  +--------------------+--------------------+
                  |                                         |
          approved stream paths                       approved site paths
                  |                                         |
          Icecast on loopback                       Caddy on loopback
                  |                                         |
    +-------------+-------------+                static app + live JSON
    |       |       |       |    |
 flagship  lofi   yacht   jazz  C'est
    ^       ^       ^       ^    ^
    +-------+-------+-------+----+
        speech-safe schedulers
                  |
           Liquidsoap playout
                  |
       approved manifests + atomic state
                  |
      configurable external media root
                  |
        +---------+----------+
        |                    |
   private queue       scheduled producers
        |                    |
 authenticated ACE     bounded Chatterbox

 watchdog -> readiness -> typed read-only query -> owner / bounded LLM summaries
```

## Five stations, two playout styles

The network has exactly five current dials:

| Station | Playout style | Notable programming |
|---|---|---|
| Studay FM | Schedule-driven | Weekday clock, weekend replacements, specials, DJ breaks, continuity |
| StuLoFiDay | Flow | Time-of-day lo-fi pools |
| Yacht Zone | Flow | Yacht rock by day, house by night, sparse host breaks |
| Tokyo Jazz | Flow | Continuous instrumental jazz-hop |
| C'est Magnifistu | Flow | Eclectic music, Airelle continuity, hourly music-and-culture bulletin |

The flagship builds a timestamped schedule from show rules and writes a flat
playlist. The four flow stations use watched, approved manifests with simpler
time or rotation rules. All five produce one continuous, normalized MP3 and
publish to separate Icecast mounts.

Independent graphs matter operationally: one station can restart or lose a
content pool without forcing a network-wide restart.

## Approved-media boundary

Generated media follows a fail-closed lifecycle:

```text
generate -> candidate -> fixed review policy -> technical QA -> approved manifest -> playout
```

An `approved` sidecar alone is insufficient. Eligibility requires all of:

1. a regular audio file beneath an approved media root;
2. a valid, same-stem metadata sidecar;
3. an approval status assigned by the applicable fixed review path;
4. current technical QA tied to the file's device, inode, size, and modification
   identity;
5. any subsystem-specific gate, such as source provenance for news;
6. inclusion in the atomically published manifest consumed by playout.

Flagship music supports explicit owner taste review. Recurring presenter speech,
continuity, flow refreshes, and news can receive approval from narrow
owner-configured validators. In every case the model lacks an approval tool.

The technical gate checks format, sample rate, channel count, duration, silence,
loudness, and peak against a music or spoken-word profile. If a file changes,
its cached QA identity no longer matches and it fails closed until rescanned.

Manifest refresh is serialized under one lock and uses durable temporary-file
replacement. A failed refresh leaves the previous complete manifest in place.
Liquidsoap never observes a partial playlist.

## Runtime state and readiness

The public site and operations tools consume small state contracts rather than
scraping process output. Important artifacts include:

- per-station now-playing;
- today's flagship schedule;
- catalogue and diary feeds;
- watchdog state;
- a readiness document with boolean checks and generation time;
- generation-queue worker state and terminal receipts.

Writers validate payloads before publication, flush the temporary file, replace
the destination atomically, and flush the containing directory. Readers reject
unknown station IDs, invalid timestamps, impossible durations, malformed
readiness checks, and stale evidence.

Liveness and readiness are separate. A service can be alive while the station
is not ready. The readiness endpoint returns failure when watchdog evidence is
red, malformed, missing, or too old.

## Scheduling and truthful now-playing

The flagship scheduler resolves specials before regular shows, walks the clock
using measured asset durations, enforces track and talk rotation rules, and
validates the result before publishing it.

Speech selection is coordinated across categories rather than implemented as
three independent clocks. Each station maintains one deterministic speech
boundary covering presenter links, continuity, and bulletins:

1. at most one speech event can win a scheduling boundary;
2. once any speech event plays, another speech event remains ineligible until
   one complete music asset has played;
3. a colliding or late speech request is deferred or replaced by music;
4. unavailable speech always falls through to music.

The rule prevents combinations such as bulletin-to-hour-marker-to-DJ from
forming a voice block. It also avoids relying on an LLM to negotiate real-time
timing. Speech assets include conservative terminal padding, and playout does
not crossfade the protected voice tail into the next event.

Liquidsoap reports the file that actually started. That event, not a wall-clock
guess, drives now-playing and the progress bar. Flow stations publish the same
contract from their real track-change callbacks. This gives the website and
operator one consistent definition of what is audible.

## Generation queue v2

Expensive jobs are private, typed, and single-flight. A job record contains:

- a validated schema and generated ID;
- job type, label, priority, and optional not-before time;
- an argv array and approved working directory;
- bounded attempts and timeout;
- status, lease identity, heartbeat, and result.

The worker starts one supervisor and one command child at a time. The supervisor
persists long enough to write an atomic exit receipt. If the worker restarts, it
recognizes a live leased child or consumes the receipt; it does not blindly
launch a duplicate generation.

Queue mutation is equivalent to local command authority, so only trusted owner
workflows may enqueue, retry, reprioritize, or remove work. The LLM-facing tools
can read a bounded queue summary but cannot change it.

## Music and voice services

### ACE-Step

The music service is treated as an internal API, not a trusted library call:

- bearer authentication applies to health and generation routes;
- the listener binds to one intended interface, not every interface;
- request, upload, duration, inference, and response sizes are bounded;
- one generation runs at a time and overload returns immediately;
- production API documentation is disabled;
- temporary and output files stay inside approved roots;
- the client allowlists endpoint shape and output extensions, rejects symlinks,
  and writes audio atomically.

### Chatterbox

Chatterbox is used as reference-conditioned speech synthesis. Rendering can run
as a one-shot remote CLI or behind a small internal HTTP service. Either boundary
must provide:

- private reference storage and output containment;
- shell-safe argv or strict JSON parsing;
- authentication for an HTTP boundary;
- bounded text, request, reference, and audio size;
- serialized model use with immediate overload rejection;
- symlink and path-escape rejection;
- a generic, no-reference smoke test for deployment validation.

## News boundary

RSS is untrusted data. Feed responses, redirects, item counts, text fields, and
aggregate input are bounded before an LLM sees them. Candidate records receive
short source IDs; the model must return a structured bulletin and two or three
selected IDs.

The deterministic gate rejects:

- the wrong number of stories;
- unknown or duplicate IDs;
- prohibited hard-news terms;
- missing spoken outlet attribution;
- insufficient linkage to each selected headline;
- missing source URLs;
- invalid script shape or length.

Approved metadata retains source title, outlet, URL, published/fetched times,
and the verification record. Technical QA and approved-manifest publication are
still required. This creates traceability and a correction trail; it does not
make an LLM a fact-checker.

## Operations and model authority

The canonical local operations surface is a typed, read-only CLI. Its commands
return status, health, now-playing, queue summary, lane depth, talk stock, flags,
and bounded tails of allowlisted logs.

The scheduled operator and private ops bot receive the same fixed station-query
tool. Their model endpoint, request size, response size, step count, tool output,
and session duration are bounded. They have no terminal, filesystem, browser,
memory, queue, approval, generation, service-control, or deployment capability.

The project attempted a fully local coordinator before its tool behavior was
reliable enough for safe mutation. Local inference is now separated from the raw
model daemon by an authenticated loopback gateway. The gateway permits a small,
size-bounded generation contract for an allowlisted model and rejects model
management and other administration routes. A hosted provider may be used as a
similarly bounded fallback.

Mutation remains an owner action. A future local coordinator should not gain
mutation until tool reliability, account isolation, credentials, egress, and
command policy have all been reviewed.

## Owner feedback and music iteration

Music recipes are structured prompt pools with explicit versions. Schedulers
select only from the current version for a lane; changing a version resets its
rotation cursor instead of mixing old and new recipe state. A new version
generates candidates only, leaving the approved manifest unchanged until review
and technical QA complete.

Private preview generation copies the exact candidate through a no-symlink,
digest-checked boundary before transcoding. Owner feedback is appended to a
bounded ledger with the SHA-256 identity of the asset being rated. The submitted
digest must still match the expected candidate or current track, so delayed UI
or bot actions cannot attach a rating to a replacement asset. Feedback can guide
the next prompt version but cannot approve a file by itself.

## Public ingress

Icecast and Caddy listen on loopback. A named tunnel connects outbound to the
edge and routes only:

- the five stream mount paths and intended public status resource to Icecast;
- the built public site allowlist to Caddy.

Caddy serves a generated public directory, not the repository. Candidate review,
voice references, private reports, operational state, and documentation are not
copied into that directory. Security headers restrict framing, referrers, browser
permissions, MIME sniffing, cross-origin opener behavior, and script/network
origins.

## Storage and retention

Long-lived generated media belongs in a configurable external media root rather
than beside Git metadata. A compatibility link may be used during a staged
migration, but new consumers should resolve the canonical root and perform
containment against its real path.

Retention is audit-first. The scheduled pass can identify old experiment,
reject, retired, and archive material, but excludes runtime, approved, scheduled,
on-air, bulletin, continuity, and private voice-reference data. Quarantine is an
explicit recoverable owner action. Automatic deletion is intentionally a separate
future policy.

## Supply chain

Core automation, Chatterbox, fallback speech, and any model proxy use isolated
frozen environments. A complete change gate should include:

- lock verification and frozen synchronization;
- tests and critical lint;
- secret scanning;
- OSV review with narrow, expiring exceptions;
- deterministic CycloneDX SBOM verification;
- station-naming checks;
- pinned CI actions.

Runtime services do not resolve or install dependencies while the station is on
air.

CI runs the same frozen dependency, test, lint, naming, secret, vulnerability,
exception-expiry, and deterministic SBOM checks used locally. The runner uses a
dedicated unprivileged identity without production secrets, and protected-branch
status requires the reviewed quality/security job rather than trusting an
unrelated successful workflow.

## Remaining privileged controls

Some boundaries cannot be completed by application code or an LLM. Host
firewall changes, service-account creation, egress restriction, deployment-key
scope, runner installation, legacy-secret retirement, and final storage-link
retirement require an authenticated owner or platform administrator. The
project documents and verifies their intended state, but does not bypass the
operating system's privilege boundary to apply them automatically.

## Sources of truth

| Concern | Authority |
|---|---|
| Station list and mounts | Station registry |
| Flagship clock and presenter mappings | Flagship configuration |
| C'est programming intent | C'est configuration plus generator and playout code |
| Eligible media | Review metadata, current QA cache, and approved manifest together |
| Audible item | Liquidsoap track-change state |
| Overall readiness | Fresh validated watchdog readiness |
| Generation work | Private queue records, lease state, and receipts |
| Voice provenance | Private rights/provenance ledger |
| Deployment | Reviewed revision, frozen environment, and loaded service definition |

For subsystem details, continue through the [deep-dive index](README.md). For the
small public demo, use [SETUP.md](../SETUP.md).
