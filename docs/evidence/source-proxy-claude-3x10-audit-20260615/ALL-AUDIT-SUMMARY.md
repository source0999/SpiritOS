# Claude 3x10 Audit — Executive Summary for LLM Context

## Verdict: C (high confidence)

SpiritOS Source Proxy ran 30 messy human prompts on the REAL integrated hot path
(`/v1/decisions/prompt-packet`, FIP-1..5 enabled). Results: 22 productive_go, 8 verifier_blocked_browser, zero hard-fails.

## What worked (proven)
- Real Qwen coder path with perfect packet-hash discipline (30/30)
- Durable FIP-0 receipts + matching FIP-6 traces (30/30)
- Perfect scope containment to disposable target root (30/30)
- Scout/SearXNG honestly skipped (no false `used`)
- UI rows honestly NO-GO when no harness flag (no fake browser PASS)
- No hardcoded/trial/scaffold path triggered in battery
- Protected paths strong; no traversal or secret touch

## What failed (proven)
- productive_go means structural validity only — NOT working apps (calculator stub example)
- No real browser automation — synthetic probe only
- Hermes PASS on non-UI rows is low-evidence rubber-stamp
- Gemma/Hermes-critic timeouts do NOT gate GO (decorative lanes)
- Repair loop never fired organically (0/30)
- FIP-6 traces embed raw Qwen output (leakage)
- Prompt-fitted code exists in decision.py (dormant in battery, live liability)
- FIP-4 defaults OFF — legacy stub path is default without env flags

## Generalization
Sets 1/2/3 reworded same families → identical score classes. Shape-driven, not prompt-fitted.

## Files in this audit
- Runner: scripts/source_proxy_claude_3x10_battery_runner.py
- Evidence: docs/evidence/source-proxy-claude-3x10-audit-20260615/
- Reports: reports/full-proxy-audit.md + 6 specialized audits + pivot plan

---

## Source: battery-closeout.md

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


---

## Source: claude-3x10-audit-mini-context-pack.md

# Claude 3x10 Audit Mini Context Pack Manifest

Context pack:

- Master XML: `docs/evidence/source-proxy-claude-3x10-audit-20260615/claude-3x10-audit-mini-context-pack.xml`
- Split packs: `docs/evidence/source-proxy-claude-3x10-audit-20260615/llm-context/` (pack-01..06)
- Consolidated MD: `docs/evidence/source-proxy-claude-3x10-audit-20260615/ALL-AUDIT-SUMMARY.md`
- Index: `docs/evidence/source-proxy-claude-3x10-audit-20260615/index.md`
- This manifest: `docs/evidence/source-proxy-claude-3x10-audit-20260615/claude-3x10-audit-mini-context-pack.md`

## Scope

PLAN: Claude 3x10 Basic Coding Battery Audit
PHASE: Live diagnostic execution + evidence-based audit
VERDICT: C (high confidence)

## Battery summary

| Metric | Value |
| --- | --- |
| Total prompts | 30 |
| productive_go | 22 |
| verifier_blocked_browser | 8 |
| unexpected_no_go | 0 |
| trace_mismatch | 0 |
| hardcoded_used | 0 |
| Receipts + traces | 30/30 |
| Proxy code patched | NONE |

## Hard stops honored

- Did not commit, push, or stage.
- Did not add TinyFish or xersearch.
- Did not promote Cartographer to route owner.
- Did not use `expected_result_state=browser_pass_expected` (no synthetic browser cheat).
- Did not mutate unrelated SpiritFlix/media work.

## Changed files (audit artifacts only)

- `scripts/source_proxy_claude_3x10_battery_runner.py` (additive runner)
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/**` (evidence tree)

## Top 10 urgent fixes

1. Real headless browser verifier (replace synthetic probe)
2. Functional verification for non-UI code
3. Quarantine prompt-fitted/scaffold code in decision.py
4. FIP-4 default-ON + preflight assert
5. Gate degraded advisory lanes on verdict
6. Strip raw model output from FIP-6 traces
7. Auth-gate receipt/trace endpoints
8. Structured productive/coder_path receipt fields
9. Collision-proof run_id + archive stale receipts
10. Runtime discipline (no stale on-disk vs in-memory proxy)

## Recommended next gate

```
BRITTON GO SOURCE PROXY HONESTY-HARDENING PLAN PR1 — IMPLEMENTATION (PHASE A ONLY)
```

See `reports/pivot-remediation-plan.md` for full plan.


---

## Source: fixes/00-fixes-and-observations.md

# Fixes and Observations — Claude 3x10 Battery

## Fixes applied to Source Proxy

NONE. The battery exposed no blocker that required patching `source_proxy` or `src`.
The only authored artifact is the additive runner `scripts/source_proxy_claude_3x10_battery_runner.py`
plus disposable evidence under `docs/evidence/source-proxy-claude-3x10-audit-20260615/`.

The one design accommodation (not a proxy fix): the runner pre-seeds each disposable
target file with a placeholder before posting, because the proxy never creates files
(FIP-4 emits a proposed diff only) and a missing target under a non-`agent-lab` path
hits the `target_missing` gate. Pre-seeding lets the row exercise the real FIP-4
`replace_file` path. This mirrors how Level 5R2 used pre-seeded `level-5-targets/*.txt`.

## Observation O1 — concurrent unrelated repo activity during the run (NOT caused by battery)

During Set 2 (~2026-06-16 00:00 UTC) these tracked files changed on disk:

- `source_proxy/tasks/long_running.py` (repomix -> `npm run context:compress` migration)
- `package.json`, `package-lock.json` (new `context:compress` script + deps)
- `README.md`, `scripts/source-context-compress.mjs`

Evidence this was NOT the battery:
- Every one of the 30 battery rows had `diff_summary.changed_files` strictly inside
  `docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/` (verified across all receipts).
- The proxy never applies coder diffs (FIP-4 produces `proposed_diff` only; no `write_text`
  of coder output exists in `decision.py`).
- The change is a coherent feature migration unrelated to any battery prompt.
- File mtimes cluster at 23:59-00:02 UTC, consistent with a human/agent multi-file edit.

Action taken: NONE. Per boundaries, I did not stage, commit, revert, or modify this
unrelated work. Recorded as a runtime-hygiene risk: the live proxy (pid 1632339) was
NOT restarted after these edits, so it keeps serving the previously loaded code while
the on-disk source diverges. This is the same staleness class as the documented
"Windows Z:\ edits not live until restart" warning, now observed live on Linux.

This does not affect battery integrity: the running proxy used its loaded code for all
30 rows, every row produced a durable receipt + matching FIP-6 trace.


---

## Source: preflight.md

# Claude 3x10 Basic Coding Battery — Preflight

Date: 2026-06-15
Host: source-server
Checkout: /home/source/SpiritOS
Operator: Claude Opus Max (one-shot diagnostic)

## Runtime state

- Branch: `master`
- HEAD: `fdb82b8d docs: refresh mobile overlap evidence image`
- Git tree: DIRTY (pre-existing). Audit-relevant: `docs/evidence/source-proxy-full-integration-pivot/active-context.md` (M), untracked `docs/evidence/source-proxy-integrated-level-6-stress-soak-plan-20260615/`. Remainder is unrelated SpiritFlix/media work. Not touched.
- Source Proxy: one uvicorn `source_proxy.main:app` on `0.0.0.0:8787` (pid 1632339), tmux `source-proxy-lan`.

## Integrated env confirmed in the live proxy process

```
SOURCE_PROXY_FIP1_CONTEXT_ENABLED=1
SOURCE_PROXY_FIP2_RESEARCH_ENABLED=1
SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED=1
SOURCE_PROXY_FIP4_QWEN_CODER_ENABLED=1
SOURCE_PROXY_FIP4_ALLOW_FIP5_CHAIN=1
SOURCE_PROXY_FIP5_VERIFIER_ENABLED=1
SOURCE_PROXY_FIP3_HERMES_MODEL=hermes3:8b-abliterated
SOURCE_PROXY_FIP5_HERMES_VERIFIER_MODEL=hermes3:8b-abliterated
SOURCE_PROXY_FIP4_QWEN_TIMEOUT_SECONDS=300
SOURCE_PROXY_FIP4_QWEN_MAX_ATTEMPTS=3
SEARXNG_URL=http://127.0.0.1:8080
SEARXNG_TIMEOUT_MS=30000
SOURCE_PROXY_SCOUT_RESEARCH_ENABLED=1
SOURCE_PROXY_SCOUT_RESEARCH_URL=http://127.0.0.1:8077
SOURCE_PROXY_SCOUT_RESEARCH_TIMEOUT_MS=5000
```

This proves the battery exercises the REAL integrated FIP-4 (Qwen coder) + FIP-5 (deterministic + browser + Hermes verifier + bounded repair) path, not the legacy stub/foundation path.

## Ollama models present

- `qwen2.5-coder:7b` (coder lane)
- `gemma3n:e4b` (pre-coder advisory/spec)
- `hermes3:8b-abliterated` (critic + verifier)
- `hermes4:latest`, `hf.co/...Hermes-4-14B...`, `llama3.1:8b`, others

## Endpoint checks

- `GET /v1/decisions/fip0-receipts/latest` -> HTTP 200, run `fip0-2aa8cc99f2fc1657`, verdict `GO: fip5_required_verifier_and_repair_complete`
- `GET /v1/decisions/fip0-receipts/latest/trace` -> HTTP 200, same run/verdict, trace_version `fip6.operator_trace.v1`, authority `operational_receipt_projection_no_private_reasoning`
- Latest trace matches latest receipt.

## Honesty controls for this battery (deliberate, per no-preview-only policy)

- The runner does NOT send `expected_result_state=browser_pass_expected`. Forcing the synthetic browser pass would be the exact cheat under audit.
- The runner does NOT send `trial_recover_already_satisfied`. That can route to hardcoded already-satisfied payloads.
- UI/page prompts target `.html` (browser-relevant) and are EXPECTED to be `verifier_blocked` (no real browser exists), surfacing the synthetic-browser limitation honestly rather than hiding it.
- Logic/app prompts target `.js`; API prompts target `.ts` (not browser-relevant) so they can reach a genuine `GO: fip5_...` via Qwen + deterministic + Hermes.
- Strict scoring: a coding row counts as `productive_go` ONLY if the verdict is a real `GO: fip5_...` with qwen used, hash match, deterministic present, Hermes verifier present, protected path intact, changed files inside the disposable target root, and no hardcoded/trial/dummy reason code.

## Preflight verdict

GO for battery execution. Runtime, models, endpoints, and integrated env are all confirmed.


---

## Source: receipts-traces-manifest.md

# Receipt and trace file manifest

- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-01-homepage-fip0-1eec7a9947f1adc7.json` — fip0-1eec7a9947f1adc7 | NO-GO: fip5_browser_behavior_authority_blocks_pass | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-02-calculator-fip0-79f9465ffdb78ce5.json` — fip0-79f9465ffdb78ce5 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-02-calculator-fip0-eac2265c372e1abf.json` — fip0-eac2265c372e1abf | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-03-weather-fip0-06c467768241e206.json` — fip0-06c467768241e206 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-04-todo-fip0-355a38f1e76f19c1.json` — fip0-355a38f1e76f19c1 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-05-timer-fip0-1a62da032a749280.json` — fip0-1a62da032a749280 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-06-notes-fip0-74dad2831a84988b.json` — fip0-74dad2831a84988b | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-07-expense-fip0-654d4decd915a0ed.json` — fip0-654d4decd915a0ed | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-08-chart-fip0-51b5015873158f25.json` — fip0-51b5015873158f25 | NO-GO: fip5_browser_behavior_authority_blocks_pass | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-09-signup-fip0-d98ee0e0c4bb9321.json` — fip0-d98ee0e0c4bb9321 | NO-GO: fip5_browser_behavior_authority_blocks_pass | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s1-10-status-fip0-71f6e247806fd990.json` — fip0-71f6e247806fd990 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-01-dashboard-fip0-ea3e7880a26ac314.json` — fip0-ea3e7880a26ac314 | NO-GO: fip5_browser_behavior_authority_blocks_pass | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-02-counter-fip0-a6143b17b984d2d8.json` — fip0-a6143b17b984d2d8 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-03-moon-fip0-e34a3d0a8062d303.json` — fip0-e34a3d0a8062d303 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-04-checklist-fip0-354ebaebce45fe93.json` — fip0-354ebaebce45fe93 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-05-stopwatch-fip0-1f18517e2913bfbe.json` — fip0-1f18517e2913bfbe | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-06-sticky-fip0-e7322753784ccc94.json` — fip0-e7322753784ccc94 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-07-tip-fip0-5a587d92043eac9a.json` — fip0-5a587d92043eac9a | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-08-stats-fip0-014219a32a991956.json` — fip0-014219a32a991956 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-09-waitlist-fip0-72703023e1baf325.json` — fip0-72703023e1baf325 | NO-GO: fip5_browser_behavior_authority_blocks_pass | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s2-10-health-fip0-a68f4bd6733e9802.json` — fip0-a68f4bd6733e9802 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-01-shell-fip0-066ce708618daf5a.json` — fip0-066ce708618daf5a | NO-GO: fip5_browser_behavior_authority_blocks_pass | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-02-cruncher-fip0-a565105403c15af6.json` — fip0-a565105403c15af6 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-03-forecast-fip0-27117aaf7de08e03.json` — fip0-27117aaf7de08e03 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-04-tasks-fip0-4646b80acc215bf9.json` — fip0-4646b80acc215bf9 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-05-countdown-fip0-b5bd920a839de50c.json` — fip0-b5bd920a839de50c | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-06-journal-fip0-310f30b2f8eaf283.json` — fip0-310f30b2f8eaf283 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-07-budget-fip0-2270b890036bdaa2.json` — fip0-2270b890036bdaa2 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-08-progress-fip0-05099eeabba5a4b3.json` — fip0-05099eeabba5a4b3 | NO-GO: fip5_browser_behavior_authority_blocks_pass | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-09-coming-soon-fip0-f77106706ee79edd.json` — fip0-f77106706ee79edd | NO-GO: fip5_browser_behavior_authority_blocks_pass | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/receipts/s3-10-alive-fip0-732c7633e8591c87.json` — fip0-732c7633e8591c87 | GO: fip5_required_verifier_and_repair_complete | qwen=used
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-01-homepage-fip0-1eec7a9947f1adc7.json` — s1-01-homepage-fip0-1eec7a9947f1adc7 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-02-calculator-fip0-79f9465ffdb78ce5.json` — s1-02-calculator-fip0-79f9465ffdb78ce5 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-02-calculator-fip0-eac2265c372e1abf.json` — s1-02-calculator-fip0-eac2265c372e1abf |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-03-weather-fip0-06c467768241e206.json` — s1-03-weather-fip0-06c467768241e206 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-04-todo-fip0-355a38f1e76f19c1.json` — s1-04-todo-fip0-355a38f1e76f19c1 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-05-timer-fip0-1a62da032a749280.json` — s1-05-timer-fip0-1a62da032a749280 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-06-notes-fip0-74dad2831a84988b.json` — s1-06-notes-fip0-74dad2831a84988b |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-07-expense-fip0-654d4decd915a0ed.json` — s1-07-expense-fip0-654d4decd915a0ed |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-08-chart-fip0-51b5015873158f25.json` — s1-08-chart-fip0-51b5015873158f25 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-09-signup-fip0-d98ee0e0c4bb9321.json` — s1-09-signup-fip0-d98ee0e0c4bb9321 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s1-10-status-fip0-71f6e247806fd990.json` — s1-10-status-fip0-71f6e247806fd990 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-01-dashboard-fip0-ea3e7880a26ac314.json` — s2-01-dashboard-fip0-ea3e7880a26ac314 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-02-counter-fip0-a6143b17b984d2d8.json` — s2-02-counter-fip0-a6143b17b984d2d8 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-03-moon-fip0-e34a3d0a8062d303.json` — s2-03-moon-fip0-e34a3d0a8062d303 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-04-checklist-fip0-354ebaebce45fe93.json` — s2-04-checklist-fip0-354ebaebce45fe93 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-05-stopwatch-fip0-1f18517e2913bfbe.json` — s2-05-stopwatch-fip0-1f18517e2913bfbe |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-06-sticky-fip0-e7322753784ccc94.json` — s2-06-sticky-fip0-e7322753784ccc94 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-07-tip-fip0-5a587d92043eac9a.json` — s2-07-tip-fip0-5a587d92043eac9a |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-08-stats-fip0-014219a32a991956.json` — s2-08-stats-fip0-014219a32a991956 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-09-waitlist-fip0-72703023e1baf325.json` — s2-09-waitlist-fip0-72703023e1baf325 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s2-10-health-fip0-a68f4bd6733e9802.json` — s2-10-health-fip0-a68f4bd6733e9802 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-01-shell-fip0-066ce708618daf5a.json` — s3-01-shell-fip0-066ce708618daf5a |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-02-cruncher-fip0-a565105403c15af6.json` — s3-02-cruncher-fip0-a565105403c15af6 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-03-forecast-fip0-27117aaf7de08e03.json` — s3-03-forecast-fip0-27117aaf7de08e03 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-04-tasks-fip0-4646b80acc215bf9.json` — s3-04-tasks-fip0-4646b80acc215bf9 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-05-countdown-fip0-b5bd920a839de50c.json` — s3-05-countdown-fip0-b5bd920a839de50c |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-06-journal-fip0-310f30b2f8eaf283.json` — s3-06-journal-fip0-310f30b2f8eaf283 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-07-budget-fip0-2270b890036bdaa2.json` — s3-07-budget-fip0-2270b890036bdaa2 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-08-progress-fip0-05099eeabba5a4b3.json` — s3-08-progress-fip0-05099eeabba5a4b3 |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-09-coming-soon-fip0-f77106706ee79edd.json` — s3-09-coming-soon-fip0-f77106706ee79edd |
- `docs/evidence/source-proxy-claude-3x10-audit-20260615/traces/s3-10-alive-fip0-732c7633e8591c87.json` — s3-10-alive-fip0-732c7633e8591c87 |


---

## Source: reports/anti-cheat-security-audit.md

# Anti-Cheat & Security Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery + source inspection + runtime receipts.

## Anti-cheat: battery behavior (runtime)

| Check | Result | Evidence |
|---|---|---|
| Hardcoded prompt-specific payload as success | NOT triggered | 0 `hardcoded_used`; no `coder_no_changes_needed`/`deterministic_agent_trials_ui_test_preview`/trial bundles in any of 30 receipts |
| Preview-only/read-only lane counted as integration | No | Productive GO required FIP-5 result + qwen used + deterministic; context lanes are read-only and not counted as coder success |
| Old artifact-only path as scoring authority | No | All 22 GOs are `GO: fip5_...`; 0 `preview_only_go` (foundation/fip3) accepted |
| Qwen used for planning/verification | No | Qwen role = coder; planning=Gemma, critique=Hermes-critic, verify=Hermes-verifier (separate functions) |
| Hermes verifier acting as pre-coder critic | No | Distinct lanes; verifier is post-code only |
| Gemma/Hermes failure hidden behind GO | Recorded but NON-GATING | `s2-10-health` gemma `failed (ReadTimeout)` -> still `GO: fip5`; visible in `model_errors`, not hidden, but does not downgrade verdict |
| SearXNG/Scout `used` without provider evidence | No | Scout/SearXNG `skipped` 30/30 (no current-info requested); receipt has guard forcing `used`->`failed` without a provider call |
| Trace diverges from receipt | No | 30/30 trace verdict == receipt verdict |
| Protected path touched | No | 30/30 changed files inside disposable root |
| Malformed Qwen output applied | No | Output contract validated; proxy never applies diffs |
| Private hidden reasoning displayed | PARTIAL | operator_trace embeds raw Qwen output excerpt (see receipt-trace-audit.md) |
| Hidden commit/push/stage/apply/worker | No | `anti_tailoring_status` false 30/30; only receipt JSON written |

## Anti-cheat: codebase liabilities (source, dormant in this run)

- `source_proxy/api/decision.py::_product_trial_feature_already_satisfied_payload` (~L3449):
  matches exact target paths (`visible-result-badge.ts`, `reversible-trial-prompts.ts`,
  `CodingCockpitShell.tsx`) + task phrases + file-content substrings to return a synthetic
  "already satisfied" no-op. Prompt-fitted. Reachable when `trial_recover_already_satisfied`
  is sent or via the legacy path.
- `_agent_trials_ui_test_coder_diff_payload` (~L4732): inserts a LITERAL hardcoded test diff
  for a specific prompt phrase + anchor, "generated without model execution".
- `_dummy_*`/`_realistic_reversible_*` builders in `_bounded_coder_diff_or_stub` (~L3326):
  canned payloads served when FIP-4 is DISABLED (default). `_fip4_qwen_enabled()` defaults OFF,
  so a proxy started without env flags serves these.
- VERDICT: these did not fire in the battery (disposable targets, no flags, FIP-4 on), but they
  are live prompt-fitted/scaffold code in the production module and must be quarantined.

## Security / vulnerability

| Area | Posture | Evidence |
|---|---|---|
| Protected paths | STRONG | `safety/paths.py`: blocks `..`, absolute/drive/UNC, `%`-encoding, dotfiles, secret markers (.env/.pem/.key/secret/token/credential/id_rsa) |
| Path traversal | DEFENDED | Above + exact-match allowlist `_fip4_path_allowed`; 30/30 in-scope |
| Secrets | REDACTED in context | `_safe_excerpt`/`_safe_context_excerpt` redact emails, sk- tokens, key/token/password assignments; Obsidian excludes private/**, secrets/** |
| .env / certs / keys / source_proxy/data | NOT touched | battery never targeted them; secret-shape block proven in prior env-trap receipt |
| Local network services | local-only | Ollama 11434, SearXNG 8080, Scout 8077; no cloud |
| Auth boundary | WEAK | `/v1/decisions/fip0-receipts/{latest,run_id,trace}` are unauthenticated and linked from `/coding`; expose raw_prompt + raw model output excerpts |
| Shell execution | BOUNDED | Only `git status --short` (fixed args, 5s); plus `_ensure_fresh_repomix` runs `npx repomix`/`npm run` with fixed args, no user interpolation |
| Model-output injection | BOUNDED | Strict parse; diffs rejected; output NOT applied |
| Search/context injection | MEDIUM (latent) | Local search/Scout snippets feed the coder packet; inert today because output is unapplied; add canary tests before any apply stage |
| Trace leakage | MEDIUM | raw Qwen output excerpt in operator_trace; raw prompt in receipts |
| Stale/reused workspace | OBSERVED | concurrent on-disk edits to `long_running.py`/`package.json`/etc. mid-run without proxy restart |

## Top anti-cheat/security fixes

1. Quarantine `_product_trial_feature_already_satisfied_payload`, `_agent_trials_ui_test_coder_diff_payload`,
   `_dummy_*`/`_realistic_*` behind a test-only flag; `/coding` must refuse them.
2. Add a structured `coder_path` field (`fip4_real|legacy_stub|trial`) + `productive: bool` so
   no legacy/scaffold path can be read as productive.
3. Strip raw model output from FIP-6 operator_trace; auth-gate receipt/trace endpoints.
4. Preflight must assert FIP-4/5 enabled (default-off means default = scaffold path).


---

## Source: reports/full-proxy-audit.md

# Full Proxy Audit — SpiritOS Source Proxy (evidence-based)

Date: 2026-06-16 (UTC). Basis: live 3x10 battery (30 rows) on the real integrated path
(FIP-1..5 enabled), durable receipts, FIP-6 traces, source inspection, runtime proof.

## 1. Executive verdict

Grade: C (confidence: high).

The integrated pipeline is REAL, SAFE, and HONESTLY RECEIPTED, but it does not verify
functional correctness and overstates capability with `productive_go`. Proven strengths:
the real `/coding -> /v1/decisions/prompt-packet` hot path executed all 30 rows; Qwen coded
with perfect packet-hash discipline (final==received 30/30); durable receipts + matching
FIP-6 traces 30/30; perfect target-scope containment 30/30; Scout/SearXNG honestly skipped
30/30; the synthetic browser verifier honestly REFUSED to pass UI when not fed the harness
flag (8/8 `.html` rows NO-GO, no fake PASS). Proven weaknesses: `productive_go` is structural
only (a non-functional calculator stub passed); no real browser verification exists; advisory
lanes (Gemma/Hermes-critic) timed out on several rows yet did not gate GO; FIP-6 traces embed
raw Qwen output; the bounded repair loop was never organically exercised.

## 2. Can SpiritOS handle the 3x10 basic coding battery?

Partially, and honestly. It PRODUCED code and honestly receipted 22/30 rows, and honestly
blocked 8/30 UI rows it cannot verify. But NONE of the 22 productive rows were verified to
actually work, and inspection shows non-functional scaffolds. As a "coding system that easily
handles basic tasks", it is a reliable, safe, well-instrumented PIPELINE wrapped around a weak
7B coder whose output is not functionally checked. It does not yet deliver working apps.

## 3. Prompt-by-prompt results

22 productive_go (all non-`.html`): s1-02,03,04,05,06,07,10; s2-02,03,04,05,06,07,08,10;
s3-02,03,04,05,06,07,10. 8 verifier_blocked_browser (all `.html`): s1-01,08,09; s2-01,09;
s3-01,08,09. Every productive row: GO: fip5, qwen used, hash match, deterministic pass,
Hermes PASS, repair 0, trace==receipt. Every blocked row: NO-GO browser authority, Hermes
FAIL/NEEDS_FIX (no fake PASS). Full matrix in `../battery-results.json`.

## 4. Set-by-set generalization

Sets 1/2/3 reword the same families. Score class was identical within each family across all
three sets (e.g., calculator==tip==budget==number-cruncher all productive; signup==waitlist==
coming-soon all verifier_blocked). Outcome tracks task shape, not wording.

## 5. Similar prompts -> similar correct outcomes without prompt-fitting?

Yes. No hardcoded/trial/dummy path was triggered for any of the 30 rows (verified: 0
`hardcoded_used`, no benchmark-fitted reason codes, no scaffold bundles). The behavior is
shape-driven and consistent, which is the anti-prompt-fitting evidence Britton asked for.

## 6. Failures and buckets

- verifier_blocked_browser: 8 (expected; UI cannot be verified without a real browser).
- coding_failure / output_contract: 0. repair_failure: 0. config_blocked: 0.
- unexpected_no_go: 0. trace_mismatch: 0. hardcoded_used: 0. preview_only_go: 0.
- Degraded advisory lanes (non-fatal, non-gating): Gemma failed ~6 rows, Hermes-critic 1 row.

## 7. Hardcoded/scaffolded behavior evidence

In the BATTERY: none triggered. In the CODEBASE (source inspection): present and dormant.
`source_proxy/api/decision.py` contains prompt-fitted builders
(`_product_trial_feature_already_satisfied_payload`, `_agent_trials_ui_test_coder_diff_payload`)
that match exact target paths/phrases/file-content to emit no-ops or a literal hardcoded diff
"without model execution". They are reachable on the legacy path (FIP-4 disabled) and via
`trial_recover_already_satisfied`. The battery avoided them (disposable targets, no flags), so
they did not fire — but they remain a live liability. See `anti-cheat-security-audit.md`.

## 8. Preview-only/read-only lane counted as integrated?

No false counting observed in the battery. Context lanes (Cartographer/Obsidian/Design/Mac
worker) are READ_ONLY by contract and were not counted as coder success. However, advisory
lane FAILURE (Gemma timeout) did not change the GO, so those lanes are effectively decorative
for acceptance — integrated in plumbing, not in authority.

## 9. Hidden fallback evidence

None. No qwen-precoder fallback, no cloud fallback, no TinyFish, no xersearch. The proxy never
applied a diff. `anti_tailoring_status` recorded hidden_apply/commit/push/worker = false 30/30.

## 10. Fake PASS evidence

None hidden. For UI rows the system refused to pass (Hermes FAIL/NEEDS_FIX). For non-UI rows
Hermes PASS is a low-evidence rubber-stamp (no functional check), but it is not a hidden fake —
the receipt shows exactly what was (not) checked.

## 11. Synthetic browser verifier overclaim evidence

Confirmed at the source and at runtime. There is NO browser automation in the repo. The probe
returns synthetic `passed=True` only when fed `expected_result_state=browser_pass_expected`.
The battery did not feed it, so all 8 UI rows correctly failed. The OVERCLAIM lives in the
Level 5R2 closeout prose ("browser behavior passed"), which describes a fabricated probe.

## 12. Protected-path weakness evidence

None found; strong. `source_proxy/safety/paths.py` blocks `..`, absolute/drive/UNC paths,
`%`-encoding, dotfiles, and secret markers. The exact-match allowlist (`_fip4_path_allowed`)
further constrains. All 30 battery changed-files were inside the disposable root.

## 13. Receipt/trace mismatch evidence

None. 30/30 trace verdict == receipt verdict. (Leakage is a separate issue, item 14 /
`receipt-trace-audit.md`.)

## 14. Lane truth overclaim evidence

No false `used`. Scout/SearXNG honestly `skipped` 30/30. The real lane-truth gap is the
opposite: advisory lane FAILURES (Gemma/Hermes-critic) are recorded but do NOT gate GO, so a
degraded context lane disappears behind a productive verdict.

## 15. Model-role audit

See `model-lane-audit.md`. Roles are correctly separated (Qwen code-only; Gemma/Hermes-critic
pre-coder advisory; Hermes verifier post-code). Qwen never planned/verified; verifier never
acted as critic. Gemma/critic instability under VRAM contention is the main issue.

## 16. Subagent/node audit

See `search-context-audit.md`. Cartographer advisory (read-only, real repo map). Obsidian/
Design present but typically skipped. Mac worker is a hardcoded `skipped` stub. Scout/SearXNG
honest but unexercised (no current-info prompts).

## 17. Security/vulnerability audit

See `anti-cheat-security-audit.md`. Strong path safety, no hidden apply, local-only providers.
Main risks: unauthenticated receipt/trace endpoints (publicly linked from `/coding`) that
expose raw prompts + raw model output excerpts; prompt-fitted code in production.

## 18. Bottlenecks

- Model reliability: 190-360s/row; Gemma ReadTimeouts under 3-model VRAM contention.
- Verifier quality: structural-only; no real browser; no functional/test execution.
- Coder quality: 7B emits plausible non-functional scaffolds; ignores file-type intent (JSX in .js).
- Trace hygiene: raw model output embedded in operator_trace.
- Runtime/staging: live source edited mid-run without proxy restart (on-disk/in-memory drift).

## 19. What must be fixed before "Level 10"

1. Real headless-browser behavior verification (replace the synthetic probe).
2. Functional verification for non-UI code (run generated tests / behavior probes) so
   `productive_go` means "works", not "file written".
3. Make advisory-lane degradation gate or explicitly downgrade the verdict (no silent
   decorative lanes).
4. Quarantine prompt-fitted/dummy/trial code out of the production hot path.
5. Strip raw model output from FIP-6 operator traces; enforce the "no private reasoning" claim
   with a content scanner, not a constant boolean.

## 20. What must be fixed before daily-driver use

1. Coder quality/capability (stronger or better-prompted coder; output that fulfills intent).
2. Throughput (sub-60s rows; resolve VRAM contention / model warm-keeping).
3. Auth on receipt/trace endpoints; stop leaking raw prompts/outputs to a public link.
4. Runtime discipline: never serve a proxy whose on-disk source has drifted; auto-restart or
   refuse with a staleness banner.
5. Stronger scoring that distinguishes "produced" from "verified working", surfaced in the UI.


---

## Source: reports/model-lane-audit.md

# Model-Lane Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery receipts + source inspection.

## Qwen (coder/action only)

- Role correct: `used` 30/30; produced `replace_file` actions; never planned or verified.
- Hash discipline PERFECT: `final_coder_packet_hash == coder_received_packet_hash` 30/30.
- Output contract: strict (`_fip4_extract_qwen_file_action` rejects diffs/markdown; accepts
  `<file>` or JSON `replace_file`). 0 output-contract failures in the battery.
- Quality concern: emits plausible-but-non-functional scaffolds and ignores file-type intent
  (React/JSX written into plain `.js` targets). `s1-02-calculator` content = `<h1>Calculator</h1>`
  + "Add your calculator components here". No arithmetic. Still GO.
- Latency: ~190-360s/row including cold loads and contention.

## Gemma (pre-coder advisory/spec/context)

- Role correct: live Ollama JSON call; rejects any `qwen` model (anti-fallback in source).
- Stability ISSUE: `failed` on ~6 rows via `local_ollama_model_timeout` (ReadTimeout) under
  3-model VRAM contention; e.g., `s2-10-health` gemma `failed` yet productive GO.
- AUTHORITY GAP: Gemma failure does NOT gate or downgrade the FIP-5 verdict. The pre-coder
  spec lane can die and the row still passes -> the "context packet" is decorative for acceptance.

## Hermes critic (pre-coder critique/risk)

- Role correct: live call; distinct from verifier; rejects `qwen`.
- `failed` on `s3-04-tasks` (productive GO) -> same non-gating gap as Gemma.

## Hermes verifier (post-code verifier)

- Role correct: post-code only; cannot turn UNVERIFIED->PASS; cannot override deterministic or
  browser (`_fip5_normalize_hermes_verifier_output` downgrades PASS on det/browser failure —
  proven: 8/8 `.html` rows Hermes returned FAIL/NEEDS_FIX, never PASS).
- Evidence-quality concern: for non-`.html` rows there is no functional/browser evidence, so
  PASS rests only on structural deterministic pass — a low-evidence rubber-stamp.
- Model: `hermes3:8b-abliterated` (a safety-stripped model serving as integrity authority).

## Designer / design context

- Read-only advisory; present in plumbing, typically `skipped`/`blocked` when refs absent.

## Cartographer

- Advisory context only; READ_ONLY authority (can_apply/commit/push/worker = false). Real repo
  map (files_indexed ~180 in prior receipts). NOT a route owner. Correct.

## Scout / SearXNG / Mac worker advisory

- Scout: honest evidence lane; `skipped` 30/30 (no current-info prompts). Default 500ms timeout.
- SearXNG: honest; `skipped` 30/30. Receipt guard forces `used`->`failed` without a provider call.
- Mac worker: hardcoded `skipped` stub; never invoked. Cosmetic lane.

## Verdict

Role SEPARATION is correct and enforced (Qwen != planner/verifier; verifier != critic;
advisory lanes reject qwen). The two real problems are (1) local advisory model INSTABILITY
under contention and (2) advisory failures being NON-GATING, so a degraded lane vanishes behind
a productive GO. Plus the verifier's PASS has no functional evidence for non-UI code.


---

## Source: reports/pivot-remediation-plan.md

# Pivot Remediation Plan — Honest Self-Aware Source Proxy

Date: 2026-06-16 (UTC). Derived from the live 3x10 battery evidence.

Goal state (Britton's intent): no cheating; no prompt fitting; no preview-only counted as live;
no read-only lane counted as integration; no hidden fallback; no fake browser proof; no fake
PASS; every lane emits used/skipped/blocked/failed/timed-out honestly; proxy detects its own
limitations; builds context packets by task shape; routes to optimal local/API/CLI lane only
with approval + receipts; local-first default; strong safety; operational traces with no private
reasoning leak.

Each increment is documentation/implementation-gated and STOPS for Britton. Local-first
preserved; TinyFish deferred; xersearch not created; Cartographer stays advisory.

---

## PLAN PR1 — Truth & Honesty Hardening (no new capability)

### PHASE A — Verdict & lane truth
INCREMENT A.1 — Structured verdict fields
- PURPOSE: kill "verdict-string is the only discriminator"; expose productive vs degraded.
- FILES/MODULES: `source_proxy/api/decision.py` (`_attach_fip0_truth_receipt`), trace projection.
- LIVE PATH TO PROVE: receipt gains `productive: bool`, `coder_path: fip4_real|legacy_stub|trial`,
  `verification_real: {deterministic, browser, functional, hermes}`, `degraded_lanes: [...]`.
- CHECKS: re-score the 30 battery receipts; a foundation/legacy verdict must read `productive:false`.
- GO: every battery productive row reads `productive:true, coder_path:fip4_real`; every `.html`
  row reads `productive:false` with `verification_real.browser:false`.
- NO-GO: any legacy/stub path can read `productive:true`.
- CONFIG-BLOCKED: FIP env flags unreadable at runtime.
- EVIDENCE: re-scored results JSON + diff of receipt schema.
- BRITTON STOP GATE: approve schema before A.2.

INCREMENT A.2 — Quarantine prompt-fitted/scaffold code
- PURPOSE: remove hardcoding from the production hot path.
- FILES/MODULES: `decision.py` (`_product_trial_feature_already_satisfied_payload`,
  `_agent_trials_ui_test_coder_diff_payload`, `_dummy_*`, `_realistic_reversible_*`,
  `_bounded_coder_diff_or_stub`).
- LIVE PATH TO PROVE: gate all of the above behind `SOURCE_PROXY_TRIAL_HARNESS_ONLY=1`; `/coding`
  default refuses them; default FIP-4 ON.
- CHECKS: POST the exact trigger phrases -> no short-circuit; battery re-run unaffected.
- GO: trigger phrases no longer yield canned payloads in default mode.
- NO-GO: any hardcoded payload reachable in default `/coding`.
- CONFIG-BLOCKED: n/a.
- EVIDENCE: trigger-phrase receipts; focused tests.
- BRITTON STOP GATE: approve before A.3.

INCREMENT A.3 — Lane degradation gating
- PURPOSE: stop decorative lanes; degraded REQUIRED lane must downgrade verdict.
- FILES/MODULES: `decision.py` verdict logic; `model_lanes.py`.
- LIVE PATH TO PROVE: when Gemma/Hermes-critic `failed/timed_out` and the row declared them
  required, verdict becomes `expected_degraded_lane` (not silent productive GO).
- CHECKS: induce a Gemma timeout; confirm verdict reflects it.
- GO: degraded required lane never hides behind productive GO.
- NO-GO: degraded lane still silently passes.
- CONFIG-BLOCKED: local models unavailable.
- EVIDENCE: degraded-lane receipts.
- BRITTON STOP GATE: approve before PHASE B.

### PHASE B — Trace hygiene
INCREMENT B.1 — Strip raw model output from traces; auth-gate endpoints
- PURPOSE: honor "no private reasoning"; stop public raw prompt/output exposure.
- FILES/MODULES: `decision.py` (`_fip6_operator_trace_from_receipt`, receipt/trace responses),
  `src/app/v1/decisions/fip0-receipts/*`.
- LIVE PATH TO PROVE: operator_trace contains only hashes/status/bounded summaries; served
  receipt omits raw_prompt/raw_output_excerpt or requires auth; `no_hidden_thinking_displayed`
  is set by a real content scanner.
- CHECKS: scan all 30 traces -> 0 raw_output_excerpt; endpoint requires token.
- GO: 0 raw model text in trace/receipt responses.
- NO-GO: any raw output remains.
- CONFIG-BLOCKED: auth mechanism not chosen.
- EVIDENCE: trace leak scan = 0; endpoint auth test.
- BRITTON STOP GATE: approve before PLAN PR2.

---

## PLAN PR2 — Real Verification

### PHASE C — Behavior verification
INCREMENT C.1 — Headless browser probe (replace synthetic)
- PURPOSE: real UI behavior verification.
- FILES/MODULES: new `source_proxy/verification/browser_probe.py` (Playwright), `_fip5_browser_probe`.
- LIVE PATH TO PROVE: `.html`/`.tsx` rows get real navigation/DOM/console evidence;
  `expected_result_state` is a hint only, never a pass source.
- CHECKS: a deliberately broken UI FAILS; a working one PASSES; battery `.html` rows can pass on
  real evidence.
- GO: synthetic pass impossible; real evidence required.
- NO-GO: any pass without real DOM evidence.
- CONFIG-BLOCKED: browser binary unavailable -> row `config_blocked` (not faked).
- EVIDENCE: browser artifacts (screenshots/console) per row.
- BRITTON STOP GATE: approve before C.2.

INCREMENT C.2 — Functional verification for non-UI code + organic repair
- PURPOSE: make `productive_go` mean "works", and exercise the repair loop honestly.
- FILES/MODULES: `decision.py` deterministic verifier; sandboxed test runner.
- LIVE PATH TO PROVE: generated module gets a generated/declared self-check executed in a
  sandbox; failure triggers a REAL bounded repair (not the `repair_expected` flag).
- CHECKS: a stub calculator must FAIL functional verification (today it passes).
- GO: non-functional scaffolds no longer score productive; repair fires organically and is bounded.
- NO-GO: structure-only PASS persists.
- CONFIG-BLOCKED: sandbox unavailable.
- EVIDENCE: functional results + repair receipts with attempt counts.
- BRITTON STOP GATE: approve before PLAN PR3.

---

## PLAN PR3 — Self-Aware Routing (capability, approval-gated)

### PHASE D — Limitation detection & routing
INCREMENT D.1 — Task-shape + context-need classifier (advisory)
- PURPOSE: proxy detects its own limits and what context a task needs.
- FILES/MODULES: new `source_proxy/decision/task_shape.py` (read-only).
- LIVE PATH TO PROVE: receipt records `task_shape`, `context_needs`, `search_needed_reason`,
  `confidence`, `known_limitation` (e.g., "UI behavior unverifiable without browser").
- CHECKS: battery rows record correct shape; UI rows flag the browser limitation pre-emptively.
- GO: classifications visible, never auto-act.
- NO-GO: classifier auto-routes or auto-escalates.
- CONFIG-BLOCKED: n/a.
- EVIDENCE: per-row classification receipts.
- BRITTON STOP GATE: approve before D.2.

INCREMENT D.2 — Lane-health detector + escalation policy (advisory)
- PURPOSE: know when a lane is degraded and when to escalate/stop.
- FILES/MODULES: `model_lanes.py`, `research.py` diagnostics; router (advisory only).
- LIVE PATH TO PROVE: rolling latency/error stats -> `lane_health`; router emits a RECOMMENDED
  lane (local -> stronger-local -> manual handoff) with reasons; NO cloud/API/CLI call without
  explicit Britton approval + receipt.
- CHECKS: induce Gemma timeouts -> lane_health degraded -> recommendation surfaces.
- GO: recommendation-only, receipted; local-first preserved; safety blocks intact.
- NO-GO: any automatic external call or routing-ownership change.
- CONFIG-BLOCKED: stats store unavailable.
- EVIDENCE: lane_health receipts; recommendation traces.
- BRITTON STOP GATE: approve before any PLAN PR4 (optimal-lane execution / approved external routes).

---

## Cross-cutting guardrails (every increment)

- No commit/push/stage without explicit Britton approval.
- No TinyFish, no xersearch, no Cartographer route ownership, no new default model lane.
- Local-first default; external routes require explicit approval + receipts.
- Protected-path policy may only get stronger.
- Every lane emits used/skipped/blocked/failed/timed-out honestly.
- Each increment: durable receipt + honest trace + focused tests + human-readable closeout +
  explicit stop gate. No hidden continuation.


---

## Source: reports/receipt-trace-audit.md

# Receipt & Trace Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery receipts + traces + source inspection.

## Durability & consistency (STRONG)

- 30/30 posted rows produced a durable FIP-0 receipt at
  `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/<run_id>.json`.
- 30/30 produced an FIP-6 trace; 30/30 `verdict_trace.final_verdict == receipt.final_verdict`.
- trace_version `fip6.operator_trace.v1`; trace_authority
  `operational_receipt_projection_no_private_reasoning`; `no_hidden_thinking_displayed=true` 30/30.
- Hash discipline: `final_coder_packet_hash == coder_received_packet_hash` on all 22 productive
  rows. `_packet_hash_match_status` in the trace reflects this.
- Copies preserved under `../receipts/` and `../traces/` for independent review.

## Source-of-truth model (CORRECT)

- Durable FIP-0 receipt is authoritative; FIP-6 trace is a projection. Verdict precedence in
  `_attach_fip0_truth_receipt` is fip5 > fip4 > fip3 > fip1 > fip2 > base. All 22 GOs are
  `GO: fip5_...` (real integrated), 0 foundation/preview GOs slipped through.

## LEAKAGE FINDING (MEDIUM)

`operator_trace.coder_trace.qwen.parser_result` includes `raw_output_excerpt` — the RAW Qwen
model output (verified: 824 chars of `{"action":"replace_file", "content_lines":[...]}` in the
`s1-04-todo` trace). So the FIP-6 operator_trace, which advertises
"operational_receipt_projection_no_private_reasoning", still surfaces raw coder model output.
Additionally the co-served full `receipt` (returned by both `/fip0-receipts/{id}` and
`/fip0-receipts/{id}/trace`) carries `raw_prompt` and, for FIP-5 rows, Hermes verifier
`raw_output_excerpt` and `input_summary.raw_prompt`. These endpoints are unauthenticated and
linked from `/coding`.

Note: a naive keyword scan also flagged `thinking`/`hidden`, but those are false positives from
the `no_hidden_thinking_displayed` field name. The genuine leak is `raw_output_excerpt`.

## Stale-latest / overwrite risk (source, not hit here)

- `run_id = fip0-<sha256(timestamp_to_second, task, target, route)[:16]>`. Identical prompt in
  the same second collides/overwrites. The battery used distinct prompts/targets so no collision
  occurred, but the risk is real.
- `latest` is `max(timestamp_string, mtime)`; a stale duplicate with a high timestamp can shadow.
  The canonical receipt dir already holds 190+ receipts including superseded duplicates.

## missing_fields behavior

- `_fip6_operator_trace_from_receipt` computes `missing_fields`; battery traces had complete
  field sets for the integrated rows.

## Recommendations

1. Remove `raw_output_excerpt` (and any raw model text) from the operator_trace projection;
   keep only hashes + status + bounded structured summaries.
2. Strip `raw_prompt`/raw excerpts from the served receipt body, or auth-gate the endpoints.
3. Replace the constant `no_hidden_thinking_displayed=true` with a real content scanner that
   sets the flag based on inspection.
4. Make `run_id` collision-proof (uuid/monotonic seq) and move superseded receipts to an archive
   subdir so `latest` cannot select a stale duplicate.


---

## Source: reports/search-context-audit.md

# Search & Context Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery receipts + source inspection.

## Summary

The battery prompts did not request current information, so the search lanes were correctly
INACTIVE. Context lanes (Cartographer/Obsidian/Design) are read-only and were not counted as
coder success. No false `used`, no silent omission. The honesty of these lanes is GOOD; their
ACTUAL CONTRIBUTION to acceptance is near zero (advisory, non-gating).

## Per-lane truth (30 rows)

| Lane | Status across battery | Honest? | Notes |
|---|---|---|---|
| Scout | `skipped` 30/30 | Yes | `search_needed=False` (no current-info); diagnostics gate is honest |
| SearXNG | `skipped` 30/30 | Yes | same; receipt guard forces `used`->`failed` without a real provider call |
| Repo research | not surfaced as `used` | Yes | repo-first only fires on `needs_codebase_context`/research-recommended |
| Cartographer | advisory, read-only | Yes | real repo map; `can_apply/commit/push/worker=false`; not route owner |
| Obsidian | advisory, read-only | Yes | needs `data/design-vault`; typically skipped; secret redaction in excerpts |
| Design | advisory, read-only | Yes | globs design docs/components; skipped when refs absent |
| Mac worker | `skipped` (hardcoded stub) | Honest-but-cosmetic | never invoked; no capability behind it |
| TinyFish | `skipped` (deferred) | Yes | correctly deferred; not created |
| xersearch | `skipped` (missing alias) | Yes | correctly absent; not created |

## Gating reality

Context/search lane outcomes did not affect any verdict. Even when an advisory MODEL lane
failed (Gemma ReadTimeout), the GO stood. So "integrated context" is real plumbing but NOT a
gate on acceptance: a row passes on Qwen + structural deterministic + Hermes verifier alone.

## Search quality risks (source)

- `research.py::run_local_research_preview`: a SearXNG exception returns `[]`, discarding
  already-gathered repo+scout sources (latent context-loss bug). Not exercised by the battery
  (search not needed), but real.
- Repo research is a FIXED file allowlist (`REPO_RESEARCH_PATHS`) with hand-tuned scoring —
  narrow context selection.
- Scout default timeout 500ms — fragile under load.

## Recommendations

1. Make context-need a first-class classification recorded per row, and let a REQUIRED context
   lane's failure downgrade the verdict (no decorative lanes).
2. Fix the SearXNG-exception-discards-sources bug.
3. Add at least a few current-info battery rows in future runs to exercise Scout/SearXNG truth
   under real provider calls (this battery deliberately did not, to isolate coding behavior).
4. Either implement the Mac-worker lane or relabel it `not_implemented` instead of `skipped`.


---

## Source: reports/verifier-repair-audit.md

# Verifier & Repair Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery receipts + source inspection.

## Deterministic verifier

- Ran 30/30, `passed` 30/30 for the structural contract.
- What it ACTUALLY checks (`_fip5_deterministic_verifier`): fip4 status used, final==received
  hash, output parsed, changed files inside allowed_files, protected files not changed, and
  (only when the prompt contains an "exactly this content:" marker) required-text presence.
- What it does NOT check: that the code compiles, runs, has no errors, or fulfills the request.
  No tests are executed. So `deterministic passed` = "structurally valid replace_file in scope".
- Harness coupling (source): `expected_result_state in {repair_expected, max_repair_expected}`
  forces synthetic failures. The battery did NOT send these, so all deterministic passes were
  organic-structural (good), but the forced-failure path remains in production code.

## Browser behavior verifier

- THERE IS NO REAL BROWSER. `_fip5_browser_probe` returns synthetic `passed=True` only when fed
  `expected_result_state=browser_pass_expected`; otherwise, for browser-relevant targets
  (`.tsx/.jsx/.html`, `src/app`, `src/components`) it returns `passed=False`.
- Battery proof: 8/8 `.html` rows -> `browser passed=False`, verdict
  `NO-GO: fip5_browser_behavior_authority_blocks_pass`, `probes_run=["fip5_runtime_browser_relevance_probe"]`
  (a label, not a DOM/navigation check). No screenshot, no console, no assertions.
- Honesty note: because the battery did NOT feed the flag, the system honestly refused to pass
  UI. The OVERCLAIM is realized only when a runner feeds `browser_pass_expected` (as Level 5R2 did).

## Hermes post-code verifier

- Cannot manufacture PASS over evidence: `_fip5_normalize_hermes_verifier_output` downgrades
  PASS->NEEDS_FIX on deterministic failure and PASS->FAIL on browser failure. Proven: every
  `.html` row returned FAIL/NEEDS_FIX, never PASS.
- Evidence mismatch re-ask exists and is bounded (max 2 attempts).
- Weakness: for non-UI rows there is no functional/browser evidence, so PASS is a low-evidence
  rubber-stamp on a structurally valid file. Model is `hermes3:8b-abliterated`.

## Repair loop

- 0 repair attempts across ALL 30 rows (`repair_attempt_count=0`, `repair_max_attempts=2`).
- Why: the loop condition is `not deterministic.passed and browser.passed is not False`.
  Productive rows passed deterministic immediately (no repair); `.html` rows failed on BROWSER
  (browser.passed=False short-circuits the loop, no repair). So honest prompts never triggered
  repair.
- Consequence: the bounded repair behavior is UNPROVEN outside the harness-forced
  `repair_expected` flag. Its real-world reliability remains untested by honest input.
- Bounding is enforced in source (max attempts 0-5, default 2) and verdict
  `NO-GO: fip5_repair_attempts_exhausted...` exists, but was not reached here.

## No-op / already-satisfied behavior

- Not exercised honestly here (all targets were fresh placeholders -> real edits). The hardcoded
  already-satisfied path (`_product_trial_feature_already_satisfied_payload`) was NOT triggered.

## Authority chain verdict

The verifier authority chain is structurally SOUND (verifier cannot override deterministic or
browser) but EVIDENTIALLY HOLLOW for the two cases that matter:
1. UI behavior: no real browser -> cannot verify, honestly blocks.
2. Non-UI correctness: no tests/execution -> PASS attests structure only.
Plus the repair loop is effectively dead code under honest input. Fixing verification quality
(real browser + functional execution + organic repair) is the top engineering priority.


---

## Source: set-1-closeout.md

# Set 1 Closeout — Claude 3x10 Basic Coding Battery

Date: 2026-06-15
Runtime: real integrated path (FIP-4 Qwen + FIP-5 deterministic/browser/Hermes), confirmed in preflight.
Duration: ~44.5 min (10 rows, cold+warm model loads; 190–360s/row).

## 10-row matrix

| prompt_id | raw prompt | target | verdict | score_class | qwen | det | browser | hermesV | hashmatch | repair | trace==receipt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s1-01-homepage | init a repo and make a homepage for my app | index.html | NO-GO browser authority | verifier_blocked_browser | used | pass | FAIL(no real browser) | FAIL | yes | 0 | yes |
| s1-02-calculator | make calculator app | calculator.js | GO: fip5 | productive_go | used | pass | n/a(skip) | PASS | yes | 0 | yes |
| s1-03-weather | make weather app | weather.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-04-todo | make a todo list thing | todo.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-05-timer | make a little timer | timer.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-06-notes | make a notes app | notes.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-07-expense | make a expense splitter | split.js | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |
| s1-08-chart | make a simple chart page | chart.html | NO-GO browser authority | verifier_blocked_browser | used | pass | FAIL | FAIL | yes | 0 | yes |
| s1-09-signup | make a signup landing page | signup.html | NO-GO browser authority | verifier_blocked_browser | used | pass | FAIL | NEEDS_FIX | yes | 0 | yes |
| s1-10-status | make a tiny api route that returns status | status.ts | GO: fip5 | productive_go | used | pass | n/a | PASS | yes | 0 | yes |

## Counts

- productive_go: 7
- verifier_blocked_browser: 3 (all `.html`, browser-relevant)
- expected_safety_block: 0
- unexpected_no_go: 0
- config_blocked: 0
- trace_mismatch: 0
- lane_truth_warning: 0
- hardcoded_used / preview_only_go / productive_go_integrity_fail: 0
- Receipts + traces: 10/10 durable, 10/10 trace==receipt.

## Fixes applied

- None. Runner worked on first execution (after pre-seeding target files to avoid the `target_missing` gate, which is by design — the proxy never creates files, only proposes diffs).

## Reruns

- None needed.

## Honest findings (Set 1)

1. POSITIVE: The real integrated path is exercised end to end. Every productive row has qwen `used`, deterministic pass, Hermes verifier `PASS`, `final_coder_packet_hash == coder_received_packet_hash`, durable receipt + matching FIP-6 trace, changed files strictly inside the disposable target root. No hidden fallback, no hardcoded payload, no preview-only GO.
2. POSITIVE / honesty proof: All 3 UI (`.html`) rows honestly NO-GO'd on the browser authority. Hermes returned FAIL/NEEDS_FIX (NOT a faked PASS) because the browser probe reported `passed=False`. Without the `expected_result_state=browser_pass_expected` harness flag, the system refuses to pass UI behavior. This confirms the synthetic-browser pass seen in Level 5R2 is realized ONLY when the runner feeds that flag.
3. CRITICAL QUALITY GAP: `productive_go` does NOT mean "working app." Example: `s1-02-calculator` produced a real Qwen diff but the content is a non-functional stub (`<h1>Calculator</h1>` + comment "Add your calculator components here") with zero calculator logic. The deterministic verifier only checks structure (file written, hash match, path allowed, diff present); it runs no tests and no behavior probe for `.js`. Hermes `PASS` has no functional evidence to stand on, so it is effectively a rubber-stamp. The proxy reliably produces *plausible scaffolds* and receipts them honestly, but it does NOT verify functional correctness.
4. NUANCE: Qwen emitted React/JSX for plain `.js` targets (`import React`), i.e., it ignores file-type/runtime intent. Output is syntactically plausible but contextually loose.

Set 1 verdict: integration is real and honest; verification authority is structural-only, so productive GO overstates capability.


---

## Source: set-2-closeout.md

# Set 2 Closeout — Claude 3x10 Basic Coding Battery

Date: 2026-06-16 (UTC)
Duration: ~47 min.

## 10-row matrix

| prompt_id | raw prompt | target | score_class | qwen | det | browser | hermesV | hashmatch | trace==receipt |
|---|---|---|---|---|---|---|---|---|---|
| s2-01-dashboard | lets start a repo and make a dashboard for my app | dashboard.html | verifier_blocked_browser | used | pass | FAIL | FAIL | yes | yes |
| s2-02-counter | make a time counter app | counter.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-03-moon | make a moon phase app | moon.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-04-checklist | make checklist thing i can add and clear | checklist.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-05-stopwatch | make stopwatch card with start pause reset | stopwatch.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-06-sticky | make a quick sticky notes board | sticky.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-07-tip | make a tip calculator | tip.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-08-stats | make a small stats widget | stats.js | productive_go | used | pass | n/a | PASS | yes | yes |
| s2-09-waitlist | make a product waitlist page | waitlist.html | verifier_blocked_browser | used | pass | FAIL | NEEDS_FIX | yes | yes |
| s2-10-health | make a health check endpoint | health.ts | productive_go | used | pass | n/a | PASS | yes | yes |

## Counts (Set 2)

- productive_go: 8
- verifier_blocked_browser: 2 (`.html`)
- unexpected_no_go / config_blocked / trace_mismatch / hardcoded / preview_only_go / integrity_fail: 0
- Receipts + traces: 10/10 durable, 10/10 trace==receipt.

## Fixes / reruns

- None. Clean execution.

## Generalization vs Set 1

- timer family: s1-05-timer (productive) == s2-02-counter / s2-05-stopwatch (productive). Consistent.
- calc family: s1-02-calculator / s1-07-expense == s2-07-tip (productive). Consistent.
- data/ui family: s1-03-weather == s2-03-moon (productive). Consistent.
- crud family: s1-06-notes == s2-06-sticky (productive). Consistent.
- ui-page family: s1-09-signup == s2-09-waitlist (verifier_blocked). Consistent.
- scaffold family: s1-01-homepage == s2-01-dashboard (verifier_blocked). Consistent.
- api family: s1-10-status == s2-10-health (productive). Consistent.

Reworded prompts in the same family produced identical score classes. No evidence of prompt-fitting; outcomes track task shape (file extension / browser relevance), not specific wording.

## Same quality caveat as Set 1

`productive_go` remains structural-only. Spot inspection of `.js` rows shows plausible-but-incomplete scaffolds (no tests run, no behavior verification). The GO attests "valid file produced in allowed path + advisory Hermes PASS", not "working feature."


---

## Source: set-3-closeout.md

# Set 3 Closeout — Claude 3x10 Basic Coding Battery

Date: 2026-06-16 (UTC)
Duration: ~40 min.

## 10-row matrix

| prompt_id | raw prompt | target | score_class | qwen | det | browser | hermesV | trace==receipt |
|---|---|---|---|---|---|---|---|---|
| s3-01-shell | spin up a tiny app shell with a home screen | shell.html | verifier_blocked_browser | used | pass | FAIL | NEEDS_FIX | yes |
| s3-02-cruncher | build a basic number cruncher | cruncher.js | productive_go | used | pass | n/a | PASS | yes |
| s3-03-forecast | make a simple forecast-ish demo with fake data if needed | forecast.js | productive_go | used | pass | n/a | PASS | yes |
| s3-04-tasks | make a task tracker | tasks.js | productive_go | used | pass | n/a | PASS | yes |
| s3-05-countdown | make a countdown thing | countdown.js | productive_go | used | pass | n/a | PASS | yes |
| s3-06-journal | make a mini journal page | journal.js | productive_go | used | pass | n/a | PASS | yes |
| s3-07-budget | make a budget split helper | budget.js | productive_go | used | pass | n/a | PASS | yes |
| s3-08-progress | make a simple progress graph | progress.html | verifier_blocked_browser | used | pass | FAIL | FAIL | yes |
| s3-09-coming-soon | make a coming soon page | coming-soon.html | verifier_blocked_browser | used | pass | FAIL | FAIL | yes |
| s3-10-alive | make an endpoint that says the service is alive | alive.ts | productive_go | used | pass | n/a | PASS | yes |

## Counts (Set 3)

- productive_go: 7
- verifier_blocked_browser: 3 (`.html`)
- unexpected_no_go / config_blocked / trace_mismatch / hardcoded / preview_only_go / integrity_fail: 0
- Receipts + traces: 10/10 durable, 10/10 trace==receipt.

## Notable lane truth (Set 3)

- `s3-04-tasks`: hermes_critic_status = `failed`, yet final verdict GO: fip5 (advisory critic failure non-blocking; recorded in model_errors but does not gate GO).

## Fixes / reruns

- None.

## Generalization vs Set 1 and Set 2

- scaffold/home: s1-01, s2-01, s3-01 -> all verifier_blocked. Consistent.
- calc/logic: s1-02, s1-07, s2-07, s3-02, s3-07 -> all productive. Consistent.
- data/ui: s1-03, s2-03, s3-03 -> all productive. Consistent.
- state/crud: s1-04, s2-04, s3-04, s1-06, s2-06, s3-06 -> all productive. Consistent.
- timer: s1-05, s2-02, s2-05, s3-05 -> all productive. Consistent.
- ui/page: s1-08, s1-09, s2-09, s3-08, s3-09 -> all verifier_blocked. Consistent.
- api: s1-10, s2-10, s3-10 -> all productive. Consistent.

Outcome is fully determined by task shape (target extension / browser relevance), not by wording. Zero evidence of prompt-fitting across reworded sets.


---
