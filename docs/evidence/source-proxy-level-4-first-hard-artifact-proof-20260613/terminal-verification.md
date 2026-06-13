# Terminal Verification

Status: complete.

## Commands Run And Results

Preflight:

- `git status --branch --short --untracked-files=normal`
  - PASS before Level 4 evidence files: `## master`.
- Gate B evidence folder listing:
  - PASS; `docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/` exists with required Gate B artifacts.
- Read Gate B minimum files:
  - PASS; read `mini-context-pack.md`, `final-clean-10-rerun-summary.md`, `terminal-verification.md`, `anti-tailoring-audit.md`, `anti-cheat-integrity.md`, and sampled `final-clean-10-gate-b-results.json`.

Pre-run lock and syntax:

- `python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json`
  - PASS.
- `node --check docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs`
  - PASS.
- `python -m py_compile docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/build_level4_reports.py`
  - PASS.

Locked Level 4 10 run:

- `python Z:/docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py --prompt-file Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json --run-root Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runs --title "Source Proxy Level 4 first hard artifact complexity proof locked 10" --results Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runner-results.json --html Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runner.html --run-receipt Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-run-receipt.json --browser-results Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-level3-browser-behavior-results.json --repair-summary Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-post-behavior-repair-summary.json --model-id qwen2.5-coder:7b`
  - PASS command completion.
  - Existing Level 3-style runner output: 10 results, 6 PASS, runner overall `NO-GO`.
  - Repair summary: 3 repairs, 10 total.

Strict Level 4 probe wrapper:

- `node docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runs Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-browser-behavior-results.json Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/per-prompt-traces`
  - PASS command completion.
  - Strict Level 4 output: 10 results, 5 PASS, 5 FAIL.

Report build:

- `python docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/build_level4_reports.py --evidence-root Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613 --runner-results Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runner-results.json --browser-results Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-browser-behavior-results.json --prompt-file Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json --run-root Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-runs --output-results Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-results.json --output-html Z:/docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4.html`
  - PASS.

Anti-tailoring:

- Fixed-string search for all 10 locked Level 4 prompt strings across `source_proxy`, `src`, `scripts/agent-trials`, source-proxy scripts, and `config`.
  - PASS; no matches.
- Fixed-string search for all 10 locked Level 4 prompt ids across the same runtime/source scopes.
  - PASS; no matches.
- Fixed-string search for old Level 3 final clean strings across the same runtime/source scopes.
  - PASS; no matches.
- Suspicious branch/scaffold search:
  - `prompt ==`: only ordinary prompt trimming in `src/app/v1/coding/research-preview/route.ts`.
  - `prompt_id ==`: generic durable-run UI/store references and unrelated existing `coder-001-init-dummy-product-site`; no Level 4 prompt-id branch.
  - `fallback scaffold`: existing UI/test wording and repair-contract prohibition line only.
  - `backend-authored rescue`: repair-contract/test guardrail text only.
  - `hidden deterministic scaffold`: no match.
  - `cloud fallback`: unrelated design-demo diagnostics description only.

Final validation:

- `python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-prompt-set.json`
  - PASS.
- `python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-results.json`
  - PASS.
- `python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level-4-browser-behavior-results.json`
  - PASS.
- Per-prompt trace JSON validation for `docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/per-prompt-traces/*.json`
  - PASS.
- `python -m json.tool docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/mini-context-pack.json`
  - PASS.
- `python -c "import xml.etree.ElementTree as ET; ET.parse('docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/mini-context-pack.xml')"`
  - PASS.
- `node --check docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs`
  - PASS.
- `python -m py_compile docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/build_level4_reports.py`
  - PASS.
- Practical link audit for `level-4.html`
  - PASS; 70 hrefs checked.
- `git diff --check -- docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613`
  - PASS.
- `git status --branch --short --untracked-files=normal`
  - PASS; final status shows only the new untracked evidence folder:
  - `## master`
  - `?? docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/`

## Final Result

- Verdict: NO-GO.
- Strict Level 4 pass/fail: 5 PASS, 5 FAIL.
- Threshold: 8/10 Level 4 behavior PASS for GO.
- Runtime source code changed: no.
- Source Proxy scorer changed: no.
- Final verdict logic changed: no.
- Level 4 evidence-only probe wrapper changed after run: no.
- Branch/stash/reset/checkout/clean/stage/commit/push: not used.
