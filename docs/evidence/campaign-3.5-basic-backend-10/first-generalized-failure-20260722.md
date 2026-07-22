# Basic Backend 10 first-run generalized failure — 2026-07-22

This record is a sanitized infrastructure summary. It contains no private task
inputs, reference implementations, or task-specific repair guidance.

- Source HEAD: `36920dce`
- Run: `basic-backend-10-20260722T051718Z-4fd92e8e5ee5`
- Phase: `first`
- Result: `0/10` passed; the phase gate did not pass.
- Authenticated lifecycle executions completed: `0/10`.
- Shared terminal reason: `authoritative_plan_missing` before any coder proposal.
- Attempts: one non-mutating proposal attempt per task.
- Unauthorized mutations: `0`.
- Fabricated completions: `0`.
- Raw private-seed, reference-import, and benchmark-task-ID leaks: `0`.
- Task solutions produced by this run: `0`.

The run exposed two generalized harness/bridge defects rather than ten task
failures:

1. The generic workspace adapter generated the repository-aware architect plan,
   while the durable orchestrator required an authoritative plan before it was
   allowed to invoke that adapter.
2. The production service import attestation depended on interpreter shutdown;
   inherited startup hooks and supervised shutdown could prevent a single,
   deterministic completion snapshot.

The generalized repair persists the adapter's exact architect plan through a
plan-ready callback before the first coder provider call, records the planner
and coder context bindings in that order, gives the service interpreter sole
ownership of the import audit, and requests a verified final snapshot before
shutdown. The gate also now requires separate first and clean-rerun commands,
reopens raw HTTP evidence to rederive proof and trace, and tightens structural
oracle checks against non-behavioral false positives.

This failed run remains preserved as negative evidence. It is not eligible for
resume or terminal certification.
