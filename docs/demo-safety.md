# Running the Docker demo safely

The Docker demo is safe enough for local development after the two example
passwords are changed. That does not make it safe to put directly on the
internet.

It is a small one-station starter with seed music, simple DJ breaks, a basic
local voice and a now-playing page. It is not a copy of the private five-station
production system.

## Before the first start

Copy the environment file and replace both Icecast passwords:

```sh
cp .env.example .env
```

Set private values for:

```text
ICECAST_SOURCE_PASSWORD
ICECAST_ADMIN_PASSWORD
```

The example values are `change-me-source` and `change-me-admin`. Do not leave
them in place and do not commit `.env`. The file is already ignored by Git, but
it still helps to check what is staged before a push.

The default host ports are:

| Service | Port |
|---|---:|
| Icecast stream | `8000` |
| Web receiver | `8080` |

If either port is already used, change `ICECAST_PORT` or `WEB_PORT` in `.env`.
When `ICECAST_PORT` changes, update `station.stream_port` in `config.yaml` to the
same value. A mismatch gives the browser the wrong stream address even when the
container itself is healthy.

## Start it locally

```sh
docker compose up --build
```

Open `http://localhost:8080`. The raw stream is
`http://localhost:8000/radio.mp3`.

The first build takes longer because Docker needs to create the images. Later
starts reuse them. The default demo requires no GPU, LLM account or private
voice reference.

## Music

The seed library exists so the stack works immediately. Replace or extend it
only with audio you have the right to use and broadcast.

Adding a file to `seed/music/` is fine for the demo. It is not the production
approval system. The live Studay FM network uses separate candidate review,
technical QA and approved manifests.

## Text generation

Leaving `services.llm.base_url` empty uses the built-in canned presenter lines.
This is the simplest and safest default.

If an OpenAI-compatible endpoint is added, keep its API key in `.env` through
`LLM_API_KEY` or another private configuration path. Do not commit it. Bound the
endpoint and keep a deterministic fallback so an unavailable model does not stop
the station.

The demo URL field is an integration hook, not a hardened production boundary.
Do not expose a raw model API to the internet because the sample configuration
can reach it.

## Speech rendering

The bundled speech service uses a basic local voice. It sounds basic because it
is basic. The useful part is that the demo runs without a private reference or
external account.

`services.tts.url` can point to a compatible renderer using the `POST /tts`
contract. If reference-conditioned speech is enabled, use only a rights-cleared
private reference and keep it outside Git and the public site.

A real remote speech service needs authentication, request and response limits,
serialised rendering, path containment, symlink rejection and source-host
network restrictions. A URL on the same LAN is not a security model.

## Music generation

The demo plays the seed library and does not call ACE-Step by default.
`services.ace_step` is an optional integration field.

A remote ACE-Step service needs authentication, bounded requests and output,
single-flight generation, approved output roots and network restriction. Do not
connect the public demo straight to an unrestricted GPU service.

## Public exposure

For local use, direct host ports are convenient. Before public exposure:

1. Replace the example passwords.
2. Put the site and stream behind a reviewed TLS reverse proxy or outbound
   tunnel.
3. Expose only the intended site paths and stream mount.
4. Keep model, speech and music-generation services private.
5. Confirm the repository, `.env`, private references and raw media directories
   are not web roots.
6. Test the public hostname separately from the local containers.

The production Studay FM pattern binds Icecast and Caddy to loopback and reaches
them through an outbound named tunnel. The demo does not reproduce that boundary
for you.

## Running at login or boot

The bundled installer can build the stack, run a local stream check and install
the demo service:

```sh
deploy/install.sh
deploy/install.sh --service
```

On Linux, the service uses systemd. On macOS, it uses a launchd agent. Docker
Desktop or OrbStack must also start at login on macOS or the launchd job has
nothing to run after a reboot.

Always-on does not mean production-ready. Check that the site opens, the stream
plays, metadata advances and the service returns after a real reboot before
calling it finished.

## Keep the demo and production claims separate

The demo proves the basic stack: Icecast, Liquidsoap, hosted breaks, speech and a
web player. It does not include the production network's five independent
playouts, approval policy, private queue, readiness contracts, capability broker
or public ingress design.

That distinction matters. A one-command demo is useful. Pretending it carries
all of the live station's safeguards would be bullshit.

Continue with [the full setup guide](../SETUP.md),
[demo deployment](../deploy/README.md) and
[public access](serving.md).
