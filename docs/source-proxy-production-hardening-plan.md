# Source Proxy Production Hardening Plan

status: active

Status date: 2026-05-18
Owner: Britton
Status: active Source Proxy plan

## Source Of Truth

This is the active Source Proxy plan.

`proxyCLI.md` is retired. Do not recreate it and do not continue Phase 11 work from it.

`productionProxy.md` was the upload/staging copy used to establish this plan. This document is the durable repo copy to follow from here.

The research docs below are historical/reference material only:

- `docs/aionui-reference-study.md`
- `docs/agent-wrapper-reference-study.md`
- `docs/spirit-cowork-gap-report.md`

Those docs may contain Phase 11, AionUi, Cowork Console, or provider-layer language. Treat that language as reference or deferred research, not active build authorization.

## Current Boundary

Source Proxy remains the system of record for coding work.

Codex CLI is an experimental worker only. It may produce readonly evidence or proposal evidence when explicitly allowed, but it must not receive approve, apply, commit, or push authority.

Codex mobile is a remote review/control surface only. It can help monitor work, review output, answer questions, and approve Codex-side diagnostic or scoped actions when safe. It cannot bypass SpiritOS approval gates.

Approval, apply, commit, and push remain separate actions:

- approval does not equal apply
- apply does not equal commit
- commit does not equal push
- push requires separate explicit approval

## Deferred Work

Do not build these during this plan:

- AionUi bridge
- Spirit Cowork Console
- scheduled provider tasks
- native SpiritOS mobile execution
- autonomous multi-agent writes
- automatic commit or push
- provider marketplace
- broad MCP/plugin system
- default Codex promotion

These can be reassessed only after daily-use Source Proxy is boring, reliable, and reviewable.

## Release Gates

### Gate A: Baseline Reset Clean

- `proxyCLI.md` deletion is accepted
- stale Phase 11 language is historical or clearly deferred
- `git diff --check` passes
- `npm run typecheck` passes
- Source Proxy safety suite passes
- dashboard failures are fixed or documented as unrelated
- no fake continuation increments remain active

### Gate B: P0 Reliability Clean

- dashboard Vitest failures fixed
- live port 3000 route checks reliable
- `phase-4f-closeout` behavior clarified
- snapshot diagnostics do not create confusing FAIL states
- fresh closeout report is readable and honest

### Gate C: Codex Worker Hardened

- Codex route validation tests pass
- evidence capture and replay are stable
- dangerous flags blocked
- protected and secret paths blocked
- `allowed_files` and `target_file` are preserved
- live route is safely enabled or cleanly config-blocked
- no approve, apply, commit, or push authority

### Gate D: Remote Manual Checks Usable

- Codex mobile workflow documented
- remote manual checks work without RustDesk for common cases
- Termius/SSH fallback documented
- mobile cannot bypass Source Proxy approval gates
- manual-check packets are compact enough to review on a phone

### Gate E: Operator Console Usable

- task queue visible
- task state visible
- blockers visible
- evidence visible
- diff status visible
- tests visible
- approval state visible
- no accidental apply, commit, or push controls

### Gate F: Daily-Use Alpha

- one-command closeout works
- happy path works end-to-end
- failed path is understandable
- rollback hints visible
- Cartographer explains repo state
- Codex can propose safely
- Britton can use desktop or mobile to review work confidently

## Increment Closeout Rule

Every increment must end with:

- manual checks in one copy-paste terminal block
- expected outputs
- debug path
- rollback path
- the next increment to start after Britton pastes verification output

## Current Position

Phase 3 is complete.

- Increment 0.1 is complete: `proxyCLI.md` is intentionally retired.
- Increment 0.2 is complete diagnostically: stale planning references were identified and classified as historical/reference/deferred.
- Increment 0.3 is complete: this source-of-truth document exists.
- Phase 1 is complete: Gate B route, dashboard, and closeout confusion checks are clean.
- Phase 2 is complete: Codex route validation, safety regressions, evidence replay/truncation, and remaining trial hardening are complete without promotion.
- Increment 3.1 is complete: Codex mobile and SSH fallback authority rules are documented.
- Increment 3.2 is complete: compact mobile manual-check packet format is documented.
- Increment 3.3 is complete: phase-4f closeout emits a compact remote evidence receipt.
- Increment 3.4 is complete diagnostically: remote workflow smoke test passed without apply, commit, or push.
- Increment 4.1 is complete: `/coding` shows a read-only unified Source Proxy task queue.
- Increment 4.2 is complete: Codex evidence, diff/output excerpts, final messages, and rollback hints render as review-only artifacts.
- Increment 4.3 is complete: blocked approval/task states show a concrete blocker reason and next safe action.
- Increment 4.4 is complete: the read-only task story persists task IDs, status, blockers, artifacts, test reports, approval state, and rejection state across refresh.
- Increment 5.1 is complete: `/coding` can draft bounded proposal tasks with required target, allowed files, checks, rollback hint, and protected-target blocking.
- Increment 5.2 is complete: `/coding` shows verified diff preview evidence for changed paths, target match, allowed-file match, protected-path status, and keeps approval unavailable when preview checks fail.
- Increment 5.3 is complete: `/coding` shows deterministic verifier and reviewer result cards, labels reviewer findings as advisory, and treats unavailable LLM review as unavailable rather than a strong pass.
- Increment 5.4 is complete: `/coding` approval now requires a known target, known allowed files, clean diff preview, git apply pass, required gates pass, no protected/secret path reason, no action escalation, and an explicit human approval click.
- Increment 6.1 is complete: approved apply now requires an approval ID bound to `task_id`, target, and approved diff; stale IDs are rejected before apply; apply reports no commit or push.
- Increment 6.2 is complete: post-apply verification evidence now records commit proposal blocking, push blocking, pending/not-run checks, and shows those results in `/coding`.
- Increment 6.3 is complete: commit proposals now expose verification status/check evidence, require explicit approval, keep commit disabled in read-only preview, and block failed or incomplete post-apply verification.
- Increment 6.4 is complete: push queue previews now expose remote/ahead/behind status, explicit push blockers, branch-protection review warnings, separate push approval, and no default push action.
- Increment 7.1 is complete: `docs/plan-index.md` now marks the active Source Proxy plan, historical plan material, and deferred topics with explicit `status: active`, `status: historical`, and `status: deferred` labels.
- Increment 7.2 is complete: project-health now reports exact dirty file buckets, ahead/behind/upstream state, expected evidence files separately from other dirty files, concrete next action, and correct fallback blueprint counts for the current repo.
- Increment 7.3 is complete: Blueprint Scribe and proposal routes now expose an explicit proposal-only contract, require review and apply approval, keep direct source-of-truth writes disabled, and test generated proposal target/diff-preview requirements.
- Increment 7.4 is complete: `cartographer-soak-snapshot` now includes an autonomy escalation check proving autonomous apply, commit, push, approval bypass, and docs autopilot action remain disabled; snapshot writes remain the only expected mutation.
- Increment 8.1 is complete: `proxy-closeout` now produces one readable PASS/WARN/BLOCKED report with safety seed, regression, Codex adapter tests, dashboard smoke, live route validation, Cartographer project health, exact blockers, file-change verdict, and a concrete next safe action.
- Increment 8.2 is complete: `docs/source-proxy-regression-matrix.md` maps critical safety guarantees to exact commands, pass signals, failure meanings, debug commands, owner areas, and explicit known gaps.
- Increment 8.3 is complete: Manual Check 9 now normalizes dot-segment diff paths before target review and blocks wrong-file diffs by target/allowed-file mismatch without apply authority.
- Increment 8.4 is complete: `docs/source-proxy-daily-use-runbook.md` now defines the desktop, Codex mobile, SSH fallback, RustDesk, paste-back, stop/ask, and never-approve operator flow.
- Increment 9.1 is complete: provider capability states are now represented separately from agent roles, missing providers are config-blocked/future-optional, and routing/model recommendation remains recommendation-only with no approve/apply/commit/push authority.
- Increment 9.2 is complete: `docs/local-ollama-provider-study.md` records local Ollama inventory, planning/review-only classification, limitations, and future proposal-only adapter requirements without wiring execution authority.
- Increment 9.3 is complete: long-running tasks now expose multi-worker lanes as read-only evidence, `/coding` displays worker evidence lanes with authority stripped, and tests prove no lane can approve, apply, commit, or push.
- Increment 9.4 is complete: `docs/source-proxy-worktree-study.md` records current worktree/branch state, documents why no worktree experiment should start while the tree is dirty, and defines future approval/cleanup rules.
- Increment 10.1 is complete: `docs/spirit-cowork-console-reassessment.md` decides not to build a separate Spirit Cowork Console now and keeps Cowork-like ideas inside `/coding` unless a later workflow cannot fit there.
- Increment 10.2 is complete: `docs/aionui-bridge-reassessment.md` decides not to build an AionUi bridge now, keeps AionUi as UX/reference material only, and preserves the toy-repo-only boundary for future experiments.
- Increment 10.3 is complete: `docs/spiritos-mobile-surface-decision.md` decides not to build a native SpiritOS mobile app now, keeps Codex mobile plus SSH fallback as the near-term flow, and treats `/coding` responsive improvements as the mid-term path.
- Increment 10.4 is complete: `docs/scheduled-provider-tasks-design.md` defers scheduled provider tasks, requires notification-only defaults, and keeps apply, commit, and push behind separate future approvals.
- Increment 10.5 is complete: `docs/limited-autopilot-design.md` keeps limited autopilot deferred, requires docs-only only after long proof, and preserves the kill-switch, rollback-evidence, no-source-edit, no-commit, and no-push boundaries.
- Closeout/consolidation is in progress: `docs/source-proxy-hardening-closeout.md` records review state, dirty-tree buckets, authority boundaries, and the final consolidated verification command.

After Britton accepts closeout/consolidation, do not open a new production plan until the completed hardening work is reviewed, grouped, and staged or committed deliberately.
