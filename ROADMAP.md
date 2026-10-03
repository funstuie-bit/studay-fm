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

1. Evaluate the new Signalman editorial sessions in bounded show canaries:
   coherent record runs, actual adjacent-track links and ordinary scheduling
   resuming cleanly. Extend authority only after that evidence, not merely
   because the old proposal schema passed.
2. Keep locally hosted writing dependable across presenters, sourced news,
   continuity, diary and operations. Routine work has already moved off metered
   cloud inference; reliability and character variety are now the work.
3. Extend exact pairing to The Captain's independent Yacht flow scheduler.
   His writing is already local; following-track announcements remain a
   separate integration, not a completed feature.
4. Strengthen distinct prompt libraries and station-fit review. Human listening
   remains the gate for new music, including technically valid tracks that are
   repetitive or simply not worth another play.
5. Refine the live clay receiver and its new Big GT programme, retain long-listen
   checks, and make routine AI management useful, observable and reversible.

The [current-state guide](docs/current-state.md) separates shipped work from
experiments. A new skin is not a claim that the whole station is autonomous.

## A separate reusable AI radio project

The one-command Docker demo currently lives here because it helped explain and
test the early system. The next repository will extract a generic, reusable AI
radio station for people who want to build their own.

That future repository will own the starter stack, generic configuration,
deployment guide and reusable automation. This repository will remain the public
home of Studay FM itself. The split should be completed without breaking the
existing demo or copying private production material into either public project.
