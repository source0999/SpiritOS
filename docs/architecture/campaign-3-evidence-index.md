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

