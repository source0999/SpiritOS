# Scout v0.5 Phase 2.2 Evidence Snapshot Review

status: implemented/manual-triggered

Status date: 2026-05-20

This document records the Phase 2.2 evidence snapshot review increment. It adds a manual runner profile for reviewable Scout Level 2 evidence. It does not register a scheduler, add a worker, add cron, change services, run search, extract candidates, approve sources, reject sources, block sources, activate sources, promote packets, write proxy memory, write coding context, apply code, commit, or push.

## Purpose

Phase 2.2 gives the operator one explicit command that captures reviewable evidence for the Level 2 scheduled read-only watch design. The command is manual-triggered only. It proves the future watch payload is useful before any scheduled execution exists.

## Manual Profile

Profile:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-level-2-evidence-snapshot --json
```

Allowed write:

- one timestamped JSON file under `scout/soak-logs/scout-level-2-evidence-*.json`

Allowed reads:

- `/health`
- `/v1/scout/overview?limit=5`
- `/v1/scout/sources`
- `/v1/scout/source-candidates?limit=200`
- `/v1/scout/discovery-jobs?limit=50`
- `/v1/scout/packets/explorer?limit=100`

## Safety Boundary

The profile must not call mutation endpoints. It must not:

- run discovery search
- extract candidates
- approve sources
- reject sources
- block sources
- activate sources
- promote packets
- write proxy memory
- write coding context
- apply code
- commit
- push
- register a worker
- enable a scheduler
- change service configuration

## Acceptance Criteria

The profile passes only when:

- all read endpoints are available
- rank fields are visible
- source count is stable
- candidate counts are stable
- promotion queue remains stable
- discovery remains `manual_controlled`
- `automatic_execution` remains `false`
- `worker_registered` remains `false`
- backlog remains zero
- the only file change from the profile is the evidence snapshot
- git head does not change

## Review Notes

This is not scheduled watch activation. It is a manual evidence capture path. A later phase may use this payload shape for disabled-by-default scheduling only after another operator gate.

## Rollback

```bash
git restore docs/scout-v0-5-evidence-snapshot-review.md source_proxy/testing/runner.py
rm scout/soak-logs/scout-level-2-evidence-*.json
```

If the doc is untracked, use:

```bash
rm docs/scout-v0-5-evidence-snapshot-review.md
git restore source_proxy/testing/runner.py
rm scout/soak-logs/scout-level-2-evidence-*.json
```

## Next Permission Gate

Operator approval is required before Phase 3.1 or any implementation of scheduled execution. The recommended next increment is to keep Level 2 manual-triggered and review the evidence payload, or explicitly design a disabled-by-default scheduler guard without registering it.
