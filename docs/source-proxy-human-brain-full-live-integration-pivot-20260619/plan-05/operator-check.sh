#!/usr/bin/env bash
set -euo pipefail
cd /home/source/SpiritOS
echo "Plan 5/6 - Binary Whole-Brain Acceptance"
ROOT="docs/source-proxy-human-brain-full-live-integration-pivot-20260619"
PLAN_DIR="$ROOT/plan-05"
for f in plan.md status.md status.json gate-manifest.template.json operator-check.sh next-plan-handoff.md new-chat-start.md; do
  test -f "$PLAN_DIR/$f" || { echo "FAIL missing $PLAN_DIR/$f"; exit 1; }
done
python3 -m json.tool "$PLAN_DIR/status.json" >/dev/null
python3 -m json.tool "$PLAN_DIR/gate-manifest.template.json" >/dev/null
python3 -m json.tool "$ROOT/status.json" >/dev/null
if grep -R -E "preview_only_completion|advisory_only_completion|read_only_completion" "$PLAN_DIR/status.md" >/dev/null 2>&1; then
  echo "FAIL forbidden completion flag in status"
  exit 1
fi
git status --short
if find "$ROOT" -type d -empty -print | grep .; then
  echo "FAIL empty planning directories present"
  exit 1
fi
echo "PASS Plan 5/6 operator planning check"
