# Cartographer Daily Driver Autonomy Roadmap Plan 2 Phase 1 Closeout

## Phase

Plan 2 Phase 1: Approval Token Runtime

## Result

Completed.

This phase implements the first inert approval token runtime foundation for Cartographer. It validates explicit approval token payloads, rejects missing or malformed fields, requires an explicit approval actor, rejects self-approval, checks requested actor and scope, enforces issue and expiration timing, and returns clear accepted or rejected validation results with reasons.

The runtime remains validation-only. It does not grant autonomy, safe writes, workflow execution, queue execution, command execution, commit, push, branch, worktree, stash, clean, reset, or checkout authority.

## Increments Completed

- Increment 2.1: Inspected Cartographer API, live-state, and level 11 approval token patterns as reference only. Added `source_proxy/cartographer/approval_token_runtime.py` with pure validation.
- Increment 2.2: Added `source_proxy/tests/test_cartographer_approval_token_runtime.py` for accepted validation, fail-closed missing fields, malformed payloads, wrong actor, self-approval rejection, scope mismatch, stale and expired tokens, and no mutation or execution surface.
- Increment 2.3: Added validation-only backend API wiring at `/v1/cartographer/approval-token/validate` and a Next proxy route at the same path. The route returns validation JSON only.
- Increment 2.4: Wired `/map` to display approval token validation-only status, self-approval blocked state, blocked mutation and command authority, and safe next action. No action execution buttons were added.
- Increment 2.5: Wrote this closeout.

## Files Changed

- `source_proxy/cartographer/approval_token_runtime.py`
- `source_proxy/tests/test_cartographer_approval_token_runtime.py`
- `source_proxy/api/cartographer.py`
- `src/app/v1/cartographer/approval-token/validate/route.ts`
- `src/app/map/page.tsx`
- `src/app/map/cartographer-approval-token.ts`
- `docs/cartographer-daily-driver-autonomy-plan-2-phase-1-approval-token-runtime-closeout.md`

## Checks Run

- `git status --branch --short`
  - Completed before edits. Worktree was already dirty with many tracked and untracked files, including forbidden lanes.
- `git diff --check`
  - Passed before edits.
- `PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_live_state.py`
  - Passed: 10 passed.
- `PYTHONPATH=. .venv/bin/python - <<'PY' ...`
  - Confirmed `/v1/cartographer/live-state` is registered.
- `PYTHONPATH=. .venv/bin/python - <<'PY' ... build_approval_token_runtime_status ...`
  - Passed import check and printed `validation-only`.
- `PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token_runtime.py`
  - Passed: 9 passed.
- `PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token_runtime.py source_proxy/tests/test_cartographer_api.py || PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token_runtime.py`
  - Passed first command: 258 passed, 2 FastAPI deprecation warnings.
- `PYTHONPATH=. .venv/bin/python - <<'PY' ... approval-token routes ...`
  - Confirmed GET and POST `/v1/cartographer/approval-token/validate` are registered.
- `npm run test -- --run src/app/map || true`
  - Completed with no map test files found; Vitest exited 1 and `|| true` made the requested shell command complete.
- `git diff --check`
  - Passed after implementation.
- `curl -k -s https://localhost:3000/v1/cartographer/approval-token/validate | jq . || true`
  - Returned `{"detail":"Not Found"}` from the already-running Next server, matching the known stale-server caveat pattern.
- `PYTHONPATH=. .venv/bin/python - <<'PY' ... TestClient(app).get('/v1/cartographer/approval-token/validate') ...`
  - Passed direct app check: HTTP 200, validation status `rejected`, reason `self_approval_rejected`.

## Blockers

No implementation blocker.

The known stale running server caveat for `/v1/cartographer/live-state` was not debugged in this phase because it did not block approval token runtime implementation.

The already-running Next server also returned `{"detail":"Not Found"}` for `/v1/cartographer/approval-token/validate`. A direct FastAPI app check confirms the backend route exists and returns validation JSON. Treat the browser curl result as stale server state unless a fresh restart proves otherwise.

During final status review, unrelated untracked `src/lib/coding/timeline-events*` files appeared outside this phase's allowed files. They were not edited by this phase and were left untouched.

## What This Phase Proves

- Approval token payloads have an explicit schema.
- Missing required fields fail closed.
- Malformed payloads fail closed.
- Approval actor is explicit.
- Self-approval is rejected.
- Token scope is explicit.
- Scope mismatch is rejected.
- Token freshness and expiration are enforced.
- Validation returns clear accepted or rejected results with reasons.
- Validation does not mutate repo state.
- Validation does not execute commands.
- `/map` can display approval-token validation state without exposing action buttons.

## What This Phase Does Not Prove

- It does not grant safe write authority.
- It does not implement workflow execution.
- It does not implement queue execution.
- It does not implement command execution.
- It does not implement commit, push, branch, worktree, stash, clean, reset, or checkout behavior.
- It does not persist approval tokens.
- It does not consume approval tokens for any authority expansion.

## Final Manual Check

```bash
cd /home/source/SpiritOS

git status --branch --short
git diff --check
git diff --stat -- \
  source_proxy/cartographer/approval_token_runtime.py \
  source_proxy/tests/test_cartographer_approval_token_runtime.py \
  source_proxy/api/cartographer.py \
  src/app/v1/cartographer/approval-token/validate/route.ts \
  src/app/map/page.tsx \
  src/app/map/cartographer-approval-token.ts \
  docs/cartographer-daily-driver-autonomy-plan-2-phase-1-approval-token-runtime-closeout.md

git diff --name-only

PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token_runtime.py

curl -k -s https://localhost:3000/v1/cartographer/approval-token/validate | jq . || true

grep -nE "Plan 2|Phase 1|approval token|validation|self-approval|scope|expired|stale|blocked|accepted|rejected|manual check|next permission" \
  docs/cartographer-daily-driver-autonomy-plan-2-phase-1-approval-token-runtime-closeout.md
```

## Next Phase

Plan 2 Phase 2: Approval Token Consumption Boundary

Exact next permission phrase:

Approve Cartographer Daily Driver Roadmap Plan 2 Phase 2 Approval Token Consumption Boundary
