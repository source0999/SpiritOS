#!/usr/bin/env bash
set -euo pipefail

cd /home/source/SpiritOS

ROOT="docs/source-proxy-human-brain-full-live-integration-pivot-20260619"
PLAN_DIR="$ROOT/plan-01"
ARTIFACTS="$PLAN_DIR/artifacts"

echo "Plan 1/6 operator check"

for file in \
  "$PLAN_DIR/plan.md" \
  "$PLAN_DIR/status.md" \
  "$PLAN_DIR/status.json" \
  "$PLAN_DIR/gate-manifest.template.json" \
  "$PLAN_DIR/operator-check.sh" \
  "$PLAN_DIR/next-plan-handoff.md" \
  "$PLAN_DIR/new-chat-start.md" \
  "$ARTIFACTS/codex-takeover-baseline.md" \
  "$ARTIFACTS/codex-takeover-diff-review.md" \
  "$ARTIFACTS/1.1.1-preflight.md" \
  "$ARTIFACTS/1.1.2-event-storage-decision.md" \
  "$ARTIFACTS/phase-1.1-closeout.md" \
  "$ARTIFACTS/phase-1.2-closeout.md" \
  "$ARTIFACTS/phase-1.3-closeout.md" \
  "$ARTIFACTS/1.4.2-success-live-proof.md" \
  "$ARTIFACTS/1.4.3-failure-live-proof.md" \
  "$ARTIFACTS/1.4.4-causality-audit.md" \
  "$ARTIFACTS/1.5.1-evidence-budget.md" \
  "$ARTIFACTS/live-proof-disposable.txt" \
  "$PLAN_DIR/plan-closeout.md" \
  "$PLAN_DIR/plan-closeout.json"; do
  test -f "$file" || { echo "FAIL missing $file"; exit 1; }
done

python3 - <<'PY'
import json
from pathlib import Path

base = Path("docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-01")
for rel in ["status.json", "gate-manifest.template.json", "plan-closeout.json"]:
    json.loads((base / rel).read_text(encoding="utf-8"))
closeout = json.loads((base / "plan-closeout.json").read_text(encoding="utf-8"))
required = ["trace_id", "invocation_event_id", "consumer_event_id", "consumer_subsystem"]
missing = [key for key in required if not closeout.get(key)]
if missing:
    raise SystemExit(f"missing causal closeout keys: {missing}")
if closeout.get("failure_proof", {}).get("blocked_target_created") is not False:
    raise SystemExit("failure proof does not show blocked target stayed absent")
print("json ok")
PY

git grep -n "trace_id\|invocation_event_id\|consumer_event_id\|consumer_subsystem" \
  source_proxy/tasks/long_running.py src/components/coding/CodingCockpitShell.tsx >/dev/null
git grep -n "causal_events_json" source_proxy/tasks/long_running.py >/dev/null

.venv-source-proxy/bin/python -m pytest -q source_proxy/tests -k "causal or long_running or consumer"
npm run typecheck
npx vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx -t "reads long-running causal trace proof"

if find "$ROOT/plan-02" -path "*/artifacts/*" -print 2>/dev/null | grep -q .; then
  echo "FAIL Plan 2 artifacts are present"
  exit 1
fi

git status --branch --short --untracked-files=normal
echo "PASS Plan 1/6 operator check"
