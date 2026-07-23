# Campaign 3.5 Milestone 13 Repair Evidence

Date: 2026-07-23 UTC

Repository: `/home/source/SpiritOS-campaign-3-5-execution-20260719`

Branch: `codex/campaign-3-5-execution-20260719`

Starting HEAD: `5705acf3a9ec110bb1b84959bfc4e455e8541045`

Remote: `/home/source/SpiritOS`

## Scope and result

This milestone repairs the deterministic reviewer false positive in which a
literal found in an unrelated changed file could satisfy a target-file
requirement. It also completes the generalized production support needed by
the Basic ten-task gate: bounded local participant isolation, durable failure
containment, multi-file task authority, exact pre-apply artifact snapshots,
artifact-specific evidence, transformation verification, active
import/export preservation, and independent receipt recomputation.

Reviewer evidence is now bound to the requirement, intended artifact, actual
artifact inspected, baseline and applied hashes, relevant hunk, task, attempt,
and extraction method. Existing secondary artifacts require server-owned
snapshots or plan context. Coarse directory scope never promotes a
model-selected file into semantic-review authority.

The authorization grammar is fail-closed for negated, excluded,
non-directive, and reference-only path/test/helper language. Narrow positive
capabilities remain available for one focused test artifact or one new shared
helper when exact trusted snapshots and structural bindings prove intent.
Python imports are AST-checked; JavaScript/TypeScript module bindings are
extracted only from active syntax and resolved to the exact target path.

No benchmark task IDs, fixture-answer branches, expected patches, hidden
oracle values, private reference solutions, hosted-provider fallback,
unbounded retries, synthetic traces, or reviewer/verifier bypasses were added.

The first formal run at the original milestone head then exposed one shared
adapter/orchestrator protocol defect before any task crossed into apply: the
generic adapter emitted a bare snapshot JSON digest while the orchestrator
compared it directly with its canonical `sha256:`-prefixed representation.
The boundary now accepts only an exact lowercase bare or prefixed SHA-256
claim, recomputes the digest from the snapshots, and rejects every malformed
or mismatched value. The adapter now emits the canonical prefixed form using
the same Unicode-safe JSON serialization as the orchestrator. Downstream
receipt and proof comparisons remain exact; they were not relaxed.

The next fresh formal run at that digest-boundary head crossed the real
authenticated lifecycle for seven tasks and proved that the digest repair
worked. It also isolated two further generalized runtime boundaries. First,
production proof incorrectly required Cartographer transfer evidence for a
direct generic-workspace run even when the server-owned fixture authority was
exact, all Cartographer state was explicitly absent, and the immutable
artifact correctly carried an empty Cartographer identity. The proof now
treats Cartographer as inapplicable only for that exact state. It re-resolves
the live fixture authority, requires all three canonical Cartographer fields
to be present and `None`, requires a well-formed causal-event stream with no
`cartographer_*` event, requires an exactly empty artifact identity, and
applies the same invariant to every sealed repair attempt. Partial,
contradictory, missing, malformed, or mixed-mode history remains ineligible.

Second, a transient local Coder timeout returned immediately even though the
existing preview budget allowed three attempts. Timeout and router failures
now retry only inside that existing three-attempt bound; route-budget
exhaustion still stops immediately. Each failure is retained as an authorized
provider-transport call with no claimed response. Adapter accounting permits
at most two such failed Coder calls, requires a later successful Coder call,
and rejects failed Architect/Reviewer calls, malformed types or hashes,
unauthorized calls, terminal failures, and over-budget sequences. The
orchestrator and independent production proof recompute that accounting; the
last successful Coder response remains the exact producer identity.

The existing two-attempt Architect JSON loop was deliberately not increased.
The affected formal task consumed about 189 seconds for two invalid responses;
a third identical call could consume the 450-second route budget and starve the
Coder without addressing the systematic formatting failure.

## Validation

All commands used the pinned local Python:

`/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python`

and isolated Source Proxy data, approval-state, and long-running-task paths.

- Final affected nine-module suite: `431 passed, 48 subtests passed` in
  `28.45s`.
- Full long-running/backend, Basic gate-runner, and coding regression surfaces:
  `279 passed, 46 subtests passed` in `182.07s`.
- Anti-cheat, repair-loop, authority, trace, receipt, and Basic-asset suite:
  `194 passed` in `20.97s`.
- Final authority module after lexical hardening: `149 passed`.
- Follow-up snapshot-binding focused suite: `104 passed` in `19.25s`.
- Follow-up nine-module reviewer/orchestrator/proof sweep: `455 passed, 77
  subtests passed` in `56.09s`.
- Follow-up full long-running/backend, Basic gate-runner, and coding regression
  surfaces: `279 passed, 46 subtests passed` in `195.42s`.
- Direct proof/retry repair targeted suite: `171 passed` in `20.30s`.
- Final affected twelve-module sweep: `438 passed, 48 subtests passed` in
  `101.49s`; the before/after WIP diff SHA-256 was identical.
- Final long-running/backend, Basic gate-runner, and coding-regression sweep:
  `279 passed, 46 subtests passed` in `185.08s`; the before/after WIP diff
  SHA-256 was identical.
- Final anti-cheat, repair, approval, authority, trace, fixture, and Basic-asset
  sweep: `309 passed` in `28.14s`; the before/after WIP diff SHA-256 was
  identical.
- Five immutable direct-generic states from the second formal run (tasks 2, 3,
  4, 8, and 9) were independently re-derived under their own mode-`0600`
  server authority manifests; all five now return
  `terminal_proof_eligible=True` with no proof failures.
- All 18 changed/new Python files parsed successfully with `ast.parse`.
- `git diff --check`: clean.
- No unexpected test-created worktree files were present.

Ruff is not installed in the pinned environment, so no Ruff result is claimed.
The known synthetic outer Core/Full asset baseline test is outside the Basic
gate scope; its fixture omits `expected_disposition` and was not changed or
used to weaken Basic validation.

## Independent review

Two independent read-only audits completed after the final fixes.

- Authority/reviewer audit: no blocker; exact negative and positive probe
  matrix passed, with `320 passed, 48 subtests passed` in its five-module run.
- Final diff audit: no material blocker; its final affected sweep reported
  `562 passed, 94 subtests passed`, all 18 Python files parsed, and no
  benchmark, hidden-answer, seed, or oracle coupling in production additions.

Both audits verified artifact/snapshot authority, bounded retry behavior,
durable participant failure state, independent proof recomputation, and the
absence of benchmark-specific production branches.

Two additional read-only audits reviewed the direct-generic and transient-call
follow-up. After adversarial hardening for contradictory causal events, mixed
repair modes, missing or boolean counts, boolean indices, non-string errors,
numeric hashes, unauthorized calls, and malformed terminal sequences, both
reported no remaining blocker. One audit reproduced the five immutable
formal-state proof results above; the other reproduced a real adapter-level
timeout-to-success path with terminal provenance, one context callback, exact
producer binding, and a clean worktree.

## Recovery

Original milestone pre-commit recovery directory:

`/home/source/.source-proxy-recovery-campaign-3.5-m13-final-20260723T021622Z`

- `wip.patch` SHA-256:
  `ffd4f27ce368d7dacd276588a0dbd67eeee5c95cf8acd6ab79358a1914cdd324`
- `manifest.txt` SHA-256:
  `31147383f48045b98c8c123cf3b7ccaccdce49bc249b3daa9c4aac9d8db3e0c3`
- Both files have mode `0600`.

Follow-up digest-boundary recovery directory:

`/home/source/.source-proxy-recovery-campaign-3.5-m13-digest-final-20260723T030154Z`

Its mode-`0600` `wip.patch` captures the complete six-file follow-up diff,
including this evidence update, and its mode-`0600` `manifest.txt` records the
starting head, exact worktree inventory, and diff stat. Their final hashes are
reported in the closeout for this follow-up.

The initial ten-file WIP recovery remains preserved separately at
`/home/source/.source-proxy-recovery-campaign-3.5-m13-5705acf3/`.

## Formal gate state

The first formal phase at source head
`a9f208c6b333872450134a3f0a083212d3d6d3a4` remains immutable negative
evidence:

- Run: `basic-backend-10-20260723T022049Z-5dfbb6d061a5`.
- Phase manifest SHA-256:
  `3065efeb56167f52e05d85f95b167dd00767592522f1865278e4097a7841282a`.
- Aggregate SHA-256:
  `fbded219d6543f6b7e1a1d65fe0415502cfff27e744ab94ee45d20a68cecdd0a`.
- Result: `0/10` passed and no authenticated execution lifecycle crossed.
  Seven unrelated tasks stopped at
  `coding_semantic_review_snapshot_target_mismatch`; the remaining three
  stopped at bounded model/preview failures.
- Safety: zero unauthorized mutations, fabricated completions, hidden-answer
  leaks, changed paths, oracle/reference imports, or seed exposure. All ten
  terminal dispositions were truthful, and source head/index stayed unchanged.

The second fresh first phase at source head
`b90cd5b9049d9dd53e06b2e02b43d8dbf6513fa2` is also preserved as immutable
negative evidence:

- Run: `basic-backend-10-20260723T030359Z-150dc8827fc1`.
- Phase manifest SHA-256:
  `d81eb6224dfdc579877fbd25b579a5c5d9e835a26255347d0d3f9850506b2607`.
- Aggregate SHA-256:
  `d92e540fbbf9c101de47d68b60a2a09a3f2c33a7a48bce68f9744286e0bbe138`.
- Result: `0/10`, with seven authenticated execution lifecycles, seven exact
  approvals, and seven execute attempts. Tasks 2, 3, 4, 8, and 9 applied safe
  model-authored changes and passed public/independent verification before the
  now-repaired direct-generic production-proof applicability defect. Task 1
  additionally retained a truthful isolated anti-cheat worker failure. Task 5
  exhausted the primary preview and then timed out on its controlled fallback;
  task 6 correctly blocked an out-of-authority test-file proposal; task 7
  received two invalid Architect JSON responses; task 10 exhausted bounded
  preview repair.
- Safety: zero unauthorized mutations, fabricated completions, hidden-answer
  leaks, oracle/reference imports, or seed exposure. All ten dispositions were
  truthful, and source head/index stayed unchanged.

A completely fresh first phase must start only after this generalized follow-up
repair is committed, pushed, and verified clean. The failed manifest will not
be resumed. A clean unseen-seed rerun is permitted only if the new first phase
passes every numerical and hard-safety criterion.

Campaign 4 remains exactly
`PAUSED_FOR_CAMPAIGN_3_5_BACKEND_PROOF`; implementation, accepted commits, and
push flags remain `false`.
