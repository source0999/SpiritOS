# Limited Autopilot Design

Status date: 2026-05-18
Status: design only

## Purpose

This document decides whether Source Proxy should enable limited autopilot after the current hardening work.

No autopilot was enabled for this increment. No scheduler, provider task, apply path, commit path, or push path was added.

## Decision

Do not enable limited autopilot now.

Future limited autopilot may be considered as docs-only only after long proof. It must start as review evidence, not as a write-capable worker.

## Minimum Proof Before Reassessment

Any future reassessment needs all of these first:

- many clean soak runs over time
- repeated `cartographer-soak-snapshot` reports with no autonomy escalation
- `autopilot_action_available: false` until explicitly approved
- no unexpected file-change deltas
- no HEAD changes during diagnostics
- no protected or secret-shaped paths in target lists
- no source-code edit authority
- no commit authority
- no push authority
- clear rollback evidence for every proposed change
- visible kill switch
- explicit daily cap
- explicit allowed-docs scope
- manual operator review after evidence is produced

## Allowed Future Shape

Allowed later, after a separate approval gate:

- read-only scan
- docs-only proposal drafting
- evidence receipt generation
- rollback hint generation
- notification that review is needed
- dashboard blocker explaining why autopilot did not run

Not allowed now:

- source edits
- secret edits
- certificate edits
- `.env*` edits
- apply
- commit
- push
- branch creation
- cleanup
- provider fallback that can mutate files
- scheduled writes
- mobile execution controls

## Execution Ladder

The only acceptable future ladder is:

1. Autopilot candidate runs a read-only check.
2. Candidate produces evidence.
3. Candidate produces a docs-only proposal.
4. Operator reviews the evidence.
5. Operator explicitly approves a bounded doc write.
6. Apply remains a separate action.
7. Commit remains a separate action.
8. Push remains a separate action.

Any ladder that combines review, approval, apply, commit, or push is rejected.

## Existing Guardrails

Current Source Proxy and Cartographer evidence already requires this conservative posture:

- soak snapshots are evidence, not permission
- autonomy escalation checks must keep autonomous apply, commit, push, and approval bypass disabled
- docs autopilot action availability must stay false unless deliberately configured
- write actions remain disabled by default
- approval bypass remains blocked
- expected evidence snapshots are separated from unsafe dirty files

## Kill Switch Requirements

Before any future autopilot exists, the operator surface must show:

- autopilot enabled state
- kill switch state
- daily cap remaining
- allowed docs scope
- last run time
- latest evidence link
- latest blocker
- approval state
- rollback hint

If the kill switch state is unknown, autopilot must be blocked.

## Safety Boundary

This design does not authorize:

- enabling autopilot
- docs autopilot writes
- source edits
- secret edits
- scheduled tasks
- provider fallback automation
- apply
- commit
- push
- approval bypass
- autonomous multi-agent writes

Source Proxy remains the system of record for all authority boundaries.

## Recommendation

Keep limited autopilot deferred.

Reassess only after daily-use alpha is stable, soak evidence is boring across many runs, rollback evidence is reliable, and Britton explicitly approves a docs-only autopilot experiment with a visible kill switch.

## Manual Check

```bash
cd /home/source/SpiritOS
sed -n '1,260p' docs/limited-autopilot-design.md
grep -n "Do not enable limited autopilot now\\|docs-only only after long proof\\|does not authorize" docs/limited-autopilot-design.md
git diff --check
```

Expected output:

- design document only
- decision says no limited autopilot now
- future shape is docs-only only after long proof
- source edits, apply, commit, and push remain unauthorized
- `git diff --check` has no output

## Rollback

```bash
git restore docs/limited-autopilot-design.md docs/source-proxy-production-hardening-plan.md
```
