# Scout Polish Master Plan v0.4

Status date: 2026-05-16
Owner: Britton
System: SpiritOS Scout
Current focus: turn Scout from "working backend intelligence feed" into a clear, trusted, polished intelligence control center.

## 0. Current diagnosis

Scout is not broken.

Scout currently has:

- Scout API healthy.
- Scout smoke runner passing.
- Source gate runner passing.
- Search diagnostics passing.
- SearXNG reachable from Scout through host.docker.internal.
- 18 source candidates visible.
- 5 active sources.
- 2 approved candidates.
- 1 blocked candidate.
- 1 rejected candidate.
- 12 recommended candidates.
- 2 needs-review candidates.
- Soak snapshot passing and writing timestamped evidence.

The current issue is:

- scout-search-smoke fails because the daily discovery job limit has been reached.
- The failure happens before search preview or extract.
- Active sources did not change.
- Approved candidate count did not change.
- Preview did not create candidates.
- Extract did not create sources.
- No auto approval happened.

Current queued discovery jobs:

- 5 queued jobs.
- Several duplicate Pydantic jobs.
- One spam/noise test job.
- One FastAPI release job.
- All have started_at null.
- All have finished_at null.

Plain meaning:

Scout can search, but the queue and daily budget layer are not polished yet.

## 1. Core safety rules

Scout may:

- observe
- search within strict limits
- create discovery jobs within budget
- preview search results
- extract source candidates
- score candidates
- explain why a source looks useful
- recommend sources
- queue packets
- recheck packets
- write soak snapshots
- produce evidence

Scout must not:

- auto-activate sources by default
- approve sources without human approval
- reject or block sources without human intent
- write to /coding
- write to proxy memory by default
- trigger code edits
- approve/apply/commit/push anything
- hide failures behind vague success text
- call a budget-blocked search smoke "normal pass"

## 2. Product model

Scout should be split into three clear gates.

### Source Gate

Question:
Should Scout be allowed to watch this source?

Examples:

- github://pydantic/pydantic
- https://docs.pydantic.dev/
- https://blog.python.org/feeds/posts/default

Actions:

- approve source
- reject source
- block source
- view review history
- view reason codes
- view trust score
- view poller support

### Packet Gate

Question:
Is this specific intelligence packet useful enough to promote?

Actions:

- recheck packet
- queue packet for promotion
- promote packet
- save for later
- ignore
- view source
- view usefulness reason

### Discovery Gate

Question:
What search jobs are queued, running, blocked, duplicate, stale, or over budget?

Actions:

- view jobs
- view budget
- run search smoke only when budget allows
- pause job
- resume job
- cancel stale job
- dedupe duplicate jobs
- view search preview
- extract candidates without activating sources

## 3. Master acceptance criteria

Scout Polish v0.4 is done when:

1. Dashboard clearly separates Source Gate, Packet Gate, Discovery Gate, Sources, and Diagnostics.
2. Source Queue no longer feels like a mystery.
3. Queue and Recheck buttons are renamed or explained.
4. Discovery budget shows used, remaining, limit, and next reset.
5. Search smoke reports BLOCKED_BY_BUDGET instead of generic FAIL when daily cap is reached.
6. Queued discovery jobs show stale, duplicate, blocked, running, failed, or completed status.
7. Stale/duplicate discovery jobs can be safely canceled or deduped with human approval.
8. Search preview never creates candidates.
9. Extract creates/updates candidates only.
10. No source becomes active without approval.
11. Candidate cards show trust, reason codes, provenance, and review history.
12. Approved unsupported source types show poller_supported false as an info state, not an error.
13. Packet cards explain why something is useful now, saved later, ignored, or review-worthy.
14. Low-risk source automation starts as ranking only.
15. Auto approval remains disabled until multiple soak runs prove safety.
16. Soak snapshots stay clean.
17. Tests exist for budget, source gate, packet gate, search smoke, and UI controls.
18. Documentation tells Britton exactly what to run or click next.

# Phase 0: Discovery Budget and Queue Clarity

Goal:
Make Scout explain why search smoke failed and what is happening with queued discovery jobs.

Do this before deeper UI polish.

## Increment 0.1: Discovery budget read model

### Goal

Expose a simple budget status object:

- daily limit
- jobs used today
- jobs remaining today
- queued jobs
- running jobs
- completed jobs
- failed jobs
- next reset estimate
- whether search smoke can create a new job

### Files likely touched

- scout/src/scout/api/discovery_jobs.py
- scout/src/scout/sources/discovery_jobs.py
- scout/src/scout/sources/storage.py
- scout/src/scout/tests/test_discovery_jobs.py
- source_proxy/testing/runner.py, only if runner needs budget display
- src/lib/scout-overview.ts, only if UI consumes it later

### Implementation notes

Add a budget summary to the discovery jobs response or a dedicated endpoint.

Suggested shape:

{
  "budget": {
    "daily_limit": 3,
    "used_today": 3,
    "remaining_today": 0,
    "can_create_job": false,
    "blocked_reason": "daily_limit_reached",
    "next_reset_hint": "next UTC day"
  }
}

Do not change actual budget limits yet.

### Manual checks

```bash
cd ~/SpiritOS

curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '{
  count,
  budget,
  jobs: [.jobs[]? | {
    id: .job_id,
    query,
    topic: .topic_anchor,
    status,
    created_at,
    started_at,
    finished_at,
    error,
    max_results,
    budget
  }]
}'

Then run:

PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-search-smoke
Expected outputs

When daily cap is reached:

budget.daily_limit is visible.
budget.remaining_today is 0.
can_create_job is false.
search smoke does not pretend the provider is broken.
active source count stays unchanged.
approved candidate count stays unchanged.
Debug if failed
Check how discovery_jobs_per_day is loaded from Scout settings.
Check whether job creation uses UTC day boundaries.
Check whether queued jobs count against the daily cap.
Check whether duplicate queued jobs are counted multiple times.
Print job created_at timestamps.
Rollback
Remove budget summary field.
Keep existing discovery job list behavior.
Next step

Implement Increment 0.2 to classify queued jobs.

Permission gate

Ask Britton before patching Increment 0.1.

Increment 0.2: Discovery job state classification
Goal

Make queued jobs easier to understand.

Each job should show:

queued
running
completed
failed
blocked_by_budget
stale_queued
duplicate_queued
spam_test
needs_attention
Files likely touched
scout/src/scout/api/discovery_jobs.py
scout/src/scout/sources/discovery_jobs.py
scout/src/scout/tests/test_discovery_jobs.py
src/lib/scout-overview.ts
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
Implementation notes

Add computed fields. Do not mutate jobs during this increment.

Example:

{
"status": "queued",
"computed_status": "duplicate_queued",
"attention_label": "Duplicate queued search",
"safe_next_action": "cancel_duplicate_or_wait"
}

Rules:

Same query and same topic more than once equals duplicate_queued.
Queued for more than a threshold with no started_at equals stale_queued.
Query with obvious spam terms can be labeled spam_test or noisy_test.
Do not delete anything automatically.
Manual checks
curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '{
  count,
  jobs: [.jobs[]? | {
    id: .job_id,
    query,
    topic: .topic_anchor,
    status,
    computed_status,
    attention_label,
    safe_next_action,
    created_at,
    started_at,
    finished_at
  }]
}'
Expected outputs

Your current queue should show:

Pydantic duplicate jobs labeled as duplicate_queued.
The spam query labeled as noisy_test or needs_attention.
Old jobs with no started_at labeled as stale_queued if they cross the threshold.
No candidates created.
No sources changed.
Debug if failed
Confirm API response includes computed fields.
Confirm timestamps parse as timezone-aware datetimes.
Confirm query normalization lowercases and trims strings.
Confirm duplicate detection groups by query and topic.
Rollback
Remove computed fields.
Keep original job statuses.
Next step

Implement Increment 0.3 for safe job controls.

Permission gate

Ask Britton before patching Increment 0.2.

Increment 0.3: Safe discovery job controls
Goal

Add human-approved job controls:

pause job
resume job
cancel stale job
cancel duplicate job

No automatic cleanup yet.

Files likely touched
scout/src/scout/api/discovery_jobs.py
scout/src/scout/sources/discovery_jobs.py
scout/src/scout/tests/test_discovery_jobs.py
src/app/api/scout/discovery-jobs/[jobId]/pause/route.ts
src/app/api/scout/discovery-jobs/[jobId]/resume/route.ts
possible new cancel route
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
Implementation notes

The action response should be normalized:

{
"ok": true,
"action": "cancel",
"job_id": "...",
"previous_status": "queued",
"new_status": "canceled",
"message": "Discovery job canceled.",
"mutated_sources": false,
"mutated_candidates": false
}

Hard rule:

Canceling a job must not delete review history, source candidates, active sources, or packets.

Manual checks

Pick one duplicate queued Pydantic job only.

curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '.jobs[] | {id:.job_id, query, status, computed_status}'

Then cancel one duplicate only through the UI or API.

After:

curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '.jobs[] | {id:.job_id, query, status, computed_status}'
curl -s "http://localhost:8077/v1/scout/sources" | jq '.count'
curl -s "http://localhost:8077/v1/scout/source-candidates" | jq '.counts'
Expected outputs
One selected duplicate job becomes canceled.
Other jobs remain untouched.
Source count stays 5.
Approved candidate count stays 2.
No packet promotion happens.
Review history remains visible.
Debug if failed
Check route path.
Check job ID lookup.
Check DB update transaction.
Check frontend proxy route.
Check that canceled jobs are not picked up by scheduler.
Rollback
Revert new job-control endpoint.
Restore DB backup if a job state was changed incorrectly.
Next step

Implement Increment 0.4 to make search smoke budget-aware.

Permission gate

Ask Britton before patching Increment 0.3.

Increment 0.4: Budget-aware scout-search-smoke
Goal

Make scout-search-smoke return clearer states:

PASS
FAIL
SKIP
BLOCKED_BY_BUDGET

It should not call this a real failure when the only issue is daily budget exhaustion.

Files likely touched
source_proxy/testing/runner.py
source_proxy/tests/test_runner or relevant runner tests
docs/proxy-test-runner-plan.md
scout/docs/V0_3_PHASE4F_CLOSEOUT_EVIDENCE.md, if docs need updating
Implementation notes

Current behavior:

create discovery job fails 422
result is FAIL
recommendation says fix needed

New behavior:

create discovery job fails 422 daily limit reached
result is BLOCKED_BY_BUDGET or SKIP
safety invariants still printed
recommendation says wait for reset, cancel stale duplicate jobs, or temporarily raise budget for bounded smoke
Manual checks
cd ~/SpiritOS
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-search-smoke
Expected outputs

When budget is exhausted:

Result: BLOCKED_BY_BUDGET or SKIP
blocked_reason: daily_limit_reached
source count delta: 0
approved count delta: 0
preview not run
extract not run
recommendation is specific

When budget is available:

Search smoke creates one bounded job.
Preview does not create candidates.
Extract creates/updates candidates only.
Sources do not change.
Approved count does not increase.
Debug if failed
Check exact API error body for 422.
Match on stable reason code, not only text.
Ensure runner still returns FAIL for real provider errors.
Ensure active source mutation checks still run.
Rollback
Revert runner result classification.
Keep old FAIL behavior.
Next step

Move to Phase 1 runner/report polish.

Permission gate

Ask Britton before patching Increment 0.4.

Phase 1: Runner and Diagnostic Report Polish

Goal:
Make runner outputs easy to understand without asking ChatGPT what they mean.

Increment 1.1: Standard Scout runner result language
Goal

Normalize runner states across Scout profiles.

Allowed result states:

PASS
FAIL
SKIP
BLOCKED_BY_BUDGET
BLOCKED_BY_CONFIG
PROVIDER_UNAVAILABLE
NEEDS_HUMAN_REVIEW
Files likely touched
source_proxy/testing/runner.py
source_proxy/testing/self_tests.py, only if shared formatting is needed
source_proxy/tests/test_coding_self_tests.py
scout/docs or docs/proxy-test-runner-plan.md
Implementation notes

Do not change behavior first. Change the language and structure.

Every report should include:

profile
result
mutation boundary
checks
invariants
findings
recommendation
next command
Manual checks
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-smoke
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-source-gate
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-search-diagnostics
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-search-smoke
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-soak-snapshot
Expected outputs
All profiles use the same report structure.
Read-only profiles say mutated false.
Soak snapshot says wrote_snapshot true.
Search smoke explains budget state clearly.
Debug if failed
Check profile-specific report builders.
Check inconsistent field names.
Check text output and JSON output if both exist.
Rollback
Revert report formatting changes only.
Next step

Implement runner JSON output for dashboard controls.

Permission gate

Ask Britton before patching Increment 1.1.

Increment 1.2: Add JSON output mode for Scout runner
Goal

Make runner outputs easier for the dashboard to display.

Files likely touched
source_proxy/testing/runner.py
source_proxy/api/coding_self_tests.py or runner API route
src/components/dashboard/HomelabTestRunnerWidget.tsx
tests for runner API
Implementation notes

Add:

PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-smoke --format json

JSON should include:

profile
result
checks
counts
invariants
mutation_boundary
recommendation
next_steps
Manual checks
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-smoke --format json | jq .
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-search-smoke --format json | jq .
Expected outputs
Valid JSON.
No stack traces mixed into JSON.
Dashboard can parse it.
Human-readable text mode still works.
Debug if failed
Validate JSON with jq.
Keep logs on stderr, not stdout.
Confirm all profile result objects are serializable.
Rollback
Remove JSON flag.
Keep text runner unchanged.
Next step

Connect dashboard diagnostics cards to JSON runner output.

Permission gate

Ask Britton before patching Increment 1.2.

Increment 1.3: Dashboard diagnostic controls
Goal

Add clear buttons:

Run Scout Smoke
Run Source Gate Check
Run Search Diagnostics
Run Search Smoke
Write Soak Snapshot
Files likely touched
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/components/dashboard/HomelabTestRunnerWidget.tsx
src/hooks/useScoutOverview.ts
src/app/v1/coding/self-tests/run/route.ts or relevant runner proxy route
dashboard tests
Implementation notes

Search Smoke must require confirmation because it can create a discovery job and candidates.

Soak Snapshot must say it writes one JSON file.

Read-only checks should be labeled read-only.

Manual checks

In dashboard:

Click Run Scout Smoke.
Confirm result appears without terminal.
Click Run Source Gate Check.
Click Run Search Diagnostics.
Do not click Search Smoke until budget state is visible.
Click Soak Snapshot and confirm one new file is created.

CLI verification:

ls -lt scout/soak-logs | head
Expected outputs
Read-only controls do not mutate.
Search Smoke shows confirmation.
Soak Snapshot shows wrote_snapshot true.
UI shows PASS, FAIL, or BLOCKED_BY_BUDGET clearly.
Debug if failed
Check Next API route.
Check runner API response shape.
Check CORS/proxy origin.
Check frontend state refresh after completion.
Rollback
Hide new buttons.
Keep CLI runner intact.
Next step

Move to Phase 2 dashboard structure.

Permission gate

Ask Britton before patching Increment 1.3.

Phase 2: Dashboard Information Architecture

Goal:
Make Scout feel obvious instead of crowded.

Increment 2.1: Split the Scout widget into clear lanes
Goal

Replace the crowded tab feeling with clear sections:

Overview
Source Gate
Packet Gate
Discovery
Sources
Diagnostics
Files likely touched
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/lib/scout-overview.ts
src/hooks/useScoutOverview.ts
CSS or dashboard style files
dashboard tests
Implementation notes

Do not remove functionality. Reorganize it.

Recommended layout:

Top status cards:

Scout online/offline
Packets checked
Source candidates
Active sources
Discovery jobs
Budget remaining
Next job/run

Primary actions:

Source Gate: approve/reject/block candidates
Packet Gate: recheck/queue/promote packets
Discovery: inspect jobs and budget
Diagnostics: run smoke/search/soak checks
Manual checks

Open dashboard and verify:

Source Gate exists.
Packet Gate exists.
Discovery exists.
Sources exists.
Diagnostics exists.
Counts match CLI output.

CLI comparison:

curl -s "http://localhost:8077/v1/scout/source-candidates?limit=50" | jq '.counts'
curl -s "http://localhost:8077/v1/scout/sources" | jq '.count'
curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '.count'
Expected outputs
UI count cards match API.
User can tell the difference between packet actions and source actions.
No source approval happens from merely opening the widget.
Debug if failed
Check data mapping in src/lib/scout-overview.ts.
Check stale hook cache.
Check API proxy.
Check responsive layout overflow.
Rollback
Restore previous tab layout.
Keep backend unchanged.
Next step

Rename confusing buttons.

Permission gate

Ask Britton before patching Increment 2.1.

Increment 2.2: Rename Queue and Recheck buttons
Goal

Make every button say what system it affects.

Files likely touched
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
dashboard tests
Implementation notes

Change labels:

Queue becomes Queue Packet
Recheck becomes Recheck Packet
Approve becomes Approve Source
Reject becomes Reject Source
Block becomes Block Source
Search Preview becomes Preview Search
Extract becomes Extract Candidates

Add helper text:

Queue Packet does not approve a source.
Recheck Packet does not change active sources.
Approve Source activates a source.
Extract Candidates does not activate sources.
Manual checks

In dashboard:

Find a packet.
Confirm buttons say Queue Packet and Recheck Packet.
Find a source candidate.
Confirm buttons say Approve Source, Reject Source, Block Source.
Hover or read helper text.
Expected outputs
No ambiguous Queue button remains.
No ambiguous Recheck button remains.
Source actions are visually separate from packet actions.
Debug if failed
Search for old label strings.
Check mobile layout truncation.
Check tests for text changes.
Rollback
Revert label text only.
Next step

Add action impact previews.

Permission gate

Ask Britton before patching Increment 2.2.

Increment 2.3: Action impact previews
Goal

Before a user clicks an action, show what it will and will not change.

Files likely touched
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/lib/scout-overview.ts
dashboard tests
Implementation notes

Examples:

Approve Source:

Will add source to active registry.
May show poller_supported false.
Will not create packets immediately.
Will not touch /coding.

Queue Packet:

Will add packet to promotion queue.
Will not approve a source.
Will not change active source count.

Recheck Packet:

Will rerun checks for this packet.
Will not change source registry.
Manual checks

Click or hover action preview for:

Approve Source
Reject Source
Block Source
Queue Packet
Recheck Packet
Expected outputs
Each action has clear impact text.
Destructive or state-changing actions require confirmation.
Read-only actions do not require scary confirmation.
Debug if failed
Check modal state.
Check action type mapping.
Check UI overflow on phone.
Rollback
Remove preview modal.
Keep renamed buttons.
Next step

Improve Source Gate cards.

Permission gate

Ask Britton before patching Increment 2.3.

Phase 3: Source Gate Trust Review

Goal:
Make source approvals feel safe and explainable.

Increment 3.1: Candidate trust cards
Goal

Each source candidate card should show:

URI
source kind
status
confidence score
trust label
recommendation
reason codes
discovered_from
poller support prediction
safe next action
Files likely touched
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/lib/scout-overview.ts
scout/src/scout/api/source_trust.py
source candidate API tests
dashboard tests
Implementation notes

Reason codes should be humanized.

Example:

canonical_uri_valid:
"The URL has a clean canonical shape."

official_docs_pattern:
"This looks like official documentation."

discovered_from_search_result:
"Scout found this from a bounded search job."

Manual checks
curl -s "http://localhost:8077/v1/scout/source-candidates?limit=20" | jq '.candidates[] | {
  uri:.canonical_uri,
  status,
  score:.confidence_score,
  trust:.trust_label,
  recommendation,
  reasons:.reason_codes
}'

Then compare UI cards to CLI.

Expected outputs
Recommended candidates explain why they are recommended.
Needs-review candidates explain what is missing.
Blocked/rejected candidates show review state.
No active source changes.
Debug if failed
Check reason_codes_json parsing.
Check missing explanation fallback.
Check UI for undefined fields.
Rollback
Hide enhanced details.
Keep API unchanged.
Next step

Add review history timeline.

Permission gate

Ask Britton before patching Increment 3.1.

Increment 3.2: Review history timeline
Goal

Show who approved, rejected, or blocked a candidate, when, and why.

Files likely touched
scout/src/scout/api/source_trust.py
scout/src/scout/sources/storage.py
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
source API tests
dashboard tests
Implementation notes

Each candidate should show:

previous status
new status
reviewed_by
created_at
reason
metadata
source_id if approval created a source
Manual checks
curl -s "http://localhost:8077/v1/scout/source-candidates?limit=50" | jq '.candidates[] | select((.review_history // []) | length > 0) | {
  uri:.canonical_uri,
  status,
  review_history
}'
Expected outputs
Approved Python source shows approve event.
Blocked malformed Python URL shows block reason.
Rejected item shows reject reason.
UI timeline matches API.
Debug if failed
Check review_history is included for all statuses.
Check approve response includes review event or source metadata.
Check old candidates with no history handle empty state.
Rollback
Hide timeline.
Keep stored review history.
Next step

Normalize action responses.

Permission gate

Ask Britton before patching Increment 3.2.

Increment 3.3: Normalize approve, reject, block responses
Goal

Make all source actions return the same response shape.

Files likely touched
scout/src/scout/api/source_trust.py
scout/src/scout/sources/storage.py
scout/src/scout/tests/test_sources_api.py
src/app/api/scout/source-candidates/[candidateId]/approve/route.ts
src/app/api/scout/source-candidates/[candidateId]/reject/route.ts
src/app/api/scout/source-candidates/[candidateId]/block/route.ts
dashboard tests
Implementation notes

Response shape:

{
"ok": true,
"action": "approve",
"candidate": {},
"source": {},
"review_event": {},
"message": "Source candidate approved.",
"poller_supported": false,
"warnings": []
}

Unsupported source type should not look scary.

Message:

"Approved, but this source type is not pollable yet. It is stored as an active registry source but will not be scheduled."

Manual checks

Use one disposable candidate only after Britton approves the test.

curl -s -X POST "http://localhost:8077/v1/scout/source-candidates/<ID>/reject" \
  -H "Content-Type: application/json" \
  -d '{"reason":"manual test"}' | jq .
Expected outputs
ok true.
action visible.
candidate/source/review_event shape consistent.
source count changes only on approve.
reject/block do not activate source.
Debug if failed
Check route response model.
Check old frontend assumptions.
Check candidate refresh after action.
Rollback
Revert response normalization.
Keep existing backend action behavior.
Next step

Add source health and poller support labels.

Permission gate

Ask Britton before patching Increment 3.3.

Increment 3.4: Source health and poller support labels
Goal

Make active sources easier to understand.

Each active source should show:

active
static config or approved registry
poller_supported true/false
last checked
last packet created
last error
health label
Files likely touched
scout/src/scout/api/sources.py
scout/src/scout/storage/source_tracking.py
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
source API tests
Implementation notes

Do not treat poller_supported false as failure.

Labels:

Polling: Scout can regularly check this.
Stored only: Source is approved, but no poller exists yet.
Needs attention: source has repeated errors.
Static source: loaded from config.
Approved source: approved from Source Gate.
Manual checks
curl -s "http://localhost:8077/v1/scout/sources" | jq '{
  count,
  sources: [.sources[] | {
    uri:.canonical_uri,
    origin:.source_origin,
    poller:.poller_supported,
    status,
    health:.health_label
  }]
}'
Expected outputs
GitHub and RSS static sources show poller true.
Approved web pages show poller false with helpful label.
Source count remains 5 unless user manually approves a source.
Debug if failed
Check static config source merge.
Check registry source merge.
Check poller support mapping.
Rollback
Hide health labels.
Keep API unchanged.
Next step

Move to Discovery pipeline hardening.

Permission gate

Ask Britton before patching Increment 3.4.

Phase 4: Discovery and Search Pipeline Hardening

Goal:
Make search useful without making it reckless.

Increment 4.1: Execute or advance queued jobs safely
Goal

Figure out why queued jobs have never started and add a safe way to advance them.

Files likely touched
scout/src/scout/sources/discovery_jobs.py
scout/src/scout/api/discovery_jobs.py
scout/src/scout/tests/test_discovery_jobs.py
source_proxy/testing/runner.py
dashboard discovery controls
Implementation notes

Before patching, diagnose:

Is the scheduler supposed to run queued jobs?
Is there an endpoint to advance a job?
Are jobs intentionally inert until search-preview/extract is called?
Does queued mean "saved plan" or "waiting worker"?

Do not create a broad scheduler until this is clear.

Manual checks
curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '.jobs[] | {
  id:.job_id,
  status,
  created_at,
  started_at,
  finished_at,
  error
}'

docker logs --since 2h scout_v0_1 | grep -i "discovery\|job\|search" | tail -n 80
Expected outputs
Clear explanation of why jobs are queued.
No source activation.
No hidden job execution.
Debug if failed
Check scheduler startup.
Check discovery_jobs_enabled.
Check job status transitions.
Check logs around job creation.
Rollback
Documentation-only if diagnosis finds no code needed.
Revert any scheduler change.
Next step

Add preview/extract controls.

Permission gate

Ask Britton before patching Increment 4.1.

Increment 4.2: Search preview and extract controls
Goal

Let Britton run search preview and extract candidates from the dashboard safely.

Files likely touched
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/app/api/scout/discovery-jobs/[jobId]/search-preview/route.ts
src/app/api/scout/discovery-jobs/[jobId]/extract-candidates/route.ts
scout/src/scout/api/discovery_jobs.py
tests
Implementation notes

Preview:

read provider results
no candidate creation
no source activation

Extract:

create/update candidates only
no source activation
no approval

Both require budget visibility.

Manual checks

Use one selected job.

curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '.jobs[] | {id:.job_id, query, status}'

# Run preview through UI or API.
# Then compare counts.

curl -s "http://localhost:8077/v1/scout/source-candidates" | jq '.counts'
curl -s "http://localhost:8077/v1/scout/sources" | jq '.count'
Expected outputs

After preview:

candidate counts unchanged.
source count unchanged.
results visible.

After extract:

candidate counts may increase.
source count unchanged.
approved count unchanged.
new candidates show search provenance.
Debug if failed
Check job ID.
Check SearXNG connectivity.
Check candidate upsert logic.
Check source count before/after.
Rollback
Hide preview/extract UI.
Keep backend endpoints if safe.
Next step

Strengthen dedupe and provenance checks.

Permission gate

Ask Britton before patching Increment 4.2.

Increment 4.3: Canonical dedupe and provenance hardening
Goal

Prevent duplicate candidate spam.

Files likely touched
scout/src/scout/sources/search_candidates.py
scout/src/scout/sources/discovery.py
scout/src/scout/sources/storage.py
scout/src/scout/tests/test_canonicalization.py
scout/src/scout/tests/test_search_candidate_extraction.py
Implementation notes

Rules:

Same canonical URI equals one candidate.
Preserve multiple discovery events.
Strip tracking params.
Normalize GitHub repo URIs.
Preserve original display URI.
Keep blocked sources blocked.
Manual checks

Run search extract twice on the same job.

curl -s "http://localhost:8077/v1/scout/source-candidates?limit=200" | jq '.counts'
Expected outputs
Candidate count does not double after repeated extraction.
Existing candidates update last_seen_at.
Discovery history records repeated finding.
Blocked/rejected sources do not reappear as recommended.
Debug if failed
Print canonical URI before upsert.
Check unique DB constraint.
Check blocked source lookup.
Check reason code merge.
Rollback
Revert canonicalization changes.
Restore DB backup if duplicate explosion occurs.
Next step

Add spam/noise safety tests.

Permission gate

Ask Britton before patching Increment 4.3.

Increment 4.4: Spam and noisy query guardrails
Goal

Make Scout treat spammy or low-trust searches as test/noise, not useful intelligence.

Files likely touched
scout/src/scout/sources/scoring.py
scout/src/scout/tests/test_source_scoring.py
scout/src/scout/tests/test_search_candidate_extraction.py
Implementation notes

The existing queued job:

"fastapi free download coupon crack tutorial mirror spam"

should be labeled as noisy_test, spam_risk, or low_trust.

Do not auto-block everything from one query. Score cautiously.

Manual checks

Run scoring tests and inspect candidate output.

scout/.venv/bin/python -m pytest scout/src/scout/tests/test_source_scoring.py scout/src/scout/tests/test_search_candidate_extraction.py
Expected outputs
Official FastAPI docs rank high.
Spam-like results rank low or needs_review.
No spam source becomes active.
Reason codes explain spam risk.
Debug if failed
Check spam pattern list.
Check allowlist override.
Check official docs pattern.
Check borderline candidate scoring.
Rollback
Disable new spam reason code.
Keep existing scoring behavior.
Next step

Move to Packet Gate intelligence polish.

Permission gate

Ask Britton before patching Increment 4.4.

Phase 5: Packet Gate Intelligence Polish

Goal:
Make Scout explain what it knows and why it matters.

Increment 5.1: "Why useful?" packet explanations
Goal

Each packet should answer:

What is this?
Why is Scout showing it?
Why useful now?
Why saved later?
Why ignored?
What source did it come from?
What action is recommended?
Files likely touched
scout/src/scout/api/overview.py
scout/src/scout/api/packets.py
scout/src/scout/packets/schema.py
src/lib/scout-overview.ts
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
packet tests
Implementation notes

Add human fields:

usefulness_label
usefulness_reason
recommended_action
confidence_label
source_trust_label
Manual checks
curl -s "http://localhost:8077/v1/scout/overview?limit=10" | jq '.packets[]? | {
  id:(.packet_id // .id),
  title,
  status:(.human_status_label // .effective_status // .status),
  usefulness_label,
  usefulness_reason,
  recommended_action
}'
Expected outputs
Useful Now packets explain why.
Saved Later packets explain why they are not urgent.
Review items explain what needs review.
No source or candidate mutation.
Debug if failed
Check packet schema fields.
Check old packets with missing data.
Check overview mapping.
Check fallback labels.
Rollback
Hide usefulness fields.
Keep packet status unchanged.
Next step

Clarify recheck behavior.

Permission gate

Ask Britton before patching Increment 5.1.

Increment 5.2: Recheck packet evidence
Goal

After pressing Recheck Packet, show what changed.

Files likely touched
scout/src/scout/api/packets.py
scout/src/scout/debugger/runner.py
src/app/api/scout/packets/[packetId]/recheck/route.ts
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
tests
Implementation notes

Recheck result should show:

previous status
new status
checks run
errors
source count delta
candidate count delta
promotion state delta

Expected rule:

Recheck packet should not change active source count.

Manual checks

Pick one harmless packet.

Before:

curl -s "http://localhost:8077/v1/scout/sources" | jq '.count'
curl -s "http://localhost:8077/v1/scout/source-candidates" | jq '.counts'

Click Recheck Packet.

After:

curl -s "http://localhost:8077/v1/scout/sources" | jq '.count'
curl -s "http://localhost:8077/v1/scout/source-candidates" | jq '.counts'
Expected outputs
Packet check result visible.
Source count unchanged.
Candidate counts unchanged unless recheck explicitly discovers candidate links from already extracted artifact, which should be documented.
UI shows success or failure.
Debug if failed
Check packet ID route.
Check debugger runner output.
Check state refresh.
Check source/candidate count deltas.
Rollback
Disable recheck UI.
Keep backend route.
Next step

Clarify packet promotion queue.

Permission gate

Ask Britton before patching Increment 5.2.

Increment 5.3: Packet promotion queue clarity
Goal

Make Queue Packet and Promote Packet obvious.

Files likely touched
scout/src/scout/api/promotions.py
scout/src/scout/packets/promotions.py
src/app/api/scout/packets/[packetId]/queue-promotion/route.ts
src/app/api/scout/promotions/finalize/route.ts
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
tests
Implementation notes

Promotion states:

not_queued
queued
promoted
rejected
stale

UI should show:

queued by
queued at
promoted by
promoted at
promotion reason
Manual checks

Pick one harmless packet.

curl -s "http://localhost:8077/v1/scout/promotions" | jq .

Click Queue Packet.

curl -s "http://localhost:8077/v1/scout/promotions" | jq .
Expected outputs
Packet enters queue.
Source count unchanged.
Candidate count unchanged.
Promotion queue updates.
Debug if failed
Check promotion API route.
Check packet ID mapping.
Check UI refresh.
Check duplicate queue handling.
Rollback
Disable queue button.
Keep promotion records.
Next step

Document memory bridge as inactive until explicitly enabled.

Permission gate

Ask Britton before patching Increment 5.3.

Increment 5.4: Semantic memory bridge safety label
Goal

Make "Semantic memory inactive" understandable.

Files likely touched
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/lib/scout-overview.ts
source_proxy/proxy_memory/scout_intake.py, only for read-only status
tests
Implementation notes

Display:

Semantic memory: Inactive

Meaning:

"Scout is storing packets and source decisions, but it is not writing into proxy memory or coding context automatically."

Add future state labels:

inactive
read_only_context
manual_import_only
approved_memory_write
Manual checks

Open widget and confirm semantic memory state text is clear.

CLI:

curl -s "http://localhost:8077/v1/scout/overview?limit=5" | jq '.semantic_memory // .memory // empty'
Expected outputs
User knows inactive is safe.
No proxy memory write occurs.
No /coding integration appears.
Debug if failed
Check overview response.
Check fallback display when field missing.
Check source_proxy scout intake stays inactive.
Rollback
Hide semantic memory card.
Next step

Move to controlled autonomy ladder.

Permission gate

Ask Britton before patching Increment 5.4.

Phase 6: Controlled Autonomy Ladder

Goal:
Let Scout become smarter without making it reckless.

Increment 6.1: Auto-rank only
Goal

Scout automatically ranks candidates, but takes no action.

Files likely touched
scout/src/scout/sources/scoring.py
scout/src/scout/api/source_trust.py
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
tests
Implementation notes

Add labels:

Low-risk recommended
Good but needs review
Weak evidence
Noisy
Block candidate suggested

No automatic approve/reject/block.

Manual checks
curl -s "http://localhost:8077/v1/scout/source-candidates?limit=50" | jq '.candidates[] | {
  uri:.canonical_uri,
  status,
  score:.confidence_score,
  recommendation,
  automation_tier,
  suggested_action
}'
Expected outputs
Official sources rank high.
Spam/noisy candidates rank low.
suggested_action appears.
No state changes happen.
Debug if failed
Check scoring thresholds.
Check official domain patterns.
Check low-evidence candidates.
Check blocked/rejected override.
Rollback
Hide automation_tier.
Keep old score fields.
Next step

Add one-click review bundles.

Permission gate

Ask Britton before patching Increment 6.1.

Increment 6.2: One-click review bundles
Goal

Let Scout group low-risk recommendations for faster human review.

Files likely touched
scout/src/scout/api/source_trust.py
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
tests
Implementation notes

Create groups:

Official GitHub repos
Official docs
Release notes
Known ecosystem blogs
Needs review
Block suggested

Bundle action should still require human confirmation.

No bulk auto-approve yet.

Manual checks

Open Source Gate.

Confirm groups exist.

Click a group preview.

Do not approve all yet.

Expected outputs
Group counts visible.
Each candidate remains individually inspectable.
No source changes from opening a group.
Debug if failed
Check grouping logic.
Check candidate status filters.
Check UI performance with many candidates.
Rollback
Disable grouped view.
Return to flat list.
Next step

Add manual batch approval with clear confirmation.

Permission gate

Ask Britton before patching Increment 6.2.

Increment 6.3: Manual batch approval with strict confirmation
Goal

Allow Britton to approve multiple selected low-risk sources at once.

Files likely touched
scout/src/scout/api/source_trust.py
src/app/api/scout/source-candidates/batch-approve/route.ts
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
tests
Implementation notes

Hard rules:

User must select candidates.
UI must show exact URIs.
UI must show poller support.
UI must show source count before and after estimate.
No blocked/rejected candidates can be batch approved.
Batch approval writes review history for each candidate.
Manual checks

Select 2 safe candidates only after approval.

Before:

curl -s "http://localhost:8077/v1/scout/sources" | jq '.count'
curl -s "http://localhost:8077/v1/scout/source-candidates" | jq '.counts'

Batch approve selected candidates.

After:

curl -s "http://localhost:8077/v1/scout/sources" | jq '.count'
curl -s "http://localhost:8077/v1/scout/source-candidates" | jq '.counts'
Expected outputs
Source count increases exactly by selected approved sources that are not already active.
Approved count increases.
Review history created.
Blocked/rejected candidates untouched.
Debug if failed
Check duplicate active source handling.
Check transaction behavior.
Check partial failure reporting.
Check review history write.
Rollback
Disable batch approval.
Manually pause or disable mistakenly approved sources if needed.
Restore Scout DB backup if state is badly wrong.
Next step

Do not implement auto-approve yet. Run soak first.

Permission gate

Ask Britton before patching Increment 6.3.

Increment 6.4: Auto-approval dry-run only
Goal

Prepare future auto-approval without actually approving anything.

Files likely touched
scout/src/scout/sources/scoring.py
scout/src/scout/api/source_trust.py
source_proxy/testing/runner.py
tests
Implementation notes

Add a dry-run report:

"These candidates would be eligible for auto-approval under current rules."

Rules for eligibility:

official allowlisted domain or known official GitHub org
score >= 0.95
metadata sufficient
not blocked
not rejected
not duplicate active
not unsupported unless explicitly allowed
within daily auto-approval cap
dry_run only
Manual checks
curl -s "http://localhost:8077/v1/scout/source-candidates?limit=50" | jq '.candidates[] | select(.auto_approval_dry_run == true) | {
  uri:.canonical_uri,
  score:.confidence_score,
  reasons:.reason_codes
}'
Expected outputs
Dry-run eligible list appears.
No candidate status changes.
No source count changes.
No review history action is written as approval.
Debug if failed
Check score threshold.
Check allowlist.
Check duplicate active filter.
Check blocked/rejected filters.
Rollback
Hide dry-run field.
Keep manual approval flow.
Next step

Run a long soak before any real auto-approve mode.

Permission gate

Ask Britton before patching Increment 6.4.

Phase 7: Soak, Regression, and Closeout

Goal:
Prove Scout is stable before trusting it more.

Increment 7.1: Scout focused regression pack
Goal

Run backend tests for source registry, source gate, discovery jobs, search extraction, provider, and soak safety.

Files likely touched
Tests only unless failures reveal bugs.
Manual checks
cd ~/SpiritOS

scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_source_registry.py \
  scout/src/scout/tests/test_sources_api.py \
  scout/src/scout/tests/test_discovery_jobs.py \
  scout/src/scout/tests/test_search_candidate_extraction.py \
  scout/src/scout/tests/test_search_provider.py \
  scout/src/scout/tests/test_v03_soak_safety.py
Expected outputs
All focused tests pass.
Any skipped tests are explained.
No DB mutation outside test DB.
Debug if failed
Fix one failing test group at a time.
Do not patch unrelated UI while backend tests fail.
Check test DB isolation.
Rollback
Revert failing patch.
Restore last known green state.
Next step

Run dashboard tests.

Permission gate

Ask Britton before patching fixes from this increment.

Increment 7.2: Dashboard Scout UI tests
Goal

Prevent UI regressions.

Files likely touched
src/components/dashboard/tests/HomelabScoutIntelligenceWidget.test.tsx
src/lib/scout-overview.ts tests
src/hooks/useScoutOverview.ts tests
Manual checks
cd ~/SpiritOS

npx vitest run src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
npm run typecheck
npx eslint src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/lib/scout-overview.ts src/hooks/useScoutOverview.ts
Expected outputs
Widget tests pass.
Typecheck passes.
ESLint passes or known warnings are documented.
UI still loads on dashboard.
Debug if failed
Fix type errors first.
Fix broken mock API data.
Fix text assertions after label rename.
Check mobile layout after logic passes.
Rollback
Revert UI patch.
Keep backend improvements.
Next step

Run soak snapshots over time.

Permission gate

Ask Britton before patching fixes from this increment.

Increment 7.3: 24 to 72 hour soak routine
Goal

Prove boring stability.

Files likely touched
scout/docs/V0_3_PHASE10_LONG_RUNNING_SOAK.md
docs or dashboard closeout docs
no code unless soak finds bugs
Manual checks

Start baseline:

cd ~/SpiritOS
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-soak-snapshot

Then run every few hours:

PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-smoke
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-source-gate
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-soak-snapshot
Expected outputs
No uncontrolled source activation.
No runaway DB growth.
No repeated log errors.
Rejected and blocked decisions stay durable.
Candidate counts remain bounded.
Discovery jobs are explainable.
Search smoke only runs when budget allows.
Debug if failed
Compare latest soak snapshot to baseline.
Check docker logs.
Check DB size growth.
Check discovery job creation rate.
Check source count before and after.
Rollback
Disable discovery jobs.
Disable search.
Restore Scout DB backup.
Fall back to static sources only.
Next step

Write Scout v0.4 closeout evidence.

Permission gate

Ask Britton before patching any soak-related bug.

Increment 7.4: Scout v0.4 closeout document
Goal

Create a closeout doc proving what Scout can and cannot do.

Files likely touched
scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md
docs/proxy-test-runner-plan.md
README.md only if needed
Implementation notes

Closeout doc should include:

final commands
final dashboard controls
source gate behavior
packet gate behavior
discovery budget behavior
search smoke behavior
soak snapshot evidence
safety boundaries
known limitations
next recommended phase
Manual checks

Open doc and verify it answers:

What does Scout do?
What should Britton click?
What is safe?
What is not built yet?
How do we know it is stable?
Expected outputs
Closeout doc exists.
It matches actual runner commands.
It does not claim auto-approval is active.
It lists remaining limitations honestly.
Debug if failed
Compare doc to current command output.
Remove claims not backed by tests.
Update screenshots or examples if stale.
Rollback
Delete closeout doc draft.
Keep code unchanged.
Next step

Move to either Scout-to-Proxy context bridge or Cartographer/Blueprinter integration, depending on current project priority.

Permission gate

Ask Britton before writing the closeout document.

Recommended implementation order

Do not build all of this at once.

Recommended order:

Phase 0.1: Discovery budget read model.
Phase 0.2: Discovery job state classification.
Phase 0.4: Budget-aware scout-search-smoke.
Phase 2.1: Split dashboard into clear lanes.
Phase 2.2: Rename Queue/Recheck buttons.
Phase 3.1: Candidate trust cards.
Phase 3.2: Review history timeline.
Phase 4.1: Diagnose queued job execution.
Phase 4.2: Search preview/extract controls.
Phase 5.1: Why useful packet explanations.
Phase 6.1: Auto-rank only.
Phase 7.3: 24 to 72 hour soak routine.

Do not start real auto-approval until after:

Source Gate is clear.
Discovery budget is clear.
Search smoke handles budget correctly.
Review history is visible.
Soak snapshots stay clean.
Batch approval has been manually tested.
Auto-approval dry-run has proven safe.
First patch recommendation

Start with:

Phase 0.1: Discovery budget read model

Reason:

The latest failure is not a search provider failure. It is a budget/queue clarity failure.

The first patch should make Scout say:

"Search smoke is blocked because the daily discovery job limit has been reached. Active sources were not changed. Candidates were not changed. Next safe step: inspect queued jobs, cancel stale duplicates, or wait for budget reset."

First patch should not:

approve sources
reject sources
block sources
create new discovery jobs
extract candidates
change search budgets
touch /coding
write proxy memory
commit
push
Prompt to Codex for first increment

Work in ARPA mode:
Analyze repo/resources first.
Research the existing Scout discovery job API, storage, runner output, and tests.
Plan the change.
Ask permission before patching.
Do not commit.
Do not push.
Do not approve, apply, or execute any workflow.

Task:
Implement Scout Polish Master Plan v0.4, Phase 0.1 only.

Increment:
Phase 0.1: Discovery budget read model.

Goal:
Expose a clear discovery budget summary so Scout can explain when scout-search-smoke is blocked by the daily discovery job limit.

Current evidence:
scout-search-smoke failed with:
create discovery job: FAIL (422): discovery job daily limit reached

But safety invariants stayed good:
source count delta 0
approved count unchanged
preview did not create candidates
extract did not change sources
no auto approval

Current discovery jobs:
5 queued jobs
several duplicate Pydantic jobs
one spam/noisy test job
one FastAPI release job
all have started_at null
all have finished_at null

Required behavior:
Add a budget summary to the discovery jobs response or an equivalent read-only endpoint.

Minimum budget fields:
daily_limit
used_today
remaining_today
can_create_job
blocked_reason
next_reset_hint

Do not change budget values.
Do not create jobs.
Do not cancel jobs.
Do not approve/reject/block candidates.
Do not activate sources.
Do not touch /coding or proxy memory.

Files to inspect:
scout/src/scout/api/discovery_jobs.py
scout/src/scout/sources/discovery_jobs.py
scout/src/scout/sources/storage.py
scout/src/scout/config.py
scout/src/scout/tests/test_discovery_jobs.py
source_proxy/testing/runner.py
docs/proxy-test-runner-plan.md

Files likely touched:
scout/src/scout/api/discovery_jobs.py
scout/src/scout/sources/discovery_jobs.py
scout/src/scout/tests/test_discovery_jobs.py
source_proxy/testing/runner.py only if needed for display
docs/proxy-test-runner-plan.md only if needed

Manual checks after patch:
cd ~/SpiritOS

curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '{
count,
budget,
jobs: [.jobs[]? | {
id: .job_id,
query,
topic: .topic_anchor,
status,
created_at,
started_at,
finished_at,
error,
max_results,
budget
}]
}'

PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-search-smoke

Expected output:
budget.daily_limit is visible.
budget.used_today is visible.
budget.remaining_today is visible.
budget.can_create_job is false when cap is exhausted.
budget.blocked_reason is daily_limit_reached when cap is exhausted.
scout-search-smoke reports BLOCKED_BY_BUDGET or a clearer budget-blocked state instead of vague FAIL if you touch the runner.
Source count stays unchanged.
Approved candidate count stays unchanged.
No active sources are mutated.
No candidates are created by budget inspection.

Debug if failed:
Check settings.discovery_jobs_per_day.
Check UTC date filtering.
Check whether queued jobs count toward the daily cap.
Check exact 422 error body from create job.
Check discovery job timestamps.
Check API serialization.

Rollback:
Revert files touched in this increment.
Do not delete existing Scout DB.
Do not mutate existing jobs.

Before patching, return:

Current diagnosis from repo inspection.
Exact files you propose to touch.
Exact implementation plan.
Manual checks.
Expected outputs.
Risks.
Rollback.
Ask: "Do you want me to implement Phase 0.1 now?"

# Scout v0.4.1: Live State Reconciliation and Packet Synthesis Route Blocker

Status date: 2026-05-19

Goal:
Correct the Scout plan against the latest live soak evidence before deeper polish. Scout core is stable, but packet synthesis is not fully proven while model-backed synthesis cannot reach Ollama.

## Current live state summary

Live diagnostics on 2026-05-19 show:

- `/health` returns HTTP 200 with `{"status":"observing","version":"v0.1"}`.
- `scout_v0_1` is up and Docker reports it as healthy.
- Scout is still in observing mode.
- Source count is stable at 5 active sources.
- Candidate counts are bounded: `needs_review: 2`, `approved: 2`, `recommended: 12`, `rejected: 1`, `blocked: 1`, `stored: 0`.
- Discovery has 5 queued jobs, 0 running jobs, 0 completed jobs, and 0 failed jobs.
- Discovery execution is `manual_controlled`.
- `automatic_execution` is false.
- `worker_registered` is false.
- Queued discovery jobs are saved controlled plans, not an active background worker.

Passing test evidence from the latest Scout evidence set:

- focused soak/discovery checks passed: 23 passed
- full Scout suite passed: 159 passed, 3 skipped

## Live API counts

Sources:

- total active sources: 5
- static config GitHub/RSS sources remain active
- manually approved web page sources remain active
- no source activation should happen without manual approval

Source candidates:

- `needs_review`: 2
- `approved`: 2
- `recommended`: 12
- `rejected`: 1
- `blocked`: 1
- `stored`: 0

Discovery queue:

- queued jobs: 5
- running jobs: 0
- completed jobs: 0
- failed jobs: 0
- max results per queued job: 5
- budget per queued job: 5
- daily limit visible in API response

## Safety boundaries

Continue to enforce these boundaries:

- Do not auto-activate sources.
- Do not auto-approve, auto-reject, or auto-block source candidates.
- Do not write to proxy memory.
- Do not write to coding context.
- Do not treat queued discovery jobs as active background work.
- Do not call Scout fully autonomous.
- Do not claim a clean long soak while repeated model errors remain in logs.

## Blocker: packet synthesis model route

Recent live logs repeatedly show:

```text
packet_synthesis_model_failed
litellm.APIConnectionError: OllamaException - [Errno 111] Connection refused
```

Current route evidence:

- Scout is attached to Docker network `scout_default`.
- `spirit-ollama` is not attached to `scout_default` in the observed Docker inspect output.
- `docker port spirit-ollama` reports no published port.
- Host `localhost:11434/api/tags` responds with local Ollama models.
- The requested in-container probe using `wget` could not validate Scout-to-Ollama routing because `wget` is not installed in `scout_v0_1`.
- The repeated Scout log error still proves the live packet synthesis model call is failing with connection refused.

Packet synthesis is not fully proven. This blocks deeper polish until the model route is fixed or intentionally downgraded.

## Decision

Scout is stable observer/polish-ready in the deterministic shell:

- health is good
- container health is good
- deterministic source, candidate, and discovery gates are explainable
- discovery jobs are saved controlled plans, not an active background worker
- source candidate states persist and remain bounded

Scout is not fully v1 autonomous, and the model-backed packet synthesis path is not soak-clean.

Do not proceed to deeper polish until one of these is true:

- Scout-to-Ollama route is repaired and packet synthesis completes without repeated `packet_synthesis_model_failed` logs.
- Product scope explicitly downgrades packet synthesis to deterministic/no-model behavior for this release and documents that decision.

## Next increment

Name:
Scout v0.4.1 live-state reconciliation and Ollama route fix plan.

Goal:
Diagnose and repair Scout-to-Ollama networking/model routing so packet synthesis can be validated by soak evidence.

Allowed first step:
Read-only route diagnosis only.

Likely diagnosis areas:

- Scout container model base URL configuration
- Docker network membership for Scout and Ollama
- whether Ollama should be reached through a published host port or shared Docker network DNS
- whether the live Ollama service is the same service Scout is configured to call
- whether the Scout image has a useful in-container HTTP probe tool

Do not implement a route fix without a separate permission gate.

## Manual checks

Run read-only checks before any route change:

```bash
cd ~/SpiritOS

curl -s -i http://localhost:8077/health | sed -n '1,40p'
curl -s http://localhost:8077/v1/scout/sources | jq '{count}'
curl -s "http://localhost:8077/v1/scout/source-candidates?limit=200" | jq '{counts}'
curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '{count,budget,execution}'

docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Networks}}' | grep -E 'scout|ollama|searxng|spirit' || true
docker inspect scout_v0_1 --format '{{json .NetworkSettings.Networks}}' 2>/dev/null | jq . || true
docker inspect spirit-ollama --format '{{json .NetworkSettings.Networks}}' 2>/dev/null | jq . || true
docker port spirit-ollama 2>/dev/null || true

curl -sS --max-time 5 http://localhost:11434/api/tags | jq . 2>/dev/null || true
docker logs --tail=300 scout_v0_1 2>&1 | grep -E 'packet_synthesis_model_failed|ollama|11434|model' || true
```

If probing from inside the Scout container, first confirm the available probe tools:

```bash
docker exec scout_v0_1 sh -lc 'command -v curl || command -v wget || command -v python || true'
```

Then use the available tool to check:

- `http://host.docker.internal:11434/api/tags`
- `http://spirit-ollama:11434/api/tags`
- `http://localhost:11434/api/tags` from inside Scout

## Expected outputs

Stable deterministic Scout shell:

- `/health` stays HTTP 200.
- source count remains 5 unless manually approved changes happen.
- source candidate counts remain bounded.
- discovery execution remains manual-controlled.
- `automatic_execution` remains false.
- `worker_registered` remains false.
- queued jobs remain explainable saved search plans.

Packet route fixed:

- Scout can reach the configured Ollama endpoint from inside the Scout runtime.
- packet synthesis no longer logs repeated `packet_synthesis_model_failed`.
- packet synthesis creates expected packet/verdict artifacts during the manual packet check.

## Rollback and no-op notes

This increment starts as docs and diagnostics only. There is nothing to roll back if only read-only checks are run.

Before any Docker, compose, network, service, code, commit, push, cleanup, or promotion action, stop and ask for explicit permission.
