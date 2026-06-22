#!/usr/bin/env bash
set -euo pipefail

STAGE_DIR="docs/spiritos-full-repo-cleanup-20260621/F03"
PYTHON="/home/source/SpiritOS/.venv-source-proxy/bin/python"
EXPECTED_ACCEPTANCE_SHA="94fd549cfd8498e09e3923cbdd19eb549b23a6367b6bfdc7eaf7170847dc601f"
EXPECTED_HOLDOUT_SHA="a46e8b752bd531c2882891184415cd8c800f443a51c3362954c93869305e3ac0"

printf 'F03 operator check
'

test -f "$STAGE_DIR/acceptance-contract.json"
test -f "$STAGE_DIR/holdout-manifest.json"
test -f "$STAGE_DIR/status.json"

actual_acceptance_sha="$(sha256sum "$STAGE_DIR/acceptance-contract.json" | awk '{print $1}')"
actual_holdout_sha="$(sha256sum "$STAGE_DIR/holdout-manifest.json" | awk '{print $1}')"
test "$actual_acceptance_sha" = "$EXPECTED_ACCEPTANCE_SHA"
test "$actual_holdout_sha" = "$EXPECTED_HOLDOUT_SHA"
printf '  [OK] frozen contract hashes match
'

"$PYTHON" - <<'PY'
import json
from pathlib import Path
from source_proxy.decision.escalation_contract import (
    BrainSwitchEvidence,
    BrainSwitchRecommendation,
    recommend_brain_switch,
)
from source_proxy.diagnostics.status_codes import FailureClass

stage = Path('docs/spiritos-full-repo-cleanup-20260621/F03')
for name in ['acceptance-contract.json', 'holdout-manifest.json', 'status.json']:
    json.loads((stage / name).read_text())
contract = json.loads((stage / 'acceptance-contract.json').read_text())
expected = {
    'LOCAL_RETRY_RECOMMENDED',
    'LOCAL_DECOMPOSITION_RECOMMENDED',
    'LOCAL_MODEL_INSUFFICIENT',
    'API_ESCALATION_RECOMMENDED',
    'HUMAN_DECISION_REQUIRED',
}
assert set(contract['verdicts_frozen']) == expected
verdict = recommend_brain_switch(BrainSwitchEvidence(
    task_shape='operator_check_formatting',
    local_attempts=1,
    formatting_failures=1,
    failure_classification=FailureClass.MODEL_FORMATTING_FAILURE,
))
assert verdict.recommendation is BrainSwitchRecommendation.LOCAL_RETRY_RECOMMENDED
assert verdict.dry_run_only is True
assert verdict.provider_call_performed is False
print('  [OK] verdict contract imports and dry-run formatting check passes')
PY

"$PYTHON" -m pytest source_proxy/tests/test_brain_switch_contract.py -q
"$PYTHON" -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py -q
printf '  [OK] F3 focused tests and F1/F2 compatibility tests pass
'

allowed='^(source_proxy/decision/escalation_contract.py|source_proxy/tests/test_brain_switch_contract.py|source_proxy/decision/model_lanes.py|source_proxy/routing/litellm_router.py|docs/spiritos-full-repo-cleanup-20260621/F03/.*|docs/spiritos-full-repo-cleanup-20260621/cleanup-state.json)$'
changed="$( { git diff --name-only; git ls-files --others --exclude-standard; } | sort -u )"
if [ -n "$changed" ]; then
  unexpected="$(printf '%s
' "$changed" | grep -Ev "$allowed" || true)"
  if [ -n "$unexpected" ]; then
    printf 'Unexpected F03 path(s):
%s
' "$unexpected" >&2
    exit 1
  fi
fi
printf '  [OK] changed paths remain F3-scoped
'

protected='^(src/components/spiritflix|src/lib/spiritflix|scripts/media|services/jellyfin)'
if printf '%s
' "$changed" | grep -Eq "$protected"; then
  printf 'Protected path touched
' >&2
  exit 1
fi
printf '  [OK] protected SpiritFlix/media/Jellyfin paths untouched
'

new_runtime_diff="$(git diff -- source_proxy/decision/escalation_contract.py source_proxy/decision/model_lanes.py source_proxy/tests/test_brain_switch_contract.py)"
if printf '%s
' "$new_runtime_diff" | grep -Ei 'openai|anthropic|deepseek|api_key|OPENAI|ANTHROPIC|DEEPSEEK' >/dev/null; then
  printf 'Forbidden provider/API token in new F3 contract diff
' >&2
  exit 1
fi
if printf '%s
' "$new_runtime_diff" | grep -Ei 'if .*A2|if .*A5|if .*A9|Set A|4R' >/dev/null; then
  printf 'Benchmark-keyed production branch in F3 runtime diff
' >&2
  exit 1
fi
printf '  [OK] no provider token or benchmark-keyed production branch in F3 contract diff
'

git diff --check
printf '  [OK] git diff --check
'
printf 'F03 operator check: PASS
'
