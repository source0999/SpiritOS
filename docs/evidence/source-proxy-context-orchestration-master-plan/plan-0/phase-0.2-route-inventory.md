# Plan 0 Phase 0.2: Source Proxy and `/coding` Route Inventory

Status: GO

Execution boundary: read-only file and text inventory only. No backend route calls. No model calls. No coder trials. No runtime behavior changes.

## Increment 0.2.1: Source Proxy Backend and `/coding` Inventory

Commands run:

- `rg --files src/app source_proxy src/components/coding | rg "(coding|source_proxy|v1|actions|chat|decision|route|agent|cartographer|scout|design|repomix)"`
- `rg -n "@app\\.|APIRouter|router\\.|FastAPI|/v1/|prompt-packet|execute-approved|preview|coding|repomix|Cartographer|Scout|Design" source_proxy src/app src/components/coding -g "*.py" -g "*.ts" -g "*.tsx"`
- `Get-ChildItem -Recurse -File -LiteralPath 'src\\app' | Where-Object { $_.Name -eq 'route.ts' -or $_.Name -eq 'page.tsx' }`
- `Get-Content source_proxy\\main.py`
- `Get-Content source_proxy\\self_status.py | Select-Object -First 260`
- `Get-Content source_proxy\\api\\chat.py | Select-Object -First 220`
- `Get-Content src\\app\\coding\\page.tsx`

Observed primary backend registration:

- `source_proxy/main.py` creates the FastAPI app titled `Source Proxy`.
- Registered routers include action preview, Cartographer, chat, Codex adapter, coding self-tests, context index, context inventory, decision, diff verification, healthcheck, long-running tasks, Obsidian context, sandbox terminal, Scout intake, self status, tools manifest, and workspace tools.
- `source_proxy/main.py` declares apply authority separately through `POST /v1/tasks/long-running/{task_id}/execute-approved`.
- `source_proxy/api/chat.py` exposes `GET /v1/models` and `POST /v1/chat/completions`.

Observed `/coding` frontend surface:

- `src/app/coding/page.tsx` renders `CodingCockpitShell`.
- `src/components/coding/CodingCockpitShell.tsx` is the large current cockpit shell using Source Proxy status, trials, runs, prompt packets, and diagnostics.
- `src/components/coding/CodingAgentInterface.tsx` remains another large coding interface surface.

Observed app-router surfaces relevant to this master plan:

- `/coding`
- `/proxy-backend`
- `/v1/decisions/route`
- `/v1/decisions/prompt-packet`
- `/v1/actions/preview`
- `/v1/actions/execute-approved`
- `/v1/verification/diff-preview`
- `/v1/coding/bounded-diff-preview`
- `/v1/coding/cartographer/preview`
- `/v1/coding/design-vault/preview`
- `/v1/coding/helper-agents/preview`
- `/v1/coding/mac-advisory`
- `/v1/coding/research-preview`
- `/v1/coding/gauntlet/preview`
- `/v1/coding/runs`
- `/v1/coding/runs/active`
- `/v1/coding/runs/recent`
- `/v1/coding/trial-fixture-baseline`
- `/v1/coding/trial-receipt-reconcile`
- `/v1/coding/workspace-read`
- `/v1/context/index`
- `/v1/context/inventory`
- `/v1/context/obsidian/query`
- `/api/research/web-search`
- `/api/scout/*`
- multiple `/v1/cartographer/*` routes, including repo-map, components, live-state, status, proposals, push queue, approval token, and apply-approved surfaces.

Result: PASS. Inventory was captured without treating route presence as integration.

## Increment 0.2.2: Preview, Advisory, Integrated, and Production-Ready Classification

Classification from current inventory:

- Preview surfaces: bounded diff preview, Cartographer preview, Design vault preview, helper-agents preview, gauntlet preview, research preview, action preview, manual result preview, diff preview.
- Advisory surfaces: Mac advisory, Scout/research packet previews, helper agent previews, Design vault preview, Cartographer read-only/status/map routes where no apply authority is granted.
- Authority-bearing or mutation-adjacent surfaces: `execute-approved`, Cartographer `apply-approved`, Cartographer push/commit approval paths, long-running task advance/verify/execute boundaries.
- Receipt/status surfaces: coding runs, active runs, recent runs, trial receipt reconcile, self status, tools manifest, context index, context inventory.
- Integrated Source Proxy context-orchestrated coder path: not accepted by this inventory alone. Plan 4 must prove the context packet builder is on the real `/coding` hot path and that the coder receives the final packet.
- Production-ready context-orchestrated coder path: not accepted in Plan 0. Plan 5 must prove 3 of 3 basic messy prompts pass A+.

Result: PASS. Existing routes are classified as surfaces, not accepted integration.

## Increment 0.2.3: Repomix Current Appearance

Observed Repomix-related files and references:

- `repomix.config.json`
- `repomix-output.xml`
- `repomix-output.ast.xml`
- `source_proxy/tests/test_coder_agent_repomix_diff.py`
- `source_proxy/tests/test_reviewer_deterministic.py`
- `source_proxy/tests/test_self_status.py`
- `source_proxy/tests/test_source_proxy_end_to_end.py`

Plan 0 policy:

- Repomix is allowed as one fallback context source.
- Repomix is not accepted as the main repo-context brain.
- Repomix presence is not full-context readiness.
- Any fallback-only coder run must block or warn visibly and record fallback-only status.

Result: PASS. Repomix is classified as a fallback/source candidate only.

## Phase 0.2 Closeout

Checks passed:

- Source Proxy backend routers inventoried.
- `/coding` shell route identified.
- Preview/advisory/authority/receipt surfaces classified.
- Route-exists acceptance explicitly rejected.
- Repomix-only full-context claims explicitly rejected.

GO/NO-GO: GO to Phase 0.3 model/provider route truth.

Next permitted phase: Phase 0.3 only.
