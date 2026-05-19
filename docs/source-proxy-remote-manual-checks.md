# Source Proxy Remote Manual Checks

Status date: 2026-05-18
Status: active remote authority rules

## Purpose

This document defines how Codex mobile may be used for Source Proxy manual checks without changing SpiritOS authority boundaries.

Codex mobile is a review and control surface. Source Proxy remains the system of record for task scope, allowed files, evidence, approval gates, apply gates, commit gates, and push gates.

For the daily desktop, mobile, SSH, and RustDesk operator flow, use `docs/source-proxy-daily-use-runbook.md`.

## Allowed Through Codex Mobile

Codex mobile may be used to:

- monitor Codex task status
- answer Codex questions about scope or next checks
- review terminal output pasted by Codex
- review diffs summarized by Codex
- review test output
- request read-only checks
- approve Codex-side diagnostic commands when the command is scoped, non-destructive, and does not bypass Source Proxy
- approve Codex-side scoped file edits only when the increment already authorizes those exact files

Examples of allowed mobile-approved diagnostic commands:

```bash
git diff --check
git status --short
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py
npm run typecheck
curl -k -sS --max-time 20 https://localhost:3000/v1/self/status | jq '.'
```

## Forbidden Through Codex Mobile

Codex mobile must not be used to:

- bypass Source Proxy
- approve SpiritOS apply, commit, or push outside their explicit gates
- treat a Codex app approval as SpiritOS approval
- merge or push from the Codex app as the default workflow
- run broad cleanup
- edit secrets, certificates, tokens, credentials, or `.env*` files
- approve provider-layer implementation
- start AionUi bridge work
- start Spirit Cowork Console work
- promote Codex to default coding worker
- enable scheduled provider tasks
- enable autonomous multi-agent writes

## Authority Rules

Remote review does not change the action ladder:

- review does not equal approval
- approval does not equal apply
- apply does not equal commit
- commit does not equal push
- push requires separate explicit approval

Any action that would write files, apply diffs, commit, push, delete files, clean artifacts, change protected paths, or change provider authority must be handled by the active Source Proxy increment and its permission gate.

## Safe Remote Workflow

Use this sequence for mobile work:

1. Codex states the active increment and files in scope.
2. Codex runs only the requested manual-check command or an equivalent read-only diagnostic.
3. Codex reports actual output, expected output, and any mismatch.
4. Britton approves the next increment only after the manual check is understandable.
5. Any apply, commit, or push remains behind its own Source Proxy gate.

## Mobile Manual-Check Packet Format

Use this compact format when Britton is reviewing from a phone.

```text
CHECK:
PURPOSE:
COMMAND:
EXPECTED PASS:
EXPECTED DIRTY:
BLOCKED IF:
PASTE BACK:
NEXT:
ROLLBACK:
```

Field rules:

- `CHECK`: short name for the increment or verification.
- `PURPOSE`: one sentence explaining why the check matters.
- `COMMAND`: one copy-paste shell block or one semicolon-separated mobile-safe command.
- `EXPECTED PASS`: exact success signal, such as `26 passed, 2 warnings` or `diff-check exit=0`.
- `EXPECTED DIRTY`: files expected to appear in `git status --short`, if relevant.
- `BLOCKED IF`: conditions that stop the increment.
- `PASTE BACK`: the smallest output section needed for review.
- `NEXT`: the next increment only if the check passes.
- `ROLLBACK`: targeted restore command for files touched by the increment.

Example:

```text
CHECK: Codex route safety pack
PURPOSE: Confirm Codex route blocks unsafe targets and keeps no-authority readonly mode.
COMMAND: cd /home/source/SpiritOS; PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_codex_cli_adapter.py; git diff --check; echo "diff-check exit=$?"
EXPECTED PASS: pytest passes; diff-check exit=0
EXPECTED DIRTY: source_proxy/tests/test_codex_cli_adapter.py only for this increment
BLOCKED IF: protected target returns 200, apply mode is accepted, or diff check fails
PASTE BACK: pytest summary, blocked route response, diff-check line
NEXT: Increment 2.3
ROLLBACK: git restore source_proxy/tests/test_codex_cli_adapter.py
```

For mobile terminal apps that strip line breaks, prefer semicolon-separated command blocks.

## Receipt Format

When a runner profile supports remote evidence, it should print a compact receipt that can be pasted back into ChatGPT or Codex without the full log.

```text
CHECK:
RESULT:
COMMAND:
HEAD_BEFORE:
HEAD_AFTER:
DIRTY_FILES:
EXPECTED_DIRTY:
BLOCKERS:
NEXT_ACTION:
```

Field rules:

- `CHECK`: profile or increment being verified.
- `RESULT`: `PASS` or `FAIL`.
- `COMMAND`: exact command that produced the receipt.
- `HEAD_BEFORE` and `HEAD_AFTER`: commit hashes observed before and after the check, or `unknown` if unavailable.
- `DIRTY_FILES`: current `git status --short` entries, compacted when long.
- `EXPECTED_DIRTY`: known evidence artifacts such as timestamped soak snapshots.
- `BLOCKERS`: failed checks that stop the next increment.
- `NEXT_ACTION`: the recommended next action after reviewing the receipt.

## SSH Fallback

If the command needs raw terminal access, use SSH/Termius instead of RustDesk when possible.

Use SSH for:

- long command output that is easier to copy from a terminal
- restarting local dev services
- checking ports
- running manual checks that must occur on the host

Do not use SSH fallback to bypass Source Proxy approval gates.

## Debug Path

If wording or workflow implies Codex mobile owns SpiritOS approvals, rewrite it.

If a remote command says it will apply, commit, push, clean, delete, or edit secrets, stop and require a new explicit Source Proxy permission gate.

If mobile output is too large to review, switch to a shorter manual-check packet in the next increment.

## Rollback

This document is documentation only.

Rollback:

```bash
git restore docs/source-proxy-remote-manual-checks.md docs/source-proxy-production-hardening-plan.md
```
