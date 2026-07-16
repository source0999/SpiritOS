# Campaign 1 Authority Inventory and Implementation Map

Schema: `spiritos-campaign-1-authority-inventory/v2`

## Current accepted authority state

Campaign: `spiritos-campaign-1`. Phase: **Campaign 1 complete**. Verdict: `GO_CAMPAIGN_1_COMPLETE`. The authority requirements below are all accepted; there is no current owner decision, critical blocker, or remaining authority gate. Campaign 2 has not started.

| Requirement | Canonical owner and accepted control | Evidence ceiling | Disposition |
| --- | --- | --- | --- |
| AR-001 SpiritFlix | server-owned authenticated preview/issuance with exact `spiritflix-admin-executor` consume/finalize bindings for seven bounded writers; ordinary BFF sessions remain non-administrative | administrative authority lifecycle | accepted |
| AR-002 Cartographer | proposal/read-only observation with durable selection transfer; legacy mutation routes/helpers fail closed; one canonical selection consumer | proposal and consumer boundary | accepted |
| AR-003 Design | persisted preview, authenticated issuance, canonical writeback consume/finalize, and matched acknowledgement envelope | approved writeback boundary | accepted |
| Coding Prompt 1 | canonical target-plugin adapter resolves repository/worktree/root/head/prompt/profile before preview, execution, verification, acknowledgement, and evidence | target identity and lifecycle | accepted |

Protected reference heads remain Source Proxy `594d66ef8280953af767a273d7c91be765d1a6eb`, SpiritFlix `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`, and architecture audit `05612d2ae358bc01b6ef997243137649f8d65f14`. Borrowed SpiritFlix `_worktrees/` remain untouched.

## Evidence links

- AR-001: [admin operator lifecycle](campaign-1-evidence/ar001-admin-operator-lifecycle-20260714.md) and [server-owned session](campaign-1-evidence/ar001-server-owned-session-20260714.md).
- AR-002: [durable selection consumer](campaign-1-evidence/cartographer-durable-selection-20260714.md).
- AR-003: [Design acknowledgement envelope](campaign-1-evidence/design-writeback-acknowledgement-20260714.md).
- Prompt 1: `docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json` records an authoritative redacted GO lifecycle receipt.

## Historical discovery record — non-current

Earlier route inventories identified caller-controlled paths, duplicate registrations, and an un-decided canonical-shell migration. Those descriptions guided the accepted migrations above. They are historical discovery evidence only and must not be read as current authority findings, blockers, owner decisions, or open requirements.
