# Studay FM now

Last verified: 4 October 2026. Receiver captures remain dated 2 October.

This is the public project record, not a deployment mirror. The Docker demo is
still the original single-station starter; the live five-station network has
its own production system.

## On air

- Five shared live streams, a weekday clock, weekend crew and specialist shows.
- Five public, continuously supervised [YouTube simulcasts](youtube-simulcast.md),
  carrying the same station audio with separate animated clay scenes.
- Seventeen programme/flow hosts, plus The Signalman as continuity keeper:
  eighteen fictional voices in the public roster.
- A claymation receiver with responsive station art, a vinyl player, clay motion,
  a persistent mini player, saved favourites, sharing and an installable shell.
- Big GT's **The Grove Pocket**, Thursday and Friday **00:00-02:00 Pacific**.
  These are the mornings following Wednesday and Thursday nights.
- Track-bound flagship presenter links: the introduced record is the exact
  eligible asset paired with the speech, not a randomly chosen next song.
- A half-hourly Signalman diary: a factual station duty book with original
  deadpan asides and the odd wandering thought. Past entries stay intact.
- Self-hosted routine writing, speech and music generation, kept away from the
  real-time broadcast path.

## Which machine does which job?

| Component | Current role |
|---|---|
| Small Mac station host | Schedules, five Liquidsoap playouts, Icecast, public-state publication, receiver serving and five independently supervised YouTube relays |
| RTX 3090 music worker | ACE-Step 1.5 XL Turbo batches with the 1.7B planner; reviewed prompts and separate listening packages |
| Local writing host | Cydonia presenter prose, Gemma sourced news and short continuity; The Captain has a local writing route too |
| Two-node DGX Spark cluster | Self-hosted DeepSeek for editorial selection, diary, the read-only operator, Discord assistant and local operations agent |
| Separate speech worker | Reference-conditioned Chatterbox voices with serialized rendering and audio QA |

These are interchangeable roles, not a requirement to copy the same hardware.
Clients use configured, bounded interfaces. Addresses, credentials, reference
audio, private media and recovery records are deliberately absent here.

There is no routine paid text-generation dependency in this setup. Hardware,
electricity and any separately chosen commercial music generation still cost
money; self-hosted does not mean free. A cloud fallback can be explicitly
configured, but is not the normal station writing route.

## Creative freedom, real boundaries

The new Signalman editorial sessions select ordered runs from an exact
owner-reviewed shortlist, retain a little show memory and brief the assigned
presenter about the adjacent records. Speech cadence belongs to show policy,
not a model deciding never to speak. Private listening editions have been
accepted and a narrow, expiring Crate canary path is implemented. This is not
network-wide autonomous direction.

The Captain's Yacht continuity remains generic until its separate flow engine
can guarantee the same adjacent-track binding. Neither programme selection nor
good prose can approve unreviewed music.

Generation packages, listening reviews and production media have separate
roles. Exact hashes and import receipts tie an owner decision to the actual
record; filenames are not approval. Technical checks cannot establish musical
quality, so listening remains part of the process.

## What this refresh does not claim

It does not ship the private production deployment, guarantee that every
generated track sounds good, promise unattended recovery from every outage or
turn a short show experiment into a fully autonomous network. The retired
general generation-queue service is not a live prerequisite; current batches
use serialized, checkpointed workers.

YouTube transport reconnects are implemented; automatic replacement of a broadcast
ended by YouTube is not. User services recover after login and an unlocked secret
store, not before disk unlock. The new channel avatar and banner are prepared, but
have not been applied to the channel. Simulcast listener-count subtraction is also
still outstanding.

See [Programme direction](programme-direction.md), [Music](music.md),
[Receiver](receiver-guide.md) and [Roadmap](../ROADMAP.md).
