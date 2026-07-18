# Campaign 3 Ledger

## Current Checkpoint

Checkpoint ID: `campaign_3_gate_3_4_mac_worker_external_network_blocked`

Verdict: `GATE_3_3_COMPLETE_GATE_3_4_EXTERNAL_HOST_BLOCKED`

State:

- completed gates: `gate_3_0_entry_verification_and_control_plane`, `gate_3_1_extended_lane_inventory_and_classification`, `gate_3_2_scout_and_coding_research_integration`, `gate_3_3_obsidian_coding_knowledge_integration`
- next gate: `gate_3_4_mac_worker_and_mac_coding_frameworks`
- Campaign 3 GO: false
- Campaign 4 started: false
- implementation gates started: true

Entry verification:

- R1 terminal tag `foundation-remediation-r1-terminal-20260718T120047Z` peels to `86cd484c8d09a14291da6a1226ecf24030d29caf`.
- R1 source implementation parent is `ec204d63e431d10501c67db0264082db6e4d31e4`.
- R1 bundle verification passed from the shared Git store.
- R1 bundle sidecar records SHA-256 `2c85f98ce5bb277be7b05419acb25a9dbd419080c1de2d5b38357d4fdd809964`.
- Shared Git object integrity passed `git fsck --strict --no-progress` with only dangling objects reported.
- Historical design Campaign 3 remains `4aec510409e8bb82386190af9fa8f666efcbc63e` and remains classified as `CAMPAIGN_3_SCOPE_DIVERGED_TO_DESIGN`.

Gate 3.1 and 3.2 runtime-backed inventory and research:

- `docs/architecture/campaign-3-goal.md`
- `docs/architecture/campaign-3-plan.md`
- `docs/architecture/campaign-3-state.json`
- `docs/architecture/campaign-3-ledger.md`
- `docs/architecture/campaign-3-lane-inventory.md`
- `docs/architecture/campaign-3-decommission-registry.md`
- `docs/architecture/campaign-3-evidence-index.md`
- `docs/architecture/campaign-3-test-profiles.json`
- `source_proxy/contracts/coding_lane_contracts.py`
- `packages/contracts/schemas/coding/extended-lane-contracts.v1.json`
- `source_proxy/coding/extended_lane_registry.py`
- `source_proxy/coding/runtime_lane_boundary.py`
- `source_proxy/tests/test_extended_lane_registry.py`
- `source_proxy/decision/scout_research.py`
- `source_proxy/context/source_readiness.py`
- `source_proxy/tests/test_campaign_3_scout_research.py`
- `source_proxy/context/obsidian.py`
- `source_proxy/tests/test_campaign_3_obsidian_context.py`

The registry has exactly eight retained, selectable production lanes. Scout
providers, preview-only helpers, the Mac advisory route, and all prompt-only or
callerless aliases are non-selectable. Every retained lane binds its producer,
consumer, timeout, fallback, authority class, contract, and immutable-evidence
obligation. The runtime boundary rejects output lacking downstream acknowledgement
and consumption.

Stop line:

Scout owns the task-bound query, provider chain, bounded source selection, primary-source preference, fetch hashes, freshness, citations, failure status, and claim ceiling. SearXNG and fetch cannot be independently selected or counted. The context adapter carries the exact receipt to the canonical broker for downstream acknowledgement.

Gate 3.2 was completed before the bounded Obsidian integration recorded below.

Obsidian reads are bounded to the registered root and include exact note hashes,
freshness, stale-note status, and repository-conflict flags. Repository truth still
outranks notes. A write request only yields a root/path-bound server-owned plan;
it cannot write until canonical approval, executor, verification, evidence, and
compensating restoration bind it.

Gate 3.3 is complete. The next authorized task resumes at `gate_3_4_mac_worker_and_mac_coding_frameworks`.

External blocker recorded 2026-07-18: the configured Dell route resolves
`spirit-mac-mini` to `10.0.0.147:22` as user `spiritmac` with the configured
identity file, but a direct preflight from Dell returned `No route to host`.
No Mac job, placeholder, or `not applicable` response was counted. Gate 3.4
requires restoration of network reachability to this configured host (or an
authorized replacement host registration) before it can produce the required
source-bound macOS build/WebKit/platform-verification result.

The Gate 3.4 dispatch boundary is implemented and tested: it rejects unbound
commits and unsafe commands, records a result hash, denies write authority, and
does not count a timeout or source mismatch as platform verification. Live proof
remains pending the external route restoration.
