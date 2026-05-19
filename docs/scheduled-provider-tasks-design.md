# Scheduled Provider Tasks Design

Status date: 2026-05-18
Status: design only

## Purpose

This document decides how SpiritOS should think about scheduled provider tasks after Source Proxy hardening.

No scheduler was built for this increment. No scheduled provider execution was enabled.

## Decision

Do not add scheduled provider tasks now.

Future scheduled work must be notification-only by default. Any write-capable task must require a separate explicit approval after the scheduled check produces evidence.

## Near-Term Allowed Shape

Allowed later, after a separate approval gate:

- scheduled read-only health checks
- scheduled evidence collection
- scheduled Cartographer/Scout summaries
- scheduled notification that a manual review is needed
- scheduled proposal drafting that cannot apply files

Not allowed now:

- scheduled file writes
- scheduled apply
- scheduled commit
- scheduled push
- scheduled cleanup
- scheduled provider fallback that can mutate files
- scheduled secret, certificate, token, or `.env*` edits

## Hard Requirements For Future Scheduled Tasks

Any future scheduled provider task must define:

- exact TaskSpec
- allowed files
- forbidden files
- max runtime
- max daily run count
- budget/cost limit
- provider capability requirement
- no apply, commit, or push authority
- notification-only default
- approval before any write
- audit record for every run
- rollback guidance for any proposed change
- kill switch

## Execution Model

The only safe future ladder is:

1. Schedule runs a read-only check.
2. Check emits evidence.
3. Operator receives a notification or dashboard blocker.
4. Human reviews the evidence.
5. Human explicitly approves any proposal.
6. Apply remains separate.
7. Commit remains separate.
8. Push remains separate.

Any design that combines these steps is rejected.

## Relationship To Existing Systems

Cartographer docs autopilot and soak checks already prove why this must stay conservative:

- soak evidence is not approval
- autopilot action availability must stay false unless explicitly configured
- kill switch must remain visible
- daily cap must be explicit
- source edits are not allowed as a default scheduled behavior

Scout scheduler state is diagnostic context only. It does not authorize Source Proxy provider tasks.

## Notification Policy

Future scheduled tasks may notify:

- check passed
- check failed
- evidence is ready for review
- provider unavailable
- budget/cap exhausted
- approval needed

Notifications must not imply:

- approval granted
- apply completed
- commit created
- push completed
- unsafe cleanup is allowed

## Future UI Requirements

Before any schedule UI exists, `/coding` or Cartographer must show:

- schedule name
- last run time
- next run time
- read-only status
- provider used
- evidence link
- approval state
- blockers
- kill switch state
- daily cap remaining

No per-schedule apply, commit, or push button should exist.

## Safety Boundary

This design does not authorize:

- scheduler implementation
- background provider tasks
- automatic writes
- automatic apply
- automatic commit
- automatic push
- provider fallback automation
- mobile execution controls

Source Proxy remains the system of record for all authority boundaries.

## Recommendation

Defer scheduled provider tasks.

If scheduling is revisited, start with read-only notification checks only. Do not schedule writes until repeated soak evidence, explicit approval gates, budget limits, and rollback/audit flows are boring.

## Manual Check

```bash
cd /home/source/SpiritOS
sed -n '1,260p' docs/scheduled-provider-tasks-design.md
grep -n "Do not add scheduled provider tasks now\\|notification-only by default\\|does not authorize" docs/scheduled-provider-tasks-design.md
git diff --check
```

Expected output:

- design document only
- decision says no scheduled provider tasks now
- notification-only default is explicit
- apply, commit, and push remain separate gates
- `git diff --check` has no output

## Rollback

```bash
git restore docs/scheduled-provider-tasks-design.md docs/source-proxy-production-hardening-plan.md
```
