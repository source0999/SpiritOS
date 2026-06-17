# Claude 3x10 Basic Coding Battery — Closeout

Date: 2026-06-15/16 (UTC)
Runtime: source-server, real integrated path (FIP-1..5 enabled, confirmed in preflight).
Total wall time: ~2h25m across 30 rows + 1 smoke row (190-360s/row; 3 local models contend for VRAM).

## Headline

- 30/30 prompts posted to the REAL `/v1/decisions/prompt-packet` hot path.
- 30/30 durable FIP-0 receipts; 30/30 FIP-6 traces; 30/30 trace verdict == receipt verdict.
- 22 `productive_go`; 8 `verifier_blocked_browser`. Zero hard-fails.
- 0 unexpected_no_go, 0 config_blocked, 0 trace_mismatch, 0 hardcoded_used, 0 preview_only_go, 0 productive_go_integrity_fail, 0 coding_failure, 0 repair_failure.
- 30/30 changed files strictly inside the disposable target root. No protected-path touch.
- Scout skipped 30/30; SearXNG skipped 30/30 (honest — no current-info requested). No false `used`.

## Score classes (deduped by prompt_id)

```json
{"productive_go": 22, "verifier_blocked_browser": 8, "total": 30, "hard_fail_rows": []}
```

## What "productive_go" actually means here (critical caveat)

`productive_go` was awarded when: verdict `GO: fip5_required_verifier_and_repair_complete`,
qwen `used`, `final_coder_packet_hash == coder_received_packet_hash`, deterministic verifier
`used/passed`, Hermes verifier present, FIP-5 result present, changed files inside target root,
no hardcoded/trial markers. ALL 22 met this.

BUT the deterministic verifier checks only STRUCTURE (file written, hash match, allowed path,
diff present, protected not touched). It runs no tests and, for non-`.html` files, no behavior
probe. Spot inspection (`s1-02-calculator`) shows the produced "calculator" is a non-functional
React stub: `<h1>Calculator</h1>` + `{/* Add your calculator components here */}`. So
`productive_go` = "Qwen produced a structurally valid file in the allowed path and Hermes
rubber-stamped it", NOT "the app works." Functional correctness is unverified across all 22.

## Why all 8 `.html` rows are `verifier_blocked_browser`

The runner deliberately did NOT send `expected_result_state=browser_pass_expected` (that flag
fabricates a browser pass). For browser-relevant targets the FIP-5 browser probe reported
`passed=False` (no real browser exists), so the verdict is
`NO-GO: fip5_browser_behavior_authority_blocks_pass` and Hermes returned FAIL/NEEDS_FIX — it
did NOT fake a PASS. This is honest behavior and confirms the synthetic-browser pass seen in
Level 5R2 is realized ONLY when a runner feeds the flag.

## Generalization (Set 1 vs 2 vs 3)

Same task family across different wording produced identical score classes every time
(timer/calc/crud/data/api -> productive; scaffold/landing-page -> verifier_blocked). Outcome is
fully determined by task shape (file extension / browser relevance), not by prompt wording.
No prompt-fitting, no hardcoded path triggered.

## Lane truth observed

- Qwen coder: `used` 30/30. Hash discipline perfect (final==received 30/30).
- Gemma advisory: `used` on most, `failed` (ReadTimeout/schema) on ~6 rows including productive
  GOs `s2-02-counter`, `s2-10-health`. Failure recorded in `model_errors` but did NOT gate GO.
- Hermes critic: `used` on most, `failed` on `s3-04-tasks` (productive GO). Non-blocking.
- Hermes verifier: PASS for productive, FAIL/NEEDS_FIX for `.html`. No fake UI PASS.
- Deterministic: passed 30/30 (structural).
- Browser: skipped (passed) for non-`.html`; failed for `.html` (no real browser).
- Repair loop: 0 attempts across all 30 (never organically triggered by honest prompts).
- Scout/SearXNG: skipped 30/30 (honest). Cartographer/Obsidian/Design/Mac-worker: advisory,
  read-only (see search-context-audit.md).

## Trace integrity + leakage

- 30/30 traces match receipts; trace_authority `operational_receipt_projection_no_private_reasoning`.
- HOWEVER `operator_trace.coder_trace.qwen.parser_result.raw_output_excerpt` embeds ~800 chars of
  raw Qwen model output. The "no private reasoning" projection still surfaces raw coder output.

## Fixes applied

- None to the proxy. See `fixes/00-fixes-and-observations.md`.

## Concurrent unrelated activity during the run

- A repomix -> `npm run context:compress` migration modified `source_proxy/tasks/long_running.py`,
  `package.json`, `package-lock.json`, `README.md`, `scripts/source-context-compress.mjs` at
  ~00:00 UTC. NOT caused by the battery. Proxy not restarted -> on-disk/in-memory drift. Not touched.

## Evidence

- Matrix: `battery-matrix.json`; raw: `battery-raw.json`; results: `battery-results.json`;
  console: `battery-console.log`; receipts: `receipts/`; traces: `traces/`; per-set closeouts:
  `set-1-closeout.md`, `set-2-closeout.md`, `set-3-closeout.md`; reports: `reports/`.
