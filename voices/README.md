# Voices

Drop a reference clip here to give a host a real, cloned voice (instead of the
built-in robotic espeak).

1. Add a short, clean recording, a few seconds of one person speaking is enough,
   for example `my_host.wav`.
2. Point a real voice-cloning TTS at it. In `config.yaml`:

   ```yaml
   services:
     tts:
       url: "http://your-chatterbox-host:8066"   # a Chatterbox (or compatible) server
       voice_ref: "/voices/my_host.wav"          # this file, as the dj sees it
   ```

This folder is mounted into the `dj` service read-only at `/voices`, so
`voice_ref` paths start with `/voices/`.

The bundled espeak TTS ignores `voice_ref` (it cannot clone). The cloning happens
in whatever server you point `services.tts.url` at. The contract that server must
speak is documented at the top of `stack/tts/server.py`:
`POST /tts {text, voice_ref} -> audio/wav`.

Do not commit real people's voices you do not have the rights to use.
