# Deploying for real

This guide applies to the current generic Docker demo. The demo is due to move
to a separate reusable AI radio repository; it is not the private Studay FM
production deployment.

The Docker demo runs the whole station on one box. To run it like the live
network, you split the work across machines and keep it always on. Nothing here
changes the app: it is the same stack, wired to services on other hosts and set
to start at boot.

## The shape

| Role | Runs | Notes |
|---|---|---|
| **Stream host** | this repo's Docker stack (Icecast, Liquidsoap, site, dj, tts) | modest, always-on, the public front door |
| **Music box** | [ACE-Step](https://github.com/ace-step/ACE-Step) as an HTTP service | a GPU; generates fresh tracks |
| **Voice box** | [Chatterbox](https://github.com/resemble-ai/chatterbox) behind the `POST /tts` contract | a GPU; renders reference-conditioned presenter speech |
| **LLM** | any OpenAI-compatible endpoint | content writing only, local or hosted |

You can collapse these onto fewer machines, or keep everything on the stream host
(the demo default) and only move the heavy pieces out when you need them.

## 1. Install the stream host

On the always-on box:

```sh
git clone https://github.com/funstuie-bit/studay-fm
cd studay-fm
deploy/install.sh            # build + run, with a health check
deploy/install.sh --service  # also start at boot (systemd on Linux, launchd on macOS)
```

`install.sh` creates `.env` with random Icecast passwords the first time. Edit
`.env` (ports) and `config.yaml` (station, shows, service URLs) to taste.

## 2. Point at your GPU and LLM boxes

Install ACE-Step, Chatterbox and an LLM from their own projects on their own
machines. Then wire them in `config.yaml`:

```yaml
services:
  llm:
    base_url: "http://your-llm-box:11434/v1"
    model: "llama3.1"
  tts:
    url: "http://your-voice-box:8066"     # a Chatterbox speaking POST /tts
    voice_ref: "/voices/your_host.wav"    # a clip you dropped in voices/
  ace_step: "http://your-music-box:4009"  # music generation
```

The stream host reaches these over your network. The demo's URL fields are a
simple integration contract, not a production security boundary. Before using a
remote music or speech service for a real station, add authentication, request
and response limits, single-flight behavior, path containment, and source-host
network restrictions as described in [SETUP.md](../SETUP.md). Do not expose a
model API directly to the internet.

The bundled `tts` (espeak) service is only the fallback. Once
`services.tts.url` points at a compatible renderer, that service voices the
breaks. Use only rights-cleared private references.

## 3. Always-on

`deploy/install.sh --service` installs one of:

- **Linux:** a systemd unit (`deploy/studayfm-demo.service`) that runs the stack
  and restarts it on failure. Manage with `sudo systemctl status studayfm-demo`.
- **macOS:** a launchd agent (`deploy/com.studayfm.demo.plist`). Docker Desktop or
  OrbStack must be set to start at login for this to survive a reboot.

Put the site and the Icecast mounts behind a reverse proxy or a
[Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
so you expose one hostname with no open inbound ports. See the top-level
[SETUP.md](../SETUP.md) for the wider architecture and the hard-won reliability
lessons.
