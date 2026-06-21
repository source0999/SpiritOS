# Plan 0/6 Artifacts

Truth-freeze, reuse-health, risk, and compression artifacts for
`source-proxy-human-brain-full-live-integration-pivot-20260619/plan-00/plan.md`.

Evidence base: tracked source at HEAD `a9ce0c2c`. All evidence is read-only source
inspection; no live invocation was performed or claimed (Plan 0 forbids live integration).

## Reading order
1. `0.1-canonical-active-route.md` — canonical `/coding` route trace + subsystem inventory + causal-identifier presence.
2. `0.2-machinery-health-check.md` — per-subsystem health (central gate, decision pipeline, Cartographer, runtime health, verification, specialists, docker-compose).
3. `0.3-reuse-adapt-retire-matrix.md` — disposition matrix + duplicate-machinery scan.
4. `0.4-human-brain-integration-contract.md` — operator role + required causal-identifier contract + no-conflation rule.
5. `0.5-mvi-contract-and-feasibility.md` — thin-but-real MVI definition, candidate, feasibility table.
6. `0.6-risk-evidence-reviews-authority.md` — risk register, evidence budget, review gates, authority map, hard-stop status.
7. `0.7-compression-decision.md` — proposed compression decision CD-0 (awaits Britton).
8. `plan-00-closeout-verdict.md` — Plan 0 closeout verdict (BLOCKED_HUMAN) + Plan 1 prerequisites.

## Headline finding
`invocation_event_id`, `consumer_event_id`, `trace_id`, and `consumer_subsystem` are
ABSENT across `source_proxy/**/*.py` (zero matches). Existing real identifiers
(`task_id`, `approval_id`, `run_id`) exist on the decision-bearing long-running-task +
central-gate path. The single blocking gap for any future live GO is the missing
causal-event seam — proposed for closure by compression decision CD-0 in Plan 1,
not in Plan 0.

## Status
Plan 0 deliverables COMPLETE. Live GO NOT achieved and NOT claimed (correct for a
truth-freeze plan). Plan 1 progression BLOCKED on Codex deep review GO + operator
check PASS + Britton-approved compression decision + Britton Plan-1 permission.
