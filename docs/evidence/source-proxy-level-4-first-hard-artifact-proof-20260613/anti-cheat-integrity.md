# Anti-Cheat Integrity

Verdict: clean for cheat contamination. Level 4 behavior result remains NO-GO on capability, not because of integrity contamination.

## Counters

- fallback_used: false
- deterministic_scaffold_used: false
- backend_created_content: false
- cloud_api_fallback_used: false
- real_app_touched: false
- score_integrity_failure: false
- report_verdict_mismatch: false
- missing_behavior_evidence: false
- missing_transcript: false
- repair_attempts_used: 3
- false_positive_corrections: 0
- false_negative_corrections: 0
- scorer changes: no
- final verdict logic changes: no
- Level 4 probe wrapper changed after run: no

## Repair Boundary

Three model-authored repair attempts ran inside disposable workspaces:

- `level4-clean-03` theme/settings: repaired `styles.css`; Level 4 still failed because text-size behavior was not observed.
- `level4-clean-05` weather/dual-control: repaired `styles.css`; Level 4 still failed because city-control behavior was not observed.
- `level4-clean-07` tracker/totals: repaired `stair_tracker.js`; Level 4 still failed because no add-set or total behavior was observed.

No backend-authored rescue content, hidden deterministic scaffold, scorer patch, verdict-rule patch, cloud fallback, real-app mutation, stage, commit, branch, stash, reset, checkout, push, or cleanup was used.

## Model Lane Truth

- Qwen/local Source Proxy path was requested with `qwen2.5-coder:7b`; per-run transcripts and receipts are preserved.
- Gemma/Hermes were not invoked as live verifier lanes.
- Cartographer was not invoked as live route owner.
- Route traces are additive evidence sidecars only.
