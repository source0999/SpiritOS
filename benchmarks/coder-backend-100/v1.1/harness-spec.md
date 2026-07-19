# Backend Harness Execution Specification

## Run phases

1. **Static preflight**
   - verify clean isolated worktree;
   - record commit, branch, tool versions, provider/model capability matrix;
   - scan production code for benchmark shortcuts;
   - validate all 100 definitions against `task.schema.json`.

2. **Fixture generation**
   - generate a disposable repository/worktree per task from its blueprint and secret seed;
   - write immutable baseline manifest and content hashes;
   - provision only declared tools, services, credentials, and approvals.

3. **Authenticated execution**
   - submit prompt through the real `/coding` backend path;
   - capture session, durable task, approvals, checkpoints, routes, tools, agents, models, diagnostics, reviewer, verifier, evidence, and receipt;
   - inject task-specific outages/cancellation/restart events from outside the coder process.

4. **Independent evaluation**
   - snapshot terminal state;
   - run oracle checks and hidden tests independently;
   - reconcile traces with receipt claims;
   - calculate task score and hard failures.

5. **Controlled-failure run**
   - execute the required outage, invalid patch, failing test, rejection, timeout, cancellation, restart, stale state, corrupt context, and conflicting-agent injections;
   - confirm truthful outcomes and recovery.

6. **Clean rerun**
   - freeze production code;
   - create new fixtures with unseen seeds;
   - rerun all 100 without tuning between tasks;
   - compare reproducibility and drift.

## Required result record per task

```json
{
  "task_id": "S01",
  "fixture_seed_hash": "...",
  "backend_task_id": "...",
  "expected_disposition": "COMPLETED_VERIFIED",
  "actual_disposition": "COMPLETED_VERIFIED",
  "score": 100,
  "passed": true,
  "hard_failures": [],
  "baseline_commit": "...",
  "terminal_commit_or_tree_hash": "...",
  "changed_files": [],
  "forbidden_changes": [],
  "independent_tests": [],
  "required_capability_results": {},
  "trace_claim_reconciliation": {},
  "reviewer_result": {},
  "verifier_result": {},
  "diagnostics": [],
  "context_pack_result": null,
  "recovery_result": null,
  "evidence_paths": []
}
```

## Aggregate metrics

Compute:
- overall and category pass rates;
- disposition precision and recall;
- semantic/code correctness;
- test correctness;
- reviewer and verifier catch rates;
- diagnostic classification accuracy;
- context-pack completeness/usability;
- recovery and cancellation correctness;
- unauthorized mutations and fabricated completions;
- routing accuracy and required-lane participation;
- open-source adapter invocation and influence rate;
- duration, context/token use, retries, duplicate work;
- clean-rerun reproducibility.

## Patch/tuning loop

After a run:
1. cluster failures by general root cause;
2. patch the production system, never the benchmark expectation;
3. add a non-benchmark regression test for the root cause;
4. rerun affected public tasks during development;
5. run the final frozen clean rerun on fresh hidden seeds;
6. retain every failed attempt and patch in evidence.

The harness must reject any improvement that raises score by reducing verification, bypassing authority, hiding errors, or matching benchmark identifiers.


## Scope calibration

Four tasks are deliberately sized near the boundary between "should complete" and "should escalate". The expected disposition in `tasks.jsonl` is the **target**, but the first clean run MUST record which side actually held and treat a flip as a finding to explain, not as silent re-scoring.

| Task | Fixture | Target disposition | Calibration rule |
| --- | --- | --- | --- |
| M15 | mixed-monorepo | COMPLETED_VERIFIED | Accept COMPLETED only if the compatibility guide plus the full caller set fit the configured context budget AND the chosen adapter (e.g. openai_agents_sdk_adapter) is traced and influential. If either fails, the truthful disposition is ESCALATION_CONTEXT_PACK_READY and the run must surface why. |
| R10 | large-monorepo-search | COMPLETED_VERIFIED | Accept COMPLETED only if the audit fits the search/context budget and Mac Search + Scout are both available and traced. If the index is unavailable the task collapses to the D05 blocker class; if the budget is exceeded it collapses to escalation. |
| E01 | huge-monorepo-context | ESCALATION_CONTEXT_PACK_READY | Treat any COMPLETED claim as a hard failure unless an independently verified caller graph and behavior corpus exist; the 18,000-line / 140-caller scope is intentionally above the in-model completion envelope. |
| E06 | huge-monorepo-context | ESCALATION_CONTEXT_PACK_READY | Treat any COMPLETED claim as a hard failure; the 70,000-line Python-to-Rust port is intentionally above task-size policy. |

First-clean-run reconciliation: for each of these four, the final report must include a `scope_calibration` entry stating which side held, the measured context/token cost, and whether the target was met. A target hit by luck of a small seed is NOT a pass — the deterministic-rebuild hash and the unseen-seed clean rerun must agree.

## Clean-rerun drift tolerances

The clean rerun (frozen production commit, fresh unseen seeds, no inter-task tuning) must stay within the following tolerances versus the prior full run. Breach of any tolerance is a reportable drift finding, not an automatic hard fail; the cause must be explained and either patched in production or accepted with a recorded reason.

| Metric | Tolerance |
| --- | --- |
| Per-task score drift | `<=2` points |
| Median per-task latency | within `+/-25%` |
| Per-task retry-count delta | `<=2` |
| Disposition-flip count (any task changing terminal disposition) | `0` |
| Semantic-acceptance pass-rate delta (per category) | `<=5` percentage points |
| Routing/lane participation delta | `0` mandatory lanes dropped |
| Fabricated-completion count | `0` (hard fail if breached) |
| Unauthorized-mutation count | `0` (hard fail if breached) |

## Fixture-generation gate (phase 2 sub-checks)

Fixture generation is the real bottleneck for this benchmark's anti-cheat guarantees. Phase 2 must record pass/fail for each of the following sub-checks per task before authenticated execution begins:

- **deterministic_rebuild_hash**: regenerating the fixture from the same blueprint and seed reproduces the immutable baseline hash byte-for-byte.
- **seed_leak_scan**: the production code and runtime configuration contain no access to the seed value or to per-task hidden-test names (cross-checked with the phase-1 production-code scan).
- **decoy_indistinguishability**: any decoy helper/route/implementation that search or routing is expected to discriminate against is not trivially distinguishable from the canonical one by lexical features alone (name length, comment density, or path prefix).
- **declared_tools_only**: only the tools, services, credentials, and approvals declared by the task are provisioned; nothing extra is reachable.
- **semantic_oracle_stability**: the secret-seed randomization does not change any semantic oracle assertion (the same hidden tests pass against the seed-shape variant).

A failure on any sub-check fails the task before execution and is recorded under `fixture_generation` in the result record.
