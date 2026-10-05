# Five stations. Five little clay worlds.

All five Studay FM stations are live and Public on
[YouTube](https://www.youtube.com/@studayfm), as of 4 October 2026. Each has its
own animated studio or station scene, with the same live programme heard on the
[web receiver](https://studayfm.com). YouTube adds playback delay; the outlets
are not claimed to be sample-synchronised.

| Station | Watch | What you hear |
|---|---|---|
| Studay FM | [Live](https://www.youtube.com/watch?v=wjP1TvmlOG4) | The scheduled flagship cast, music and presenter links |
| StuLoFiDay | [Live](https://www.youtube.com/watch?v=_9Zg0hVV1xg) | Lo-fi dayparts, dusty beats and quiet company |
| Tokyo Jazz | [Live](https://www.youtube.com/watch?v=6N55L0ihO04) | Instrumental jazz-hop and beat-tape |
| Yacht Zone | [Live](https://www.youtube.com/watch?v=ny2XejlQhag) | Yacht rock by day, yacht house by night, with The Captain |
| C'est Magnifistu | [Live](https://www.youtube.com/watch?v=-hJWbzl-90M) | Eclectic music, Airelle and sourced music-and-culture news |

Watch links identify today's broadcasts. They may change if a broadcast ends;
the channel link is the durable starting point.

## Another window, not another station

```text
Existing live station audio + reviewed clay loop -> independent relay -> YouTube
```

The station's existing Icecast audio is the source of truth. Each relay copies
a reviewed 30-second 1080p/30 fps H.264 loop and encodes live audio as stereo
AAC at 128 kbps. It sends the combined signal over certificate-verified RTMPS.
There is no duplicate playlist, browser rendering dependency, OBS requirement
or additional LLM or speech-generation call.

Five separate supervised workers isolate failures. A stopped transport was
recovered in 13 seconds while its broadcast stayed live and the other stations
kept running. That is a recovery test, not a promise that an external platform
cannot fail.

## What continuous operation means

Workers detect stalled audio/video and reconnect with bounded backoff. The
host supervisor restarts workers that exit. On this deployment, restart after
a reboot requires user login and an unlocked secret store. Ingest credentials
remain outside repositories, configuration files and process arguments.

Monitoring uses media progress and transition-only alerts. Progress at the
sender is not proof that a viewer hears sound. The owner confirmed LoFi audio
and picture; all five broadcasts report live status and healthy ingest, but
automated end-to-end listening for every station is not claimed.

If YouTube ends a broadcast, reconnecting its encoder is not enough. Automatic
broadcast replacement is not implemented; control-room intervention is still
needed. Technical relay connections also appear in Icecast listener totals
until audience accounting is updated. YouTube chat is not a station-control
interface.

## Cost and artwork

At roughly 5.1 Mbps per station, five continuous feeds target about 25.6 Mbps
of upload, or 8.3 TB in a 30-day month before overhead. There is no paid relay
service or new metered AI workload, but bandwidth, power and hardware are real
costs. The existing station host runs the relays; no extra model capacity is
needed for video.

The clay loops are already on air. A matching channel picture and mobile-safe
2560 x 1440 banner have also been prepared; applying that channel branding is
a separate owner review step, not a completed upload.

This public repository documents the design. It deliberately does not include
the private encoder deployment, stream keys, account administration helpers or
media-reference material. The Docker demo remains a single-station starter.

See [Current state](current-state.md), [Production flow](production-flow.md)
and [Roadmap](../ROADMAP.md).
