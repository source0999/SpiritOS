# Plan 3 Cleanup + Stabilization Closeout

Date: 2026-06-09

Scope: Cleanup and stabilization only before Plan 4. This round repaired the messy prompt harness, re-ran the three previously failed prompts, re-ran successful prompts as sanity checks, and added a small new messy prompt set.

## Harness Improvements

Added:

- `scripts/agent-trials/run-plan3-messy-e2e.py`

What changed:

- Replaced inline Python/stdin harness behavior with a durable script file.
- Avoided Windows `multiprocessing` respawn from `Z:\<stdin>`.
- Runs each prompt in a subprocess with a per-row watchdog.
- Writes row-level JSON after each prompt so a timeout cannot erase the whole round.
- Uses Ollama HTTP `/api/generate` with `stream=false`.
- Keeps `qwen2.5-coder:7b` as the model.
- Calls the central gate for model calls only.
- Prechecks protected/out-of-lane targets before context/model work.
- Uses disposable temp workspaces and does not apply generated proposals.

## Prompt Results

Artifact:

- `docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/plan-3-messy-stabilization-results.json`

Summary:

- Total prompts: 9.
- Preview-ready proposals: 7.
- Clean protected-path block: 1.
- Safe no-change/block: 1.
- Timeouts: 0.
- Exceptions: 0.
- Apply attempted: 0.
- Transport: `ollama_http_api_generate_stream_false`.
- Model: `qwen2.5-coder:7b`.

Previously failed prompts:

| Prompt | Result | Evidence |
| --- | --- | --- |
| `cart-count-messy` | GO | `preview_ready`, 35 diff lines, HTTP Ollama, no apply |
| `sort-price-messy` | GO | `preview_ready`, 14 diff lines, HTTP Ollama, no apply |
| `blocked-real-app-trap-messy` | GO | `blocked_cleanly`, `protected_target_precheck`, no model call, no apply |

Sanity reruns:

| Prompt | Result | Evidence |
| --- | --- | --- |
| `local-filter-messy` | GO | `preview_ready`, 29 diff lines |
| `empty-state-messy` | GO | `preview_ready`, 14 diff lines |
| `category-chips-messy` | GO | `preview_ready`, 17 diff lines |

New messy prompts:

| Prompt | Result | Evidence |
| --- | --- | --- |
| `focus-state-messy` | GO | `preview_ready`, 8 diff lines |
| `readme-noop-messy` | GO | safe no-change/block, `coder_no_changes_needed`, no apply |
| `product-card-label-messy` | GO | `preview_ready`, 10 diff lines |

## Remaining Issues

- Local `qwen2.5-coder:7b` is slow on this workload. Most model rows took about 230-238 seconds.
- A 240-second watchdog is too tight for some rows; 420 seconds cleared the borderline rows.
- The protected-path trap now avoids the slow path by prechecking lane scope first.

## Verification

Commands run:

```powershell
python -m py_compile scripts\agent-trials\run-plan3-messy-e2e.py
python -m json.tool docs\evidence\source-proxy-context-orchestration-master-plan\plan-3\plan-3-messy-stabilization-results.json > $null
git diff --check -- scripts/agent-trials/run-plan3-messy-e2e.py docs/evidence/source-proxy-context-orchestration-master-plan/plan-3
node scripts\gate-status
git status --branch --short --untracked-files=normal -- scripts/agent-trials/run-plan3-messy-e2e.py docs/evidence/source-proxy-context-orchestration-master-plan/plan-3 .gate/state.json
```

Observed:

- Script compile: passed.
- JSON parse: passed.
- Diff whitespace check: passed.
- Gate status: `RUNNING_INCREMENT`, approved increment `evaluation-round`, model-call approval only, no apply approval.
- Git status: new stabilization harness and Plan 3 evidence only in this cleanup lane.

## Manual Verification Commands

```powershell
python -m py_compile scripts\agent-trials\run-plan3-messy-e2e.py
python scripts\agent-trials\run-plan3-messy-e2e.py --prompt blocked-real-app-trap-messy --timeout-seconds 60 --output docs\evidence\source-proxy-context-orchestration-master-plan\plan-3\manual-smoke.json
python -m json.tool docs\evidence\source-proxy-context-orchestration-master-plan\plan-3\plan-3-messy-stabilization-results.json > $null
python - <<'PY'
import json
from pathlib import Path
p = Path('docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/plan-3-messy-stabilization-results.json')
d = json.loads(p.read_text())
print(json.dumps(d['summary'], indent=2))
PY
node scripts\gate-status
git diff --check -- scripts/agent-trials/run-plan3-messy-e2e.py docs/evidence/source-proxy-context-orchestration-master-plan/plan-3
```

## Stop

Cleanup + stabilization result: GO for review.

Do not start Plan 4 until Britton reviews this closeout and explicitly approves Plan 4.
