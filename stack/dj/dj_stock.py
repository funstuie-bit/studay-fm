#!/usr/bin/env python3
"""Stock the DJ talk pool: write short breaks, voice them, quality-gate them.

This is the demo's version of the real pipeline (write -> render -> QA). For each
show it writes a handful of in-character breaks (via an LLM if configured, else
built-in canned lines), voices each through the TTS service (the bundled espeak,
or your Chatterbox), loudness-levels the result, and drops the approved WAVs into
the shared talk pool that Liquidsoap watches. No LLM and no cloud needed to see
it work; wire in the real services to make it good.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

import yaml

CONFIG = os.environ.get("CONFIG", "/config.yaml")
TALK_DIR = pathlib.Path(os.environ.get("TALK_DIR", "/talk"))

# Built-in fallback lines, used when no LLM is configured. Kept generic and
# station-branded so talk works out of the box.
CANNED = [
    "You're with {host} on {station}. Stay close.",
    "That was a good one. More music in a moment, right here on {station}.",
    "No ads, no requests, no regrets. This is {station}.",
    "{host} here on {show}. Keeping you company.",
    "Every track machine made, not one of them real. That is the whole point. {station}.",
    "The music does not stop, and neither do we. {station}.",
    "This is {show}. Let it play.",
    "Somewhere a machine loved this song a little too much to stop. {station}.",
    "Settle in. {host} with you on {station}.",
    "Back to the music. {station}, all day and all night.",
]


def log(msg):
    print(f"[dj] {msg}", flush=True)


def http_json(url, payload, headers=None, timeout=60):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json",
                                          **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_bytes(url, payload, timeout=120):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def clean_line(s):
    s = s.strip().strip('"').strip("'")
    s = re.sub(r"^\s*\d+[.)]\s*", "", s)   # drop "1." / "2)" numbering
    s = re.sub(r"^[-*]\s*", "", s)          # drop bullet markers
    return s.strip()


def write_lines_llm(show, station, n, llm):
    base = llm.get("base_url", "").rstrip("/")
    url = base + "/chat/completions"
    key = llm.get("api_key") or os.environ.get("LLM_API_KEY", "")
    system = (
        f"You are {show['host']}, presenter of {show['name']} on {station}, a "
        f"24/7 AI radio station. Tone: {show.get('tone', 'warm')}. Write short "
        "spoken radio links to say between songs: one or two sentences, under 30 "
        "words each, in character, no stage directions, no quotation marks, no "
        "song titles. No em dashes."
    )
    user = f"Write {n} different breaks, one per line, numbered 1 to {n}."
    body = {"model": llm.get("model", ""),
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0.9, "max_tokens": 500}
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    data = http_json(url, body, headers=headers)
    content = data["choices"][0]["message"]["content"]
    lines = [clean_line(x) for x in content.splitlines()]
    return [x for x in lines if len(x) > 4][:n]


def write_lines_canned(show, station, n):
    out = []
    for i in range(n):
        tmpl = CANNED[i % len(CANNED)]
        out.append(tmpl.format(host=show["host"], show=show["name"], station=station))
    return out


def voice_params(host):
    h = int(hashlib.md5(host.encode()).hexdigest(), 16)
    return {"pitch": 35 + h % 40, "speed": 140 + (h // 40) % 28}


def tts_render(text, tts_cfg, host):
    url = tts_cfg["url"].rstrip("/") + "/tts"
    vp = voice_params(host)
    payload = {"text": text, "voice_ref": tts_cfg.get("voice_ref", ""),
               "speed": vp["speed"], "pitch": vp["pitch"]}
    return http_bytes(url, payload)


def qa(raw_wav, out_path, title="", artist=""):
    """Loudness-level to a broadcast-ish target, force 44.1k stereo, reject duds.

    Tags the clip so the now-playing display shows who is talking during a break
    (talk clips otherwise have no metadata and would blank the title out).
    """
    proc = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-ar", "44100", "-ac", "2",
         "-metadata", f"title={title}", "-metadata", f"artist={artist}",
         str(out_path)],
        input=raw_wav, capture_output=True,
    )
    if proc.returncode != 0 or not out_path.exists():
        return False
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(out_path)],
        capture_output=True, text=True,
    ).stdout.strip()
    try:
        if float(dur) < 1.0:      # too short to be a real line
            out_path.unlink(missing_ok=True)
            return False
    except ValueError:
        out_path.unlink(missing_ok=True)
        return False
    return True


def wait_for_tts(tts_cfg, tries=30):
    url = tts_cfg["url"].rstrip("/") + "/health"
    for _ in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            time.sleep(1)
    return False


def stock_once(cfg):
    station = cfg["station"]["name"]
    talk = cfg.get("talk", {})
    n = int(talk.get("lines_per_show", 6))
    llm = (cfg.get("services", {}) or {}).get("llm", {}) or {}
    tts_cfg = (cfg.get("services", {}) or {}).get("tts", {}) or {}
    use_llm = bool(llm.get("base_url"))

    TALK_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for show in cfg.get("shows", []):
        try:
            lines = (write_lines_llm(show, station, n, llm) if use_llm
                     else write_lines_canned(show, station, n))
            if not lines:
                lines = write_lines_canned(show, station, n)
        except Exception as e:  # noqa: BLE001
            log(f"LLM failed for {show['id']} ({e}); using canned lines")
            lines = write_lines_canned(show, station, n)

        made = 0
        for i, line in enumerate(lines):
            out = TALK_DIR / f"{show['id']}_{i:02d}.wav"
            try:
                raw = tts_render(line, tts_cfg, show["host"])
                if qa(raw, out, title=show["host"], artist=show.get("name", "")):
                    made += 1
                    log(f"  {show['id']} [{made}] {line[:60]!r}")
            except Exception as e:  # noqa: BLE001
                log(f"  tts/qa failed for {show['id']} line {i}: {e}")
        total += made
        log(f"{show['id']}: {made} breaks stocked ({'LLM' if use_llm else 'canned'})")
    return total


def main():
    cfg = yaml.safe_load(pathlib.Path(CONFIG).read_text()) or {}
    talk = cfg.get("talk", {}) or {}
    if not talk.get("enabled"):
        log("talk disabled in config; nothing to do (music-only)")
        return 0

    tts_cfg = (cfg.get("services", {}) or {}).get("tts", {}) or {}
    if not wait_for_tts(tts_cfg):
        log(f"TTS at {tts_cfg.get('url')} never became healthy; leaving music-only")
        return 0

    refresh = int(talk.get("refresh_minutes", 0))
    while True:
        made = stock_once(cfg)
        log(f"pass complete: {made} breaks total")
        if refresh <= 0:
            return 0
        log(f"sleeping {refresh} min before next stock pass")
        time.sleep(refresh * 60)


if __name__ == "__main__":
    sys.exit(main())
