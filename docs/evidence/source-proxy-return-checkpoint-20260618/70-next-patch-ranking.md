# Next Patch Ranking

No patch was implemented.

## Ranking

| Rank | Candidate | Problem solved | Evidence needed | Risk | Likely files | Tests required | Before model intelligence work? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Runtime health/status/liveness truth | Replaces invalid `/health` expectations and makes live readiness explicit. | `/health` and `/v1/health` are 404; valid proof is scattered across `/docs`, `/openapi.json`, `/healthcheck`, `/v1/self/status`, `/v1/models`, watchers. | Low/medium | `source_proxy/main.py`, status route modules, docs/runbook, tests. | API route tests, status JSON schema tests, no-mutation status smoke. | Yes. Runtime truth should precede model claims. |
| 2 | Process supervision/runbook integration | Makes proxy/Next/Ollama process ownership and restart boundaries explicit. | Runtime is in tmux, not proven as supervised service; prior OOM killed uvicorn before reboot. | Medium | runbook docs, watcher scripts, maybe non-mutating status integration. | Read-only watcher tests, docs validation, liveness smoke. | Yes, after health/status truth. |
| 3 | Browser verifier hardening | Reconciles Claude "no real browser" with Level 5R2 browser-pass claims. | Claude audit blocked 8 UI rows; Level 5R2 later claims browser evidence passed. | Medium/high | verifier lane modules, browser verifier code/tests, evidence docs. | Browser verifier unit tests plus one approved browser smoke. | Yes, before UI/productive claims. |
| 4 | Repair loop actually firing | Proves repair works under organic failures, not just visible bounded metadata. | Claude battery had 0 attempts; Level 5R2 says bounded loop visible. | Medium | decision/verifier/repair modules, tests. | Targeted repair-loop tests, no broad gauntlet unless approved. | After runtime truth and verifier reconciliation. |
| 5 | Qwen coder timeout/empty-output handling | Improves local coder failure classification and avoids generic no-diff masking. | Prior no-diff diagnostics identify parser/output classification loss; Qwen quality remains weak. | Medium | `source_proxy/tasks/long_running.py`, `source_proxy/api/decision.py`, coding UI tests. | Backend parser tests, workflow regression pack, UI result rendering tests. | After status truth unless coding lane is the immediate approved focus. |

## Other candidates

- `productive_go` definition hardening: important, but depends on verifier/functional evidence.
- Gemma/Hermes timeout/degraded lane handling: important after runtime/model contention is characterized.
- Search/web/Obsidian/research proof: should wait behind runtime health and verifier truth.
- Trace hygiene regression guard: high value and low risk; could be paired with status work if scope stays tight.
- Integrated gauntlet harness: not next; broad/noisy and explicitly not approved.

## Recommendation

Recommended next proxy patch: `Runtime health/status/liveness truth`.

Reason: current work can return to Source Proxy analysis, but implementation should start by making the live source of truth explicit and non-ambiguous. That patch is smaller and safer than jumping back into browser/model intelligence while the repo is dirty and runtime authority is split across old evidence, live endpoints, tmux, and watcher logs.
