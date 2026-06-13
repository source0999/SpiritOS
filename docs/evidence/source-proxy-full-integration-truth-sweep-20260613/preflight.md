# Preflight

Date: 2026-06-13

Current git status at start:

```text
## master
?? docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/
```

Dirty files at start:

- Untracked: `docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/`

Current Source Proxy evidence state inspected:

- `docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/`
- `docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/`
- `docs/evidence/source-proxy-chatgpt-mini-context-pack-20260613/`
- related Source Proxy evidence folder inventory under `docs/evidence/`

Latest accepted Level 3 status:

- Level 3 Gate B: GO.
- Evidence says Qwen ran via `qwen2.5-coder:7b`.
- Evidence says Gemma/Hermes verifier lanes were not live.
- Evidence says Cartographer was not live route owner.

Latest Level 4 status:

- Level 4: NO-GO.
- 5/10 strict Level 4 behavior PASS.
- Evidence-only wrapper and per-prompt traces were created.
- Per-prompt traces mark Qwen invoked, Gemma/Hermes not invoked, and Cartographer not live route owner.

Why the level ladder is paused:

- Recent levels tested artifact/Qwen behavior, not full SpiritOS Source Proxy integration.
- Missing truth receipts make it unsafe to claim full integration.
- The next level should wait until live invocation receipts exist for non-Qwen integrations.

Files/directories inspected:

- `source_proxy/main.py`
- `source_proxy/api/decision.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/decision/router.py`
- `source_proxy/decision/research.py`
- `source_proxy/decision/scout_research.py`
- `source_proxy/decision/model_lanes.py`
- `source_proxy/decision/verifier_lane.py`
- `source_proxy/decision/cartographer_routing.py`
- `source_proxy/context/obsidian.py`
- `source_proxy/api/obsidian_context.py`
- `source_proxy/api/scout_intake.py`
- `source_proxy/proxy_memory/scout_intake.py`
- `source_proxy/cartographer/lane_registry.py`
- `source_proxy/api/cartographer.py`
- `backend/docker-compose.yml`
- `backend/searxng.yml`
- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md`
- `docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md`
- Level 3/4 evidence folders listed above

Forbidden actions avoided:

- No Level 5.
- No new artifact batch.
- No Level 4 repair continuation.
- No scorer/verdict patch.
- No cloud fallback.
- No trial-prompt mutation of real app files.
- No branch, stash, reset, checkout, clean, commit, push, or staging.
