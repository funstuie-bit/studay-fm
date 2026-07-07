#!/usr/bin/env python3
"""A tiny, dependency-free TTS server for the demo, backed by espeak-ng.

It defines the contract the `dj` service speaks to, so you can replace it with a
real voice-cloning server (Chatterbox, etc.) without touching anything else:

    POST /tts   {"text": "...", "voice_ref": "...", "voice": "en",
                 "speed": 150, "pitch": 50}
                -> 200 audio/wav   (the spoken line)
    GET  /health -> 200 "ok"

The espeak backend ignores `voice_ref` (it has no cloning); a Chatterbox-backed
server would use it as the reference clip. Everything else about the pipeline
stays the same.
"""
import json
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 5002


def synth(text, voice="en", speed=150, pitch=50):
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        subprocess.run(
            ["espeak-ng", "-v", str(voice), "-s", str(int(speed)),
             "-p", str(int(pitch)), "-w", f.name, text],
            check=True, capture_output=True,
        )
        f.seek(0)
        return f.read()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quieter logs
        pass

    def do_GET(self):
        if self.path.rstrip("/") == "/health":
            self._send(200, b"ok", "text/plain")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path.rstrip("/") != "/tts":
            return self._send(404, b"not found", "text/plain")
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
            text = (body.get("text") or "").strip()
            if not text:
                return self._send(400, b"missing text", "text/plain")
            wav = synth(text, body.get("voice", "en"),
                        body.get("speed", 150), body.get("pitch", 50))
            self._send(200, wav, "audio/wav")
        except subprocess.CalledProcessError as e:
            self._send(500, b"tts failed: " + (e.stderr or b""), "text/plain")
        except Exception as e:  # noqa: BLE001
            self._send(500, str(e).encode(), "text/plain")

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"[tts] espeak-ng server on :{PORT}")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
