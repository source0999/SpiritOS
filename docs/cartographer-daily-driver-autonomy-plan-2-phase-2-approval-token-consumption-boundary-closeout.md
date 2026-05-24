# Cartographer Daily Driver Autonomy Roadmap Plan 2 Phase 2 Closeout

## Phase

Plan 2 Phase 2: Approval Token Consumption Boundary

## Result

Completed.

This phase adds a preview-only consumption boundary for Cartographer approval tokens. The boundary validates a token with the Phase 1 runtime, then checks explicit consumption context before reporting whether a requested action is eligible or blocked.

The boundary remains inert. It does not grant autonomy, safe writes, workflow execution, queue execution, command execution, commit, push, branch, worktree, stash, clean, reset, checkout, persistence, token minting, or approval generation.

## Increments Completed

- Increment 2.1: Added `source_proxy/cartographer/approval_token_consumption.py` with a pure preview-only consumption boundary.
- Increment 2.2: Added `source_proxy/tests/test_cartographer_approval_token_consumption.py` covering eligible previews, invalid tokens, missing context, scope mismatch, action mismatch, stale HEAD, trust mismatch, file boundary failures, forbidden actions, kill switch blocking, and no mutation or execution surface.
- Increment 2.3: Added backend API wiring at `/v1/cartographer/approval-token/consume-preview` plus a matching Next proxy route. The route returns preview JSON only.
- Increment 2.4: Wired `/map` to show the consumption boundary status, preview-only flag, blocked reasons, and safe next action. No execution controls were added.
- Increment 2.5: Wrote this closeout.

## Files Changed

- `source_proxy/cartographer/approval_token_consumption.py`
- `source_proxy/tests/test_cartographer_approval_token_consumption.py`
- `source_proxy/api/cartographer.py`
- `src/app/v1/cartographer/approval-token/consume-preview/route.ts`
- `src/app/map/page.tsx`
- `src/app/map/cartographer-approval-token.ts`
- `docs/cartographer-daily-driver-autonomy-plan-2-phase-2-approval-token-consumption-boundary-closeout.md`

## Checks Run

- `git status --branch --short`
  - Completed before edits. Worktree was already dirty with many tracked and untracked files, including forbidden lanes.
- `git diff --check`
  - Passed before edits and after implementation.
- `PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token_consumption.py`
  - First run found and fixed a public-surface leak from the imported Phase 1 validator.
  - Final result: 8 passed.
- `PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token_runtime.py source_proxy/tests/test_cartographer_approval_token_consumption.py`
  - Passed: 17 passed.
- `PYTHONPATH=. .venv/bin/python - <<'PY' ... approval-token routes ...`
  - Confirmed GET and POST `/v1/cartographer/approval-token/validate` plus GET and POST `/v1/cartographer/approval-token/consume-preview` are registered.
- `npm run test -- --run src/app/map || true`
  - Completed with no map test files found; Vitest exited 1 and `|| true` made the shell command complete.

## What This Phase Proves

- Token consumption is preview-only.
- Token consumption requires the Phase 1 token validator to accept the token.
- Missing consumption context fails closed.
- Scope mismatch is blocked.
- Action class mismatch is blocked.
- Forbidden action classes are blocked.
- Stale HEAD is blocked.
- Trust tier mismatch is blocked.
- Requested files outside exact allowed files are blocked.
- Requested files matching forbidden files are blocked.
- Wildcard file scopes are blocked.
- Kill switch active state blocks eligibility.
- Preview output returns clear eligible or blocked status with reasons.
- `/map` displays the boundary without adding execution controls.

## What This Phase Does Not Prove

- It does not grant safe write authority.
- It does not consume a token to execute an action.
- It does not persist approval tokens.
- It does not mint approval tokens.
- It does not write receipts or evidence.
- It does not implement workflow execution.
- It does not implement queue execution.
- It does not implement command execution.
- It does not implement commit, push, branch, worktree, stash, clean, reset, or checkout behavior.

## Final Manual Check

```bash
cd /home/source/SpiritOS

git status --branch --short
git diff --check
git diff --stat -- \
  source_proxy/cartographer/approval_token_consumption.py \
  source_proxy/tests/test_cartographer_approval_token_consumption.py \
  source_proxy/api/cartographer.py \
  src/app/v1/cartographer/approval-token/consume-preview/route.ts \
  src/app/map/page.tsx \
  src/app/map/cartographer-approval-token.ts \
  docs/cartographer-daily-driver-autonomy-plan-2-phase-2-approval-token-consumption-boundary-closeout.md

git diff --name-only

PYTHONPATH=. .venv/bin/python -m pytest \
  source_proxy/tests/test_cartographer_approval_token_runtime.py \
  source_proxy/tests/test_cartographer_approval_token_consumption.py

PYTHONPATH=. .venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from source_proxy.main import app

response = TestClient(app).get("/v1/cartographer/approval-token/consume-preview")
print(response.status_code)
body = response.json()
print(body["runtime"]["status"])
print(body["preview"]["status"])
print(body["preview"]["reasons"])
print(body["preview"]["authority_granted"])
PY

curl -k -s https://localhost:3000/v1/cartographer/approval-token/consume-preview | jq . || true

grep -nE "Plan 2|Phase 2|approval token|consumption|preview|eligible|blocked|scope|stale|trust|kill switch|forbidden|manual check|next permission" \
  docs/cartographer-daily-driver-autonomy-plan-2-phase-2-approval-token-consumption-boundary-closeout.md
```

## Next Phase

Plan 2 Phase 3: Token Storage Or Durable Record Decision

Exact next permission phrase:

Approve Cartographer Daily Driver Roadmap Plan 2 Phase 3 Token Storage Or Durable Record Decision
