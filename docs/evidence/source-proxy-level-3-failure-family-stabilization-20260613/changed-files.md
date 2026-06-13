# Changed Files

Date: 2026-06-13

## System Files

- `source_proxy/decision/task_spec_intake.py`
  - Expanded generic disposable static UI detection for standalone theme/mode/toggle/color/flipper widgets and radio/audio player wording.
- `source_proxy/decision/artifact_behavior_contract.py`
  - Strengthened general family contracts for timers/countdowns/stopwatches, player controls, notes/memos, password/passphrase/safety meters, and drawing/canvas surfaces.
- `source_proxy/decision/human_messy_homepage.py`
  - Added generic family implementation checklist text to the model prompt based on behavior probe family.
- `source_proxy/decision/artifact_repair_contract.py`
  - Preserves string `expected` probe metadata, primary/secondary failure buckets, and allowed relative files in repair packets.
  - Strengthens repair prompt output contract toward Source Proxy `WriteFile` JSON or explicit `<file path="...">` blocks.

## Tests

- `source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`
- `source_proxy/tests/test_artifact_behavior_contract.py`
- `source_proxy/tests/test_artifact_repair_loop.py`

## Evidence

- `docs/evidence/source-proxy-level-3-failure-family-stabilization-20260613/`
- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-level3-stabilization-*`
- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-level3-stabilization-*`

## Boundaries Preserved

- No prompt-specific branches for locked prompt strings.
- No scoring threshold change.
- No final verdict loosening.
- No fallback/scaffold/backend-authored/cloud/sidecar rescue.
- No real app trial prompt mutation.
- No git staging, commit, branch, stash, reset, checkout, clean, or push.
