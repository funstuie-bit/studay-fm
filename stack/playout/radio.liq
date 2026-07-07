#!/usr/bin/env liquidsoap
# Studay FM demo playout.
#
# Reads the seed library and publishes one continuous, crossfaded, loudness-
# levelled MP3 to Icecast. Station details come from /shared/station.liq, which
# bootstrap.py generates from config.yaml, so nothing here is hardcoded.

%include "/shared/station.liq"

log.level.set(3)
# The container runs as root (so it can apt-install python for the config step),
# and Liquidsoap refuses root by default. This is a single-purpose container, so
# allow it.
settings.init.allow_root := true

# The music library, shuffled, reloaded periodically so tracks you add show up.
music = playlist(mode="randomize", reload=1800, reload_mode="seconds", "/music")

# Smooth transitions and even loudness between tracks.
music = crossfade(duration=station_crossfade, music)
music = normalize(music)

# Weave in hosted DJ breaks the dj service stocks into /talk (watched for new
# clips). Every N songs, drop in one break. If talk is disabled or the pool is
# empty, this is just the music flow. A short blank covers any moment the pool is
# briefly empty during a restock, so the stream never stalls.
talk_count = list.length(file.ls("/talk", absolute=true))
radio =
  if station_talk_every > 0 and talk_count > 0 then
    talk = playlist(mode="randomize", reload_mode="watch", "/talk")
    talk = fallback(track_sensitive=true, [talk, blank(duration=0.3)])
    rotate(weights=[station_talk_every, 1], [music, talk])
  else
    music
  end

# Never let the stream fall silent: if everything is empty, play safe silence.
radio = mksafe(radio)

# Publish the current track to /shared/now.json for the website to poll.
def on_meta(m) =
  payload = json.stringify({
    title  = m["title"],
    artist = m["artist"],
    show   = station_name
  })
  file.write(data=payload, "/shared/now.json")
end
radio.on_metadata(synchronous=true, on_meta)

# The public stream.
output.icecast(
  %mp3(bitrate=station_bitrate),
  host=environment.get("ICECAST_HOST"),
  port=8000,
  password=environment.get("ICECAST_SOURCE_PASSWORD"),
  mount=station_mount,
  name=station_name,
  description="A Studay FM demo station",
  genre="AI generated",
  radio)
