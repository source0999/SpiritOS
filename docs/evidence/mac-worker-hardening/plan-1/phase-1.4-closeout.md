# Phase 1.4 Closeout

Date: 2026-05-28

## Increments completed

- Increment 1.4.1: `run_safe_check` ran `git status --branch --short --untracked-files=normal`; evidence in `increment-1.4.1-run-safe-check-git-status.md`.
- Increment 1.4.2: `run_safe_check` ran `git diff --check`; evidence in `increment-1.4.2-run-safe-check-diff-check.md`.
- Increment 1.4.3: Safe command allowlist hardened; evidence in `increment-1.4.3-safe-command-allowlist.md`.

## Safe git checks

Confirmed working through `/api/coding/mac-worker`:

- `git status --branch --short --untracked-files=normal`
- `git diff --check`

The `git status` output honestly reports:

```text
## main...origin/main
?? scripts/mac-worker/
```

This confirms the Mac path is a real checkout with a documented untracked worker overlay.

## Unsafe command blocking

Confirmed blocked through `/api/coding/mac-worker`:

```text
rm -rf .
```

Blocked result shape includes:

- `success:false`
- `error:"check_command is not allowlisted: rm -rf ."`
- `reason_code:"safe_check_command_not_allowlisted"`
- `blocked_command:"rm -rf ."`
- `recommended_checks`

## Blocked state honesty

The blocked command is not falsely green. The API returns `ok:false`, `success:false`, and the blocked command name.

Known follow-up for Phase 1.6: the registry currently marks `online:false` and `worker_available:false` after a blocked job because those fields are derived from last job success. This is honest about the last result but not precise about node reachability.

## Forbidden action review

No forbidden action occurred.

- No autonomous Mac write authority was added.
- No hidden workers were started.
- No daemon was created.
- No launch agent was created.
- No persistent process was started.
- No mutating check command was executed.
- No secrets were touched.
- Cartographer, Scout production workflows, production routing, model routing, and provider authority were not mutated.

## Checks

Focused checks run in this phase:

- `npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts --reporter=dot`: passed.
- `python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py`: passed.
- `node --check scripts/mac-worker/spirit-mac-worker.mjs`: passed.
- API safe Git status: passed.
- API safe Git diff check: passed.
- API unsafe command block: passed.

## GO / NO-GO

GO to Phase 1.5.

Next authorized increment: Increment 1.5.1, create Mac job acceptance matrix.
