# Compact Handoff Packet

## Decision

`FREEZE_VERIFIED__JCODE_LIMITED_GO_WITH_REMEDIATIONS`

JCode is qualified only as a possible Layer 4 per-task CLI challenger. The new
seam is disabled, non-executing, and absent from all production call paths. It
is not integrated into Proxy or Terra High.

## Exact scope

- worktree: `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726`
- branch: `codex/source-proxy-jcode-qualification-20260726`
- base/HEAD before edits: `1641ddb1c71e6b364e98aa9aeff4b4719627d926`
- upstream JCode: `2444e7b6bc80d421ae3ee404081bdb41150a1830`
- frozen benchmark: untouched and hash-matched
- Campaign 2: operator acceptance pending
- Campaign 4: remains paused/not started in both recorded meanings

## What exists

- `source_proxy/jcode/adapter.py`: capability/status, envelope validation,
  fixed environment/provider configuration, and command preview only;
- `source_proxy/tests/test_jcode_qualification_adapter.py`: 21 fail-closed tests;
- this 25-artifact qualification packet plus directory index;
- a new 20-task diagnostic manifest, designed and sealed but not run.

Key hashes: adapter
`206b076951cfae22f110a7535f29ffc40045f681ef90986dcb071089667ecdcf`;
focused test
`ce1ba28431af335007f46e23a156bf2c6d14cac389a1d9e95909b987ff3f0fd0`;
diagnostic manifest
`149e2cdc7407f19cb4b0a431edb246affaaaeebabaa0694a22af57dcb6cadbb6`.

## What does not exist

No process runner, API route, orchestrator import, executor registration, model
call, state migration, dependency, binary, service, benchmark run, push, merge,
deployment, Campaign 4 change, or Terra High direct path.

## Evidence

- JCode locked source check passed with no defaults and vendored OpenSSL.
- JCode targeted provider/API tests: 34 passed; safety tests: 9 passed.
- isolated JCode harness reproduced direct file and Bash tool execution.
- Proxy adapter: 30 passed.
- Proxy boundary regression: 165 passed, 2 skipped, 13 subtests passed.
- registered coding pack: 136 passed and 3 unrelated base-HEAD failures.
- benchmark hashes exactly match the freeze receipt.

## Blockers

C2 operator acceptance; external filesystem and network containment; process
supervision; pinned binary/model-parameter/budget enforcement; complete
NDJSON/result mapping; a committed diagnostic fixture;
live exact-model proof; paired A/B evidence; second-run reproduction. Campaign 6
is additionally required before challenger-model C/D lanes.

## Commit state

No local commit was created because the registered coding regression pack was
not fully green. The three failing expectations are in unchanged existing
decision/fixture behavior; repairing them is outside this annex's scope.

## Single next action

The operator reviews the existing Campaign 2 packet and explicitly accepts or
rejects it. No JCode execution is authorized by this handoff.
