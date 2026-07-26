# Campaign 1 Acceptance Receipt

status: `ACCEPTED_FOR_CAMPAIGN_2_AUTHORIZATION`

## Acceptance identity

| Field | Value |
|---|---|
| Receipt | `C1-RCPT-001` acceptance publication |
| Accepted source commit | `aa06361cbf88d113d30f38fcf0b566d2d371a637` |
| Accepted Campaign 0 parent | `bbe195111e202afe8610cd02adf528f0e92857c7` |
| Branch | `codex/source-proxy-campaign-1-terminal-truth-20260726` |
| Worktree | `/home/source/SpiritOS-source-proxy-campaign-1-terminal-truth-20260726` |
| Independent verdict | `C1_CAMPAIGN_VERIFIED_READY_FOR_OPERATOR_ACCEPTANCE` |
| Operator decision | Accepted in the Campaign 2 authorization prompt on 2026-07-26 |

## Acceptance matrix

| Check | Result | Evidence |
|---|---|---|
| Worktree and branch | GREEN | The named isolated worktree resolved to the expected branch. |
| Source commit | GREEN | `HEAD` was `aa06361cbf88d113d30f38fcf0b566d2d371a637`. |
| Campaign 0 parentage | GREEN | `bbe195111e202afe8610cd02adf528f0e92857c7` is an ancestor of the accepted source commit. |
| Scoped dirty state | GREEN | The Campaign 1 worktree was clean before this receipt was added. |
| Local/remote source match | GREEN | Local and `origin/codex/source-proxy-campaign-1-terminal-truth-20260726` both resolved to the accepted source commit before publication. |
| Operator review packet | GREEN | `campaign-1-operator-review-packet-20260725.md` remains present and unchanged. |
| Registered backend evidence | GREEN | The review packet records `44`, `56`, and `81` passing tests for the registered backend slices. |
| Terminal-truth regression evidence | GREEN | The review packet records `139` passing assertions across `46` coding-regression subtests. |
| Frontend, typecheck, and build evidence | GREEN | The review packet records `193` passing frontend tests, typecheck, and production build success. |
| Daily-runtime isolation | GREEN | The daily Uvicorn process remained in `/home/source/SpiritOS`; it was neither used for proof nor modified. |
| New P0/P1 blocker | GREEN | Independent verification returned the ready-for-operator-acceptance verdict and no new Campaign 1 blocker was reported. |

## Boundaries

This receipt accepts the terminal-truth and legacy-path-lockdown implementation
only. It does not authorize Campaign 3, any daily-runtime replacement,
deployment, a merge to a primary branch, or a claim that BT05 or BT06 has been
functionally repaired.

The final publication commit for this receipt is recorded after its push and is
the only permitted parent for the Campaign 2 implementation line.

## Accepted token

`CAMPAIGN_1_TERMINAL_TRUTH_LEGACY_LOCKDOWN_ACCEPTED`
