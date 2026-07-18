# Campaign 3 Evidence Index

## Gate 3.0 Control-Plane Evidence

| Evidence | Path Or Command | Status |
| --- | --- | --- |
| R1 terminal tag peel | `git rev-parse foundation-remediation-r1-terminal-20260718T120047Z^{commit}` | verified as `86cd484c8d09a14291da6a1226ecf24030d29caf` |
| R1 bundle verification | `git bundle verify foundation-remediation-r1-terminal.bundle` | passed |
| R1 bundle SHA-256 sidecar | `foundation-remediation-r1-terminal.bundle.sha256` | records `2c85f98ce5bb277be7b05419acb25a9dbd419080c1de2d5b38357d4fdd809964` |
| Shared Git integrity | `git fsck --strict --no-progress` | passed with dangling objects only |
| Corrected worktree | `/home/source/SpiritOS-campaign-3-extended-coding-lanes-20260718` | created from R1 terminal |
| Goal | `docs/architecture/campaign-3-goal.md` | authored |
| Plan | `docs/architecture/campaign-3-plan.md` | authored |
| State | `docs/architecture/campaign-3-state.json` | authored |
| Ledger | `docs/architecture/campaign-3-ledger.md` | authored |
| Lane inventory seed | `docs/architecture/campaign-3-lane-inventory.md` | authored |
| Decommission registry seed | `docs/architecture/campaign-3-decommission-registry.md` | authored |
| Test profile registry | `docs/architecture/campaign-3-test-profiles.json` | authored |
| Campaign 4 stub | `docs/architecture/campaign-4-stub.md` | authored |

## Later Evidence Requirements

Gate 3.1 and later must add immutable evidence for retained lane runtime contract validation, production caller and consumer proof, Scout research provenance and citations, Obsidian note identity and conflicts, Mac worker source-bound execution, retained sub-agent invocation and consumption, cross-lane conflicts, diagnosis envelope, degradation and fallback, all-lane proving task, final terminal receipt, manifest, tag, bundle, sidecar, and restoration instructions.

## Gate 3.4 Mac Evidence

| Evidence | Path Or Command | Status |
| --- | --- | --- |
| Current Tailscale host resolution | `sources-mac-mini.tailb69ea6.ts.net` (`100.117.164.42`) | live and host-key verified |
| Source-bound capability preflight | `task_9847e2580eb5` | consumed, `INTEGRATED_LIVE` |
| Source-bound Mac diff validation | `task_3040562f14be` | consumed, `INTEGRATED_LIVE` |
| Controlled cancellation | `task_5a4baf10aca3` | persisted `BLOCKED_ENV` on `mac_worker_timeout` |
| Receipt, hashes, and cleanup | `docs/evidence-manifests/campaign-3/gate-3-4-mac-verification.json` | recorded |

## Gate 3.5 Retained Sub-Agent Evidence

| Evidence | Path Or Command | Status |
| --- | --- | --- |
| Initial real local-provider run | `task_69d9705ebc74` | Gemma, Qwen, and verifier consumed; Hermes timeout recorded |
| Hermes recovery run | `task_5720249daa51` | local fallback output consumed |
| Invocation, identities, hashes, decommission | `docs/evidence-manifests/campaign-3/gate-3-5-retained-sub-agents.json` | recorded |

## Gate 3.6 Conflict Evidence

| Evidence | Path Or Command | Status |
| --- | --- | --- |
| Stale-context precedence and consumption | `task_93b719cfd8d0` | current repository truth selected; product PASS ceiling withheld |
| Conflict receipt | `docs/evidence-manifests/campaign-3/gate-3-6-conflict-resolution.json` | recorded |

## Gate 3.7 Diagnosis Evidence

| Evidence | Path Or Command | Status |
| --- | --- | --- |
| Read-only diagnosis envelope | `task_93b719cfd8d0` | extended lifecycle, claim ceiling, and redaction verdict returned |
| Receipt | `docs/evidence-manifests/campaign-3/gate-3-7-diagnosis-envelope.json` | recorded; no UI wiring |

## Gate 3.8 Recovery Evidence

| Evidence | Path Or Command | Status |
| --- | --- | --- |
| Recovery policy and failure receipts | `docs/evidence-manifests/campaign-3/gate-3-8-recovery.json` | Scout, Obsidian, Mac, model, and conflict cases recorded |

## Gate 3.9 Genuine All-Lane Proof

| Evidence | Path Or Command | Status |
| --- | --- | --- |
| Source-bound all-lane lifecycle receipt | `docs/architecture/evidence/campaign-3-gate-3-9-all-lane-r1-receipt-813912ce.json` | passed at `813912cef6`; authenticated approval, canonical apply, review, verification, anti-cheat, undo/reset, clean rerun, and teardown verified |
| Immutable SHA-256 sidecar | `docs/architecture/evidence/campaign-3-gate-3-9-all-lane-r1-receipt-813912ce.sha256` | `6df55c4d66223a7ad6e5670594c853e9956d184e2bdec5614f48a01a12beb406` |
| Controlled recovery | receipt `inner_proving.runs[0].extended_lanes.controlled_failures` | context-model and Mac-worker recovered; external-host failure recorded |

## Gate 3.10 Coding Backend Readiness

| Evidence | Path | Status |
| --- | --- | --- |
| Backend contract receipt | `docs/architecture/evidence/campaign-3-gate-3-10-coding-readiness.json` | passed; read-only, no Campaign 4 UI wiring |
| Hash sidecar | `docs/architecture/evidence/campaign-3-gate-3-10-coding-readiness.sha256` | recorded |

## Gate 3.11 Terminal Acceptance

| Evidence | Path | Status |
| --- | --- | --- |
| Terminal acceptance manifest | `docs/architecture/evidence/campaign-3-terminal-acceptance.json` | passed |
| Hash sidecar | `docs/architecture/evidence/campaign-3-terminal-acceptance.sha256` | recorded |
| Recovery anchor | `campaign-3-extended-coding-lanes-integrated-20260718T214644Z` and `/home/source/SpiritOS-campaign-3-terminal-anchor-20260718T214644Z/` | final tag and bundle anchor |
