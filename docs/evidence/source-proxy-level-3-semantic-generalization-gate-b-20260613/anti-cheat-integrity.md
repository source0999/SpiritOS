# Anti-Cheat Integrity

Verdict: clean.

## Final Rerun Counters

- fallback_used: false
- deterministic_scaffold_used: false
- backend_created_content: false
- cloud_api_fallback_used: false
- real_app_touched: false
- score_integrity_failure: false
- report_verdict_mismatch: false
- missing_behavior_evidence: false
- missing_transcript: false
- repair_attempts_used: 2
- false_positive_corrections: 0
- false_negative_corrections: 0
- score_warnings: 0

## Scorer And Verdict Logic

- Scorer changes: no.
- Final verdict logic changes: no.
- `source_proxy/decision/artifact_final_verdict.py` was not changed in Gate B.

## Model/Verifier Lane Truth

- Qwen ran for the final clean similar 10 rerun via `qwen2.5-coder:7b`.
- Gemma/Hermes verifier lanes were not invoked as live lanes.
- Cartographer was not activated as live route ownership.
- Route traces are evidence sidecars only.

## Repair Boundary

Two bounded repair attempts ran:

- theme prompt: one attempt, still failed.
- drawing prompt: one attempt, passed after repair.

Repairs remained model-authored, path-bound, and within disposable workspaces. No backend-authored rescue content was used.
