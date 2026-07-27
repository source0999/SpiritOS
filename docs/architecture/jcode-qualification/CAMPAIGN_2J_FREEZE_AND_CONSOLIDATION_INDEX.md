# Campaign 2-J Freeze and Consolidation Index

status: `RAW_EVIDENCE_PRESERVED_CANONICAL_PACKET_PENDING_COMMIT`

## Freeze

The original qualification packet was created against Source Proxy commit
`1641ddb1c71e6b364e98aa9aeff4b4719627d926` and pinned JCode commit
`2444e7b6bc80d421ae3ee404081bdb41150a1830`. Campaign 2 acceptance is recorded
separately at `17f3ce8739192e5c91534dc7ddde1086e83d5e0e`.

The frozen benchmark hashes, source pin, and all prior machine-readable
receipts remain in `archive/pre-2j-normalization-20260727/`. Nothing was
deleted or rewritten during normalization.

## Raw artifact classification

| Raw artifact | Classification | Canonical destination |
|---|---|---|
| `CAMPAIGN_AMENDMENT_JCODE.md` | merge into canonical | `CAMPAIGN_2J_AMENDMENT.md` |
| `CAMPAIGN_CONTRADICTION_MATRIX.md` | merge into canonical | amendment and handoff |
| `campaign_freeze_receipt.json` | source receipt | archive retained |
| `CAMPAIGN_FREEZE_RECEIPT.md` | merge into canonical | this index |
| `COMPACT_HANDOFF_PACKET.md` | merge into canonical | `COMPACT_HANDOFF_PACKET.md` |
| `CURRENT_CAMPAIGN_TRUTH.md` | merge into canonical | amendment and handoff |
| `current_lane_inventory.json` | source companion | archive retained |
| `CURRENT_LANE_INVENTORY.md` | merge into canonical | `CURRENT_LANE_INVENTORY.md` |
| `FINAL_AUDIT_REPORT.md` | merge into canonical | source/security audit and handoff |
| `final_audit_result.json` | source receipt | archive retained |
| `HUMAN_TO_AI_LAYER_MAP.md` | merge into canonical | architecture contract |
| `jcode_acceptance_matrix.json` | source companion | archive retained |
| `JCODE_ACCEPTANCE_MATRIX.md` | merge into canonical | qualification manifest/matrix |
| `JCODE_CAPABILITY_GAP_MATRIX.md` | merge into canonical | qualification manifest/matrix |
| `JCODE_EXECUTION_CONTRACT.md` | merge into canonical | architecture/execution contract |
| `JCODE_INTEGRATION_DECISION.md` | merge into canonical | amendment and architecture contract |
| `JCODE_INTEGRATION_OPTIONS.md` | merge into canonical | source/security audit |
| `JCODE_LAYER_PLACEMENT.md` | merge into canonical | architecture/execution contract |
| `JCODE_PINNED_SOURCE_RECEIPT.md` | merge into canonical | source/security audit |
| `JCODE_QUALIFICATION_EXPERIMENT.md` | merge into canonical | qualification manifest/matrix |
| `jcode_qualification_manifest.json` | source companion | archive retained |
| `jcode_risk_register.json` | source companion | archive retained |
| `JCODE_RISK_REGISTER.md` | merge into canonical | source/security audit |
| `JCODE_SECURITY_AND_TRUST_AUDIT.md` | merge into canonical | source/security audit |
| `JCODE_SOURCE_AUDIT.md` | merge into canonical | source/security audit |
| `README.md` | duplicate navigation | superseded by this index |

The remaining three untracked artifacts are canonical implementation evidence:
`source_proxy/jcode/__init__.py`, `source_proxy/jcode/adapter.py`, and
`source_proxy/tests/test_jcode_qualification_adapter.py`.
