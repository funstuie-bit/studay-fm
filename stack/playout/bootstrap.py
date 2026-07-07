#!/usr/bin/env python3
"""Read config.yaml and write the two small files the stack consumes:

  <out>/station.json  - read by the website (name, tagline, stream URL bits)
  <out>/station.liq   - included by radio.liq (station name, mount, crossfade...)

Keeping this here means config.yaml is the single source of truth: the site and
the playout never hardcode the station details.
"""
import json
import sys
from pathlib import Path

import yaml


def liq_string(value: str) -> str:
    """Quote a Python string as a Liquidsoap string literal."""
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    cfg_path = Path(sys.argv[1] if len(sys.argv) > 1 else "/config.yaml")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "/shared")
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load(cfg_path.read_text()) or {}
    st = cfg.get("station", {}) or {}
    talk = cfg.get("talk", {}) or {}

    name = st.get("name", "Demo FM")
    tagline = st.get("tagline", "")
    mount = st.get("mount", "radio.mp3")
    stream_port = int(st.get("stream_port", 8000))
    bitrate = int(st.get("bitrate", 128))
    crossfade = float(st.get("crossfade", 2.0))
    # 0 disables the talk weave; otherwise drop a break every N songs.
    talk_every = int(talk.get("every", 4)) if talk.get("enabled") else 0

    # For the website.
    (out_dir / "station.json").write_text(json.dumps({
        "name": name,
        "tagline": tagline,
        "mount": mount,
        "streamPort": stream_port,
        "bitrate": bitrate,
    }, indent=2))

    # For Liquidsoap (radio.liq does: %include "/shared/station.liq").
    (out_dir / "station.liq").write_text("\n".join([
        "# generated from config.yaml by bootstrap.py, do not edit",
        f"let station_name = {liq_string(name)}",
        f"let station_mount = {liq_string(mount)}",
        f"let station_bitrate = {bitrate}",
        f"let station_crossfade = {crossfade}",
        f"let station_talk_every = {talk_every}",
        "",
    ]))

    print(f"[bootstrap] station='{name}' mount='{mount}' "
          f"bitrate={bitrate} crossfade={crossfade}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
