# Internal generation boundaries

An internal API is still an API. Putting ACE-Step, Chatterbox or a local model on
the same network does not make every request safe, every path valid or every
client trustworthy.

Studay FM uses separate boundaries for music, speech, text and news. They share
the same basic rules: authenticate the caller, bound the work, contain the
files, reject overload and keep candidate output away from live playout.

## ACE-Step music generation

ACE-Step runs behind an authenticated, single-flight service.

The server:

- requires a private bearer token for health and generation routes;
- binds to one intended interface rather than every interface;
- disables interactive API documentation in production;
- limits request, upload, duration, inference and response sizes;
- permits one active generation and returns `429` when busy;
- keeps temporary files and output under approved roots;
- avoids logging prompts, lyrics or tokens.

The client allowlists the scheme, host, port and endpoint shape. It rejects
embedded credentials, redirects, unexpected response shapes, unsupported audio,
symlink targets and extension mismatches. Accepted output is written atomically
with private permissions.

Single-flight exists twice. The private queue starts one expensive job at a
time, and the API independently rejects concurrent inference. If either layer is
misconfigured, the other one still prevents an accelerator pile-up.

## Chatterbox speech rendering

Chatterbox can run through a one-shot remote command or an internal HTTP
service. Both routes keep references private and serialize model use.

The command route uses a fixed account and entry point, argv-safe arguments,
approved reference and output roots, a bounded timeout and private temporary
files. It does not expose a general remote shell.

The HTTP route refuses to start without a strong private token. Health and
synthesis require authentication. JSON type, body length, text size, reference
size, output size and audio duration are bounded. Unexpected fields, invalid
numeric ranges, path escapes and symlinks fail. Concurrent synthesis returns
`429` instead of building an invisible backlog.

A generic no-reference smoke test proves the renderer and audio path without
moving private character material into deployment checks.

## Text generation

Presenter writing and other text work use an OpenAI-compatible contract. The
local route passes through an authenticated, loopback-only, inference-only
gateway for one allowlisted model.

The gateway forwards the generation route needed by the station. It does not
forward model pull, delete, filesystem or administration routes. Requests,
responses, token counts, timeouts and retries are bounded. The presenter writer
has no tools.

Local and hosted providers can sit behind the same contract. Neither receives
operational authority just because it supplied the text.

## News feeds

RSS is untrusted input. The fetcher allowlists feeds, requires HTTPS after
redirects, limits response bytes and item counts, bounds every text field and
labels the result as source data before the model sees it.

The model selects two or three short source IDs and returns a fixed JSON shape.
Code then checks the IDs, story count, permitted editorial scope, spoken outlet
attribution, source URLs, headline linkage and script length.

The accepted sidecar retains outlet, source title, URL, publish time, fetch time
and verification record. This provides traceability. It does not magically turn
the model into a fact-checker. If the gate fails, no bulletin is produced and
music continues.

## The private queue

Expensive work enters a typed local queue. Each job records a generated ID, job
type, label, priority, optional start time, argv array, approved working
directory, timeout, attempt limit, lease, heartbeat and terminal receipt.

The worker runs one supervisor and one command child. After a restart it checks
the live lease or consumes the exit receipt. It does not blindly launch a second
copy of the same GPU job.

General model tools can read a summary but cannot add, retry, reprioritise or
remove jobs. Queue mutation is command authority, regardless of how friendly the
button looks.

## Shared failure rule

Generation never sits in the real-time audio path. A music, speech, text or news
failure produces no new candidate. It does not bypass review and it does not stop
the current approved material from playing.

See [Music generation](music.md), [Presenter voices](voices.md),
[Newsreader](newsreader.md) and [Production flow](production-flow.md).
