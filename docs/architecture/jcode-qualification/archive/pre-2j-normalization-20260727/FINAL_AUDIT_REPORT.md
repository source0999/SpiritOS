# Final JCode Qualification Audit

Verdict: `FREEZE_VERIFIED__JCODE_LIMITED_GO_WITH_REMEDIATIONS`

1. **Canonical repository/worktree/branch/HEAD.** Source Proxy at
   `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726`, branch
   `codex/source-proxy-jcode-qualification-20260726`, based on
   `1641ddb1c71e6b364e98aa9aeff4b4719627d926`.
2. **Current campaign.** C0 and C1 accepted; C2 implementation/negative proof
   complete with operator acceptance pending; C3-C6 not started.
3. **Campaign 4.** Historical `/coding` UI Campaign 4 remains paused; future
   Gate B Scout/Obsidian Campaign 4 remains not started.
4. **Contradictions.** Stale manifest checkout/head, dirty daily master versus
   campaign authority, C2 implementation versus acceptance, missing current
   remote refs, historical checkout drift, separate C3.5 repository, Campaign 4
   name collision, extended-lane registry versus causal wiring, registered
   models versus availability, JCode safety design versus normal execution,
   partial sidecar API, and absent canonical Terra High component are recorded
   in `CAMPAIGN_CONTRADICTION_MATRIX.md`.
5. **Lane truth.** One Proxy orchestrator owns durable execution. Core
   approval/reviewer/verifier/anti-cheat/evidence lanes are active/proven;
   extended/research/Mac/advisory lanes are partial; several challengers are
   configured only; LangGraph/OpenHands/Agents SDK are absent; UI runtime proof
   is absent/paused. Full 40-lane matrix is attached.
6. **JCode pin.** Commit
   `2444e7b6bc80d421ae3ee404081bdb41150a1830`, workspace/release ancestor
   `v0.58.0`; later `v0.59.0`/`v0.60.0` tags are not ancestors of the pin.
7. **JCode build/test.** Locked no-default vendored-OpenSSL check passed; 34
   provider/API and 9 safety tests passed. Default feature compilation had a
   recorded host-resource `rustc SIGSEGV`. Isolated harness behavior reproduced
   file mutation and Bash execution.
8. **Layer placement.** Primary Layer 4 cognitive execution runtime, with
   subordinate Layer 2/6/8 extensions only.
9. **May own.** Bounded within-task loop, permitted discovery/model/tool calls,
   bounded retry, full raw event return, and claimed executor result.
10. **Must never own.** Human/task authority, database/state, model route,
    approvals, worktree/protected-path policy, review, verification, anti-cheat,
    terminal outcome, benchmark oracle, commit, push, or deployment.
11. **Selected mode.** Option A, one fresh external CLI process per task, behind
    a disabled Proxy-owned adapter and external containment.
12. **Rejected modes.** Sidecar has incomplete permission/session bridge and
    contamination risk; embed/vendor has excessive coupling/dependency burden;
    concepts-only is fallback; no-integration remains current runtime posture.
13. **Campaign amendment.** Proposed non-advancing `Campaign 2-J - JCode
    Executor Qualification`, eligible only after C2 acceptance.
14. **Experiment.** New 20-task manifest created (5 read-only, 5 single-file, 5
    multi-file, 3 retry, 2 ambiguity), SHA-256 `149e2cdc7407f19cb4b0a431edb246affaaaeebabaa0694a22af57dcb6cadbb6`;
    no task or frozen benchmark was run.
15. **Safety.** Normal JCode mutation is not universally safety-gated. External
    filesystem/network/process/evidence controls remain live-run blockers.
16. **Files changed.** 29 new files only: 3 adapter/test files and 26 files in
    `docs/architecture/jcode-qualification/` including this index/packet. No
    existing campaign, benchmark, API, orchestrator, dependency, or service file
    changed.
17. **Validation.** Adapter 30 passed. Boundary suite 165 passed, 2 skipped, 13
    subtests. JSON parsed and manifest counted 20. Frozen hashes matched. The
    registered coding pack had 136 pass/3 fail in unchanged existing behavior;
    its npm wrapper also lacked the fresh worktree's `.venv-campaign1` path.
18. **Local commit.** None. The instruction permits commit only after tests and
    integrity checks pass; the registered coding pack is not fully green.
19. **Remaining blockers.** C2 acceptance, external path/egress containment,
    process supervision, pinned binary and model-parameter/budget enforcement,
    complete result mapper, fixture commit, model proof,
    paired comparison, zero-regression evidence, and clean reproduction.
20. **Single next action.** Operator explicitly accepts or rejects the existing
    Campaign 2 review packet. This report authorizes no JCode execution.

## Claim ceiling

The Source Proxy candidate contains a disabled qualification seam and evidence
packet. JCode is not integrated: no traced request, runtime invocation, complete
execution evidence, independent diff, verification, anti-cheat completion, or
canonical JCode outcome exists.

## Registered Regression Failures

The final registered pack repeated the same three failures against unchanged
tracked base behavior:

- `test_bounded_proposal_diff_preview_ignores_json_envelope_requirements`;
- `test_prompt_packet_live_trial_creates_hidden_allowed_agent_lab_target`;
- `test_prompt_packet_live_trial_reuses_hidden_allowed_existing_agent_lab_target`.

The first receives `blocked` instead of `preview_ready`; the latter two receive
`coder_replacement_content_validation_failed` instead of an empty reason. No
tracked implementation or test involved in these failures was edited, and no
existing source file imports `source_proxy.jcode`.
