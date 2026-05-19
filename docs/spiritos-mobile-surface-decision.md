# SpiritOS Mobile Surface Decision

Status date: 2026-05-18
Status: decision document only

## Purpose

This document decides what SpiritOS mobile should do now that Codex mobile, SSH fallback, and the `/coding` operator console exist.

No native mobile app was started for this decision. No mobile execution surface was built.

## Decision

Do not build a native SpiritOS mobile app now.

Near term: use Codex mobile plus SSH fallback for review and manual checks.

Mid term: improve the responsive `/coding` operator console for phone and tablet review.

Later: consider a native app only if the responsive web console cannot support the required operator workflows.

## Current Mobile Surfaces

| Surface | Use Now | Authority |
| --- | --- | --- |
| Codex mobile | Ask Codex to run scoped checks, summarize output, and continue increments. | Review/control only; no Source Proxy bypass. |
| SSH/Termius | Run raw terminal commands, restart services, inspect ports/logs. | Manual terminal only; no bypass of approval gates. |
| `/coding` in browser | Review task state, evidence, blockers, approvals, worker lanes. | Source Proxy UI; approval/apply/commit/push stay gated. |
| RustDesk | GUI fallback when browser-only visual inspection is required. | Manual GUI only; no authority change. |

## What Mobile Should Do Now

Mobile should support:

- reviewing manual-check results
- reading compact evidence receipts
- approving Codex-side scoped diagnostics
- reviewing `/coding` task state
- checking blockers and next safe actions
- deciding whether to continue to the next increment

Mobile should not support:

- native apply
- native commit
- native push
- broad cleanup
- scheduled provider execution
- autonomous worker actions
- secret or certificate edits
- provider promotion

## Why No Native App Yet

- Codex mobile already covers the highest-value remote review loop.
- SSH/Termius already covers host terminal fallback.
- `/coding` is the correct Source Proxy authority surface.
- A native app would create a second control plane before daily-use alpha is boring.
- Mobile execution controls are high risk unless notification, audit, and approval gates are already proven.

## Mid-Term Web Improvements

Improve `/coding` before considering native mobile:

- tighter mobile layout for task queue and evidence cards
- compact approval checklist view
- clearer blocked-state receipt
- larger tap targets for review-only controls
- sticky next-safe-action summary
- better copy/paste receipt blocks
- responsive worker-lane display

These are web-console improvements, not native app work.

## Future Native App Gate

Only reassess a native app if all of these are true:

- daily-use alpha is stable
- `/coding` responsive view is not enough
- mobile workflows are documented and repeated
- notification needs cannot be met through web/Codex/SSH
- Source Proxy approval gates remain central
- no native app action can bypass apply, commit, or push approval

## Safety Boundary

This decision does not authorize:

- native mobile app development
- mobile execution controls
- mobile apply, commit, or push
- background provider tasks
- scheduled checks
- push notifications that imply approval
- bypassing Source Proxy gates

The mobile rule remains:

- mobile can review
- mobile can request scoped diagnostics
- mobile can approve Codex-side safe docs edits only when the active increment already authorizes them
- Source Proxy remains the system of record
- apply, commit, and push remain separate explicit gates

## Recommendation

Use Codex mobile plus SSH fallback now.

Make `/coding` more responsive if mobile review remains painful. Do not start a native SpiritOS mobile app until the web console proves insufficient.

## Manual Check

```bash
cd /home/source/SpiritOS
sed -n '1,260p' docs/spiritos-mobile-surface-decision.md
grep -n "Do not build a native SpiritOS mobile app now\\|Use Codex mobile plus SSH fallback now\\|does not authorize" docs/spiritos-mobile-surface-decision.md
git diff --check
```

Expected output:

- decision document only
- decision says no native app now
- Codex mobile plus SSH fallback remains near-term flow
- `/coding` remains the Source Proxy web console
- `git diff --check` has no output

## Rollback

```bash
git restore docs/spiritos-mobile-surface-decision.md docs/source-proxy-production-hardening-plan.md
```
