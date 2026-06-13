# New Chat Handoff

Use this handoff in a new ChatGPT/Codex planning chat.

Current state: Source Proxy v0.2 Artifact Repair Intelligence planning docs were created under `docs/evidence/source-proxy-v0.2-artifact-repair-plan/`. This is plan-only work. No implementation has started.

Evidence inspected:

- `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/`
- `docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/`
- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/`
- Revamped `diagnostic-summary.md`, `manifest.json`, `behavior-check-results.json`, `artifact-review-summary.json`, `artifact-behavior-report.html`, and all 11 per-run receipt/score/transcript/diff/evidence-packet sets.
- v0.1 `canonical-truth-contract.md`, `behavior-fixture-contract.md`, and `v0.1-readiness-report.md`.

Missing evidence: `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612-real-behavior-audit/` was not found.

What v0.1 proved: Source Proxy can preserve evidence, receipts, transcripts, scores, diffs, review pages, canonical truth labels, behavior fixtures, and permission boundaries. v0.1 is a GO for an evidence-backed foundation only, not autonomous execution.

What v0.2 is for: bridge from truth-telling diagnostics into limited local repair coaching around Qwen. Target flow is prompt, intent resolver, behavior contract, generation, preview check, behavior check, failure packet, limited repair, re-test, final verdict, and handoff if needed.

Current diagnostic results: Browser-confirmed useful PASS examples include homepage and timer. Diagnostic-summary PASS examples also include todo and weather, but they need durable browser probes before being counted as stronger behavior proof. Known behavior failures are calculator (`2 + 3 =` returned `0`), dark theme (class changed but computed colors did not), habit tracker (static hard-coded habits), notes markdown-only, and missing preview/artifact cases for music player, password checker, and drawing pad. Planning baseline is about 4/11 useful PASS, target v0.2 is 7/11 or 8/11 without cheating, stretch 9/11, required truth target 0 known false positives.

Created files:

- `README.md`
- `v0.2-plan.md`
- `evidence-inventory.md`
- `phase-index.md`
- `implementation-increments.md`
- `acceptance-criteria.md`
- `diagnostic-lessons.md`
- `qwen-local-limitations.md`
- `verification-matrix.md`
- `risk-and-permission-rules.md`
- `new-chat-handoff.md`
- `plan-closeout.md`
- `plan-findings.json`

Permission boundaries: no Source Proxy patch, no generated artifact patch, no provider/API calls, no worker starts, no diagnostic reruns, no Obsidian writes, no production source changes, no git operations, no hidden background jobs, no automatic high-usage escalation.

What Britton wants next: review the v0.2 plan and decide whether to approve implementation Phase 0 or Phase 1. No implementation starts without Britton approval.
