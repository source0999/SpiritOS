# Existing Browser Verifier Review

## Existing Verifier Files

- `source_proxy/api/decision.py`
  - `_fip5_browser_probe`
  - `_fip5_browser_verifier`
  - `_browser_verifier_harness`
  - `_structured_verdict_fields`
  - FIP0 receipt attachment for `browser_verifier_status`, `browser_behavior_status`, `verification_real`, and `productive`.
- `source_proxy/decision/verifier_lane.py`
  - Advisory verifier packet and output normalization.
  - Already blocks verifier PASS when browser behavior evidence is missing or failed.
- Tests:
  - `source_proxy/tests/test_prompt_packet_context_metadata.py`
  - `source_proxy/tests/test_verifier_lane.py`
  - `source_proxy/tests/test_artifact_final_verdict.py`
  - `source_proxy/tests/test_artifact_behavior_contract.py`

## Existing Verifier Fields

Current browser verifier output has legacy fields:

- `status`: `used`, `skipped`, `blocked`, `failed`, `timed_out`, or `config_blocked`
- `passed`
- `authoritative`
- `checks`
- `target_path`
- `timeout_ms`
- `verifier_version`
- `browser_engine`

Receipts expose:

- `browser_behavior_status`
- `browser_verifier_status`
- `browser_verifier_checks`
- `browser_verifier_target_path`
- `browser_probe_summary`
- `verification_real`
- `verification_real_reasons`
- `productive`

## Known Audit Complaints

- Return checkpoint says browser verifier truth is contradictory across old/new evidence.
- Claude audit found browser UI rows blocked and no real browser verifier for some claims.
- Level 5R2 evidence later claims browser evidence passed.
- `productive_go` is still too structural and should not be hardened in this patch.

## What Is Real Today

- `_fip5_browser_verifier` can run Playwright/Chromium headlessly against generated HTML content in a temporary file.
- The harness blocks non-file/data/about network requests.
- The harness captures page errors and console errors in bounded lists.
- Synthetic browser pass through `_fip5_browser_probe` is rejected by default unless trial harness mode is explicitly enabled.

## What Is Structural Or Degraded Today

- Browser pass is currently just `status == used` plus `passed is True`; the output does not carry the richer truth schema requested in this patch.
- Existing checks prove page load and visible text, but do not explicitly distinguish DOM-only/text-only/screenshot-only proof from interactive behavior proof.
- Unsupported browser targets are marked as `skipped` with `passed=True`, which is safe for legacy flow but too easy to misread as behavior proof.
- Playwright unavailable is `config_blocked`, but no structured `degraded_reason` field exists.

## Files Likely To Touch

- `source_proxy/api/decision.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`
- `docs/evidence/source-proxy-browser-verifier-hardening-20260618/`

## Files Explicitly Not Touched

- Frontend/Next files.
- Productive-go hardening beyond using the browser truth fields already present in receipt calculation.
- Qwen coder behavior.
- Repair loop.
- Service/watchdog/systemd/Docker/media files.

Raw evidence:

- raw/10-evidence-read.txt
- raw/11-source-proxy-files.txt
- raw/12-verifier-rg.txt
