# Studay FM direction

Studay FM started as a hobby. It exists to make strange, entertaining radio and
to explore how far a genuinely AI-managed station can go. It should remain fun
to listen to and fun to build.

## The goal

The destination is a fully autonomous radio network where AI can manage routine
programming, music generation, presenter production, continuity, monitoring and
recovery inside clear owner-defined limits. The owner sets the creative direction
and keeps an emergency stop, but should not have to operate the station by hand.

The current system is highly automated rather than fully autonomous. Sensitive
or irreversible actions stay owner-controlled until the system can make and
explain those decisions reliably, prove the result, and roll back safely. This is
staging towards autonomy, not a decision to abandon it.

## What work belongs

Work should do at least one of these things:

- make the station sound better;
- reduce routine owner intervention;
- make AI decisions more dependable and reviewable;
- keep the five streams reliably on air; or
- make the project more enjoyable as a hobby.

Complexity that does none of these should be deferred or removed.

## Near-term priorities

1. Improve the newly live track-aware presenter writing: add more variety, refine
   difficult character briefs, and extend exact pairing to The Captain on Yacht
   Zone.
2. Move suitable routine writing from hosted models to reviewed local models,
   starting with sourced news behind the same deterministic editorial gate.
3. Redesign the programme-director experiment around show-aware, audible choices;
   its existing shadow remains review-only and has not earned live control.
4. Improve station-fit admission and supplier evaluation for generated music so
   new batches strengthen each dial's identity before entering rotation.
5. Continue long-listen acceptance of the public receiver and expand the AI
   manager only through observable capabilities with receipts, rollback and an
   owner emergency stop.

## A separate reusable AI radio project

The one-command Docker demo currently lives here because it helped explain and
test the early system. The next repository will extract a generic, reusable AI
radio station for people who want to build their own.

That future repository will own the starter stack, generic configuration,
deployment guide and reusable automation. This repository will remain the public
home of Studay FM itself. The split should be completed without breaking the
existing demo or copying private production material into either public project.
