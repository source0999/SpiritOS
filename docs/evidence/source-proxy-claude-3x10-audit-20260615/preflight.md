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
