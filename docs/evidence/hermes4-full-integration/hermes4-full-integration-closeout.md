# Hermes 4 Full Integration Evidence Closeout

Date: 2026-05-29T20:04:43-04:00

## Final validation
```text
## main...origin/main
 M .env.example
 M .env.local.example
 M README.md
 M _reference/dashboardDemo/index.html
 M _reference/dashboardDemo/src/App.tsx
 M _reference/dashboardDemo/src/index.css
 M _reference/dashboardDemo/vite.config.ts
 M backend/.env.example
 M config/source-proxy.example.env
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.1.1-current-baseline.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.1.2-a-plus-gap-list.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.2.1-overlay-decision.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.2.2-worker-overlay-formalized.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.3.1-scout-research-packet-inspection.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.3.2-scout-research-local-smoke.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.3.3-scout-research-result-shape.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.3.4-scout-research-api-proof.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.4.1-search-provider-boundary.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.4.2-safe-search-packet-mode.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.4.3-web-search-packet-proof.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.5.1-browser-design-boundary.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.5.2-browser-design-smoke.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.5.3-browser-design-result-packet.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.6.1-proxy-flow-map.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.6.2-explicit-mac-advisory-opt-in.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.6.3-realistic-proxy-mac-flow-proof.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.7.1-a-plus-acceptance-matrix.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.7.2-full-verification.md
A  docs/evidence/mac-worker-hardening/plan-2/increment-2.7.3-final-mac-smoke-proof.md
A  docs/evidence/mac-worker-hardening/plan-2/phase-2.1-closeout.md
A  docs/evidence/mac-worker-hardening/plan-2/phase-2.2-closeout.md
A  docs/evidence/mac-worker-hardening/plan-2/phase-2.3-closeout.md
A  docs/evidence/mac-worker-hardening/plan-2/phase-2.4-closeout.md
A  docs/evidence/mac-worker-hardening/plan-2/phase-2.5-closeout.md
A  docs/evidence/mac-worker-hardening/plan-2/phase-2.6-closeout.md
A  docs/evidence/mac-worker-hardening/plan-2/phase-2.7-closeout.md
A  docs/evidence/mac-worker-hardening/plan-2/plan-2-closeout.md
A  docs/mac-worker-operator-contract.md
 M docs/plan-index.md
 M package-lock.json
 M package.json
 M playwright.config.mjs
A  scripts/mac-worker/spirit-mac-worker.mjs
A  scripts/mac-worker/spirit_mac_worker.py
 M source_proxy/api/decision.py
 M source_proxy/routing/litellm_router.py
 M source_proxy/routing/ollama_route.py
 M source_proxy/self_status.py
 M source_proxy/tasks/long_running.py
 M source_proxy/tests/test_ollama_route.py
 M source_proxy/tests/test_prompt_packet_context_metadata.py
 M source_proxy/tests/test_self_status.py
 M src/app/__tests__/static-shell-routes.test.tsx
 M src/app/coding/__tests__/page.test.tsx
 M src/app/coding/page.tsx
 M src/app/proxy-backend/page.tsx
 M src/app/v1/decisions/prompt-packet/route.ts
 M src/components/coding/CodingCockpitShell.tsx
M  src/components/coding/CodingCommandCenterShell.tsx
 M src/components/coding/__tests__/coding-cockpit-shell.test.tsx
M  src/components/coding/__tests__/coding-command-center-shell.test.tsx
 M src/lib/coding/model-provider-status.ts
 M src/lib/coding/plain-english-scope.ts
A  src/lib/mac-worker/__tests__/contract.test.ts
A  src/lib/mac-worker/types.ts
 M src/lib/server/ollama.ts
 M src/lib/spirit/tools/tool-registry.ts
?? .codex-smoke/coding-plan1-runner-desktop.png
?? .codex-smoke/coding-plan1-runner-tablet.png
?? .codex-smoke/coding-trial-diagnostic-bridge-default.png
?? .codex-smoke/coding-trial-diagnostic-bridge-details.png
?? .codex-smoke/manual-natural-test-a.png
?? .codex-smoke/manual-natural-test-b.png
?? .codex-smoke/manual-natural-test-c.png
?? .codex-smoke/manual-natural-test-d.png
?? .codex-smoke/plan1-coding-desktop.png
?? .codex-smoke/plan1-coding-tablet.png
?? .codex-smoke/plan1-proxy-backend-desktop.png
?? .codex-smoke/plan2-2.3.1-coding-desktop.png
?? .codex-smoke/plan2-2.3.2-coding-tablet.png
?? .codex-smoke/plan2-2.3.3-coding-mobile.png
?? .codex-smoke/plan3-3.1.4-runner-desktop.png
?? .codex-smoke/plan3-3.1.4-runner-tablet.png
?? .codex-smoke/plan3-3.3-coding-trial.png
?? .codex-smoke/plan3-3.3-combined-trial.png
?? .codex-smoke/plan3-3.3-design-trial.png
?? .codex-smoke/plan4-4.2-backend-api.png
?? .codex-smoke/plan4-4.2-frontend-ui.png
?? .codex-smoke/plan4-4.2-messy-no-target.png
?? .codex-smoke/plan4-4.2-noop.png
?? .codex-smoke/plan4-4.2-test-writing.png
?? .codex-smoke/plan5-5.1-component-handoff.png
?? .codex-smoke/plan5-5.1-responsive-mobile.png
?? .codex-smoke/plan5-5.1-visual-critique.png
?? .codex-smoke/plan6-6.2-combined-desktop.png
?? .codex-smoke/plan6-6.2-combined-mobile.png
?? basic.js
?? config/backup.env.example
?? docs/agent-runtime-trial-harness-mac-subagent-port-master-plan-v0.1.md
?? docs/agent-runtime-trial-harness-mac-subagent-port-new-chat-handoff-v0.1.md
?? docs/backup-system/
?? docs/evidence/agent-runtime-trial-harness/
?? docs/evidence/backup-system/
?? docs/evidence/hermes4-full-integration/
?? docs/evidence/mac-worker-hardening/plan-1/
?? docs/hermes4-full-integration-closeout.md
?? docs/runbooks/
?? docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md
?? scripts/agent-trials/
?? scripts/backups/
?? src/app/api/coding/
?? src/app/v1/coding/mac-advisory/
?? src/lib/coding/__tests__/agent-trials-ui.test.ts
?? src/lib/coding/__tests__/model-provider-status.test.ts
?? src/lib/coding/__tests__/plain-english-scope.test.ts
?? src/lib/coding/agent-trials-ui.ts
?? src/lib/mac-advisory/
?? src/lib/mac-worker/client.ts
?? src/lib/mac-worker/contract.ts
?? src/lib/mac-worker/registry.ts
?? tests/ui-agent-trials/
hermes4:latest                                           3e79497c9643    9.0 GB    17 minutes ago    
hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M    ce5cb56a7898    9.0 GB    18 minutes ago    
hermes3:8b-abliterated                                   621eb9c2e65e    4.7 GB    4 days ago        
qwen2.5-coder:7b                                         dae161e27b0e    4.7 GB    11 days ago       
    "configured_roots": [
            "status": "configured",
        "capability": "read_only_listing_when_configured",
            "reason": "Only configured roots and allowlists may be reported."
            "model": "ollama_chat/hermes4:latest",
            "configured_ollama_model": "hermes4:latest",
            "probe_ok": true,
            "selected_via": "probe:fallback_default+available_hermes"
            "missing_reason": "not_probed_in_phase_9_1",
            "missing_reason": "not_configured",
            "missing_reason": "not_configured",
        "auth_status": "not_probed",
            "Capability probe only; no Codex task is executed.",
            "alias": "local",
            "model": "ollama_chat/hermes4:latest",
docs/evidence/hermes4-full-integration/hermes4-full-integration-closeout.md
docs/evidence/hermes4-full-integration/increment-1.1-ollama-8tb-model-path.md
docs/evidence/hermes4-full-integration/increment-1.2-hermes4-runtime-smoke.md
docs/evidence/hermes4-full-integration/increment-1.3-model-reference-inventory.md
docs/evidence/hermes4-full-integration/increment-2.1-local-default-patch.md
docs/evidence/hermes4-full-integration/increment-2.2-source-proxy-local-routing.md
docs/evidence/hermes4-full-integration/increment-2.3-coding-status-surface.md
docs/evidence/hermes4-full-integration/increment-3.1-hermes4-tool-compat-probe.md
docs/evidence/hermes4-full-integration/increment-3.2-tool-support-docs-status.md
docs/evidence/hermes4-full-integration/increment-4.1-spirit-health.md
docs/evidence/hermes4-full-integration/increment-4.2-source-proxy-health-status.md
docs/evidence/hermes4-full-integration/increment-4.3-source-proxy-chat-smoke.md
docs/evidence/hermes4-full-integration/increment-4.4-tests-and-typecheck.md
docs/evidence/hermes4-full-integration/increment-5.1-closeout-doc.md
docs/evidence/hermes4-full-integration/phase-1-closeout.md
docs/evidence/hermes4-full-integration/phase-2-closeout.md
docs/evidence/hermes4-full-integration/phase-3-closeout.md
docs/evidence/hermes4-full-integration/phase-4-closeout.md
```

## Closeout result

NO-GO for Hermes 4 daily-driver cutover until live frontend runtime OLLAMA_MODEL is updated from llama3.1:8b to hermes4 and Next is restarted with approval. GO for install, 8TB storage proof, Source Proxy Hermes 4 local route, and Source Proxy Hermes 4 chat smoke.
