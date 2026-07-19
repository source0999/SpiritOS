# Source Proxy Coder Backend 100 (pack v1.1)

This pack defines exactly 100 deterministic, production-path coding tasks for Campaign 3.5. Pack v1.1 refines the GPT-authored v1.0 based on the grok evaluation residuals plus a structural audit of the v1.0 pack. No task content (prompts, fixtures, capabilities, dispositions) was rewritten; the refinements strengthen the oracle, anti-cheat, validation, and operational guidance.

## Files

- `manifest.json` — benchmark identity, counts, thresholds, hard failures, and changelog.
- `tasks.jsonl` — canonical machine-readable task stream.
- `tasks.json` — pretty-printed equivalent.
- `task.schema.json` — task definition schema (unchanged from v1.0).
- `tasks.md` — full human-readable benchmark.
- `oracle-contract.md` — independent scoring, anti-cheat, trace reconciliation, escalation-pack usability rubric, and tuning rules.
- `harness-spec.md` — execution topology, scope calibration, clean-rerun drift tolerances, fixture-generation gate, failure injection, result schema.
- `fixture-blueprints.md` — fixture family index, generation requirements, and coverage matrix.
- `validation-report.json` — structured per-check validator output.
- `_build_v1_1.py` — the generator that produced this pack from the v1.0 seed (kept for reproducibility).

## Exact distribution

```
straightforward_code_change: 25
multi_file_feature: 15
bug_diagnosis_and_repair: 15
repository_search_knowledge_intensive: 10
context_overflow_or_complex_escalation: 10
ambiguous_or_conflicting_request: 5
missing_tool_dependency_model_provider: 5
unauthorized_or_approval_gated_mutation: 5
cancellation_interruption_recovery_resume: 5
deliberately_impossible: 5
```

## Expected disposition distribution

```
COMPLETED_VERIFIED: 70
ESCALATION_CONTEXT_PACK_READY: 10
BLOCKED_OR_DEGRADED_TRUTHFULLY: 20
```

## Non-negotiable rule

The coder sees only the prompt and normal repository context. Expected disposition, expected artifacts, hidden tests, scoring, seed, and oracle checks stay outside the production coder process.

A score improvement is valid only when it comes from a general production-system improvement. Task-ID matching, fixture detection, hidden-test inspection, weakened verification, fabricated traces, or altered expectations are hard failures.

## Trace-event reconciliation (v1.1)

The `required_trace_events` lists are the **target contract** the backend must emit; they are NOT verified against the actual Source Proxy event emissions in this pass. Before the first clean run, these names MUST be reconciled against the real events emitted under `source_proxy/`. A mismatch is a Run-phase-1 preflight failure and MUST be resolved by either aligning the backend to emit the named events or by formally amending this pack — never by silently renaming events or by weakening the trace-to-claim reconciliation.

## Changelog v1.0 -> v1.1

1. Filled every task's `notes` field (all 100 were empty in v1.0).
2. Added a formal 10-dimension escalation-pack usability rubric to `oracle-contract.md`; the `>=90/100` bar is now decomposed into weighted, pass/fail-boundaried dimensions.
3. Added a `## Scope calibration` section to `harness-spec.md` covering the oversized tasks (M15, R10, E01, E06) — explicit complete-vs-escalate boundary and first-clean-run reconciliation rule.
4. Added explicit numeric `## Clean-rerun drift tolerances` to `harness-spec.md` (score drift <=2/task, latency +-25%, retry delta <=2, disposition flips = 0, semantic acceptance delta <=5%).
5. Added a `## Coverage matrix` to `fixture-blueprints.md` mapping adapter claims (LangGraph, OpenHands, retained-context, Obsidian-equivalent, mac_search, scout, openai_agents_sdk_adapter, security_reviewer) to the specific task IDs that must exercise each.
6. Promoted fixture generation to a named gate in `harness-spec.md` phase 2 with seed-leak, decoy-indistinguishability, and deterministic-rebuild sub-checks.
7. Tailored `forbidden_behavior` per category (v1.0 had a single shared list across all 100 tasks).
8. Tailored `randomization` per category (v1.0 had a single shared list).
9. Expanded `hard_failures` into category-specific sets, including new rules: "COMPLETED claim after injected cancellation without recovery trace" (cancellation category) and "fake tool/migration/provider/model success" (missing-tool category).
10. Enriched `oracle_checks` per task with independent AST/HTTP/behavior/nonmutation/category-specific canary layers.
11. Upgraded `validation-report.json` to a structured per-check report that runs jsonschema against the unchanged `task.schema.json` (with a hand-rolled fallback).
12. Added this README's trace-event reconciliation note.

The original v1.0 task content (IDs, titles, prompts, fixtures, capabilities, dispositions, scoring weights) is preserved unchanged.
