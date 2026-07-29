# Gate 2-J.9 Process Supervision Specification

status: `PGRP_PLUS_CGROUP_SCOPE_SPECIFIED`

schema: `source-proxy.gate-2j-9-process-supervision-specification/v1`
extends: `source_proxy/jcode/supervision.py` (proven process-group SIGTERM->SIGKILL + reap).

## 1. Ownership

The dispatcher owns the full JCode process tree. The JCode process and all its descendants
run inside one systemd transient cgroup scope `jcode-run-<run_id>`, which gives reliable
whole-tree enumeration and cleanup independent of whether children detach from the process group.

## 2. Lifecycle

| Phase | Mechanism |
|---|---|
| Process creation | launch bwrap vector under `systemd-run --scope --unit=jcode-run-<run_id>` with cgroup limits; `start_new_session=True` (retained) |
| stdout/stderr capture | piped to `stdout.log`/`stderr.log` with hashing |
| Event-pipe capture | NDJSON event stream to `events.ndjson` |
| Readiness timeout | operator-sealed (proposed 15 s): wait for `process.started` + `jcode.version_attested` |
| Inactivity timeout | operator-sealed (proposed 60 s): no new event for this interval -> cancel |
| Total timeout | 300 s (sealed): hard cancel + cleanup |
| Graceful cancellation | `SIGTERM` to the process group (retained) |
| Forced termination | `SIGKILL` to the process group after grace (retained) |
| Descendant discovery | enumerate cgroup `cgroup.procs` (not just pgrp), so detached children are found |
| Complete tree termination | `SIGKILL` any remaining `cgroup.procs`, then confirm cgroup empty |
| Exit-code interpretation | map via terminal-mapping spec |
| Cleanup verification | assert `cgroup.procs` empty and run root removed |
| Evidence sealing after abnormal exit | always, even on timeout/cancel/crash |

## 3. Failure-mode tests (Gate 2-J.9C with fake executor; 2-J.9J controlled matrix)

Each MUST be demonstrated:

- JCode hangs (no readiness) -> readiness timeout -> cancel -> cleanup.
- JCode ignores termination -> SIGKILL escalation -> cleanup.
- Child process survives parent exit -> cgroup enumeration kills it.
- Event stream stops -> inactivity timeout -> cancel.
- Event stream malformed -> parser failure -> cleanup + sealed incomplete evidence.
- Output limit exceeded -> truncation + budget violation mapping.
- Model request hangs -> bridge/inactivity timeout -> cancel.
- Tool command hangs -> supervision total/inactivity timeout.
- Cancellation during file write -> cleanup + independent diff still collected (overlay intact).
- Timeout during model streaming -> bridge terminates upstream + cleanup.
- Bridge disappears -> request failure mapping + cleanup.
- Worktree becomes unavailable -> infrastructure failure mapping + cleanup.
- Evidence directory unwritable -> sealed failure mapping + cleanup.

## 4. Reap receipt

Every run emits a supervision receipt: `status` (completed/timed_out/cancelled),
`process_exit_code`, `termination_signal`, `process_group_reaped`, `cgroup_empty`,
`elapsed_seconds`, `descendants_killed`. The existing `run_supervised_jcode_command` return
shape is extended with `cgroup_empty` and `descendants_killed`.
