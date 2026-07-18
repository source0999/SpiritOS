# Campaign 3 Lane Inventory

This planning inventory is the seed registry for Gate 3.1. Gate 3.1 must replace provisional rows with complete runtime-backed entries.

| Lane ID | Classification | Owner | Contract Version | Authority Class | Producer Anchor | Consumer Anchor | Status | Migration Requirement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `core.context-broker` | mandatory | Source Proxy | `coding/core-lane-contracts.v1` | read/select only | `source_proxy/context/canonical_broker.py` | `source_proxy/coding/orchestrator.py` | ADOPT | extend to consume Scout, Obsidian, context-model, conflict metadata |
| `core.planner` | mandatory | Source Proxy | `coding/core-lane-contracts.v1` | advisory | `source_proxy/coding/orchestrator.py` | `source_proxy/coding/orchestrator.py` | ADOPT | add extended-lane applicability decisions |
| `core.coder` | mandatory | Source Proxy | `coding/core-lane-contracts.v1` | proposes diff only | `source_proxy/coding/orchestrator.py` | `source_proxy/tasks/long_running.py` | ADOPT | require consumed extended context when applicable |
| `core.reviewer` | mandatory | Source Proxy | `coding/core-lane-contracts.v1` | independent review | `source_proxy/verification/diff.py` | `source_proxy/coding/orchestrator.py` | ADOPT | review extended-lane claims and conflicts |
| `core.verifier` | mandatory | Source Proxy | `coding/core-lane-contracts.v1` | independent verification | `source_proxy/decision/verifier_lane.py` | `source_proxy/coding/orchestrator.py` | ADOPT | verify extended outputs and degraded verdicts |
| `core.anti-cheat` | mandatory | Source Proxy | `coding/core-lane-contracts.v1` | independent anti-cheat | `source_proxy/verification/anticheat/registry.py` | `source_proxy/coding/orchestrator.py` | ADOPT | detect synthetic extended participants |
| `core.evidence-recorder` | mandatory | Source Proxy | `coding/core-lane-contracts.v1` | immutable evidence | `source_proxy/coding/orchestrator.py` | completion evaluator | ADOPT | include extended-lane provenance |
| `extended.scout-research` | conditional | Scout through Source Proxy | `campaign-3/scout-research/v1` | read/research only | `source_proxy/decision/scout_research.py` | canonical context broker, planner, coder, reviewer, verifier | EXTEND | make canonical research lane with real source provenance |
| `extended.searxng-provider` | conditional | Scout provider | `campaign-3/scout-provider/v1` | provider only | existing Scout/search integration references | `extended.scout-research` | EXTEND | demote behind Scout, never standalone authority |
| `extended.web-fetch-docs` | conditional | Scout provider | `campaign-3/scout-provider/v1` | provider only | Scout fetch/browser tooling | `extended.scout-research` | BUILD | bind fetch/browser evidence to Scout request |
| `extended.obsidian-knowledge` | conditional | Source Proxy context | `campaign-3/obsidian-context/v1` | bounded read, optional canonical write | `source_proxy/context/obsidian.py` | canonical context broker, conflict resolver | EXTEND | add vault registry, freshness, conflict, optional write authority |
| `extended.mac-worker` | conditional | Mac worker through Source Proxy | `campaign-3/mac-worker/v1` | authority-bound command execution | `source_proxy/decision/mac_integration.py`, `scripts/mac-worker/spirit_mac_worker.py` | verifier, final verdict | EXTEND | make real platform verifier with source binding and cleanup |
| `extended.context-model` | conditional | Source Proxy model router | `campaign-3/context-model/v1` | advisory model output | `source_proxy/decision/model_lanes.py` | canonical context broker, planner | EXTEND | add output identity and conflict handling |
| `extended.retained-sub-agent` | conditional | Source Proxy agent registry | `campaign-3/sub-agent/v1` | advisory unless explicitly authority-bound | `source_proxy/decision/model_lanes.py`, `source_proxy/agents/` | planner, reviewer, verifier | EXTEND | retain only agents with caller, consumer, evidence |
| `extended.platform-verifier` | conditional | Source Proxy verifier | `campaign-3/platform-verifier/v1` | verification only | `source_proxy/decision/verifier_lane.py` | final verdict | BUILD | reconcile Mac and local verification |
| `extended.conflict-resolver` | mandatory | Source Proxy orchestrator | `campaign-3/conflict-resolution/v1` | resolution and claim ceiling | `source_proxy/coding/orchestrator.py` | diagnosis, verifier, evidence | BUILD | explicit conflict records and precedence |
| `extended.diagnosis-envelope` | mandatory | Source Proxy backend | `campaign-3/diagnosis-envelope/v1` | read-only observability | `source_proxy/api/coding_observability.py` | Campaign 4 `/coding` UI | EXTEND | expose full extended lane lifecycle |
| `extended.failure-injection` | test-only | Source Proxy harness | `campaign-3/failure-injection/v1` | test harness only | future C3 harness | completion regression suite | BUILD | controlled extended-lane failures |

Required fields for every retained Gate 3.1 row: ID, owner, contract version, authority class, producer, consumer, input schema, output schema, failure schema, timeout, retry, fallback, applicability, acknowledgement, observability, evidence, migration status.

