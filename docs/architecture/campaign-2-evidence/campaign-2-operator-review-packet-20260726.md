# Campaign 2 Operator Review Packet

status: `READY_FOR_OPERATOR_REVIEW_NOT_YET_ACCEPTED`

## Identity

| Field | Value |
|---|---|
| Campaign | 2 - Full-Pipeline Benchmark Authority |
| C2 implementation commit | `2ecbb56d6524215843616d52e08cd95d32bdf4ea` |
| C2 source tree | Recorded in `c2-fpa-001-contract-2ecbb56d.json` |
| C1 accepted source | `aa06361cbf88d113d30f38fcf0b566d2d371a637` |
| C1 acceptance publication | `4e5772182cdf879ab2a05243e916f7760f22b41c` |
| C2 worktree | `/home/source/SpiritOS-source-proxy-campaign-2-full-pipeline-benchmark-authority-20260726` |
| Daily runtime | Untouched; its process CWD remains `/home/source/SpiritOS` and is outside this proof path. |

## Frozen public artifacts

| Artifact | SHA-256 |
|---|---|
| `c2-fpa-001-contract-2ecbb56d.json` | `a5810be30fbbd2a5d77256adee0a04f41acfd5eeeff11ab7eeaf850aba44dfda` |
| `c2-rcpt-001-negative-nonconsumed-layer-20260726.json` | `98f07ee9210f960430478f3f45463ce4983ab422bd4c99ab5e2fcccbbe7cb4d2` |
| Negative receipt public digest | `4e91143c7e834d9bef5273b0e3be550e5e90e2fbb2709a63c8c60f5498f72d8b` |

The receipt is bound to the clean, pushed `2ecbb56d` source/tree and contains
only a private-oracle digest. It does not contain expected patches, hidden
assertions, or verifier diagnostics.

## What the authority gate proves

- Exactly ten immutable task identities span controlled and unfamiliar
  repository classes.
- Every required task capability must be applicable before outcome and provide
  registration, canonical invocation, consumption, counterfactual influence,
  failure behavior, and durable receipt evidence.
- A missing task, stale/foreign source or runtime, report-time terminal repair,
  sidecar/mock, oracle exposure, omitted failure, or warm rerun is a hard fail.
- Aggregate pass rates and a self-reported score cannot upgrade a result;
  only two independent literal `10/10` runs plus operator acceptance could
  authorize the full-pipeline terminal token.
- Basic Backend 10 remains a useful core diagnostic and is prevented from
  authorizing full-pipeline success.

## Executed evidence

| Check | Result |
|---|---|
| C2 authority focused tests | `9 passed in 0.06s` |
| C2-FI-002 source-bound negative run | PASS: `C2_NEGATIVE_CONTROL_REJECTED_NONCONSUMED_LAYER` |
| Campaign 1 orchestrator tests | `44 passed in 11.78s` |
| Campaign 1 proof tests | `56 passed in 9.17s` |
| Long-running C1 tail cases | `8 passed` individually; the combined full command exceeded its cap, while the accepted C1 packet retains the original `81 passed` record |
| Registered coding regression | `139 passed, 46 subtests passed in 49.95s` |
| Frontend/typecheck/build validation | Frontend regression exit `0` (`193` tests), typecheck exit `0`, and standalone build exit `0` in `103.4s`, run serially at `c3f59492`. Next 16 does not run ESLint during `next build`; lint exit `1` (`78` errors, `109` warnings) is documented separately as pre-existing, deferred debt. |

## Review decisions required

- [ ] Accept `C2-FPA-001`: task manifest, capability matrix, applicability policy, literal threshold, and resource policy.
- [ ] Accept the isolated private-oracle boundary and access-audit rule.
- [ ] Confirm the negative receipt correctly rejects registration/invocation without canonical consumption.
- [ ] Accept the required independent first-run and clean-rerun policy.
- [x] Review the completed frontend/typecheck/build validation disposition; the separate pre-existing lint finding remains deferred and does not accept Campaign 2.
- [ ] Decide whether to authorize the additional live oracle-leak, cross-run substitution, and clean-rerun failure injections.
- [ ] Confirm no Campaign 3 work, daily-runtime replacement, deployment, or primary-branch merge is authorized by this packet.

## Non-exit statement

Campaign 2 is ready for operator review but is not accepted. The full pipeline
is not green, Campaign 3 through Campaign 6 remain unstarted, and this packet
does not emit a Campaign 2 success token.
