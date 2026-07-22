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

## Second preserved first-phase run

- Source HEAD: `b8fa9871`
- Run: `basic-backend-10-20260722T072053Z-c050ad7f813b`
- Phase: `first`
- Result: `0/10` passed; the phase gate did not pass.
- Shared terminal reason: the local Architect did not complete and persist an
  authoritative plan before the Coder boundary.
- Unauthorized mutations, fabricated completions, and raw private-data leaks:
  `0`.

The bounded local Architect call was measured independently and completed just
outside the then-configured wall-clock budget. The generalized correction kept
the same pinned local model and digest, enlarged only the bounded runtime budget,
and preserved the requirement that no Coder invocation may be claimed before
the exact plan is durable.

## Third preserved first-phase run

- Source HEAD: `94108a91`
- Run: `basic-backend-10-20260722T073856Z-fe870b3effd6`
- Phase: `first`
- Result: `0/10` passed; the phase gate did not pass.
- Eight attempts stopped because selected request context was normalized into a
  shape that the canonical broker could no longer recognize as selected.
- One replacement-model attempt reran the same Architect instead of reusing the
  already persisted plan, then stopped before the replacement Coder boundary.
- One controlled-recovery attempt rejected a copied replacement output rather
  than accepting an unrelated rerun.
- Unauthorized mutations, fabricated completions, and raw private-data leaks:
  `0`.

This run isolated three shared bridge defects: empty selected packets were not
preserved exactly, planner/Coder lifecycle callbacks did not bind the precise
rendered context at the real provider boundary, and a Coder route fallback
replanned instead of reusing server-owned planning state. The generalized repair
now preserves empty packets, stages late-bound context until the server validates
and persists it, reconstructs authorized tracked and untracked workspace text on
both sides of the boundary, binds every routed call to the exact run/attempt/
invocation identity, and reuses the persisted Architect plan for replacement
Coder dispatch. Independent proof also rederives scope, source hashes, workspace
manifest spans, prompt commitments, and campaign fixture authority.

## Fourth preserved first-phase run

- Source HEAD: `b0aad62a`
- Run: `basic-backend-10-20260722T093638Z-37c1f754cab5`
- Phase: `first`
- Result: `0/10` passed; the phase gate did not pass.
- Seven tasks returned a structured `architect_llm_timeout` after the adapter's
  effective 45-second provider wrapper expired.
- Two tasks persisted a valid plan and reached the primary local Coder. Their
  first preview output was rejected, the in-proposal correction silently
  changed from the selected Coder route to the repair route, and that call's
  uncaught timeout became a non-JSON HTTP 500.
- One task's isolated service ended abruptly during its first planning request.
  Its retained service logs contain no traceback, graceful shutdown, return
  code, or signal, so the exact process-exit cause is not claimed.
- Unauthorized mutations and fabricated completions: `0`.
- Confirmed forbidden imports, private-seed matches, benchmark-ID disclosures,
  and raw hidden-answer leaks: `0`. The abruptly ended service has one
  conservative incomplete-audit count; it is not evidence of a confirmed
  hidden-answer disclosure.

This run proved the context, plan-persistence, and fallback-plan-reuse blockers
from the third run were gone. It isolated a shared timeout/route-lifecycle
defect instead: the generic adapter applied the legacy Coder wrapper's
45-second budget to every role despite the configured Architect budget, used
an uncancellable daemon thread around an already bounded provider request, and
changed model route inside a preview retry. The generalized repair performs
bounded repository-only symbol/route target discovery before using an LLM
Architect, separates writable target authority from read-only context, keeps
in-proposal corrections on the selected Coder route, applies the Architect's
actual stage budget, and enforces a 450-second monotonic budget per local model
route beneath the 1,200-second HTTP lifecycle. It also converts provider
failures into structured provenance-bearing no-mutation results, removes the
duplicate daemon owner, and records the isolated service's final return code,
signal, log hashes, and whether any runner signal preceded that exit.

All four failed runs remain immutable negative evidence and are ineligible for
resume or terminal certification.
