# Running the current Docker demo

This demo is the reusable starter that grew alongside Studay FM. It remains here
temporarily, but it will move into a separate generic AI radio repository. It is
not a copy of the private five-station production deployment.

This guide has two tracks:

1. run the small Docker demo unchanged;
2. grow it into a hardened multi-station system using the production patterns
   documented in this repository.

The live project is working towards full AI management. Current production
authority remains narrower than that destination while reversible operational
control is developed and proved.

## The fast path

### 1. Run the demo

```sh
git clone https://github.com/funstuie-bit/studay-fm
cd studay-fm
cp .env.example .env
# edit the two example passwords
docker compose up --build
```

Open `http://localhost:8080`. The stream is
`http://localhost:8000/radio.mp3`.

The defaults need no GPU, LLM account, or private voice reference. The demo uses
seed tracks, canned presenter lines, and a basic local voice.

### 2. Make the demo yours

Edit `config.yaml`:

- change the `station` name, tagline, mount, and ports;
- edit the example `shows`;
- add rights-cleared tracks to `seed/music/`;
- leave `services.llm.base_url` empty for canned lines, or point it at an
  OpenAI-compatible writing endpoint;
- keep the default speech service, or point `services.tts.url` at a compatible
  reference-conditioned renderer;
- use only reference audio you have the right to use.

If you change `ICECAST_PORT` in `.env`, keep `station.stream_port` in
`config.yaml` aligned with it.

### 3. Run the demo at login or boot

```sh
deploy/install.sh
deploy/install.sh --service
```

The installer builds the Docker stack, performs a local stream check, and can
install the bundled demo service for macOS or Linux. See
[deploy/README.md](deploy/README.md).

This is still the demo deployment. Before exposing it publicly, replace example
passwords and put it behind a reviewed TLS/reverse-proxy or outbound-tunnel
boundary.

## The production target

A full Studay-style network separates real-time streaming from generation and
keeps every mutation behind an owner-controlled workflow.

```text
public listeners
       |
outbound named tunnel
       |
 +-----+------+
 |            |
Icecast      Caddy
loopback     loopback
 |            |
five         public allowlist
playouts     + validated JSON
 |
approved manifests
 |
external media root
 |
private queue + fixed producers
 |
ACE-Step and Chatterbox

watchdog -> readiness -> typed read-only CLI/operator/bot
```

The current Studay FM network has five station roles:

- flagship schedule-driven radio;
- lo-fi flow;
- yacht-rock/day and house/night flow;
- jazz-hop flow;
- eclectic C'est flow with continuity and sourced music-and-culture news.

You can start with one and add the others as independent playout services.

## Before you scale

Decide these boundaries first:

- Which account owns the station, and can it be a non-admin service account?
- Where will private state, scoped credentials, media, logs, and references live?
- Which hosts may reach music and speech APIs?
- Who can review and approve media?
- Which exact commands may enter the private generation queue?
- Which paths are copied to the public site?
- How will you detect stale state, not just dead processes?
- What is the rollback for each component?

Do not solve these questions by giving an LLM a shell and a denylist. A broad
shell remains broad authority even when wrapped in prompt rules.

## Roles and prerequisites

| Role | Runs | Notes |
|---|---|---|
| Stream origin | Icecast, Caddy, Liquidsoap, publishers, watchdog | Keep light and always-on |
| Music node | ACE-Step behind an authenticated bounded service | Single-flight accelerator workload |
| Speech node | Chatterbox CLI or authenticated bounded service | Private references, serialized renders |
| Writing provider | Local or hosted OpenAI-compatible endpoint | Content generation only |
| Operations model | Local or hosted endpoint | Typed read-only station query only |

Typical stream-origin prerequisites:

- [Icecast](https://icecast.org/);
- [Liquidsoap](https://www.liquidsoap.info/);
- [Caddy](https://caddyserver.com/) or an equivalent static origin;
- an outbound connector such as
  [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/);
- a current Python and [uv](https://github.com/astral-sh/uv);
- launchd, systemd, or another per-component supervisor;
- `ffmpeg` and `ffprobe` for media QA.

Use frozen dependency environments. Do not let an on-air service resolve or
install packages at startup.

## Build order

### 1. Define a station registry

Create one canonical registry for station IDs, display names, mounts, public
feeds, and service roles.

IDs should be stable and Studay-named. Validate them anywhere state is written.
Adding a station should require deliberate updates to registry, Icecast,
Liquidsoap, public routing, site UI, and watchdog expectations.

### 2. Choose an external media root

Long-lived generated media should not live beside Git metadata. Configure a
dedicated media root with owner-only write access.

If migrating an existing project:

1. inventory regular files, directories, bytes, and path/size digest;
2. stop every consumer;
3. use an atomic same-filesystem move;
4. verify the inventory;
5. use a temporary compatibility link only if required;
6. update consumers one at a time;
7. keep an owner-only migration record.

All output validation must resolve the canonical root and reject path escapes or
unexpected symlinks.

### 3. Put Icecast and Caddy on loopback

Icecast should accept local source connections and serve the station mounts on
loopback. Caddy should serve a dedicated public build directory on loopback.

The public build is an allowlist. Do not serve:

- repository documentation;
- candidate review or audition pages;
- private state and reports;
- queue records and logs;
- voice references;
- configuration or secrets.

Use an outbound named tunnel to route exact mount paths to Icecast and approved
site paths to Caddy. Keep one intended connector per origin and verify the
connector count.

### 4. Build one continuous playout per station

Each Liquidsoap graph should:

1. consume approved manifests;
2. layer only empty-safe continuity or bulletin fallbacks;
3. normalize with bounded gain;
4. limit peaks;
5. use a safe source so one missing item cannot kill output;
6. emit one continuous MP3 to its mount;
7. publish the actual track-change file.

Run audio processes at interactive priority. Keep generation, model loading,
large scans, and batch transcoding off the audio path.

### 5. Publish contracted state atomically

Define small schemas for:

- per-station now-playing;
- today's schedule;
- catalogue;
- diary;
- watchdog state;
- readiness.

Writers should:

1. validate the complete payload;
2. write a private temporary file in the destination directory;
3. flush it;
4. replace the destination atomically;
5. flush the directory.

Readers should reject unknown IDs, invalid timestamps, impossible durations,
malformed checks, and stale readiness.

### 6. Harden the ACE-Step boundary

Run [ACE-Step](https://github.com/ace-step/ACE-Step) behind a small internal
service that:

- authenticates every route, including health;
- binds to one intended interface;
- disables production API documentation;
- bounds request, upload, duration, inference, response, and audio sizes;
- serializes inference and returns `429` when busy;
- uses private temporary storage;
- does not log prompts, lyrics, or credentials.

The client should allowlist endpoint shape, bound responses, validate audio,
confine outputs to approved roots, reject symlinks, and write atomically.

Add a host firewall or source-host restriction where possible. Private-network
placement alone is not authentication.

### 7. Harden the Chatterbox boundary

Use [Chatterbox](https://github.com/resemble-ai/chatterbox) as a
reference-conditioned renderer, not as an open LAN service.

For a remote CLI:

- use a dedicated restricted account or forced command;
- pass argv safely;
- allowlist reference and output roots;
- serialize renders;
- apply a bounded timeout.

For HTTP:

- fail startup without a strong token;
- authenticate health and synthesis;
- require bounded JSON;
- cap text, reference, output, and audio sizes;
- reject unexpected fields, symlinks, and path escapes;
- return `429` for concurrent synthesis.

Validate deployments with a generic no-reference test first. Keep private
references outside Git and the public site, and maintain a private
rights/provenance ledger.

### 8. Build the script pipeline

Presenter writing should be stateless and configuration-driven:

- character identity and tone;
- segment types and least-used angles;
- allowed and forbidden topics;
- word ranges and handoffs;
- spoken-text-only output;
- deterministic fallback.

Bound the model endpoint, request, response, tokens, timeout, and retries. Give
the scriptwriter no tools.

Accepted text is still a candidate. It must be rendered, reviewed, technically
checked, and published in an approved manifest before playout can select it.

### 9. Add the approved-media gate

An asset is eligible only when all of these agree:

- regular contained audio;
- valid same-stem sidecar;
- an approval status assigned by the configured review policy, such as explicit
  owner taste review for flagship music or fixed validators for scheduled
  speech, flow refreshes, and news;
- current technical QA tied to exact file identity;
- subsystem-specific requirements such as news provenance;
- atomic manifest inclusion.

The technical profiles should check format, sample rate, channels, duration,
internal silence, loudness, and peak. Modifying a file invalidates the cached
pass. Automated approval policies should be narrow and reviewable, and a model
must never be able to assign status through an operations tool.

Publish under one lock. A failed build must preserve the prior manifest.

### 10. Add generation queue v2

Expensive jobs should enter a private typed queue with:

- generated validated ID;
- type, label, priority, and optional not-before time;
- argv array, never `shell=True`;
- approved working directory;
- bounded attempts and timeout;
- running lease identity and heartbeat;
- atomic exit receipt;
- pending, running, done, and failed states.

The worker starts one supervisor and one command child at a time. On restart it
waits for a live leased child or consumes its receipt rather than launching a
duplicate.

Queue mutation is command authority. Keep it local and owner-controlled.

### 11. Add source-attributed news

Treat every feed field as untrusted:

- allowlist feeds;
- require HTTPS after redirects;
- bound response and item counts;
- assign short source IDs;
- require structured model output selecting two or three IDs;
- require spoken outlet attribution;
- retain source title, outlet, URL, and timestamps;
- reject prohibited editorial scope and weak headline linkage.

This gate provides traceability, not automatic fact-checking. Curate sources,
retain a correction process, and prefer no bulletin over an unverified one.

Render once and fan out to active targets. Each target should inject at a track
boundary and withdraw its copy after airing or timeout.

### 12. Add watchdog and readiness

Run a one-shot watchdog on a schedule. Check:

- five expected sources and mounts;
- public and local routing;
- now-playing advancement;
- state freshness and schema validity;
- approved manifests and technical QA;
- queue leases, receipts, cardinality, and dead letters;
- pool depth and newest-item freshness;
- producer heartbeats;
- news supply and failures;
- expected loopback listeners;
- disk, media, and log growth.

Emit alerts only on boolean transitions. Write watchdog state and readiness
atomically. Serve readiness as failed when evidence is missing, invalid, red, or
stale.

### 13. Add typed read-only operations

Expose a local CLI with a fixed command set:

- overall status and health;
- now-playing;
- queue summary;
- music-lane depth;
- talk/continuity stock and freshness;
- owner flags;
- bounded tails of allowlisted logs.

The LLM-facing operator and private ops bot should receive only the same typed
query capability. Do not provide terminal, filesystem, browser, queue, approval,
generation, restart, or deployment tools.

Studay FM originally aimed for a local self-governing coordinator. The local
coordinator and earlier local-model Hermes configuration were not reliable
enough for safe tool use. The current private Hermes gateway uses a bounded
DeepSeek fallback to observe and recommend. Mutation remains owner-controlled.

Revisit local coordination only after:

- reliable typed tool use;
- dedicated non-admin service account;
- scoped credentials and restricted SSH;
- outbound network policy;
- separately reviewed mutation commands and approvals.

### 14. Add retention and supply-chain gates

Keep retention audit-first. Exclude approved, scheduled, on-air, runtime,
bulletin, continuity, and private reference material. Move selected old
experiment, reject, retired, and archive files only through an explicit
recoverable quarantine step. Do not schedule deletion by default.

For dependencies:

- use isolated frozen environments;
- verify locks;
- scan with OSV;
- document narrow expiring exceptions;
- scan the current tree for secrets;
- generate deterministic CycloneDX SBOMs;
- pin CI actions;
- run tests, critical lint, naming checks, and link checks.

## Deployment order

For a new multi-station build:

1. start Icecast and Caddy on loopback;
2. start one playout and verify its local mount;
3. publish validated now-playing;
4. add the tunnel route and verify public access;
5. add the remaining playouts one at a time;
6. deploy approved-media audit and manifests;
7. deploy queue and fixed content producers;
8. deploy ACE-Step and Chatterbox after negative auth/size/path tests and real
   canaries;
9. deploy news;
10. deploy watchdog/readiness;
11. deploy the typed read-only operator and private bot last.

After each step, verify the existing mounts still advance. Do not turn one
component rollout into a blanket restart.

## Customizing the network

- **New presenter:** create a fictional brief, record provenance for any private
  reference, generate candidate scripts, render, review, QA, and publish.
- **New show:** add its clock window, lane compatibility, cadence, presenter, and
  stock checks.
- **New station:** add registry entry, approved manifests, Liquidsoap graph,
  Icecast mount, tunnel route, site card, state publisher, and watchdog checks.
- **Different taste:** edit character briefs and affirmative music recipes, then
  add bounded candidates without wiping live stock.

## Hard-won rules

- Candidate is not approved, and approved is not live until technical QA and
  manifest publication agree.
- Internal APIs require authentication, bounds, and path containment.
- Real-time audio gets priority; heavy work goes elsewhere.
- State must be validated, atomic, and fresh.
- Monitor activity as well as standing totals.
- Queue mutation is local command authority.
- A model can be useful without being the control plane.
- Prefer a missing generated insert over bypassing a failed gate.
- Backfill before retirement; never empty a live lane first.
- Restart the smallest affected component only after evidence.

Continue with [Architecture](docs/ARCHITECTURE.md) and the
[deep-dive index](docs/README.md).

## Historical attribution

Studay FM is the canonical project identity. It began from ideas and code in the
open-source [writ-fm project](https://github.com/keltokhy/writ-fm), credited here
as historical upstream inspiration. The current station registry, approved-media
model, queue, readiness, security boundaries, and owner-controlled operations are
Studay FM architecture.
