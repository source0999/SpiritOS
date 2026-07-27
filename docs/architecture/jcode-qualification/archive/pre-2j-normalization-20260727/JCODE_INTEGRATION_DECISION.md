# JCode Integration Decision

Decision: `LIMITED_GO_WITH_REMEDIATIONS` for **Option A, a disabled per-task
external CLI qualification adapter**. Production adoption and live diagnostic
execution are not approved.

## Decision logic

1. The Proxy already has one durable orchestrator, approval service, model
   router, reviewer, verifier, anti-cheat, and evidence finalizer.
2. JCode has a reproducible headless CLI, explicit tool filters, provider
   profiles, and NDJSON output suitable for a replaceable Layer 4 runtime.
3. JCode's normal tool path is not universally permission-classified, and its
   project instructions, optional state, network surfaces, and streaming risks
   do not satisfy Proxy trust requirements as-is.
4. A process-per-task design preserves rollback and allows an identical paired
   comparison without importing JCode authority or a second database.
5. No JCode task can run until external containment and evidence mapping exist.

## Non-recursion invariant

JCode may receive only a fixed, loopback, inference-only endpoint. The adapter
rejects non-loopback endpoints. The endpoint must not route to `/coding`, task
creation, approval, or any orchestration API. A request path that re-enters the
launcher is a hard configuration failure.

## Current implementation claim

`VERIFIED FACT`: `source_proxy/jcode/adapter.py` adds a fail-closed capability,
envelope, environment, provider-profile, and command-preview seam. It does not
spawn JCode and has no import or call site in the orchestrator or API.

Therefore this change is **not an integration claim**. It is a reviewable
contract boundary and configuration-blocked candidate.

## Remediations required before one live diagnostic

- explicit C2 operator acceptance and separate Campaign 2-J authorization;
- OS-enforced writable path containment matching the allowed-file manifest;
- default-deny egress with only the exact loopback inference endpoint;
- supervised process group with timeout/cancel/kill/reap reconciliation;
- pinned built binary hash and exact provider/model identity evidence;
- hard application of the declared model parameters and turn/token budgets;
- strict NDJSON framing, sequence/completeness checks, raw byte capture, and
  execution-result mapping;
- independent Proxy diff, tests, reviewer, verifier, anti-cheat, and finalizer;
- a fresh worktree, HOME, JCODE_HOME, runtime directory, and task id per run;
- second clean dry run of adapter containment canaries before model use.

Until then `JCODE_EXECUTOR_ENABLED` remains false and even setting it true only
changes the preview reason; `would_run_task` and `can_run_live_task` remain false.
