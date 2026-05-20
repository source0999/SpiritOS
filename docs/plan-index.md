# SpiritOS Plan Index

status: active

Status date: 2026-05-20

## Active Plans

| Plan | Status | Role | Authority |
| --- | --- | --- | --- |
| `docs/source-proxy-production-hardening-plan.md` | status: active | Current Source Proxy production plan | Records green safety gate and constrains next work |
| `docs/codingUI.md` | status: active | Active `/coding` UI polish plan | Authorizes planning for UI polish only; implementation still requires approval |
| `docs/design-systems-master-v0.1.md` | status: planning complete | Manual-first Design Intelligence Stack plan | Does not authorize implementation; next increment requires explicit approval |
| `productionProxy.md` | status: historical | Uploaded staging copy | Historical only; follow the durable repo copy instead |

## Source Proxy Plan Authority Map

The green Source Proxy safety gate passed on 2026-05-20 based on user-provided evidence: global safety regression passed, Source Proxy tests passed, Scout backend tests passed, Cartographer safety passed, dashboard smoke passed, no unexpected mutation occurred, no unexpected Level 2 evidence appeared, no commit occurred during the run, HEAD stayed stable at `3e55bdc`, and `main` matched `origin/main` at `3e55bdc`.

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
