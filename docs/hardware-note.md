# Hardware note: RTX 3090 and M3 Max

For Studay FM's ACE-Step batches, the NVIDIA RTX 3090 was the better production
machine. It completed generation substantially faster than the M3 Max Apple
backend and a larger share of its output survived the human listening review.

That is the result. It is not a general CUDA versus Apple benchmark.

## What was compared

The comparison came from real Studay FM batch generation while the music library
was being rebuilt. It used the station's ACE-Step setup and evolving prompt
library, then listened to the generated tracks before admitting any of them to
rotation.

Two outcomes mattered:

1. How quickly the machine completed the batch.
2. How many generated tracks were good enough to keep after listening.

The RTX 3090 won on both in this work. Bulk generation moved there as a result.

## What is not recorded

The public project notes do not contain exact elapsed times, batch sizes, model
versions, backend versions, inference settings or acceptance percentages for a
controlled side-by-side test. The prompt library was also being improved during
the wider review period.

Without those records, publishing a percentage or claiming one platform is
universally better would be made-up precision. There is enough evidence to
explain the station's hardware decision. There is not enough to publish a useful
hardware benchmark.

## Why acceptance rate mattered

Technical success was not the final measure. A generated file could decode,
have normal loudness and pass routine checks, then still contain glitches,
incoherent sections or three minutes of something nobody wanted to hear again.

Roughly 2,000 candidates were auditioned across the wider library rebuild. Some
failed technically. Plenty passed every automated check and were still rejected
because they were boring or repetitive. Generation speed only saved time if the
result produced records worth keeping.

## The decision this changed

The RTX 3090 became the bulk music-generation route for this station and this
configuration. The public record makes no broader judgement about other work on
the M3 Max.

If the model, backend or prompt library changes, the comparison should be run
again with recorded versions, fixed recipes, equal batch sizes, exact timings
and the same listening policy. Until then, this remains one practical station
decision, not buying advice.

See [Music generation](music.md) and
[Production flow](production-flow.md).
