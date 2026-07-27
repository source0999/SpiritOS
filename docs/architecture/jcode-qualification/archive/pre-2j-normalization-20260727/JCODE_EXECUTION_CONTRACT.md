# JCode Execution Contract

Schema names reserved by the preview seam:

- request: `coding.jcode-execution-request/v1`
- result: `coding.jcode-execution-result/v1`
- adapter: `jcode-qualification-adapter/v1`

These extend the existing executor/context/evidence concepts; they do not create
a task database, router, approval system, or terminal-state schema.

## Execution request

| Contract field | Current envelope mapping | Owner/rule |
| --- | --- | --- |
| task/correlation/repository id | exact fields | issued by Proxy |
| immutable prompt/hash | file under fresh `JCODE_HOME/input` plus SHA-256 | Proxy writes and validates; raw prompt is not placed on argv |
| base commit/worktree | `base_commit`, `workspace` | disposable Proxy worktree only |
| context packet/hash | file under fresh input root plus SHA-256 | Proxy-selected context only |
| allowed/protected paths | `allowed_files`, `protected_files` | Proxy capability manifest; external enforcement still required |
| allowed/denied tools | explicit tuples | shell, browser, network, memory, swarm, MCP, launch, selfdev denied |
| command/network policy | `no_shell`, `inference_only_external_guard_required` | no runtime widening |
| environment allowlist | `LANG`, `LC_ALL`, `PATH`, `TZ` only | credentials are not inherited |
| model route | fixed profile/model/loopback endpoint | no direct cloud or orchestration route |
| model parameters | bounded max tokens, seed, temperature, top-k/top-p | unknown/out-of-range values block; live application is not implemented |
| budgets | turns, tokens, wall clock, output bytes | Proxy-owned hard ceilings |
| approval capability | always false | JCode cannot approve or apply by authority |
| evidence output | path under fresh evidence root | raw append-only capture in future runtime |
| fresh state | fresh session and JCODE_HOME required | no resume, memory, caches, or transcript reuse |
| feature flags | all optional/irreversible features false | unknown enabled flag blocks |

## Command preview

The seam builds the equivalent of:

```text
jcode --cwd WORKTREE --no-update --no-selfdev --quiet --trace \
  --provider-profile FIXED_PROFILE --model FIXED_MODEL \
  --disable-base-tools --tools READ_AND_EDIT_ALLOWLIST \
  --disabled-tools REQUIRED_DENYLIST run --ndjson HASHED_PACKET_INSTRUCTION
```

This is a preview only. A future runner must write the fixed provider profile
into the fresh JCODE_HOME, enforce the external sandbox, and capture argv/env as
evidence without leaking the prompt or secrets.

## Execution result

The candidate must return or allow Proxy to derive: task/correlation ids,
adapter and JCode versions, provider profile, actual model, start/end,
termination reason, process exit, complete event log/transcript, request and
response metadata, all tool calls/results, attempted/denied commands, files
read/written/created/deleted, claimed outcome, raw stdout/stderr, usage/retries,
timeout/cancellation state, and evidence hashes.

`BLOCKER`: no runner currently applies the validated model parameters or hard
turn/token budget to JCode, and no live result mapper exists. Any missing sequence, terminal
sentinel, raw stream, actual model, or process termination record is
`EVIDENCE_INCOMPLETE`, never success.

## Independent Proxy determination

Regardless of executor output, Proxy determines actual Git diff, protected-path
violations, test results, reviewer outcome, verifier outcome, anti-cheat outcome,
and the single final terminal state. The JCode `claimed_outcome` is evidence only.
