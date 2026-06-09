# Plan 0 Phase 0.3: Current Model and Provider Route Truth

Status: GO

Execution boundary: Plan 0-approved route-truth correction only. No model/provider call. No coder trial. No `/v1/chat/completions` call. No Coder 50 or Coder 100.

## Increment 0.3.1: Configured Provider Aliases and Displayed Model Truth

Commands run:

- `rg -n "qwen2\\.5-coder:7b|qwen2\\.5-coder:14b|SOURCE_PROXY|CODER|OLLAMA|model|alias|local|coder" .env.example config source_proxy src/components/coding src/lib/coding tests/ui-agent-trials -g "*.env" -g "*.example" -g "*.py" -g "*.ts" -g "*.tsx" -g "*.json"`
- `Get-Content source_proxy\\routing\\ollama_route.py | Select-Object -First 260`
- `Get-Content source_proxy\\routing\\litellm_router.py | Select-Object -First 260`
- `Get-Content config\\source-proxy.example.env`
- `Select-String -Path '.env.local' -Pattern 'SOURCE_PROXY_CODER_OLLAMA_MODEL|SOURCE_PROXY_OLLAMA_MODEL|SOURCE_PROXY_CLASSIFIER_OLLAMA_MODEL'`

Observed before correction:

- `.env.example` set `SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:14b`.
- `config/source-proxy.example.env` set `SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:14b`.
- `.env.local` set `SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:14b`.
- `source_proxy/routing/ollama_route.py` preferred `qwen2.5-coder:14b` before `qwen2.5-coder:7b`.
- `source_proxy/routing/ollama_route.py` reported `auto:qwen2.5-coder:14b` when no explicit coder model env was set.
- `source_proxy/routing/litellm_router.py` exposes aliases `local`, `coder`, `classifier`, `openai`, `anthropic`, and `deepseek`.
- `source_proxy/api/chat.py` uses those aliases for `GET /v1/models` and `POST /v1/chat/completions`.

Result: PASS with mismatch found. Current truth did not match the master-plan model decision before correction.

## Increment 0.3.2: Switch or Confirm Coder Default as `qwen2.5-coder:7b`

Files changed in this increment:

- `.env.example`
- `config/source-proxy.example.env`
- `.env.local`
- `source_proxy/routing/ollama_route.py`
- `source_proxy/tests/test_ollama_route.py`

Applied correction:

- Set example coder lane env to `SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b`.
- Set local coder lane env to `SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b`.
- Changed unconfigured coder candidate order to prefer `qwen2.5-coder:7b`.
- Changed the auto route truth label to `auto:qwen2.5-coder:7b`.
- Updated focused route tests to assert 7B default with 14B preserved as comparison/fallback.

Checks run:

- `.\\.venv-source-proxy-windows\\Scripts\\python.exe -m pytest source_proxy\\tests\\test_ollama_route.py`
- `rg -n "SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2\\.5-coder:7b|auto:qwen2\\.5-coder:7b|prefer Qwen 7B|qwen2\\.5-coder:14b" .env.example config/source-proxy.example.env .env.local source_proxy/routing/ollama_route.py source_proxy/tests/test_ollama_route.py`

Check result:

- `source_proxy/tests/test_ollama_route.py`: 14 passed.
- Grep confirmed `SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b` in `.env.example`, `config/source-proxy.example.env`, and `.env.local`.
- Grep confirmed `auto:qwen2.5-coder:7b` in `source_proxy/routing/ollama_route.py`.

Result: PASS. The coder default is now corrected to 7B in the route truth surfaces inspected by Plan 0.

## Increment 0.3.3: Preserve 14B as Comparison-Only

Preservation rule:

- `qwen2.5-coder:14b` remains in the candidate list after `qwen2.5-coder:7b`.
- 14B is comparison/fallback only.
- 14B cannot become default until it passes the same output-contract tests as 7B and Britton approves a default switch.

Observed evidence:

- `source_proxy/routing/ollama_route.py` keeps `qwen2.5-coder:14b` as a candidate after `qwen2.5-coder:7b`.
- `source_proxy/tests/test_ollama_route.py` asserts 14B as `available_ollama_model_fallback` when both 7B and 14B are present.

Result: PASS. 14B was preserved, not abandoned.

## Phase 0.3 Closeout

Checks passed:

- Model/provider route truth inspected.
- 14B-default mismatch identified.
- Plan 0-approved correction changed coder default to `qwen2.5-coder:7b`.
- 14B remains comparison/fallback.
- Focused route tests pass.

GO/NO-GO: GO to Phase 0.4 workflow law.

Next permitted phase: Phase 0.4 only.
