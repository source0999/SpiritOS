# Campaign 3 Ledger

## Current Checkpoint

Checkpoint ID: `campaign_3_terminal_complete`

Verdict: `CAMPAIGN_3_EXTENDED_CODING_LANES_INTEGRATED`

State:

- completed gates: `gate_3_0_entry_verification_and_control_plane`, `gate_3_1_extended_lane_inventory_and_classification`, `gate_3_2_scout_and_coding_research_integration`, `gate_3_3_obsidian_coding_knowledge_integration`, `gate_3_4_mac_worker_and_mac_coding_frameworks`, `gate_3_5_retained_coding_sub_agents`, `gate_3_6_cross_lane_conflict_resolution`, `gate_3_7_extended_observability_and_diagnosis_backend`, `gate_3_8_degradation_fallback_and_resumability`, `none`
- next gate: `gate_3_9_genuine_all_lane_proving_task`
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

Repeated recovery verification: the current host also reports TCP port 22 failed
and `DestinationHostUnreachable` for `10.0.0.147`. This confirms that neither
the Dell hop nor the configured local path can reach the registered Mac worker.

Mac recovery evidence: resolved `sources-mac-mini.tailb69ea6.ts.net` through the
registered Tailscale identity (`100.117.164.42`) and verified the existing SSH key
against the prior registered host key. An isolated Mac checkout from the Campaign
3 bundle ran `git diff --check` at `7a98d3cc7293392e85009245aa87fa5a96329b42`;
the worker returned the same observed commit and log hash recorded in
`docs/evidence-manifests/campaign-3/gate-3-4-mac-verification.json`. Timeout,
cancellation, downstream acknowledgement, recovery, and cleanup remain required.

The isolated Mac checkout and Dell transfer bundles were removed after the receipt;
cleanup is now proven for that real execution.

Gate 3.4 completed with current Tailscale identity resolution rather than the stale
LAN endpoint. At commit `1b932b9c575a237509724f2c9387d25e68416067`, the Mac
reported macOS 15.7.7, Xcode 26.0.1, Swift 6.2, SafariDriver 26.5, and discoverable
codesign/pkgbuild/productbuild tools. The source-bound platform preflight and
`git diff --check` were consumed by `coding_verifier_mac_evidence_consumer`. A
bounded no-write cancellation probe persisted `BLOCKED_ENV` on timeout, then a
fresh source-bound preflight recovered to `INTEGRATED_LIVE`. See
`docs/evidence-manifests/campaign-3/gate-3-4-mac-verification.json` for hashes,
task identities, and cleanup confirmation. The next authorized task is Gate 3.5.

Gate 3.5 completed with real, bounded local-provider output. Gemma, Qwen, and
the functional verifier produced consumed outputs; Hermes 14B timed out and
persisted its resource-pressure failure before the declared local Hermes fallback
produced a distinct consumed recovery output. This was JSON-only no-write work,
not a full Coder 10 execution. The invocation, output, consumer, failure, and
recovery receipts are recorded in
`docs/evidence-manifests/campaign-3/gate-3-5-retained-sub-agents.json`.

Gate 3.6 completed with a persisted stale-context conflict receipt. Current
repository/Mac source truth outranked a stale operational claim, the verifier
consumed the result, and the resolver imposed `resolved_conflict_no_product_pass`.
Equal-precedence disagreement fails closed. Evidence:
`docs/evidence-manifests/campaign-3/gate-3-6-conflict-resolution.json`.

Gate 3.7 adds a backend-only diagnosis envelope to the existing read-only task
observability API. It exposes extended lane lifecycle, output/evidence identity,
consumption, acknowledgement, conflict claim ceiling, recovery availability, and
redaction status without starting any coding UI work. Evidence:
`docs/evidence-manifests/campaign-3/gate-3-7-diagnosis-envelope.json`.

Gate 3.8 completed with persisted Scout-provider and Obsidian-vault failures,
the prior real Mac timeout, retained-sub-agent timeout/recovery, and conflict
claim-ceiling evidence. The recovery policy makes required-lane failure block
full success and keeps a replacement below the full-success claim ceiling.
Evidence: `docs/evidence-manifests/campaign-3/gate-3-8-recovery.json`.

## Gate 3.9 Evidence

- Isolated all-lane lifecycle receipt: `docs/architecture/evidence/campaign-3-gate-3-9-all-lane-r1-receipt-813912ce.json`.
- Receipt SHA-256: `6df55c4d66223a7ad6e5670594c853e9956d184e2bdec5614f48a01a12beb406`.
- Source-bound commit: `813912cef6ace07fcd170f519d518bd755c9d9f8`; all required extended lanes were live, two controlled recoveries were recorded (including Mac external-host failure), and undo/reset, clean rerun, operator-session revocation, and isolated-service teardown passed.

## Gate 3.10 Backend Readiness

- Read-only Campaign 3 readiness envelope expands authoritative task/run, observability, cancel/recovery, undo/reset, browser-fixture, and receipt-reconciliation contracts without granting UI mutation authority.
- Evidence: `docs/architecture/evidence/campaign-3-gate-3-10-coding-readiness.json`; focused backend suite passed 12 tests.

## Gate 3.11 Final Acceptance

- Terminal acceptance manifest: `docs/architecture/evidence/campaign-3-terminal-acceptance.json`.
- Gate 3.9 immutable receipt, Gate 3.10 backend-only contract receipt, all validators, targeted regression suites, TypeScript, and scoped production build passed.
- Campaign 4 remains unstarted; no push, Coder 10 run, or full coding-UI wiring was performed.
