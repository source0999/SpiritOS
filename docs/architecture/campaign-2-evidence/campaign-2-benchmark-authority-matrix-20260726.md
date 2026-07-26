# Campaign 2 Benchmark Authority Matrix

status: `IMPLEMENTATION_IN_PROGRESS_OPERATOR_ACCEPTANCE_PENDING`

## Dependency and scope

| Field | Value |
|---|---|
| Campaign 1 accepted source | `aa06361cbf88d113d30f38fcf0b566d2d371a637` |
| Campaign 1 acceptance publication | `4e5772182cdf879ab2a05243e916f7760f22b41c` |
| Dependency token | `CAMPAIGN_1_TERMINAL_TRUTH_LEGACY_LOCKDOWN_ACCEPTED` |
| Campaign 2 branch | `codex/source-proxy-campaign-2-full-pipeline-benchmark-authority-20260726` |
| Campaign 2 worktree | `/home/source/SpiritOS-source-proxy-campaign-2-full-pipeline-benchmark-authority-20260726` |
| Rollback point | `4e5772182cdf879ab2a05243e916f7760f22b41c` |
| Gap ownership | `SOL-P0-001`, `SOL-P1-007`, and the `SOL-P1-008` equivalence/rejection proof framework |

Campaign 2 freezes and enforces benchmark authority. It does not implement
Campaign 3-6 capabilities, repair BT05/BT06, mutate the daily runtime, or
claim that the complete proxy is green.

## Current authority audit

| Benchmark | Task breadth | Production lifecycle authenticity | Required layers | Causal enforcement | Oracle isolation | Clean rerun | Promotion rule | Current authority |
|---|---|---|---|---|---|---|---|---|
| Basic Backend 10 | Ten core backend tasks | Authenticated lifecycle evidence | Core lifecycle and terminal proof | Per-run trace reconciliation, but no per-task extended-layer causal edges | Private container/profile | First and clean phase support | `LOCAL_PROXY_BASIC_CODING_GATE_PASSED` | `VALID_CORE_GATE_NOT_FULL_PIPELINE_GATE` |
| Campaign 3.5 runner | Disposable fixture task execution | Harness invokes production target adapter | Fixture authority, private task store, adapter | Target-specific, not full-pipeline matrix | Private store outside fixture | Phase manifests | Harness report | Historical/incremental evidence only |
| Core-30/full-100 assets | Broader catalog/reference material | Not a single full-pipeline authority | Catalog-specific | No frozen cross-layer 10-task authority | Asset-local | Not an authority rule | Diagnostic only | Historical evidence only |
| Campaign 2 authority | Frozen literal ten-task suite | Receipt must name authenticated canonical entry and producer-owned terminal truth | Canonical lifecycle, terminal truth, and selected task capability | Registered, invoked, consumed, influential, failure-bound, receipt-bound rederived per applicable capability | Isolated verifier digest/access audit | Independent first and clean namespace/state required | Only strict 10/10 plus operator acceptance | Authoritative gate implementation; operator acceptance pending |

### Basic Backend 10 limitation reproduced

`BasicBackendGateRunner.validate_preflight` accepts the global
`MAPPED_RUNTIME_CONFIRMED_PHASE_0` trace-map marker. That status is a preflight
check for the disposable LumaCart trace map. It neither requires an extended
layer event for each task nor verifies canonical consumer acknowledgement or a
counterfactual. Consequently a Basic Backend 10 pass can coexist with
disconnected extended layers. Campaign 2 preserves that runner and prevents
its terminal token from becoming full-pipeline authority.

## Frozen authority requirements

The machine-readable `C2-FPA-001` contract is generated only from a clean,
pushed C2 commit. It contains immutable task hashes for exactly ten tasks across
the controlled and unfamiliar repository classes; a literal `10/10` threshold;
the pre-outcome applicability policy; source/tree identity; first and clean
rerun requirements; and the add-only future-slice rule.

Every applicable capability must provide `REGISTERED`, `INVOKED`, `CONSUMED`,
`INFLUENTIAL`, `FAILURE_BOUND`, and `RECEIPT_BOUND` evidence. The scorer ignores
the receipt's self-declared result and rederives the boundaries. It rejects a
missing canonical call, consumer acknowledgement, controlled counterfactual,
failure receipt, mocked edge, sidecar edge, source/runtime mismatch, oracle
leak, missing task, or reused clean state.

## Operator decision still required

The implementation can emit only the blocked C2 terminal disposition until an
operator reviews and accepts the frozen contract, oracle boundary, thresholds,
resource policy, and clean-rerun policy. A green product result is neither
required nor claimed by this document.
