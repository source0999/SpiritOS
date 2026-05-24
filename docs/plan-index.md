# SpiritOS Plan Index

status: active

Status date: 2026-05-20

## Active Plans

| Plan | Status | Role | Authority |
| --- | --- | --- | --- |
| `docs/source-proxy-production-hardening-plan.md` | status: active | Current Source Proxy production plan | Records green safety gate and constrains next work |
| `docs/source-proxy-codex-class-production-master-plan-v1.0.md` | status: active roadmap | Current Source Proxy `/coding` Codex-class production roadmap | Supersedes stale Plan 6.2 labels and sequences `/coding` work by Britton's phase/increment workflow |
| `docs/source-proxy-codex-class-new-chat-handoff-v1.0.md` | status: active handoff | New-chat continuation handoff for the current Source Proxy `/coding` roadmap | Tells future Codex chats how to start the active phase without jumping into feature work |
| `docs/backend-console-usability-reset-plan-v0.1.md` | status: planning-only | `/proxy-backend` usability reset plan | Plans a plain backend operator page only; does not authorize implementation, autonomy, or execution controls |
| `docs/codingUI.md` | status: active | Active `/coding` UI polish plan | Authorizes planning for UI polish only; implementation still requires approval |
| `docs/design-system-overhaul-master-v0.2.md` | status: planning active | Active SpiritOS design-system overhaul planning spine | Does not authorize implementation; keeps future design work Source Proxy gated |
| `docs/design-systems-master-v0.1.md` | status: planning complete | Manual-first Design Intelligence Stack plan | Does not authorize implementation; next increment requires explicit approval |
| `productionProxy.md` | status: historical | Uploaded staging copy | Historical only; follow the durable repo copy instead |

## Design System Status Summary

`docs/design-system-overhaul-master-v0.2.md` is the active planning spine for the SpiritOS design-system overhaul. It keeps future design-system work manual-controlled and Source Proxy gated.

Current handling:

- v0.2 is planning-only and does not authorize implementation.
- For design-system overhaul planning, `docs/design-system-overhaul-master-v0.2.md` is the current source of truth.
- v0.1 design intelligence docs remain supporting references and history.
- Design Vault artifacts are proposal evidence, not runtime or apply authority.
- Reverse Designer, Design Blender, Scout design intake, visual verification, and design apply lane work remain contract/scaffold level until later approved increments.
- No production UI, route, package, Scout runtime, Source Proxy runtime, or Cartographer authority change is authorized by the design-system plan.

## Source Proxy Plan Authority Map

The green Source Proxy safety gate passed on 2026-05-20 based on user-provided evidence: global safety regression passed, Source Proxy tests passed, Scout backend tests passed, Cartographer safety passed, dashboard smoke passed, no unexpected mutation occurred, no unexpected Level 2 evidence appeared, no commit occurred during the run, HEAD stayed stable at `3e55bdc`, and `main` matched `origin/main` at `3e55bdc`.

### Current Source Proxy Production Roadmap

| Plan | Handling |
| --- | --- |
| `docs/source-proxy-codex-class-production-master-plan-v1.0.md` | Active `/coding` Codex-class production roadmap. Follow this for Phase 0 through Phase 11 sequencing. |
| `docs/source-proxy-codex-class-new-chat-handoff-v1.0.md` | Active handoff for starting a new Codex chat in the correct phase/increment workflow. |

### Active Source Of Truth

| Plan | Handling |
| --- | --- |
| `docs/source-proxy-production-hardening-plan.md` | Active production authority and safety boundary. It records the green gate and says the next approved track is `/coding` UI polish, not new autonomy. |
| `docs/codingUI.md` | Active only for `/coding` UI polish after the green gate. It must use existing Source Proxy contracts and gates. |

### Active Supporting References

| Plan | Handling |
| --- | --- |
| `docs/source-proxy-regression-matrix.md` | Keep as the regression command and safety guarantee map. |
| `docs/source-proxy-daily-use-runbook.md` | Keep as the operator workflow reference. |
| `docs/source-proxy-remote-manual-checks.md` | Keep as the remote/mobile/manual check reference. |
| `docs/source-proxy-worktree-study.md` | Keep as the worktree and branch-safety reference. |
| `docs/continue-lite-console-plan.md` | Keep as supporting reference only where it describes implemented `/coding` console history and read-only history patterns. |

### Scout Manual-Controlled Stop Points

| Plan | Handling |
| --- | --- |
| `docs/scout-v0-6-dry-run-closeout-index-and-stop-point.md` | Scout v0.6 dry-run-only lane is parked/manual-controlled. It does not authorize proxy intake, proxy memory writes, coding context writes, promotion finalization, background workers, scheduled writes, commits, or pushes. |
| `docs/scout-v0-7-reopen-decision-record.md` | Scout v0.7 decision keeps Scout-to-Proxy import parked. It authorizes planning for read-only review ergonomics only and does not reopen proxy intake, proxy memory writes, coding context writes, promotion finalization, background workers, scheduled writes, commits, or pushes. |
| `docs/scout-v0-7-manual-controlled-review-ergonomics-plan.md` | Scout v0.7 review ergonomics plan is planning/manual-controlled. It only plans read-only review clarity and does not authorize source automation, discovery execution, packet promotion, proxy intake, proxy memory writes, coding context writes, background workers, scheduled writes, commits, or pushes. |
| `docs/scout-v0-7-diagnostics-summary-copy.md` | Scout v0.7 diagnostics summary copy is active/manual-controlled. It only adds live read-only Scout safety copy to the dashboard and `/intelligence`; it does not authorize source automation, discovery execution, packet promotion, proxy intake, proxy memory writes, coding context writes, background workers, scheduled writes, commits, or pushes. |
| `docs/scout-v0-7-review-ergonomics-stop-point.md` | Scout v0.7 review ergonomics is parked/manual-controlled. It records the stop point after read-only review clarity work and requires a new operator decision before any further Scout increment. |
| `docs/scout-v0-8-next-lane-decision-record.md` | Scout v0.8 next lane decision record is planning/manual-controlled. It chooses to keep Scout parked until a later explicit lane selection and does not authorize Scout implementation, automation, proxy memory writes, coding context writes, commits, or pushes. |
| `docs/scout-v0-8-closeout-summary.md` | Scout v0.8 closeout summary is closed/manual-controlled. It records Scout as parked with green read-only gates, zero backlog, dry-run-only closeout mode, and no proxy memory, coding context, or promotion finalization writes. |
| `docs/scout-v0-9-next-phases-plan.md` | Scout v0.9 next phases plan is planning/manual-controlled. It selects Manual-Controlled Lane Expansion and keeps autonomy, scheduled writes, proxy memory writes, coding context writes, hidden workers, commits, and pushes forbidden. |
| `docs/scout-v0-9-lane-contract-schema.md` | Scout v0.9 increment 0.3.1 is planning/manual-controlled. It defines the lane contract schema only and keeps all Scout writes, autonomy, scheduled work, hidden workers, commits, and pushes forbidden. |
| `docs/scout-v0-9-dry-run-receipt-format.md` | Scout v0.9 increment 0.3.2 is planning/manual-controlled. It defines advisory dry-run receipt fields only and does not authorize execution, receipt emission, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-review-decision-labels.md` | Scout v0.9 increment 0.3.3 is planning/manual-controlled. It defines advisory review decision labels only and does not authorize source mutation, packet promotion, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-phase-0-3-closeout.md` | Scout v0.9 increment 0.3.4 is closed/manual-controlled. It closes lane contracts, dry-run receipts, and review labels as docs-only and keeps all writes, autonomy, scheduled work, hidden workers, commits, and pushes forbidden. |
| `docs/scout-v0-9-design-intake-plan.md` | Scout v0.9 increment 1.1 is planning/manual-controlled. It plans stored-only, manual-fed design intake and does not authorize crawling, auto-discovery, design extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-design-pattern-taxonomy.md` | Scout v0.9 increment 1.2 is planning/manual-controlled. It defines design pattern taxonomy for manual stored-only references and does not authorize crawling, extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-design-review-packet-format.md` | Scout v0.9 increment 1.3 is planning/manual-controlled. It defines advisory design review packet fields and does not authorize analysis execution, code generation, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-phase-1-closeout.md` | Scout v0.9 increment 1.4 is closed/manual-controlled. It closes stored-only design intake planning and does not authorize implementation, crawling, extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-review-grouping-plan.md` | Scout v0.9 increment 2.1 is planning/manual-controlled. It plans advisory review grouping only and does not authorize source mutation, discovery, extraction, promotion, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-better-summaries-plan.md` | Scout v0.9 increment 2.2 is planning/manual-controlled. It defines advisory review summary fields only and does not authorize automatic generation, mutation, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-operator-decision-flow.md` | Scout v0.9 increment 2.3 is planning/manual-controlled. It defines human operator decisions only and does not authorize runtime source mutation, discovery, extraction, promotion, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-phase-2-closeout.md` | Scout v0.9 increment 2.4 is closed/manual-controlled. It closes review intelligence planning and does not authorize source mutation, discovery, extraction, promotion, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-manual-triggered-discovery-boundary.md` | Scout v0.9 increment 3.1 is planning/manual-controlled. It defines a manual-trigger-only discovery boundary and does not authorize scheduled discovery, background workers, source activation, extraction, writes, autonomy, commits, or pushes. |
| `docs/scout-v0-9-source-allowlist-model.md` | Scout v0.9 increment 3.2 is planning/manual-controlled. It defines source lifecycle states only and does not authorize source record writes, activation, discovery, extraction, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-discovery-budget-rate-limits.md` | Scout v0.9 increment 3.3 is planning/manual-controlled. It defines conservative discovery budgets only and does not authorize discovery execution, source activation, extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-phase-3-closeout.md` | Scout v0.9 increment 3.4 is closed/manual-controlled. It closes safe discovery prep and does not authorize discovery execution, crawling, source activation, extraction, writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-context-handoff-packet.md` | Scout v0.9 increment 4.1 is planning/manual-controlled. It defines an advisory context handoff packet only and does not authorize proxy intake, proxy memory writes, coding context writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-approval-gate-requirements.md` | Scout v0.9 increment 4.2 is planning/manual-controlled. It defines future human approval requirements only and does not authorize proxy intake, proxy memory writes, coding context writes, autonomy, scheduled work, hidden workers, commits, or pushes. |
| `docs/scout-v0-9-integration-risk-table.md` | Scout v0.9 increment 4.3 is planning/manual-controlled. It lists integration risks and mitigations only and does not authorize proxy intake, proxy memory writes, coding context writes, autonomy, scheduled work, hidden workers, commits, or pushes. |

### Historical Or Reference Only

| Plan | Handling |
| --- | --- |
| `productionProxy.md` | Historical uploaded staging copy. It may explain old sequencing, but the durable repo authority is `docs/source-proxy-production-hardening-plan.md`. |
| `docs/source-proxy-closeout-consolidation-plan.md` | Historical closeout/consolidation planning after the green gate. |
| `docs/source-proxy-hardening-closeout.md` | Historical closeout evidence and summary. |
| `docs/aionui-reference-study.md` | UX/reference research only. |
| `docs/agent-wrapper-reference-study.md` | UX/provider-reference research only. |
| `docs/spirit-cowork-gap-report.md` | Historical gap report only. |
| `docs/cartographer-level-1-autonomy-plan.md`, `docs/cartographer-level-2-autonomy-plan.md`, `docs/cartographer-level-3-autonomy-plan.md` | Historical phase plans unless a future active plan explicitly reopens a specific bounded increment. |

### Deferred, Not Active

The following topics are visible but inactive. Do not promote them into implementation work from stale docs:

- AionUi bridge
- Cowork console
- provider-layer expansion
- scheduled provider tasks
- native mobile app
- autopilot or autonomy features
- default Codex promotion
- commit/push automation

`proxyCLI.md` is retired, intentionally absent, and must not be recreated. Phase 11 language is historical and must not be used to invent new increments.

## Retired Or Historical Plans

| Plan Or Topic | Status | Handling |
| --- | --- | --- |
| `proxyCLI.md` | status: historical | Retired and intentionally deleted |
| Phase 11 language | status: historical | Do not treat as next action |
| AionUi bridge | status: deferred | Do not build unless a later active plan explicitly reopens it |
| Spirit Cowork Console | status: deferred | Do not build unless a later active plan explicitly reopens it |
| Provider-layer implementation | status: deferred | Do not build unless a later active plan explicitly reopens it |

## Reference Research

| Document | Status | Handling |
| --- | --- | --- |
| `docs/aionui-reference-study.md` | status: historical | Research input only |
| `docs/agent-wrapper-reference-study.md` | status: historical | Research input only |
| `docs/spirit-cowork-gap-report.md` | status: historical | Gap report only |

These files are research inputs. They do not authorize provider-layer implementation, AionUi integration, or Cowork Console work.

## Resolution Rule

When plan documents conflict, follow the single `status: active` Source Proxy plan above. Treat `status: historical` documents as evidence and `status: deferred` topics as visible but inactive.

## Old Plan Cleanup Queue

No deletion was performed during this planning pass. Archive or deletion work requires explicit user approval unless a later pass lists exact files and receives permission.

| File path | Category | Reason | Risk if deleted | Recommended action | User permission required |
| --- | --- | --- | --- | --- | --- |
| `docs/source-proxy-production-hardening-plan.md` | keep active | Current Source Proxy authority and green-gate status. | High: deleting would remove the safety boundary and source of truth. | Keep active. | No |
| `docs/codingUI.md` | keep active | Next active `/coding` UI polish plan. | High: deleting would remove the next approved track. | Keep active. | No |
| `docs/source-proxy-regression-matrix.md` | keep reference | Maps safety guarantees to commands and failure meanings. | Medium: deleting would make future gate checks less reviewable. | Keep reference. | No |
| `docs/source-proxy-daily-use-runbook.md` | keep reference | Operator workflow for daily Source Proxy use. | Medium: deleting would remove practical manual workflow guidance. | Keep reference. | No |
| `docs/source-proxy-remote-manual-checks.md` | keep reference | Codex mobile, SSH, and remote manual check reference. | Medium: deleting would weaken remote review workflow guidance. | Keep reference. | No |
| `docs/source-proxy-worktree-study.md` | keep reference | Captures worktree/branch safety guidance. | Medium: deleting would lose context for future branch/worktree decisions. | Keep reference. | No |
| `docs/continue-lite-console-plan.md` | keep reference | Useful where it records implemented read-only console history and workflow memory ideas. | Low/medium: deleting could lose UI history context. | Keep reference, cite only when aligned with current gates. | No |
| `productionProxy.md` | mark historical | Uploaded staging copy with old sequencing and duplicate plan text. | Low/medium: deleting could lose provenance for old plan decisions. | Archive candidate after review; do not use as active authority. | Yes |
| `docs/source-proxy-closeout-consolidation-plan.md` | mark historical | Closeout planning now superseded by green-gate status. | Low: mostly planning provenance. | Keep historical or archive with closeout docs. | Yes |
| `docs/source-proxy-hardening-closeout.md` | mark historical | Green-gate closeout/evidence record. | Medium: deleting could remove useful evidence summary. | Keep historical evidence, not active plan. | Yes |
| `docs/spirit-cowork-gap-report.md` | mark historical | Contains old Phase 11/Cowork/AionUi language but also explicitly defers it. | Low/medium: deleting could lose research rationale. | Keep historical or archive under research if archive structure is approved. | Yes |
| `docs/aionui-reference-study.md` | mark historical | Toy-repo AionUi UX research only. | Low: deleting loses UX notes. | Keep as reference research. | Yes |
| `docs/agent-wrapper-reference-study.md` | mark historical | Provider-wrapper research with broad future ideas. | Low: deleting loses comparison notes. | Keep as reference research. | Yes |
| `docs/aionui-bridge-reassessment.md` | mark historical | Explicit no-build decision for AionUi bridge. | Medium: deleting could make the deferral less discoverable. | Keep historical decision record. | Yes |
| `docs/spirit-cowork-console-reassessment.md` | mark historical | Explicit no-build decision for separate Cowork console. | Medium: deleting could make the deferral less discoverable. | Keep historical decision record. | Yes |
| `docs/scheduled-provider-tasks-design.md` | mark historical/deferred | Explicitly defers scheduled provider tasks. | Medium: deleting could hide why scheduled work is inactive. | Keep as deferred decision record. | Yes |
| `docs/limited-autopilot-design.md` | mark historical/deferred | Explicitly defers limited autopilot. | Medium: deleting could hide autopilot boundaries. | Keep as deferred decision record. | Yes |
| `docs/spiritos-mobile-surface-decision.md` | mark historical/deferred | Defers native mobile app while keeping responsive `/coding` active. | Low/medium: deleting could revive native app confusion. | Keep as deferred decision record. | Yes |
| `docs/cartographer-level-1-autonomy-plan.md` | archive candidate | Old phase plan; may contain implemented or superseded autonomy details. | Medium: deleting could lose historical Cartographer context. | Archive only after a Cartographer docs review. | Yes |
| `docs/cartographer-level-2-autonomy-plan.md` | archive candidate | Old phase plan; superseded by current safety cap and green-gate status. | Medium: deleting could lose historical autonomy constraints. | Archive only after a Cartographer docs review. | Yes |
| `docs/cartographer-level-3-autonomy-plan.md` | archive candidate | Old phase plan; not active for `/coding` polish. | Medium: deleting could lose historical execution-gate rationale. | Archive only after a Cartographer docs review. | Yes |
| `proxyCLI.md` | delete candidate if found | Retired and intentionally absent; recreating it would be misleading. | None if absent; high confusion risk if recreated. | Keep absent. If it reappears as a stale copy, request permission to delete. | Yes |
