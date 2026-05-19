# Cartographer Level 1 Autonomy Plan

## Safety Boundary

Cartographer v1 is safety-locked and human-review ready. Level 1 autonomy is not permission to apply changes. Soak evidence is review evidence only.

Level 1 must obey these non-negotiable boundaries:

- No source-code edits by Level 1 autonomy
- No secret, certificate, token, or `.env` edits
- No apply
- No commit
- No push
- No branch creation
- No delete or cleanup
- No approval bypass
- No provider fallback that can mutate files
- No scheduler writes
- No mobile execution controls
- No self-promotion from Level 1 to Level 2

Existing docs-autopilot dry-run, apply, and soak surfaces may exist. Level 1 may use only read-only scan, dry-run, and evidence behavior. It must not call apply unless a later explicit approval plan allows it.

## Autonomy Ladder

- Level 0: read-only observation and status reporting
- Level 1: assisted autonomy, read-only scan plus docs-only proposal drafting and evidence receipts
- Level 2: human-approved docs-only apply, still no commit or push
- Level 3: human-approved commit proposal creation, still no push
- Level 4: human-approved push queue, still no merge
- Level 5: future supervised multi-project operator, not in this plan

This plan covers Level 1 only. Levels 2 through 5 are out of scope except where they define what Level 1 must not do.

## Level 1 Policy Contract

Level 1 is evidence-first and proposal-only.

`allowed_actions`:

- read repo state
- classify dirty files
- scan docs
- scan Cartographer endpoints
- produce evidence receipts
- draft docs-only proposals
- generate rollback hints
- surface review-needed blockers

`forbidden_actions`:

- apply
- commit
- push
- branch creation
- source edits
- delete/cleanup
- secret edits
- approval bypass
- provider fallback that can mutate files
- scheduler writes
- mobile execution controls
- self-promotion

`permission_model`:

- authority_granted: false
- actions_taken: false
- write_actions_enabled: false
- operator_review_required: true
- promotion_allowed: false

If any Level 1 output implies authority to apply, commit, push, delete, self-promote, or bypass review, that output is a blocker.

## Phase 0: Baseline Hygiene Before Level 1

Purpose: Make sure the repo is clean enough to trust Cartographer evidence before adding any autonomy behavior.

### Increment 0.1: Dirty tree classification

Goal:

Classify every dirty file into clear buckets before Level 1 work starts.

Likely files touched:

- `docs/cartographer-level-1-autonomy-plan.md` only

Implementation notes:

- Do not modify existing dirty source files.
- Include commands to inspect:
  - `git status -sb`
  - `git diff --name-status`
  - `git diff -- src/components/coding/CodingCockpitShell.tsx`
  - `git diff -- src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
  - `git diff -- post-v1-closeout-note.md`
- Classify dirty files into docs, source, tests, generated output, deleted planning files, and unknown/unrelated.
- Treat the dirty `CodingCockpitShell` files and post-v1 closeout note as untouchable unless Britton explicitly approves touching them later.

Manual checks:

```bash
git status -sb
git diff --check
```

Expected output:

- Dirty files are visible and categorized.
- No unrelated dirty files are staged.
- No commit or push happens.

Debug path:

- If dirty files are unrelated to Cartographer Level 1, stop and ask Britton whether to stash, commit separately, or leave them untouched.
- If dirty files overlap a planned Level 1 implementation surface, keep Level 1 plan-only until Britton decides ownership.

Rollback:

```bash
git restore docs/cartographer-level-1-autonomy-plan.md
```

Permission gate:

Ask Britton before staging, committing, pushing, or touching the dirty `CodingCockpitShell` files.

Next step:

Move to freeze and safety revalidation.

### Increment 0.2: V1 freeze and safety revalidation

Goal:

Confirm Cartographer v1 is still valid before Level 1 planning continues.

Likely files touched:

- `docs/cartographer-level-1-autonomy-plan.md` only

Implementation notes:

- Use existing endpoints and runner profiles.
- Treat output as evidence only.
- Do not update freeze markers, proof artifacts, closeout artifacts, or soak evidence as part of this plan-only task.

Manual checks:

```bash
curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq .
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile cartographer-soak-snapshot
git status -sb
```

Expected output:

- Freeze marker is valid.
- V1 dashboard still shows ready or clearly explains blockers.
- Soak snapshot writes only expected evidence.
- HEAD does not change.

Debug path:

- If freeze validation fails, stop and diagnose freeze/proof artifacts only.
- If soak creates unexpected mutations, stop and inspect `status_delta` and `unexpected_status_delta`.

Rollback:

No rollback for read-only diagnostics. If this plan doc was edited incorrectly:

```bash
git restore docs/cartographer-level-1-autonomy-plan.md
```

Permission gate:

Ask Britton before editing freeze markers, proof artifacts, or any v1 evidence file.

Next step:

Define Level 1 contract.

## Phase 1: Level 1 Contract

Purpose: Make Level 1 boring, explicit, and testable before any behavior is wired.

### Increment 1.1: Define Level 1 policy contract

Goal:

Document the exact Level 1 permission model.

Likely files touched:

- `docs/cartographer-level-1-autonomy-plan.md`
- Possibly `docs/cartographer-trust-source-plan.md` only if needed and explicitly approved

Implementation notes:

- Keep the contract plain-language and machine-checkable.
- Define allowed actions and forbidden actions in the plan before implementation.
- State that Level 1 recommendations are evidence, not permission.
- State that Level 1 may not promote itself to Level 2.

Manual checks:

```bash
grep -n "Level 1" docs/cartographer-level-1-autonomy-plan.md
grep -n "forbidden_actions" docs/cartographer-level-1-autonomy-plan.md
git diff --check -- docs/cartographer-level-1-autonomy-plan.md
```

Expected output:

- The plan defines Level 1 in plain language.
- The forbidden actions are explicit.
- Diff check has no output.

Debug path:

- If the contract sounds like Level 2 or above, rewrite it to proposal-only and evidence-only.

Rollback:

```bash
git restore docs/cartographer-level-1-autonomy-plan.md
```

Permission gate:

Ask Britton before updating any existing trust or safety docs beyond this plan.

Next step:

Map the code surfaces that already exist.

### Increment 1.2: Existing surface inventory

Goal:

Map the current Cartographer endpoints and services that Level 1 will rely on.

Likely files touched:

- `docs/cartographer-level-1-autonomy-plan.md` only

Implementation notes:

Inventory these surfaces:

- `source_proxy/cartographer/autonomy_promotion.py`
- `source_proxy/cartographer/autopilot_config.py`
- `source_proxy/cartographer/autopilot_dry_run.py`
- `source_proxy/cartographer/autopilot_soak.py`
- `source_proxy/cartographer/project_health.py`
- `source_proxy/cartographer/trust_score.py`
- `source_proxy/cartographer/proposals.py`
- `source_proxy/cartographer/proposal_reviews.py`
- `source_proxy/cartographer/commit_proposals.py`
- `source_proxy/cartographer/push_queue.py`
- `source_proxy/api/cartographer.py`
- `src/app/v1/cartographer/docs-autopilot/dry-run/route.ts`
- `src/app/v1/cartographer/docs-autopilot/soak/route.ts`
- `src/app/v1/cartographer/docs-autopilot/apply/route.ts`
- `src/app/v1/cartographer/autonomy-promotion/route.ts`
- `src/app/v1/cartographer/project-health/route.ts`
- `src/app/v1/cartographer/trust-score/route.ts`

Responsibilities to document:

- Dry-run surfaces: read repo state and return proposal-only evidence.
- Soak surfaces: produce reviewable readiness evidence.
- Apply surfaces: out of scope and blocked for Level 1.
- Promotion surfaces: recommendation-only for Level 1.
- Commit and push surfaces: out of scope and blocked for Level 1.

Manual checks:

```bash
find source_proxy/cartographer -maxdepth 2 -type f | sort
find src/app/v1/cartographer -maxdepth 3 -type f | sort
grep -R "docs-autopilot" -n source_proxy src/app/v1/cartographer | head -80
```

Expected output:

- Plan lists existing surfaces by responsibility.
- Apply surface is marked out of scope for Level 1.

Debug path:

- If apply code appears reachable without explicit approval, mark it as a blocker for Level 1.

Rollback:

```bash
git restore docs/cartographer-level-1-autonomy-plan.md
```

Permission gate:

Ask Britton before editing code.

Next step:

Design the evidence packet.

## Phase 2: Level 1 Evidence Packet

Purpose: Make every autonomous scan produce something reviewable, explainable, and safe.

### Increment 2.1: Define Level 1 evidence schema

Goal:

Specify the JSON shape Cartographer should emit for every Level 1 dry run or soak run.

Likely files touched:

- `docs/cartographer-level-1-autonomy-plan.md`
- Later implementation may touch `source_proxy/cartographer/autopilot_dry_run.py`
- Later tests may touch `source_proxy/tests/test_cartographer_api.py` or `source_proxy/tests/test_proxy_runner.py`

Implementation notes:

Evidence packet should include:

```json
{
  "level": 1,
  "mode": "dry_run",
  "authority_granted": false,
  "actions_taken": false,
  "write_actions_enabled": false,
  "apply_enabled": false,
  "commit_enabled": false,
  "push_enabled": false,
  "allowed_scope": [],
  "forbidden_scope": [],
  "dirty_tree_summary": {},
  "candidate_count": 0,
  "candidates": [],
  "blockers": [],
  "rollback_hints": [],
  "recommended_next_action": "operator_review_required",
  "operator_review_required": true,
  "created_at": "ISO-8601 timestamp",
  "git_head_before": "sha",
  "git_head_after": "sha",
  "head_changed": false,
  "unexpected_status_delta": []
}
```

Manual checks:

```bash
grep -n "Evidence packet" docs/cartographer-level-1-autonomy-plan.md
git diff --check -- docs/cartographer-level-1-autonomy-plan.md
```

Expected output:

- Evidence packet schema is documented.
- It proves Level 1 cannot claim apply, commit, or push authority.

Debug path:

- If packet lacks before/after HEAD or status delta, add those fields before implementation.

Rollback:

```bash
git restore docs/cartographer-level-1-autonomy-plan.md
```

Permission gate:

Ask Britton before implementing schema in code.

Next step:

Design docs-only candidate rules.

### Increment 2.2: Docs-only candidate rules

Goal:

Define how Level 1 decides what it is allowed to propose.

Likely files touched:

- `docs/cartographer-level-1-autonomy-plan.md`

Implementation notes:

Allowed candidate targets:

- `docs/**/*.md`
- `README.md` only if explicitly allowed by a task spec
- Plan docs only if explicitly named

Forbidden candidate targets:

- `src/**`
- `source_proxy/**`
- `scout/src/**`
- `backend/**`
- `scripts/**`
- `.env*`
- certificates
- secrets
- package files
- lock files
- generated build output
- binary files

Candidate must include:

- exact target path
- reason
- risk level
- proposed change summary
- rollback hint
- manual check command
- why no source edit is needed

Manual checks:

```bash
grep -n "Allowed candidate targets" docs/cartographer-level-1-autonomy-plan.md
grep -n "Forbidden candidate targets" docs/cartographer-level-1-autonomy-plan.md
git diff --check -- docs/cartographer-level-1-autonomy-plan.md
```

Expected output:

- Candidate rules are strict.
- Level 1 cannot wander into source code.

Debug path:

- If a target path is ambiguous, classify it as blocked, not allowed.

Rollback:

```bash
git restore docs/cartographer-level-1-autonomy-plan.md
```

Permission gate:

Ask Britton before implementing candidate filtering.

Next step:

Design dry-run behavior.

## Phase 3: Dry-Run Only Autonomy

Purpose: Make Cartographer act smart without touching files.

### Increment 3.1: Level 1 dry-run endpoint contract

Goal:

Define what `/v1/cartographer/docs-autopilot/dry-run` should return for Level 1.

Likely files touched later:

- `source_proxy/cartographer/autopilot_dry_run.py`
- `source_proxy/api/cartographer.py`
- `src/app/v1/cartographer/docs-autopilot/dry-run/route.ts`
- `source_proxy/tests/test_cartographer_api.py`

Implementation notes:

Dry-run must:

- read repo state
- classify docs-only opportunities
- return candidates
- return blockers
- return rollback hints
- return recommended next action
- not write files
- not create commits
- not call apply
- not update proof/freeze artifacts
- not change HEAD

Manual checks:

```bash
curl -k -s https://localhost:3000/v1/cartographer/docs-autopilot/dry-run | jq .
git status -sb
git diff --check
```

Expected output:

- JSON response includes Level 1 fields.
- No file status changes after the request.
- HEAD unchanged.

Debug path:

- If status changes after dry-run, stop and mark dry-run unsafe.
- If dry-run suggests source edits, block candidate generation until filters are fixed.

Rollback:

```bash
git restore source_proxy/cartographer/autopilot_dry_run.py source_proxy/api/cartographer.py src/app/v1/cartographer/docs-autopilot/dry-run/route.ts source_proxy/tests/test_cartographer_api.py
```

Permission gate:

Ask Britton before code implementation.

Next step:

Design soak behavior.

### Increment 3.2: Level 1 soak profile

Goal:

Extend soak evidence to report Level 1 readiness without granting authority.

Likely files touched later:

- `source_proxy/testing/runner.py`
- `source_proxy/cartographer/autopilot_soak.py`
- `source_proxy/tests/test_proxy_runner.py`
- `docs/cartographer-level-1-autonomy-plan.md`

Implementation notes:

Soak profile may write only a JSON evidence snapshot under:

```text
source_proxy/cartographer/soak-logs/
```

Soak must prove:

- snapshot_log_only: true
- head_changed: false
- unexpected_status_delta: []
- autonomy escalation passed
- apply disabled
- commit disabled
- push disabled
- approval bypass disabled
- Level 1 candidate generation is proposal-only

Manual checks:

```bash
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile cartographer-soak-snapshot
git status -sb
git diff -- source_proxy/cartographer/soak-logs
```

Expected output:

- Runner passes.
- Only expected soak log appears.
- Recommendation is ready for next increment or continue soak.
- No commit or push authority appears.

Debug path:

- If the runner shows watch or blocked, follow its `next_actions` and do not continue implementation.
- If dirty tree penalty remains, classify it before promotion.

Rollback:

```bash
git restore source_proxy/testing/runner.py source_proxy/cartographer/autopilot_soak.py source_proxy/tests/test_proxy_runner.py docs/cartographer-level-1-autonomy-plan.md
```

Permission gate:

Ask Britton before changing runner behavior.

Next step:

Design proposal drafting.

## Phase 4: Docs-Only Proposal Drafting

Purpose: Let Level 1 draft proposals without applying them.

### Increment 4.1: Proposal draft contract

Goal:

Define the difference between a proposal draft and an applied file change.

Likely files touched later:

- `source_proxy/cartographer/proposals.py`
- `source_proxy/cartographer/proposal_reviews.py`
- `source_proxy/cartographer/autopilot_dry_run.py`
- `source_proxy/tests/test_cartographer_api.py`

Implementation notes:

A Level 1 proposal draft may include:

- title
- target docs path
- reason
- proposed patch text or summary
- risk level
- rollback hint
- manual check
- approval_required: true
- apply_allowed: false for Level 1
- commit_allowed: false
- push_allowed: false

It must not:

- write the target docs file
- mark itself approved
- call apply-approved
- create a commit proposal
- create a push queue item

Manual checks:

```bash
curl -k -s https://localhost:3000/v1/cartographer/proposals | jq .
curl -k -s https://localhost:3000/v1/cartographer/docs-autopilot/dry-run | jq .
git status -sb
```

Expected output:

- Proposal drafts are visible.
- Human review is required.
- No target file is changed.

Debug path:

- If a proposal appears as approved automatically, stop and fix approval separation.
- If proposal creation creates commit or push records, block Level 1.

Rollback:

```bash
git restore source_proxy/cartographer/proposals.py source_proxy/cartographer/proposal_reviews.py source_proxy/cartographer/autopilot_dry_run.py source_proxy/tests/test_cartographer_api.py
```

Permission gate:

Ask Britton before implementation.

Next step:

Design UI visibility.

## Phase 5: Operator UI For Level 1

Purpose: Make Level 1 understandable from dashboard, `/coding`, and mobile review.

### Increment 5.1: Level 1 status card

Goal:

Show exactly what Cartographer can and cannot do.

Likely files touched later:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- Possibly `src/components/coding/CodingCockpitShell.tsx`
- Related tests

Implementation notes:

UI should show:

- Autonomy Level: 1 candidate or disabled
- Mode: dry-run only
- Kill switch state
- Daily cap remaining
- Allowed docs scope
- Last evidence link
- Latest blocker
- Proposal count
- Review required
- Apply disabled
- Commit disabled
- Push disabled

Manual checks:

```bash
npx vitest run src/components/dashboard
npx vitest run src/components/coding
npm run typecheck
```

Expected output:

- UI displays Level 1 without implying action authority.
- No approve/apply/commit/push button appears inside Level 1 status.

Debug path:

- If UI language says "autopilot applied" or "ready to push", rewrite copy to "review needed" or "proposal ready".

Rollback:

```bash
git restore src/components/dashboard/HomelabCartographerWidget.tsx src/components/coding/CodingCockpitShell.tsx
```

Permission gate:

Ask Britton before touching UI files, especially if they are already dirty.

Next step:

Add negative tests.

### Increment 5.2: Mobile-safe review copy

Goal:

Make the Level 1 status readable on phone through Codex mobile or browser.

Likely files touched later:

- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/SpiritWorkspaceMobileChromeContext.tsx` if needed
- Tests only if existing patterns require them

Implementation notes:

Mobile view must prioritize:

- status
- blockers
- next safe action
- last evidence
- "do not approve yet" warnings
- no execution controls

Manual checks:

```bash
npm run typecheck
npx vitest run src/components/dashboard
```

Manual browser check on mobile viewport if Playwright/manual browser is available.

Expected output:

- Mobile view can tell Britton what happened and what to review.
- No mobile execution controls are added.

Debug path:

- If content is cramped, reduce copy and keep details in expandable sections.

Rollback:

```bash
git restore src/components/dashboard/HomelabCartographerWidget.tsx src/components/dashboard/SpiritWorkspaceMobileChromeContext.tsx
```

Permission gate:

Ask Britton before UI implementation.

Next step:

Hard-block unsafe behavior.

## Phase 6: Safety Tests And Promotion Gate

Purpose: Prove Level 1 cannot escape into Level 2 behavior.

### Increment 6.1: Negative safety tests

Goal:

Add tests that fail if Level 1 can apply, commit, push, delete, or self-promote.

Likely files touched later:

- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_proxy_runner.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`

Implementation notes:

Tests should assert:

- Level 1 dry-run does not mutate files.
- Level 1 dry-run does not change HEAD.
- Level 1 does not call apply.
- Level 1 does not create commit proposals.
- Level 1 does not create push queue items.
- Level 1 cannot target `source_proxy`, `src`, `scout/src`, `backend`, `scripts`, `.env`, certs, or secrets.
- Level 1 promotion response is recommendation-only.

Manual checks:

```bash
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "autopilot or proposal or level"
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py -k "autonomy or soak"
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py
```

Expected output:

- Tests pass.
- Unsafe authority paths are blocked.

Debug path:

- If any test fails because authority is available, stop and fix the gate before proceeding.

Rollback:

```bash
git restore source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_proxy_runner.py source_proxy/tests/test_cartographer_safety_audit.py
```

Permission gate:

Ask Britton before test implementation.

Next step:

Add promotion readiness criteria.

### Increment 6.2: Level 1 readiness score

Goal:

Create a readiness score that recommends Level 1 but does not enable it.

Likely files touched later:

- `source_proxy/cartographer/autonomy_promotion.py`
- `source_proxy/cartographer/trust_score.py`
- `source_proxy/tests/test_cartographer_api.py`

Implementation notes:

Readiness score inputs:

- v1 freeze valid
- latest soak pass
- no unexpected status delta
- head unchanged
- dirty files classified
- apply disabled
- commit disabled
- push disabled
- approval bypass disabled
- docs-only candidate filters valid
- kill switch visible
- daily cap visible
- rollback hints present

Output labels:

- blocked
- watch
- ready_for_level_1_review

Important:

The score must never enable Level 1 by itself.

Manual checks:

```bash
curl -k -s https://localhost:3000/v1/cartographer/autonomy-promotion | jq .
curl -k -s https://localhost:3000/v1/cartographer/trust-score | jq .
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "autonomy or trust"
```

Expected output:

- Recommendation is clear.
- No authority is granted.
- Human review remains required.

Debug path:

- If recommendation grants action authority, fail the test and rewrite output.

Rollback:

```bash
git restore source_proxy/cartographer/autonomy_promotion.py source_proxy/cartographer/trust_score.py source_proxy/tests/test_cartographer_api.py
```

Permission gate:

Ask Britton before implementation.

Next step:

Run closeout.

## Phase 7: Level 1 Closeout

Purpose: Prove the plan is ready to implement or prove the implementation is safe if Britton later approves building it.

### Increment 7.1: Plan-only closeout

Goal:

Close the planning task without implementing autonomy.

Likely files touched:

- `docs/cartographer-level-1-autonomy-plan.md`

Implementation notes:

Add final section:

- Current status
- Safe to implement next
- Still forbidden
- Required manual checks before first implementation increment
- Recommended first implementation increment

Manual checks:

```bash
sed -n '1,260p' docs/cartographer-level-1-autonomy-plan.md
grep -n "No source-code edits\|No apply\|No commit\|No push\|No self-promotion" docs/cartographer-level-1-autonomy-plan.md
git diff --check -- docs/cartographer-level-1-autonomy-plan.md
git status -sb
```

Expected output:

- Plan is readable.
- Safety boundaries are explicit.
- Only the plan doc changed unless Britton approved more.

Debug path:

- If extra files changed, stop and explain why before staging anything.

Rollback:

```bash
git restore docs/cartographer-level-1-autonomy-plan.md
```

Permission gate:

Ask Britton before staging, committing, pushing, or implementing.

Next step:

Report completion and recommend the first implementation increment.

### Increment 7.2: Recommended first implementation increment after plan approval

Goal:

Prepare the next safe build step, but do not do it until Britton approves.

Recommended first build increment:

Implement Level 1 dry-run evidence schema only.

Why:

It is safer than UI, safer than apply, and gives us proof before behavior.

Manual checks for that future increment:

```bash
curl -k -s https://localhost:3000/v1/cartographer/docs-autopilot/dry-run | jq .
git status -sb
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "autopilot or level"
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile cartographer-soak-snapshot
```

Expected output:

- Dry-run emits Level 1 evidence.
- No files changed except approved implementation files.
- No apply, commit, or push authority appears.

Permission gate:

Ask Britton before writing implementation code.

Next step:

Wait for explicit approval before implementation.

## Implementation Closeout And Review Packet

Status:

Level 1 is implemented as a review-only evidence layer. It can observe, classify, produce evidence, draft docs-only proposals, report rollback hints, and surface blockers. It still cannot apply, commit, push, create branches, delete files, clean up files, bypass approval, write schedules, provide mobile execution controls, or promote itself.

Implemented increments:

- Level 1 dry-run evidence schema
- Level 1 soak evidence readiness
- Docs-only proposal draft contract
- Level 1 dashboard status card
- Mobile-safe Level 1 review copy
- Level 1 negative safety tests
- Level 1 readiness score

Files intentionally touched for Level 1:

- `docs/cartographer-level-1-autonomy-plan.md`
- `source_proxy/cartographer/autonomy_promotion.py`
- `source_proxy/cartographer/autopilot_dry_run.py`
- `source_proxy/cartographer/autopilot_soak.py`
- `source_proxy/cartographer/service.py`
- `source_proxy/testing/runner.py`
- `source_proxy/tests/test_cartographer_api.py`
- `source_proxy/tests/test_cartographer_safety_audit.py`
- `source_proxy/tests/test_proxy_runner.py`
- `src/components/dashboard/HomelabCartographerWidget.tsx`
- `src/components/dashboard/__tests__/HomelabCartographerWidget.test.tsx`
- `src/styles/dashboard-demo-v4.css`

Dirty files intentionally left untouched:

- `src/components/coding/CodingCockpitShell.tsx`
- `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`
- Scout working files and Scout soak logs
- Existing deleted root planning docs
- `post-v1-closeout-note.md`
- Any unrelated files that appeared during implementation, including `docs/codingUI.md`, `playwright.config.mjs`, `tests/`, and Scout discovery job files

Current readiness score:

- Label: `watch`
- Score: `92`
- Authority granted: `False`
- Enablement allowed: `False`

Review packet:

- Dry-run endpoint emits `level: 1`, `mode: dry_run`, before/after HEAD, dirty tree summary, candidate count, candidates, blockers, rollback hints, and disabled apply/commit/push fields.
- Soak endpoint emits `level: 1`, `mode: soak`, snapshot-log-only readiness fields, disabled apply/commit/push fields, approval bypass disabled, and operator review required.
- Proposal endpoint annotates every proposal with draft-only metadata, target docs path, risk, rollback hint, manual check, and false apply/commit/push fields.
- Dashboard widget displays Level 1 as dry-run/review-only and hides approve/apply/commit/push controls.
- Mobile review copy prioritizes status, blocker, next safe action, and evidence without adding execution controls.
- Safety tests prove Level 1 cannot mutate files, change HEAD, apply, commit, push, create push queue items, target source paths as allowed, or self-promote.
- Autonomy promotion reports Level 1 readiness as recommendation-only with labels `blocked`, `watch`, or `ready_for_level_1_review`.

Still forbidden:

- No source-code edits by Level 1 autonomy
- No secret, certificate, token, or `.env` edits
- No apply
- No commit
- No push
- No branch creation
- No delete or cleanup
- No approval bypass
- No provider fallback that can mutate files
- No scheduler writes
- No mobile execution controls
- No self-promotion from Level 1 to Level 2

Closeout manual checks:

```bash
git status -sb
git diff --name-status
git diff --check
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -k "autopilot or level or proposal or autonomy or trust"
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_cartographer_safety_audit.py
PYTHONPATH=. .venv/bin/python -m pytest source_proxy/tests/test_proxy_runner.py -k "cartographer_soak_snapshot or autonomy"
npx vitest run src/components/dashboard/__tests__/HomelabCartographerWidget.test.tsx
npx vitest run src/components/dashboard
npm run typecheck
PYTHONPATH=. .venv/bin/python - <<'PY'
from source_proxy.cartographer.service import build_cartographer_autonomy_promotion
payload = build_cartographer_autonomy_promotion()
print(payload["level_1_recommendation"])
print(payload["level_1_readiness_score"])
print(payload["level_1_authority_granted"])
print(payload["level_1_enablement_allowed"])
PY
```

Expected closeout output:

- API Level 1/proposal/autonomy slice passes
- Cartographer safety audit passes
- Proxy runner soak/autonomy slice passes
- Cartographer widget tests pass
- Dashboard tests pass
- Typecheck passes
- Readiness score prints `watch`, `92`, `False`, `False` in the current dirty-tree state
- `git diff --check` has no output
- No staging, commit, push, branch creation, apply, cleanup, or CodingCockpitShell edit occurs

Rollback:

```bash
git restore docs/cartographer-level-1-autonomy-plan.md source_proxy/cartographer/autonomy_promotion.py source_proxy/cartographer/autopilot_dry_run.py source_proxy/cartographer/autopilot_soak.py source_proxy/cartographer/service.py source_proxy/testing/runner.py source_proxy/tests/test_cartographer_api.py source_proxy/tests/test_cartographer_safety_audit.py source_proxy/tests/test_proxy_runner.py src/components/dashboard/HomelabCartographerWidget.tsx src/components/dashboard/__tests__/HomelabCartographerWidget.test.tsx src/styles/dashboard-demo-v4.css
```

Permission gate:

Ask Britton before staging, committing, pushing, enabling Level 1 authority, calling apply, adding commit/push workflow, editing dirty CodingCockpitShell files, or moving to Level 2.

Recommended next increment:

Human review of the Level 1 packet, then decide whether to keep soaking at `watch` or address the blockers that prevent `ready_for_level_1_review`.
