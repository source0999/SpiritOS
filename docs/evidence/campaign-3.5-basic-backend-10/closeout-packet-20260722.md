# Source Proxy autonomous repair closeout packet - 2026-07-22

## Disposition

Work is paused for a clean handoff because the current usage window is nearly
exhausted. The autonomous-repair goal remains active. The Basic Backend 10 gate
has **not** passed, milestone 13 has not been committed, and Campaign 4 must
remain paused.

Do not report completion from this state. The correct terminal assessment is
`LOCAL_PROXY_BASIC_CODING_GATE_NOT_YET_PASSED`.

## Authoritative source state

- SSH alias: `spirit`
- Linux worktree: `/home/source/SpiritOS-campaign-3-5-execution-20260719`
- SMB edit path: `Z:\SpiritOS-campaign-3-5-execution-20260719`
- Branch: `codex/campaign-3-5-execution-20260719`
- Pushed implementation baseline before any documentation-only closeout commit:
  `e3c0506d7a55cc0e690206e84a884e19ffb8cd0f`
- HEAD subject: `milestone-12-register-generic-durable-approval`
- The remote branch was re-read with `git ls-remote` and matched this baseline.
  Re-read the actual branch HEAD on resume because the closeout documents may
  be committed separately without the WIP implementation.
- Python:
  `/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python`
- Required Campaign 4 state: `PAUSED_FOR_CAMPAIGN_3_5_BACKEND_PROOF`

Git and tests must run through SSH. Edit through the SMB path with
`apply_patch`. Stage only explicit paths; never use `git add -A`, never force
push, and do not rewrite or backfill failed evidence.

This packet path is normally covered by the repository's `/docs/evidence/**`
ignore rule. Its first preservation therefore requires an explicit
`git add -f docs/evidence/campaign-3.5-basic-backend-10/closeout-packet-20260722.md`;
verify tracking with `git ls-files` on resume.

## Completed and pushed through milestone 12

The pushed line of work repaired the shared production path rather than adding
task-specific answers. In particular it now:

1. Persists the authoritative Architect plan before the first Coder boundary.
2. Preserves selected context and binds planner/Coder lifecycle evidence to the
   actual routed invocation.
3. Reuses the persisted plan during controlled route fallback.
4. Performs bounded repository-only target discovery and keeps writable target
   authority separate from read-only context.
5. Applies role-correct local-model budgets and converts provider failures to
   structured, non-mutating results.
6. Registers `generic-workspace` at the durable approval boundary while
   retaining fail-closed rejection of unknown plugin identities.

Milestone-12 validation completed before push:

- generic durable boundary: `1 passed`
- approval authority suite: `20 passed`
- Basic gate runner suite: `68 passed`
- long-running and coding regression pack: `211 passed, 46 subtests passed`
- independent review: approved with no blockers
- remote matched local HEAD and the worktree was clean after push

## Preserved formal first-phase evidence

Every run below is immutable negative evidence and is ineligible for resume:

| # | Source HEAD | Run suffix | Result | Generalized blocker isolated |
|---|---|---|---|---|
| 1 | `36920dce` | `T051718Z-4fd92e8e5ee5` | `0/10` | authoritative plan missing |
| 2 | `b8fa9871` | `T072053Z-c050ad7f813b` | `0/10` | Architect plan did not complete/persist in budget |
| 3 | `94108a91` | `T073856Z-fe870b3effd6` | `0/10` | context normalization and fallback-plan reuse |
| 4 | `b0aad62a` | `T093638Z-37c1f754cab5` | `0/10` | role timeout and route-lifecycle defects |
| 5 | `66cdd300` | `T110326Z-9e6150a9b0d7` | `0/10` | stale durable plugin allowlist |
| 6 | `e3c0506d` | `T114139Z-4a4ce6bc59bb` | `0/10` | independent participant could not resolve sealed server-state diff |

The sixth run is the latest formal evidence. Five tasks crossed proposal,
preview, approval, and execute and reached `applied_needs_verification`. Their
verification requests then returned a non-JSON HTTP 500 before a durable
verification response, leaving their raw service status unknown and terminal
receipts untruthful. Source inspection diagnosed the participant-storage and
failure-containment path described below as the shared explanation. One task
entered the verifier-directed repair path and exhausted it, three exhausted
preview repair, and one stopped on a structured execute 422. Across the run
there were zero unauthorized mutations, zero fabricated completions, and zero
hidden-answer leaks.

Latest manifest:

`/home/source/.source-proxy-basic-backend-10-evidence-20260722/basic-backend-10-20260722T114139Z-4a4ce6bc59bb/first/phase-manifest.json`

Manifest SHA-256:
`d46255ca6995b339a1757672c5132e13dd375fd4ea01f442a1877f9ea404614c`

The sanitized six-run narrative is in
`docs/evidence/campaign-3.5-basic-backend-10/first-generalized-failure-20260722.md`.

## Current uncommitted implementation WIP

Before this packet was added, the working tree contained ten modified files,
667 insertions, and 68 deletions. Its code-only binary-diff SHA-256 was
`cb789c8528018ba6b95d9419527722fb334155e59a285f931d3b6ca7aef11b4c`.
No WIP code has been committed or pushed.

### Participant storage and failure containment

- `source_proxy/coding/participants.py`
  - Adds an artifact-hash-bound optional `backup_storage` binding.
  - Resolves `server-state:` approved diffs using strict schema, canonical-path,
    containment, hash, permission-mode, and no-symlink checks. It does not add
    a UID/GID ownership check.
  - Passes only `SOURCE_PROXY_DATA_DIR` to the participant worker.
  - Converts worker timeout/OS failures and permits only bounded sanitized child
    reasons.
- `source_proxy/coding/orchestrator.py`
  - Contains Reviewer, Verifier, Anti-Cheat, and evidence-recorder participant
    failures as durable structured lane failures instead of raw HTTP 500s.
- `source_proxy/tests/test_coding_participants.py`
- `source_proxy/tests/test_generic_backup_storage.py`
- `source_proxy/tests/test_coding_orchestrator.py`
  - Add independent server-state reads, tamper/mode/binding rejection, a real
    subprocess boundary, and durable participant-failure regressions.

### Generalized preview and constraint repair

- `source_proxy/target_plugins/generic_workspace.py`
  - Includes bounded missing requirement details in retry feedback.
  - Removes changing strategy text from convergence equivalence.
- `source_proxy/tests/test_generic_workspace_multifile.py`
  - Adds direct feedback-bounding and convergence coverage.
- `source_proxy/planning/architect.py`
  - Stops trusting model-invented exact content constraints and derives them
    from task/source evidence; ignores quoted path values as literal content.
- `source_proxy/planning/reviewer.py`
  - Attempts multi-file materialization and aggregate constraint checks.
- `source_proxy/verification/diff.py`
  - Treats quoted `.py` values as paths rather than exact textual requirements.

## Validation of the uncommitted WIP

Completed checks:

- `git diff --check`: clean
- storage/failure-focused subset: `8 passed, 59 deselected`
- bounded affected-suite run on all seven relevant test modules:
  `192 passed, 1 failed, 7 subtests passed`

The one failure is real and must be fixed before commit:

`source_proxy/tests/test_reviewer_deterministic.py::DeterministicReviewerTests::test_wrong_target_diff_does_not_satisfy_target`

The new aggregate reviewer logic allows `RequiredLiteral` in
`src/other.tsx` to satisfy a plan whose authoritative target is
`src/example.tsx`. The fix must preserve target-scoped authority while still
supporting legitimate requirements assigned to explicitly writable secondary
files. Keep the existing wrong-target regression, add an authorized
secondary-file success case, and ensure forbidden-content findings identify the
actual offending path.

Not yet completed for this WIP:

- adversarial Architect tests proving model-invented exact constraints are
  discarded while real source imports remain preserved
- focused `.py` quoted-path verification coverage, including a countertest that
  a legitimate exact filename string is not silently discarded merely because
  it has a recognized suffix
- resolution of whether controlled fallback must receive sanitized primary
  failure feedback
- one explicit provider-call cap across nested preview/reviewer retries
- full long-running, gate-runner, and coding regression suites
- independent milestone-13 review
- commit, push, clean-state verification, or fresh formal first phase

## Exact restart checklist

1. Confirm the branch, HEAD, remote, and only the documented WIP plus these two
   closeout documents are present. Do not discard or overwrite user changes.
2. Fix the deterministic Reviewer wrong-target regression first.
3. Add the missing Architect, Reviewer, and diff-verification regressions.
4. Run the focused participant/storage/orchestrator tests and these seven
   affected modules until fully green:
   - `source_proxy/tests/test_coding_participants.py`
   - `source_proxy/tests/test_generic_backup_storage.py`
   - `source_proxy/tests/test_coding_orchestrator.py`
   - `source_proxy/tests/test_generic_workspace_multifile.py`
   - `source_proxy/tests/test_architect_deterministic.py`
   - `source_proxy/tests/test_reviewer_deterministic.py`
   - `source_proxy/tests/test_diff_verification.py`
5. Run these full regression surfaces:
   - `source_proxy/tests/test_long_running_tasks.py`
   - `source_proxy/tests/test_campaign_3_5_basic_gate_runner.py`
   - `source_proxy/tests/test_coding_regression_pack.py`
6. Obtain an independent read-only diff/security review. Address every blocker.
7. Re-read and finish the sixth-run sanitized evidence entry if implementation
   details changed.
8. Commit milestone 13 using only explicit paths, push normally, and verify the
   remote matches and the authoritative worktree is clean.
9. Reconfirm Campaign 4 is exactly
   `PAUSED_FOR_CAMPAIGN_3_5_BACKEND_PROOF`.
10. Run a completely fresh formal first phase at the new pushed HEAD. Never
    resume any of the six failed manifests.
11. Only if the first-phase gate passes its score, mandatory-task, repair,
    mutation, fabrication, and leak criteria, preserve the success evidence,
    commit/push it, then run the required unseen-seed clean rerun against the
    passing first manifest and its allowed descendant HEAD.
12. Audit every prompt requirement, mark the goal complete only after both
    phases pass, and end the final report with the required terminal token.

Fresh first-phase command template:

```bash
cd /home/source/SpiritOS-campaign-3-5-execution-20260719
PY=/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python
"$PY" scripts/run-campaign-3-5-basic-backend-gate.py \
  --source-root /home/source/SpiritOS-campaign-3-5-execution-20260719 \
  --output-root /home/source/.source-proxy-basic-backend-10-evidence-20260722 \
  --python "$PY" \
  --expected-head <new-pushed-head> \
  --phase first
```

Clean rerun command template, only after a passing first phase:

```bash
cd /home/source/SpiritOS-campaign-3-5-execution-20260719
PY=/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python
"$PY" scripts/run-campaign-3-5-basic-backend-gate.py \
  --source-root /home/source/SpiritOS-campaign-3-5-execution-20260719 \
  --output-root /home/source/.source-proxy-basic-backend-10-evidence-20260722 \
  --python "$PY" \
  --expected-head <allowed-descendant-head> \
  --phase clean_rerun \
  --resume-first <passing-first-phase-manifest>
```

## Non-negotiable safety and evidence rules

- Use only pinned local inference; do not call hosted inference APIs.
- Do not inspect or expose secrets, hidden oracle inputs, raw private model
  outputs, benchmark solutions, or task-specific reference implementations.
- Do not broaden process inspection.
- Do not alter fixtures or weaken the gate to manufacture a pass.
- Preserve all failed formal runs as negative evidence.
- Do not backfill existing failed artifacts with the new storage binding.
- Do not unpause Campaign 4 until both required Campaign 3.5 phases pass.
- Never call the goal complete merely because the implementation looks
  plausible; the fresh first phase and unseen-seed clean rerun are required.
