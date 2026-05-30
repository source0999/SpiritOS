# New Chat Prompt: Cartographer Daily Driver Roadmap Plan 2 Phase 1

Copy and paste this whole prompt into the new chat.

```text
You are taking over work in /home/source/SpiritOS.

We are following Britton's workflow:

- Work one full phase at a time.
- Each phase is broken into small increments.
- Complete one increment, run its manual check yourself, then move to the next increment inside the same phase if it passes.
- Do not stop after every tiny increment unless blocked.
- At the end of the full phase, output one big manual check block for Britton to run.
- Then ask Britton for permission before moving to the next phase.
- Do not infer permission from previous approval.
- Do not commit, push, stash, clean, branch, or create worktrees unless the phase explicitly grants that authority.
- Keep allowed files narrow.
- Stop immediately if unexpected files change.

Current objective:
Start Cartographer Daily Driver Autonomy Roadmap, Plan 2, Phase 1.

Explicit permission phrase already provided for this new chat:
Approve Cartographer Daily Driver Roadmap Plan 2 Phase 1 Approval Token Runtime

Plan 1 status:
Plan 1 Phase 1, Live Cartographer State And Protected-Lane Baseline, was implemented.

Plan 1 Phase 1 changed:
- source_proxy/cartographer/live_state.py
- source_proxy/tests/test_cartographer_live_state.py
- source_proxy/api/cartographer.py
- src/app/v1/cartographer/live-state/route.ts
- src/app/map/page.tsx
- src/app/map/cartographer-live-state.ts
- docs/cartographer-daily-driver-autonomy-plan-1-phase-1-live-state-closeout.md

Important Plan 1 caveat:
- Britton's manual curl to https://localhost:3000/v1/cartographer/live-state returned {"detail":"Not Found"} from the already-running server.
- Current code registers /v1/cartographer/live-state and focused tests pass.
- Treat this as likely stale running server state unless a fresh restart proves otherwise.
- Do not spend Plan 2 time debugging the server unless the route proof blocks the first increment.

Known worktree condition:
- The repo has many pre-existing dirty and untracked files, including forbidden lanes.
- Treat those as user-owned/pre-existing.
- Do not revert, clean, stash, branch, commit, push, or reset.
- Before editing, capture current status and then only touch Plan 2 Phase 1 allowed files.
- Stop immediately if files outside the Plan 2 Phase 1 allowed list change because of your work.

Current objective details:
Plan 2 Phase 1: Approval Token Runtime

Phase goal:
Implement the first approval token runtime foundation for Cartographer so later phases can require explicit human approval before any authority expansion. This phase must remain inert by itself and must not grant autonomy, safe writes, workflow execution, queue execution, command execution, commit, push, branch, worktree, stash, clean, reset, or checkout authority.

The approval token runtime should be deterministic, fail-closed, and testable. It should validate approval payloads; it should not execute approved actions.

Plan 2 Phase 1 must prove:
- Approval token payloads have an explicit schema.
- Missing required fields fail closed.
- Malformed payloads fail closed.
- Approval actor is explicit.
- Self-approval is rejected.
- Token scope is explicit.
- Scope mismatch is rejected.
- Token freshness or expiration is enforced if included in implementation scope.
- Validation returns a clear accepted/rejected result with reasons.
- No repo mutation happens during validation.
- No command execution happens during validation.
- No workflow, queue, commit, push, branch, worktree, stash, clean, reset, or checkout behavior is implemented.

Suggested narrow allowed files for Plan 2 Phase 1:
- source_proxy/cartographer/approval_token_runtime.py
- source_proxy/tests/test_cartographer_approval_token_runtime.py
- source_proxy/api/cartographer.py
- src/app/v1/cartographer/approval-token/validate/route.ts
- src/app/map/page.tsx
- src/app/map/cartographer-approval-token.ts
- docs/cartographer-daily-driver-autonomy-plan-2-phase-1-approval-token-runtime-closeout.md

Do not touch unless absolutely required and clearly justified before editing:
- docs/cartographer-daily-driver-autonomy-roadmap-v0.1.md
- docs/cartographer-daily-driver-autonomy-plan-1-phase-1-live-state-closeout.md
- docs/cartographer-daily-driver-autonomy-plan-2-phase-1-new-chat-handoff.md

Forbidden files:
- src/app/coding/**
- src/components/coding/**
- docs/codingUI.md
- docs/source-proxy-v0.3-stress-testing-plan.md
- docs/proxy-test-runner-plan.md
- package.json
- next.config.ts
- .env*
- config/**
- scout/**
- dashboard files
- source_proxy/cartographer/apply.py
- source_proxy/cartographer/autopilot_apply.py
- source_proxy/cartographer/level_11_approval_token.py
- source_proxy/cartographer/level_12_workflow_runtime.py
- source_proxy/cartographer/level_13_worker_runtime.py
- source_proxy/cartographer/level_14_autonomy_runtime.py
- commit/push/branch/worktree modules
- generated files

Implementation rules:
- Prefer pure Python functions for token validation.
- Prefer exact structured objects over ad hoc strings.
- Prefer deterministic timestamps passed into functions during tests.
- Do not use shell=True.
- Do not run arbitrary shell strings.
- Do not write files from the token runtime.
- Do not stage files.
- Do not commit.
- Do not push.
- Do not create branches.
- Do not create worktrees.
- Do not stash.
- Do not clean.
- Do not reset.
- Do not checkout.
- Do not run package installs.
- Fail closed on invalid, stale, expired, missing, or mismatched approval data.

Increment workflow:

For Increment 2.1:
- Inspect existing Cartographer API/service patterns and existing level 11 approval-token files as reference only.
- Create source_proxy/cartographer/approval_token_runtime.py.
- Implement the pure validation model.
- Do not expose through API yet.
- Run a small Python import check if useful.

For Increment 2.2:
- Create source_proxy/tests/test_cartographer_approval_token_runtime.py.
- Cover valid token, missing fields, malformed payloads, wrong actor, self-approval rejection, scope mismatch, stale/expired token if implemented, and no-mutation/no-execution guarantees.
- Run:
  cd /home/source/SpiritOS
  PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token_runtime.py
  git diff --check

For Increment 2.3:
- Add backend/API route or proxy wiring only for validation/preview.
- Use existing source_proxy/api/cartographer.py conventions if present.
- Add Next route only if it stays validation-only:
  src/app/v1/cartographer/approval-token/validate/route.ts
- Endpoint should return validation JSON.
- No mutation endpoints.
- Run:
  cd /home/source/SpiritOS
  PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token_runtime.py source_proxy/tests/test_cartographer_api.py || PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_approval_token_runtime.py
  git diff --check

For Increment 2.4:
- Wire /map to show approval token runtime status in a simple, readable way if the phase route is available.
- Keep UI plain and readable.
- Show:
  - validation-only status
  - no mutation authority
  - no command authority
  - self-approval blocked
  - safe next action
- No action execution buttons.
- No token creation buttons unless explicitly inert sample-only display.
- No full redesign.
- Run available frontend checks if scoped and safe:
  cd /home/source/SpiritOS
  npm run test -- --run src/app/map || true
  git diff --check

For Increment 2.5:
- Write:
  docs/cartographer-daily-driver-autonomy-plan-2-phase-1-approval-token-runtime-closeout.md
- Include:
  - increments completed
  - files changed
  - tests/checks run
  - actual result
  - blockers if any
  - what Plan 2 Phase 1 proves
  - what Plan 2 Phase 1 does not prove
  - next phase title
  - exact next permission phrase

Initial checks before editing:

cd /home/source/SpiritOS

git status --branch --short
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_live_state.py
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.main import app
print([route.path for route in app.routes if "live-state" in route.path])
PY

Final manual check for Britton:

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

Expected final outcome:
- Plan 2 Phase 1 is complete.
- Approval token runtime exists.
- Approval token runtime tests pass.
- Validation-only API route exists or blocker is clearly explained.
- /map displays approval-token validation status or blocker is clearly explained.
- Only allowed files changed.
- No safe write runtime implemented.
- No workflow runner implemented.
- No queue execution implemented.
- No command runner implemented.
- No commit.
- No push.
- No branch/worktree/stash/clean/reset.

Final response format:
1. State whether Plan 2 Phase 1 completed.
2. List increments completed.
3. List files changed.
4. List checks run and actual outcomes.
5. Show Britton the final manual check block.
6. State the next phase title.
7. Ask for the exact next permission phrase before continuing.
```
