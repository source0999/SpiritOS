---
blueprint_id: cartographer-dashboard-mobile-qa
title: Cartographer Dashboard + Mobile QA
project: SpiritOS
component: cartographer
doc_type: runbook
status: runbook
source_of_truth: false
owner: Britton
code_paths:
  - src/components/dashboard/**
  - src/app/v1/cartographer/**
  - source_proxy/api/cartographer.py
  - source_proxy/cartographer/**
related_blueprints:
  - dashboard-state
  - system-state
  - project-tracker
write_policy: proposal_only_until_dashboard_approved
last_verified: 2026-05-16
---

# Cartographer Dashboard + Mobile QA

Use this checklist before calling a Cartographer dashboard change done. Cartographer remains read-only unless a later approval lane explicitly says otherwise.

## Environment

- Local desktop: `http://localhost:3000`
- LAN desktop: `http://<LAN_HOST_OR_IP>:3000`
- Tailscale: `http://<TAILSCALE_HOST_OR_IP>:3000` or the configured HTTPS host
- Source Proxy: `https://localhost:8787`

When changing `SPIRIT_PROJECT_PATH`, `NEXT_ALLOWED_DEV_ORIGINS`, certificates, or proxy env, restart the affected dev server before testing.

## API Baseline

- [ ] `curl -k https://localhost:8787/v1/cartographer/status` returns `status: observing`.
- [ ] `write_actions_enabled` is `false`.
- [ ] `safety.approval_required_for_commits` is `true`.
- [ ] `safety.approval_required_for_pushes` is `true`.
- [ ] `safety.scout_bypass_allowed` is `false`.
- [ ] `safety.source_proxy_approval_bypass_allowed` is `false`.

Expected:

```json
{
  "status": "observing",
  "write_actions_enabled": false,
  "safety": {
    "approval_required_for_commits": true,
    "approval_required_for_pushes": true
  }
}
```

## Desktop Dashboard

- [ ] Open `/`.
- [ ] Spirit Cartographer widget appears without stuck loading.
- [ ] Blueprint Review widget appears when proposal data is available.
- [ ] Project health, branch recommendations, commit proposals, push queue, and audit trail endpoints can fail closed without exposing write buttons.
- [ ] Approve/reject/request-edit controls are reachable by keyboard.
- [ ] No apply, commit, or push control appears for generated or unapproved proposals.

Expected:

```text
Cartographer dashboard QA passed: desktop
```

## LAN Dashboard

- [ ] Open `/` through the LAN host or IP.
- [ ] Dashboard shows the same Cartographer counts as local desktop for `projects`, `blueprints`, `pending_proposals`, and `write_actions_enabled`.
- [ ] LAN origin does not reuse local browser storage assumptions; treat it as a separate origin.
- [ ] Source Proxy bridge errors show an unavailable/read-only state rather than a write action.

Expected:

```text
Cartographer dashboard QA passed: LAN
```

## Tailscale Dashboard

- [ ] Open `/` through the Tailscale host or IP.
- [ ] Cartographer widgets leave loading state.
- [ ] `/v1/cartographer/project-health` and `/v1/cartographer/audit-trail` return JSON through the dashboard bridge.
- [ ] If proxy/cert/origin config is wrong, the UI shows unavailable/read-only state instead of hiding safety status.
- [ ] No push approval can be triggered accidentally from a stale or partially loaded screen.

Expected:

```text
Cartographer dashboard QA passed: Tailscale
```

## Phone Width

- [ ] Test at 360px and 390px width in dev tools or on a real phone.
- [ ] There is no horizontal page scroll.
- [ ] Cartographer cards do not overlap the mobile navigation.
- [ ] Long proposal IDs, branch names, file paths, and audit events wrap or truncate cleanly.
- [ ] Approve/reject buttons are at least 44px tall/wide and are not adjacent to push approval without a clear separation.
- [ ] Push approval cannot be tapped accidentally; pending push state remains informational unless a later explicit approval surface is active.

Expected:

```text
Cartographer dashboard QA passed: mobile
```

## Closeout

Record the checked surfaces:

```text
Cartographer dashboard QA passed:
- desktop
- LAN
- Tailscale
- mobile
```

If any surface fails, keep the related proposal in review and do not proceed to commit or push approval.

### Cartographer Review Note
- Reason: qa_gap.
- Component: dashboard.
- Changed files: src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx.
- Manual check: confirm this blueprint still matches the changed implementation.

### Cartographer Review Note
- Reason: qa_gap.
- Component: dashboard.
- Changed files: src/components/dashboard/ScoutIntelligenceCenter.tsx, src/components/dashboard/demo-v4/DashboardDemoV4ThemePicker.test.tsx.
- Manual check: confirm this blueprint still matches the changed implementation.

### Cartographer Review Note
- Reason: qa_gap.
- Component: dashboard.
- Changed files: src/components/dashboard/ScoutIntelligenceCenter.tsx.
- Manual check: confirm this blueprint still matches the changed implementation.

### Cartographer Review Note
- Reason: qa_gap.
- Component: dashboard.
- Changed files: src/components/dashboard/ScoutIntelligenceCenter.tsx, src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx.
- Manual check: confirm this blueprint still matches the changed implementation.
