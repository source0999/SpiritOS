# Mini Context Pack

Run title: Source Proxy Level 3 final clean similar 10 transparent proof
Date: 2026-06-13T15:33:08.717121+00:00
Verdict: NO-GO
Current grade recommendation: Do not accept Level 3 as GO; keep Level 3 NEEDS-FIX/NO-GO until fresh similar wording clears at least 8/10.

Goal: final clean similar 10 proof for Level 3 generalization, with transparent proxy trace and anti-tailoring/anti-cheat evidence.

What changed: new evidence-only prompt lock, run artifacts, traces, dashboard, audits, and mini context pack.
What did not change: runtime behavior, scoring, routing, model prompts, repair logic, artifact contracts, source code, real app files.

## Result Table

| id | prompt | final | bucket |
| --- | --- | --- | --- |
| final-l3-clean-01 | make a laundry flip countdown | PASS |  |
| final-l3-clean-02 | make a parking garage cost sharer | FAIL | route_blocked_no_preview |
| final-l3-clean-03 | make a dusk dawn palette switch | FAIL | route_blocked_no_preview |
| final-l3-clean-04 | make a beach bag checklist app | PASS |  |
| final-l3-clean-05 | make a pretend balcony forecast tile | FAIL | weather_static_when_update_expected |
| final-l3-clean-06 | make a campfire podcast mini player | PASS |  |
| final-l3-clean-07 | make a stair step tally counter | PASS |  |
| final-l3-clean-08 | make a sticky thought memo board | PASS |  |
| final-l3-clean-09 | make a secret phrase strength gauge | FAIL | route_blocked_no_preview |
| final-l3-clean-10 | make a finger paint doodle pad | FAIL | drawing_canvas_no_pixel_change |

Transparent proxy flow summary: see `transparent-proxy-trace-index.md` and `per-prompt-traces/`.
Model lane summary: INVOKED for all 10 prompts via qwen2.5-coder:7b; Gemma/Hermes verifier lanes were PREVIEW_ONLY/NOT_INVOKED; no Gemma transcript exists for this run.; PREVIEW_ONLY metadata/status only; no live Cartographer route ownership invocation recorded..
Anti-tailoring audit summary: No exact new prompt tailoring found in searched source/runtime scopes; new prompt strings exist only in this evidence folder.
Anti-cheat summary: no fallback/scaffold/backend/cloud/real-app contamination; two repair attempts used and both remained final FAIL.

Changed files: evidence files under this folder only.
Evidence files: `final-proof-results.json`, `final-proof.html`, `transparent-proxy-trace-index.md`, `per-prompt-traces/`, `anti-tailoring-audit.md`, `anti-cheat-integrity.md`, run artifacts under `final-clean-similar-10-runs/`.

Exact commands run:
- `python -m json.tool docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/final-proof-prompt-set.json > $null`
- `python docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py --prompt-file <evidence>/final-proof-prompt-set.json --run-root <evidence>/final-clean-similar-10-runs --title "Source Proxy Level 3 final clean similar 10 transparent proof" --results <evidence>/final-proof-intermediate-results.json --html <evidence>/final-proof-intermediate.html --run-receipt <evidence>/final-proof-run-receipt.json --browser-results <evidence>/final-proof-browser-behavior-results.json --repair-summary <evidence>/final-proof-post-behavior-repair-summary.json --model-id qwen2.5-coder:7b`
- `python docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/generate_final_proof_reports.py`
- `python -m pytest source_proxy/tests/test_artifact_behavior_contract.py source_proxy/tests/test_artifact_final_verdict.py source_proxy/tests/test_artifact_retest_result.py source_proxy/tests/test_artifact_repair_loop.py`
- `python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "artifact or behavior_contract or final_verdict or retest or repair or score_integrity or failure_bucket or fake or fallback or backend_authored"`
- `python -m pytest source_proxy/tests/test_task_spec_intake_unseen_artifacts.py`
- `python -m py_compile docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613/generate_final_proof_reports.py`
- `python -m json.tool final-proof-prompt-set.json; python -m json.tool final-proof-results.json; python -m json.tool per-prompt-traces/*.json; python -c "import xml.etree.ElementTree as ET; ET.parse('mini-context-pack.xml')"`
- `python <inline final-proof.html link audit>`
- `git diff --check -- docs/evidence/source-proxy-level-3-final-clean-similar-10-transparent-proof-20260613`
- `git status --branch --short --untracked-files=normal`

Remaining blockers: fresh similar wording reached only 5/10 behavior PASS; route inference blocked three artifacts; weather repair still left static behavior; drawing repair left canvas pixels unchanged.
Next recommended step: inspect the five failure families without starting Level 4 or creating a larger batch.
Exact files Britton should upload to ChatGPT next: `mini-context-pack.md`, `final-proof-results.json`, `transparent-proxy-trace-index.md`, and the five failing per-prompt trace JSON files.
