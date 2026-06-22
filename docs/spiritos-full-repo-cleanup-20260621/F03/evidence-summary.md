# F03 Evidence Summary

## Scope
F03 only: model-lane / brain-switch verdict contract, dry-run advisory only.
No F04/F05 work, no Set A/B/C execution, no Plan 3/4 work, no SpiritFlix/media/Jellyfin paths, no push, and no merge.

## Implementation Evidence
- Added `source_proxy/decision/escalation_contract.py` with five frozen recommendations: `LOCAL_RETRY_RECOMMENDED`, `LOCAL_DECOMPOSITION_RECOMMENDED`, `LOCAL_MODEL_INSUFFICIENT`, `API_ESCALATION_RECOMMENDED`, and `HUMAN_DECISION_REQUIRED`.
- `recommend_brain_switch()` records task shape, attempts, formatting failures, validation failures, capability evidence, lane availability, privacy/cost class, authority requirement, evidence IDs, and F1 `FailureClass`.
- Provider behavior is dry-run only: verdicts serialize `dry_run_only=True` and `provider_call_performed=False`.
- Added read-only advisory helpers in `model_lanes.py` and `litellm_router.py`; the router helper accepts supplied route statuses and does not call `route_models()`, `get_router()`, LiteLLM, Ollama, or external providers.

## Commands Run
- `/home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py -q` -> `21 passed in 0.53s` before F3 edits.
- `/home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_brain_switch_contract.py -q` -> `11 passed in 0.15s`.
- `/home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py -q` -> `21 passed in 0.74s` after F3 edits.
- `/home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_brain_switch_contract.py source_proxy/tests/test_status_codes.py source_proxy/tests/test_anticheat_registry.py source_proxy/tests/test_model_lanes.py source_proxy/tests/test_model_lane_preview_api.py` -> `38 passed in 0.77s`.
- `grep -R -n -E 'openai|anthropic|deepseek|litellm' source_proxy/decision source_proxy/tests/test_brain_switch_contract.py || true` -> hits limited to pre-existing `decision/preview.py`, pre-existing `decision/specialist_integration.py`, pycache, and the new test importing `litellm_router` by module name.
- `timeout 300 /home/source/SpiritOS/.venv-source-proxy/bin/python -m pytest source_proxy/tests -q` -> exit `124`; timed out at 300 seconds with existing failures visible.
- `docs/spiritos-full-repo-cleanup-20260621/F03/operator-check.sh` -> PASS before final commit.
- `git diff --check` -> PASS.

## Holdout / Anti-Cheat Notes
- Formatting failure remains local retry/decomposition and never becomes capability failure by itself.
- Retryable local failure remains local retry.
- API escalation requires bounded repeated validated local capability evidence and remains authority-required dry-run advice.
- Unavailable providers are never reported available.
- Benchmark labels such as A2/A5/A9 are covered in tests as labels only and do not drive production recommendations.

## Caveat
The full `source_proxy/tests` suite timed out after 300 seconds with failures visible. This is consistent with earlier cleanup slices and is not used as the F03 acceptance gate.
