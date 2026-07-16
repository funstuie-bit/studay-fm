# Voice references for the demo

The Docker demo works without a reference clip. Its bundled espeak service uses
a basic local voice.

To test a compatible reference-conditioned speech service:

1. Use a short, clean WAV that you have the right to process.
2. Keep the source private and do not commit it.
3. Point `config.yaml` at your renderer:

   ```yaml
   services:
     tts:
       url: "http://your-speech-service:8066"
       voice_ref: "/voices/my_host.wav"
   ```

This directory is mounted read-only into the `dj` service at `/voices`, so the
container-visible reference path begins with `/voices/`.

The bundled espeak service ignores `voice_ref`. A compatible external renderer
implements the contract documented in `stack/tts/server.py`:

```text
POST /tts {text, voice_ref} -> audio/wav
```

That simple demo contract does not provide production authentication or path
policy. Before using a remote speech service for a real station, add the bounded,
authenticated, single-flight, path-confined controls described in
[SETUP.md](../SETUP.md) and [docs/voices.md](../docs/voices.md).

Do not commit a real person's source recording without explicit permission and
redistribution rights.
