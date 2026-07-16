# Campaign 1 Ledger

Schema: `spiritos-campaign-1-ledger/v3`

## Authoritative current closeout record

- Campaign: `spiritos-campaign-1`; plan: [campaign-1-plan.md](campaign-1-plan.md); state: [campaign-1-state.json](campaign-1-state.json).
- Worktree / branch: `/home/source/SpiritOS-campaign-1-20260712` / `codex/spiritos-campaign-1-foundation-20260712`.
- Phase: **Campaign 1 complete**; current phase status: `complete`.
- Increment: `campaign1_final_acceptance`.
- Verdict: `GO_CAMPAIGN_1_COMPLETE`; status: `complete`; GO eligibility: `true`; S1 verified: `true`; commit safe: `true`.
- Critical Campaign 1 blocker: `none`; partial gates: `none`; next gate: `campaign1_complete` (terminal; no further Campaign 1 implementation gate).
- Accepted phases: Phase 0, Phase 1, Phase 2, and Phase 3.
- Accepted authority requirements: AR-001, AR-002, and AR-003.
- Campaign 2 started: `false`. Campaign 2 remains a guarded no-start stub only.
- Candidate implementation head: `007bb4ea8288284fb3c5600ae8fbd189b334ed80`; the current atomic control-plane checkpoint records its parent under `parent_of_atomic_checkpoint` policy.
- Authoritative authenticated lifecycle receipt: `docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json`; `truth_status=GO`, `commit_safe=true`, all required stages `evidence_complete=true`, and no failed requirements.
- Mandatory accepted profile counts: Source Proxy authority/task 85; coding backend 133; canonical coding frontend 193; canonical shell 61; Cartographer 263; Design route 3; SpiritFlix operator 3. The bounded-heap production build, continuity, authority, test-profile registry, target-adapter, evidence, secret-scan, authenticated lifecycle, anti-cheat, Undo/reset, and clean-rerun checks passed within their stated ceilings.
- Protected heads: Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`; SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`; architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`.
- Preservation: SpiritFlix `_worktrees/` is borrowed and untouched. The recovery quarantine at `/home/source/SpiritOS-campaign-1-20260712.recovery-quarantine-20260715T021242-0400` is pre-GO recovery material, remains preserved, and was not restored because it contains no unique uncommitted Campaign work.
- No push, protected-worktree mutation, quarantine restore, credential disclosure, secret commit, or Campaign 2 start occurred.

## Accepted implementation map

| Area | Accepted result | Primary evidence |
| --- | --- | --- |
| Phase 0 | neutral truth, provenance, no-reversion, and borrowed-worktree containment accepted | baseline and protected-head policy |
| Phase 1 / AR-001 | server-owned administrative authority, durable issuance/consume/finalize, and browser proof accepted | `campaign-1-evidence/ar001-admin-operator-lifecycle-20260714.md` |
| Phase 1 / AR-002 | Cartographer has one canonical proposal/selection path and legacy mutations fail closed | `campaign-1-evidence/cartographer-durable-selection-20260714.md` |
| Phase 1 / AR-003 | Design durable preview/writeback acknowledgement envelope accepted | `campaign-1-evidence/design-writeback-acknowledgement-20260714.md` |
| Phase 2 | shared contracts and enforced product/labs/fixture boundaries accepted | `a36c4437` |
| Phase 3 adapter | strict canonical Python target identity through execution, verification, acknowledgement, and evidence | `630b6632` and accepted lifecycle receipt |
| Phase 3 duplicates | only proven obsolete target-mode helpers removed; compatibility, defense, labs, fixture, and archive paths retained intentionally | `edf29096`, `84271f66` |
| Phase 3 profile truth | production frontend excludes the labs-only Command Center profile; registry documents both ceilings | `007bb4ea` |
| Phase 3 lifecycle | model-authored bundle, approval, apply, managed/direct Chromium proof, anti-cheat, Undo/reset, clean baseline, and clean rerun accepted | `docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json` |

The `operator-session` authority boundary is accepted and retained as a server-owned prerequisite for the AR-001 and Prompt 1 lifecycle evidence.

## Historical chronology — non-current and superseded

The following facts are retained only for recovery provenance. They are not open gates, current blockers, current phase status, or current verdict fields.

- Before the dedicated least-privilege E2E credential was provisioned, the authenticated lifecycle failed closed for its absence. That historical blocker was resolved by the accepted redacted lifecycle receipt above.
- Before the canonical-shell owner decision and implementation, a live-caller/labs migration decision was pending. That historical owner decision was resolved; Phase 3 is accepted.
- Earlier profile counts (authority/task 83, coding backend 131, coding frontend 258, and Design 32) belong to superseded suites or pre-reconciliation runs. They are not the current acceptance matrix.
- The 14B local candidate exhausted GPU memory while Chromium was concurrent. The isolated proof used the already-installed 7B Coder successfully; this is a resolved lane diagnostic, not a Campaign blocker.
- Earlier duplicate-path, fixture-reset, command-ownership, and evidence-externalization increments are preserved by their commits and receipts. Their former next-gate text is superseded by the terminal state above.

## Closeout rules

- The JSON state is the machine-readable source for autoloop completion. This Markdown ledger is a human reconciliation record and is never parsed to infer JSON values.
- Any future change that reopens a Campaign 1 gate must first change the JSON state to a non-terminal, non-GO checkpoint and record a new explicit closeout decision; stale historical prose cannot reopen the campaign.
- Campaign 2 requires a separate authorization and is not implied by this terminal record.
