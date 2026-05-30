# Cartographer Level 11.2 Approval Token Runtime Schema And Validation Dry Run Audit

status: implemented-schema-validation-dry-run-only

Status date: 2026-05-21

## Authority Statement

Level 11.2 defines approval token runtime shape and dry-run validation only.

It does not issue approval tokens, consume approval tokens, grant action authority, grant write authority, grant local execution authority, create an event ledger, write receipts, write evidence, apply docs changes, create branches, create worktrees, commit, push, merge, stash, checkout, clean up, automatically execute actions, automatically promote actions, self-approve, run workflows, orchestrate workers, execute a safe task queue, or enable autonomy.

## Source-of-Truth Inputs

- `docs/cartographer-level-11-1-runtime-authority-baseline-audit.md`
- `docs/cartographer-level-11-approval-token-schema-preview.md`
- `docs/cartographer-level-11-event-ledger-preview-contract.md`
- `docs/cartographer-level-11-to-14-runtime-upgrade-plan.md`
- `docs/cartographer-level-11-to-14-autonomous-operator-roadmap.md`

## Allowed Files Touched

- `source_proxy/cartographer/level_11_approval_token.py`
- `source_proxy/tests/test_cartographer_level_11_approval_token.py`
- `docs/cartographer-level-11-2-approval-token-runtime-schema-and-validation-dry-run-audit.md`

## Runtime Contract

The runtime module provides:

- `CartographerLevel11ApprovalToken`
- `CartographerLevel11ApprovalTokenValidation`
- `build_level_11_approval_token_schema_preview()`
- `validate_level_11_approval_token_dry_run()`

The validator can report whether a token-shaped object is valid for dry-run preview. It always reports action authority, write authority, and local execution authority as false.

## Fail-Closed Validation

Dry-run validation blocks malformed or unsafe token shape when:

- token id is missing.
- run id mismatches.
- action type is unsupported or mismatched.
- target files mismatch.
- allowed files are missing.
- target files are outside allowed files.
- target files intersect forbidden files.
- protected paths are in scope.
- expiration is missing, malformed, or expired.
- max attempts is invalid.
- rollback metadata is missing.
- verification metadata is missing.
- operator approval is missing or self-issued.
- token is already used.
- token is revoked.

## Protected Lanes

- proxy UI makeover.
- `/coding` UI implementation wiring.
- Source Proxy stress testing.
- Codex adapter lane.
- verifier lane.
- test runner lane.

## Why This Does Not Interfere With Parallel Work

This increment does not touch src/**, `/coding` UI paths, proxy UI makeover files, Source Proxy stress docs, Codex adapter files, verifier files, long-running task files, package files, API routes, service builders, Next config, or app routing.

It is a direct module and a direct unit test. It is not wired into `source_proxy/api/cartographer.py` or `source_proxy/cartographer/service.py`.

## Manual Checks

```bash
cd /home/source/SpiritOS

git status --branch --short
git rev-parse HEAD
git diff --stat

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_cartographer_level_11_runtime_baseline.py \
  source_proxy/tests/test_cartographer_level_11_approval_token.py

git diff --check

grep -n "does not issue approval tokens\|does not touch src/\\*\\*\|It is not wired into source_proxy/api/cartographer.py\|Cartographer Level 11.3" \
  docs/cartographer-level-11-2-approval-token-runtime-schema-and-validation-dry-run-audit.md

git status --branch --short
```

## Expected Outcome

- Level 11.1 and Level 11.2 focused tests pass.
- `git diff --check` passes.
- The approval token schema preview reports no action authority, no write authority, no local execution authority, no token issuance, and no token consumption.
- Dry-run validation fails closed for malformed, expired, self-approved, used, revoked, protected-path, and scope-mismatched tokens.
- No API route, service builder, UI, stress, Codex adapter, verifier, package, git, workflow, worker, queue, write, or execution authority is enabled.

## Rollback Notes

Rollback is limited to removing:

- `source_proxy/cartographer/level_11_approval_token.py`
- `source_proxy/tests/test_cartographer_level_11_approval_token.py`
- `docs/cartographer-level-11-2-approval-token-runtime-schema-and-validation-dry-run-audit.md`

No source rollback, API rollback, service rollback, UI rollback, package rollback, verifier rollback, stress-lane rollback, branch cleanup, worktree cleanup, stash cleanup, commit cleanup, push cleanup, or merge cleanup should be needed.

## Stop Conditions

Stop if Level 11.2 requires token issuance, token consumption, API wiring, service wiring, write authority, local execution authority, event ledger persistence, workflow execution, worker orchestration, safe task queue execution, branch/worktree authority, commit/push/merge authority, stash, checkout, cleanup, or protected-lane mutation.

## Next Increment

Cartographer Level 11.3: Event Ledger Runtime Model Dry Run
