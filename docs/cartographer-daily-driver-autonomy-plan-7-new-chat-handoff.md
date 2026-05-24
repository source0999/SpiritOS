# New Chat Handoff: Cartographer Daily Driver Roadmap Plan 7

You are taking over work in `/home/source/SpiritOS`.

Follow Britton's workflow:

- Work one full phase at a time.
- Break each phase into small increments.
- Complete an increment, run its manual check yourself, then continue inside the same phase if it passes.
- At the end of the full phase, output one manual check block for Britton.
- Ask Britton for permission before moving to the next phase.
- If Britton says "if all good go next phase in same workflow", treat that as permission to continue after the current phase's manual check passes.
- Do not commit, push, stash, clean, branch, create worktrees, reset, checkout, or run destructive git commands unless explicitly granted.
- Keep allowed files narrow.
- Stop immediately if unexpected files change because of your work.

Current completed work:

- Plan 3 Phase 1 through Phase 4 completed.
- Plan 4 Phase 1 through Phase 4 completed.
- Plan 5 Phase 1 through Phase 4 completed.
- Plan 6 Phase 1 through Phase 5 completed.
- Plan 7 Phase 1 completed: `/map` information architecture reset.

Latest verification for Plan 6:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safe_task_queue.py source_proxy/tests/test_cartographer_safe_task_queue_api.py source_proxy/tests/test_cartographer_workflow_runner.py source_proxy/tests/test_cartographer_workflow_controls.py source_proxy/tests/test_cartographer_workflow_event_ledger.py source_proxy/tests/test_cartographer_workflow_state.py source_proxy/tests/test_cartographer_safe_write.py source_proxy/tests/test_cartographer_verification_runner.py
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py
git diff --check
```

Results:

- 80 passed for the Plan 6 focused suite.
- 257 passed for `source_proxy/tests/test_cartographer_api.py`, with 2 known FastAPI deprecation warnings.
- `git diff --check` passed.

Latest verification for Plan 7 Phase 1:

```bash
npm test -- run src/app/map/__tests__/map-information-architecture.test.ts
npm run typecheck
git diff --check
```

Known worktree condition:

The repo has many pre-existing dirty and untracked files, including forbidden lanes. Treat those as user-owned/pre-existing. Do not revert, clean, stash, branch, commit, push, reset, checkout, or delete anything.

Plan 7 roadmap context:

Plan 7 is "Operator Dashboard And /map Command Center".

Purpose:

Make `/map` usable as the Cartographer cockpit, not a static wall of confusing widgets.

Completed Phase 7.1:

- Replaced the confusing static `/map` layout with simple operational sections.
- Added `src/app/map/map-information-architecture.ts`.
- Added `src/app/map/__tests__/map-information-architecture.test.ts`.
- Added `docs/cartographer-daily-driver-autonomy-plan-7-phase-1-map-ia-reset-closeout.md`.

Next phase title:

Plan 7 Phase 2: Live State Panel

Next small increment:

7.2.1: Show branch, HEAD, dirty state, protected-lane state, and recommendation.

Likely allowed files for Plan 7 Phase 2:

- `src/app/map/page.tsx`
- `src/app/map/cartographer-live-state.ts`
- `src/app/map/map-information-architecture.ts`
- exact focused `src/app/map/__tests__/**`
- `docs/cartographer-daily-driver-autonomy-plan-7-phase-2-live-state-panel-closeout.md`

Do not touch unless explicitly justified before editing:

- `source_proxy/api/cartographer.py`
- `source_proxy/cartographer/**`
- `src/app/coding/**`
- package/config files
- dashboard demo files outside the exact `/map` need

Important stale-server caveat:

Browser curl to Next routes may return stale `{"detail":"Not Found"}` from an already-running server. Direct FastAPI TestClient checks have been reliable for backend routes. For `/map`, prefer focused frontend tests and typecheck unless Britton explicitly asks for live browser verification.

Manual check shape for next phase:

```bash
cd /home/source/SpiritOS
npm test -- run <exact approved map test file>
npm run typecheck
git diff --check
git status --branch --short
```

Rules:

The `/map` page must remain simple, functional, readable, and operational. It must not grant authority. Do not add broad full-auto, self-approval, broad write, broad command, commit, push, checkout, reset, clean, stash, or destructive controls.
