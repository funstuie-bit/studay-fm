# The local operations agent

The local agent is an engineering operator. It is not an on-air DJ and it is not
the autonomous station manager the project is working towards.

Production runs the agent through the Pi coding-agent harness against a
self-hosted DeepSeek model on the DGX cluster. Routine audits, planning and maintenance conversations
therefore do not require a metered cloud model. The model choice is less
important than the boundary around it.

## The three modes

| Mode | What it can do | What it cannot do |
|---|---|---|
| **Audit** | Read bounded health, now-playing, schedules, catalogue state, review packages and generation-worker availability | Change the station |
| **Plan** | Turn one exact request into a dry-run design | Execute the plan |
| **Maintain** | Prepare generation batches, build review and naming packages, run tested imports and perform routine repairs after an exact owner instruction | Expand the request, deploy unreviewed source or approve candidate music |

The split is intentional. Asking what is wrong should not carry the same access
as fixing it.

## Audit

Audit reads the typed station view rather than searching the host. It can inspect
computed health, current tracks, schedule state, catalogue state, review package
status and generation-worker availability. Bounded log tails are available only
for named allowlisted services.

The tools remove private paths from ordinary results and keep the context small.
The agent sees the evidence needed for the question, not a tour of the machine.

A greeting starts no station audit. Observation budgets and repetition fuses
stop repeated reads or now-playing polls from becoming an endless tool loop.
The scheduled hourly operator is a separate read-only service; the Discord
assistant is another client of the bounded station broker, not this engineering
agent with a different name.

## Plan

Plan turns an exact owner request into a dry run. It can identify the affected
assets, tested procedure, checks and expected result. It cannot mutate the queue,
media library, live schedule or services.

This mode is useful for work where the proposed scope matters as much as the
command. A plan for five named files remains a plan for those five files. It does
not silently grow when another file appears in the directory.

## Maintain

Maintain can prepare private generation batches, assemble review and naming
packages, run existing tested import procedures and carry out routine repairs.
It needs an exact owner instruction for the operation being performed.

Generated music remains candidate material. Maintain can prepare it and package
it for review, but it cannot listen, assign taste approval or publish it directly
to a live manifest.

Complex architecture, security, provider and recovery changes remain outside
this mode. They require normal source work, review and deployment.

## Command visibility

The client starts with a minimal environment and records guarded actions. Any
shell command requires interactive confirmation before it runs.

The confirmation is there so the owner can see the actual execution. It is not a
second request to approve a decision already stated in the exact instruction.
If the proposed command no longer matches that instruction, it should not run.

## Blocked operations

The local agent is blocked from:

- destructive Git operations;
- credential access;
- privilege escalation;
- package installation or dependency changes;
- unapproved network changes;
- host power actions;
- public pushes;
- unrestricted service control;
- direct approval of music or speech.

Those are not missing features. They are work that should not be smuggled
through a maintenance chat because it happens to be convenient.

## Source and production stay separate

Source changes happen away from the live runtime checkout. They pass the same
tests and protected review workflow as other changes before deployment. The
agent cannot edit the live source tree and call the result done.

Routine station work should be quicker because of the agent. The burden of proof
for risky work should stay exactly where it was.

See [Model authority](model-authority.md),
[Reliability](reliability.md) and [Music generation](music.md).
