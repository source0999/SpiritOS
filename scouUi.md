# Scout Command Center MVP Master Plan

Status date: 2026-05-16
Owner: Britton
Scope: One focused UI/read-model PR
Target increment: Increment 5.1 - Scout Command Center MVP
Estimated size: 1 to 2 days max
Backend changes: None
Autonomy changes: None
Safety authority changes: None

## 0. Purpose

Turn the current Scout Intelligence page from a readable report into a real command center.

The goal is not to build more Scout intelligence yet.

The goal is to make the intelligence Scout already has easier to understand, navigate, and act on.

Current pain points:

- "Needs review" cards are not clickable.
- "Findings" makes Scout look inactive even though it processed 38 packets.
- "Source approvals" sounds technical and unclear.
- Repeated blog.python.org cards look like duplicates.
- Search queue sounds like Scout is about to search automatically, but queued jobs are manual saved search plans.
- Watched sources are confusing because there are 5 active sources, but only 3 are pollable.
- The UI does not feel like the glass command center reference yet.
- The page does not clearly show what action is safe to click next.

## 1. Current live evidence

Use the existing data. Do not invent new backend state.

Current known live shape:

- 38 raw events
- 38 extracted artifacts
- 38 packets
- 38 verdicts
- 1 promoted briefing
- 0 packet review items
- 5 active sources total
- 3 pollable sources
- 2 stored-only approved sources
- 18 source candidates
- 5 discovery jobs queued
- 0 budget left
- source candidates group cleanly by canonical root:
  - blog.python.org: 8
  - github://pydantic: 4
  - pydantic.dev: 1
  - www.python.org: 5

Important interpretation:

- "1 finding" means 1 promoted briefing, not 1 thing Scout has ever processed.
- "38 packets" means Scout processed intelligence from watched sources.
- "3 watching now" means pollable active sources.
- "2 stored only" means approved sources that are not pollable yet.
- "5 manual search plans" means saved search jobs waiting for user-driven preview/extract.
- Search jobs do not run automatically in the current UI model.

## 2. Hard scope boundaries

This MVP may touch:

- src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
- src/components/dashboard/ScoutIntelligenceCenter.tsx
- src/lib/scout-human-readable.ts
- src/lib/scout-overview.ts
- src/hooks/useScoutOverview.ts
- src/styles/dashboard-demo-v4.css, only if needed for the glass layout
- src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
- possibly src/app/intelligence/page.tsx, only if shell/layout wiring needs a tiny adjustment

This MVP may read from:

- /api/scout/overview
- /api/scout/source-candidates?limit=200
- /api/scout/sources
- /api/scout/discovery-jobs?limit=50
- /api/scout/promotions
- /v1/scout/packets if already exposed through existing client/server path

This MVP must not touch:

- scout/src/scout/api/*
- scout/src/scout/sources/*
- scout/src/scout/packets/*
- scout/src/scout/storage/*
- source_proxy/*
- approval/apply/commit/push logic
- Scout DB migrations
- Docker env wiring
- discovery job execution behavior
- source activation behavior
- memory writes
- auto-approval logic

Allowed behavior:

- Read data.
- Re-label data.
- Group candidates.
- Add clickable navigation.
- Add simple CSS bars.
- Add icons.
- Add clearer empty states.
- Add safer helper text.
- Add tests.

Forbidden behavior:

- No source approval changes.
- No auto approval.
- No batch approval changes.
- No source activation.
- No source rejection or blocking changes.
- No search job creation changes.
- No job cleanup controls yet.
- No memory writes.
- No coding context writes.
- No apply, commit, or push.

## 3. Design direction

Use the provided glass dashboard reference as inspiration, not a pixel-perfect target.

Desired feel:

- floating glass command center
- dark translucent panels
- clear icon-first sections
- metric cards that are clickable
- compact visual bars where numbers need comparison
- grouped cards instead of repeated flat rows
- calm technical language
- obvious next actions
- no unreadable low-contrast text
- no giant wall of repeated cards

Do not chase perfect visual polish before functional clarity.

Primary mental model:

1. What needs my attention?
2. What has Scout processed?
3. What is Scout allowed to watch?
4. What is waiting for a manual search step?
5. What is safe, blocked, or inactive?

## 4. Rename map

Use these labels in the UI:

Current label:
- Briefing

New label:
- Today’s Scout Summary

Current label:
- Needs review

New label:
- Review Inbox

Current label:
- Findings

New label:
- Promoted Briefings and Processed Packets

Current label:
- Source approvals

New label:
- Sources to Approve

Current label:
- Search queue

New label:
- Manual Search Plans

Current label:
- Watched sources

New label:
- Watching Now and Stored Sources

Current label:
- Health checks

New label:
- Safety and Diagnostics

Current label:
- Useful finds

New label:
- Promoted Briefings

Current label:
- Source suggestions

New label:
- Source Suggestions

Current label:
- Queued

New label:
- Waiting for manual step

## 5. Page structure

The /intelligence page should become:

1. Hero command header
2. Clickable Action Inbox
3. Scout Pipeline strip
4. Sources to Approve, grouped by canonical root
5. Promoted Briefings and Processed Packets
6. Manual Search Plans
7. Watching Now and Stored Sources
8. Safety and Diagnostics

Do not add a fake multi-scout selector yet.

Future multi-scout can come later after single Scout is excellent.

## 6. Data contract

Use existing routes and shapes.

### Source candidates

Use:

```bash
GET /api/scout/source-candidates?limit=200

or the Scout backend equivalent:

GET /v1/scout/source-candidates?limit=200

Use fields already present:

canonical_uri
display_uri
source_kind
status
confidence_score
trust_label
trust_tier
recommendation
reason_codes
discovered_from_uri
reviewed_by
reviewed_at
review_history
metadata

Group source candidates by canonical root.

Grouping rules:

github://pydantic/pydantic -> github://pydantic
github://pydantic/pydantic-ai -> github://pydantic
https://blog.python.org/... -> blog.python.org
https://www.python.org/... -> www.python.org
https://pydantic.dev/... -> pydantic.dev

Do not flatten all blog.python.org rows as separate top-level cards.

Promotions

Use:

GET /api/scout/promotions

or:

GET /v1/scout/promotions

Use it for:

promoted briefing count
promoted briefing cards
approved promotion details
promotion reason
source label
trust label
entity tags
Packets

Use:

GET /v1/scout/packets

if already available through the current client/server path.

If a frontend proxy route does not exist, do not add it in the first tiny patch unless needed. The first patch can rely on overview counts plus promotions.

Use packet count from overview:

raw_event_index
extracted_artifacts
packets
verdicts
promotion_queue
Sources

Use:

GET /api/scout/sources

or:

GET /v1/scout/sources

Split sources into:

pollable: poller_supported true
stored only: poller_supported false

UI labels:

"3 Watching now"
"2 Stored only"
Discovery jobs

Use:

GET /api/scout/discovery-jobs?limit=50

or:

GET /v1/scout/discovery-jobs?limit=50

Use existing computed fields if present:

computed_status
attention_label
safe_next_action
budget
blocked_reason
status
query
topic_anchor
created_at
updated_at
started_at
finished_at

Do not create, cancel, or run jobs in this MVP.

7. Visual components
Website icons

Use a deterministic local icon map first.

Do not use external favicon fetching yet.

Icon mapping:

github://* -> GitHub icon
blog.python.org -> Python badge or Python icon
www.python.org -> Python badge or Python icon
pydantic.dev -> Pydantic badge or "P" badge
rss_feed -> RSS icon
web_page -> Globe icon
unknown -> Globe icon

If lucide icons are available:

GitHub icon for GitHub
Rss for RSS
Globe for generic web
ShieldCheck for trusted
Clock for queued
AlertTriangle for noisy/stale
Database or Archive for stored-only

If a specific brand icon is not available, use a styled text badge.

Simple CSS graph bars

Do not add Recharts yet.

Use simple CSS bars first.

Graph cards to add:

Pipeline bar:
Raw events: 38
Cleaned artifacts: 38
Packets: 38
Verdicts: 38
Promoted: 1
Source candidate group bars:
blog.python.org
github://pydantic
pydantic.dev
www.python.org
Source status bars:
recommended
needs_review
approved
rejected
blocked
Watching split:
3 pollable
2 stored-only
Discovery budget meter:
daily limit
used
remaining
blocked reason

Only graph numbers where the visual helps Britton understand the system faster.

8. Acceptance criteria

The Scout Command Center MVP is complete when:

The top cards are clickable.
Clicking "Sources to approve" scrolls to grouped source candidates.
Clicking "Promoted Briefings" scrolls to promoted briefing cards.
Clicking "Manual Search Plans" scrolls to search jobs.
Clicking "Watching Now" scrolls to source cards.
"Findings" is no longer the main label.
UI shows "Promoted Briefings: 1" and "Processed Packets: 38."
UI shows "3 Watching now" and "2 Stored only."
Source candidates are grouped by canonical root.
Expanded source groups show exact URL/title/status/reason data.
blog.python.org no longer appears as a confusing repeated wall.
Pydantic GitHub candidates are grouped under github://pydantic.
Manual Search Plans clearly says jobs do not run automatically yet.
Search plan helper text says Preview does not activate sources.
Extraction helper text says Extract Candidates does not approve sources.
Budget left clearly shows 0 and daily_limit_reached when applicable.
Promoted briefing card is still visible.
The 38 processed packet count is visible.
Icons appear for GitHub, Python, Pydantic or generic sites.
Simple CSS bars summarize pipeline, candidate groups, and source split.
No backend files are changed.
No source activation behavior changes.
No memory write behavior changes.
No auto-approval is added.
Existing tests pass or blocked native optional deps are called out plainly.
Phase 5.1A: Read model tightening
Goal

Create the exact frontend read model needed for the command center using existing data only.

Files likely touched
src/lib/scout-human-readable.ts
src/lib/scout-overview.ts
src/hooks/useScoutOverview.ts
src/components/dashboard/tests/HomelabScoutIntelligenceWidget.test.tsx
Implementation notes

Add frontend-only derived fields:

promotedBriefingCount
processedPacketCount
pollableSourceCount
storedOnlySourceCount
sourceCandidateGroups
sourceStatusCounts
discoveryBudgetSummary
pipelineCounts
reviewInboxCount
actionInboxCards

Candidate group shape:

type ScoutSourceCandidateGroup = {
  root: string
  label: string
  iconKind: "github" | "python" | "pydantic" | "rss" | "web"
  total: number
  statuses: Record<string, number>
  highestTrustLabel: string | null
  candidates: ScoutSourceCandidate[]
}

Use /api/scout/source-candidates?limit=200.

Group by canonical root or topic anchor fallback.

Do not mutate any data.

Manual checks

Run:

cd ~/SpiritOS

curl -s "http://localhost:8077/v1/scout/source-candidates?limit=200" | jq '
  [.candidates[] | {
    uri: .canonical_uri,
    status,
    trust: .trust_label,
    kind: .source_kind,
    reasons: .reason_codes,
    review_history
  }] | length
'

curl -s "http://localhost:8077/v1/scout/sources" | jq '{
  total: .count,
  pollable: [.sources[] | select(.poller_supported == true)] | length,
  stored_only: [.sources[] | select(.poller_supported == false)] | length
}'

curl -s "http://localhost:8077/v1/scout/promotions" | jq '.counts'

Then run frontend checks:

npm run typecheck
npx eslint src/lib/scout-human-readable.ts src/lib/scout-overview.ts src/hooks/useScoutOverview.ts
Expected outputs
Candidate count remains 18.
Pollable count remains 3.
Stored-only count remains 2.
Promoted count remains 1.
TypeScript passes.
ESLint passes.
No backend mutation occurs.
Debug if failed
Check optional/null fields in API response.
Check whether source candidates use candidate_id or id.
Check whether source URI is canonical_uri, source_uri, or display_uri.
Check if promotions count lives under counts.approved or derived from approved.length.
Check if overview packet counts are under counts.packets.
Rollback

Revert changes to:

src/lib/scout-human-readable.ts
src/lib/scout-overview.ts
src/hooks/useScoutOverview.ts

No DB rollback needed because this is read-only.

Next step

Move to Phase 5.1B.

Permission gate

Codex must ask before patching.

Phase 5.1B: Command Center shell and clickable Action Inbox
Goal

Make the top of /intelligence feel like a command center and make metric cards navigate to the exact section.

Files likely touched
src/components/dashboard/ScoutIntelligenceCenter.tsx
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/styles/dashboard-demo-v4.css
src/components/dashboard/tests/HomelabScoutIntelligenceWidget.test.tsx
Implementation notes

Create an Action Inbox row:

Sources to Approve
Promoted Briefings
Manual Search Plans
Watching Now
Stored Only
Safety State

Each card should be clickable.

Use anchors:

#sources-to-approve
#promoted-briefings
#manual-search-plans
#watching-now
#safety-diagnostics

Click behavior:

scrollIntoView
highlight/focus section if simple
no route change required
no mutation

Labels:

Sources to Approve: 14 or derived review count
Promoted Briefings: 1
Processed Packets: 38
Manual Search Plans: 5
Watching Now: 3
Stored Only: 2
Manual checks

Open:

https://10.0.0.186:3000/intelligence

Click:

Sources to Approve
Promoted Briefings
Manual Search Plans
Watching Now
Safety State

Run:

npx vitest run src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
npm run typecheck
npx eslint src/components/dashboard/ScoutIntelligenceCenter.tsx src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
Expected outputs
Each top card scrolls to the correct section.
No buttons trigger source approval.
Page remains readable in dark glass theme.
No white unreadable panel regression.
Mobile does not horizontally overflow.
Debug if failed
Check anchor IDs.
Check if id is placed on section wrapper.
Check z-index and scroll container.
Check CSS theme specificity.
Check if the page is inside the correct dashboard shell.
Rollback

Revert layout changes in ScoutIntelligenceCenter.tsx and CSS.

Next step

Move to Phase 5.1C.

Permission gate

Codex must ask before patching.

Phase 5.1C: Source candidate grouping
Goal

Replace the repeated source approval wall with grouped expandable source families.

Files likely touched
src/components/dashboard/ScoutIntelligenceCenter.tsx
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/lib/scout-human-readable.ts
src/lib/scout-overview.ts
src/components/dashboard/tests/HomelabScoutIntelligenceWidget.test.tsx
Implementation notes

Rename section:

"Source approvals" becomes "Sources to Approve"

Group source candidates by canonical root:

blog.python.org
github://pydantic
pydantic.dev
www.python.org

Top group card should show:

icon
group label
total candidates
status counts
trust summary
safe summary
Expand button

Example:

Python Blog
8 source suggestions
1 approved, 6 recommended, 1 rejected
Official project blog

[Expand]

Expanded candidate row should show:

exact title or URL
status
source kind
score/confidence
trust label
recommendation
reason code chips
reviewed_by and reviewed_at if present
latest review event if present

Do not add approve/reject/block changes in this increment unless the existing buttons already work.

Manual checks

Run:

curl -s "http://localhost:8077/v1/scout/source-candidates?limit=200" | jq '
  [.candidates[] | {
    uri: .canonical_uri,
    status,
    trust: .trust_label,
    kind: .source_kind
  }]
  | group_by(
      if .uri | startswith("github://")
      then "github://" + ((.uri | split("/"))[2] // "unknown")
      else ((.uri | sub("^https?://"; "") | split("/"))[0] // "unknown")
      end
    )
  | map({root: .[0].uri, count: length})
'

UI check:

Confirm blog.python.org appears as one group.
Confirm github://pydantic appears as one group.
Confirm pydantic.dev appears as one group.
Confirm www.python.org appears as one group.
Expand each group.
Confirm exact candidate URLs are visible.

Run:

npx vitest run src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
npm run typecheck
Expected outputs
Repeated blog.python.org cards are gone.
Candidate details are still accessible.
Status counts match CLI.
Review history appears when present.
No source count changes.
No candidate status changes.
Debug if failed
Check grouping root parser.
Check GitHub URI split logic.
Check missing canonical_uri fallback.
Check whether candidates are sorted before grouping.
Check null review_history handling.
Rollback

Remove grouped rendering and return to flat candidates list.

Next step

Move to Phase 5.1D.

Permission gate

Codex must ask before patching.

Phase 5.1D: Promoted Briefings and Processed Packets clarity
Goal

Stop making Scout look inactive when it has processed 38 packets.

Files likely touched
src/components/dashboard/ScoutIntelligenceCenter.tsx
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/lib/scout-human-readable.ts
src/lib/scout-overview.ts
tests
Implementation notes

Rename section:

"Findings" becomes "Promoted Briefings and Processed Packets"

Show two separate cards:

Promoted Briefings
count from /api/scout/promotions approved list or counts.approved
currently 1
Processed Intelligence Packets
count from overview counts.packets
currently 38

Optional supporting cards:

Checked verdicts: 38
Waiting for packet review: 0
Promotion queue: 1 if relevant

Helper text:

Scout processed 38 packets, but only 1 has been promoted into your briefing lane. This is normal while promotion is manual.

Promoted briefing card should show:

title
summary
source label
trust label
promotion reason
tags

Use:

GET /api/scout/promotions

Also reference:

GET /v1/scout/packets

only if already available through the current frontend/server path.

Do not add new backend routes.

Manual checks

Run:

curl -s "http://localhost:8077/v1/scout/overview?limit=20" | jq '.counts'

curl -s "http://localhost:8077/v1/scout/promotions" | jq '{
  counts,
  approved: [.approved[]? | {
    summary,
    source_label,
    trust_label,
    human_status_label,
    reason
  }]
}'

UI checks:

Promoted Briefings shows 1.
Processed Intelligence Packets shows 38.
The explanation says why those numbers differ.
The promoted Anthropic item still appears.
Expected outputs
User no longer asks "why only 1 finding?"
Processed packet count is visible.
Promoted briefing count is visible.
No packet promotion happens from viewing the section.
Debug if failed
Check overview count field names.
Check promotions response shape.
Check empty approved array handling.
Check if old "Findings" label still appears in UI.
Rollback

Revert labels and cards only.

Next step

Move to Phase 5.1E.

Permission gate

Codex must ask before patching.

Phase 5.1E: Manual Search Plans clarity
Goal

Make the search queue understandable without changing how search works.

Files likely touched
src/components/dashboard/ScoutIntelligenceCenter.tsx
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/lib/scout-human-readable.ts
tests
Implementation notes

Rename:

"Search queue" becomes "Manual Search Plans"

Use helper text:

These are saved search plans. They do not run automatically yet.
Preview Search shows possible results.
Extract Candidates turns results into source suggestions.
Neither action approves or activates a source.

Show summary cards:

Waiting for manual step: 5
Running: 0
Budget left: 0
Blocked reason: daily_limit_reached

Show job labels:

Duplicate queued search
Stale queued search
Noisy test search
Normal queued search

Do not build cleanup controls in this MVP.

For cleanup controls, keep existing disabled text:

Cleanup controls not built yet

But make it more useful:

Cleanup controls are not built yet. Safe next step: leave queued, preview when budget resets, or plan a later cleanup patch.
Manual checks

Run:

curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '{
  count,
  budget,
  jobs: [.jobs[]? | {
    id: .job_id,
    query,
    topic: .topic_anchor,
    status,
    computed_status,
    attention_label,
    safe_next_action,
    created_at,
    updated_at
  }]
}'

UI checks:

Section title says Manual Search Plans.
It says queued does not mean running.
It says Preview does not activate sources.
It says Extract Candidates does not approve sources.
daily_limit_reached is visible and understandable.
Expected outputs
Search queue no longer feels like a hidden scheduler.
User understands why jobs are sitting there.
No jobs are created.
No jobs are canceled.
No candidates are extracted by viewing the page.
Debug if failed
Check budget field availability.
Check computed_status fallback.
Check if old "Search queue" label still appears.
Check time formatting.
Rollback

Revert section label and helper text changes.

Next step

Move to Phase 5.1F.

Permission gate

Codex must ask before patching.

Phase 5.1F: Watching Now vs Stored Only
Goal

Make active sources understandable.

Files likely touched
src/components/dashboard/ScoutIntelligenceCenter.tsx
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/lib/scout-human-readable.ts
tests
Implementation notes

Split active sources into two groups:

Watching Now
poller_supported true
these can actually be checked by Scout
Stored Only
poller_supported false
approved/active registry entries, but no poller exists yet

Show counts:

3 Watching now
2 Stored only

Do not call stored-only sources "broken."

Use helper text:

Stored only means approved in the registry, but Scout does not have a poller for this source type yet.

Each source card should show:

icon
display label
canonical URI
source kind
origin
poller support
status
last checked if available
useful packet count if available
Manual checks

Run:

curl -s "http://localhost:8077/v1/scout/sources" | jq '{
  total: .count,
  watching_now: [.sources[] | select(.poller_supported == true)] | length,
  stored_only: [.sources[] | select(.poller_supported == false)] | length,
  sources: [.sources[] | {
    uri: (.canonical_uri // .source_uri),
    kind: .source_kind,
    origin: .source_origin,
    poller_supported,
    status
  }]
}'

UI checks:

Anthropic GitHub appears under Watching Now.
FastAPI GitHub appears under Watching Now.
Python blog RSS appears under Watching Now.
Approved web pages appear under Stored Only.
Stored only does not look like an error.
Expected outputs
Source count confusion is gone.
UI matches CLI counts.
No source state changes.
Debug if failed
Check poller_supported boolean handling.
Check if source field is canonical_uri or source_uri.
Check label fallback for source display name.
Check missing health labels.
Rollback

Return to one flat source list.

Next step

Move to Phase 5.1G.

Permission gate

Codex must ask before patching.

Phase 5.1G: Simple graph cards and visual bars
Goal

Use light visual summaries where graphs help understanding.

Files likely touched
src/components/dashboard/ScoutIntelligenceCenter.tsx
src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/styles/dashboard-demo-v4.css
tests if needed
Implementation notes

Do not add Recharts yet.

Create simple CSS bar components:

CommandCenterBar
PipelineFunnelBars
StatusDistributionBars

Graph cards:

Pipeline:
raw events
artifacts
packets
verdicts
promoted briefings
Source candidate groups:
group count bars
Source statuses:
recommended
needs_review
approved
rejected
blocked
Watching split:
pollable vs stored-only
Discovery budget:
used vs remaining

Design rule:

Bars should clarify data.
They should not dominate the page.
They should use existing theme tokens.
They should remain readable in dark and light shell states.
Manual checks

Open /intelligence.

Confirm:

Pipeline visually explains 38 processed vs 1 promoted.
Candidate groups visually show blog.python.org and Python.org are separate families.
Watching split shows 3 vs 2.
Budget shows 0 remaining.

Run:

npm run typecheck
npx eslint src/components/dashboard/ScoutIntelligenceCenter.tsx src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/styles/dashboard-demo-v4.css
Expected outputs
Visual bars render.
No chart library added.
Page remains fast.
No accessibility regression.
Text remains readable.
Debug if failed
Check division by zero in bar width.
Check empty data states.
Check CSS specificity.
Check mobile wrapping.
Rollback

Remove bar components and keep text cards.

Next step

Move to Phase 5.1H.

Permission gate

Codex must ask before patching.

Phase 5.1H: Tests, manual checks, and closeout
Goal

Prove this was only a UI/read-model cleanup and did not change Scout authority.

Files likely touched
src/components/dashboard/tests/HomelabScoutIntelligenceWidget.test.tsx
maybe closeout notes if Codex writes a patch summary only
Manual checks

Backend safety checks:

cd ~/SpiritOS

scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_sources_api.py \
  scout/src/scout/tests/test_discovery_jobs.py \
  scout/src/scout/tests/test_v03_soak_safety.py

Frontend checks:

npx vitest run src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
npm run typecheck
npx eslint \
  src/components/dashboard/HomelabScoutIntelligenceWidget.tsx \
  src/components/dashboard/ScoutIntelligenceCenter.tsx \
  src/lib/scout-human-readable.ts \
  src/lib/scout-overview.ts \
  src/hooks/useScoutOverview.ts

Live runtime checks:

curl -s "http://localhost:8077/v1/scout/sources" | jq '{
  total: .count,
  pollable: [.sources[] | select(.poller_supported == true)] | length,
  stored_only: [.sources[] | select(.poller_supported == false)] | length
}'

curl -s "http://localhost:8077/v1/scout/source-candidates?limit=200" | jq '.counts'

curl -s "http://localhost:8077/v1/scout/promotions" | jq '.counts'

curl -s "http://localhost:8077/v1/scout/discovery-jobs?limit=50" | jq '{count, budget}'

UI checks:

/intelligence loads.
No washed-out white page.
Header matches SpiritOS glass style.
Action Inbox cards are clickable.
Sources to Approve groups candidates by canonical root.
Promoted Briefings shows 1.
Processed Packets shows 38.
Manual Search Plans shows 5.
Watching Now shows 3.
Stored Only shows 2.
Helper text clearly says Preview and Extract do not approve sources.
No auto-approval button appears.
No fake multi-scout dropdown appears.
Expected outputs
Backend tests pass.
Frontend widget tests pass.
Typecheck passes.
ESLint passes.
Source count unchanged.
Candidate status counts unchanged.
Promotion count unchanged.
Discovery job count unchanged.
UI is more understandable.
Debug if failed

If TypeScript fails:

Fix type narrowing in scout-human-readable.ts.
Add safe optional field handling.

If vitest fails:

Update expected labels.
Update mock source candidates to include grouped fields.
Add tests for grouped display.

If UI is unreadable:

Check dashboard atmosphere wrapper.
Check dark text on dark glass.
Check CSS variable fallback.
Check responsive layout.

If counts do not match:

Compare direct backend route vs Next /api/scout/* route.
Check stale cached fetch.
Check no-store behavior.
Check if UI is using old overview only instead of source-candidates limit 200.
Rollback

Revert touched frontend files.

Do not touch Scout DB.

Do not change backend.

Next step

After this MVP, decide whether to do:

Search job cleanup controls.
Source candidate action confirmations.
Scout-to-proxy read-only context bridge.
Longer 24 to 72 hour soak.
Later multi-scout data model.

Do not start multi-scout selector until single-Scout command center is clear.

First Codex prompt

Work in ARPA mode:
Analyze repo/resources first.
Research existing Scout frontend files and current API/proxy routes.
Plan the implementation.
Ask permission before patching.
Do not commit.
Do not push.
Do not approve, apply, activate sources, write memory, or run source-changing Scout actions.

Task:
Implement Scout Command Center MVP, Increment 5.1A only.

Goal:
Tighten the frontend read model for the Scout Intelligence Center using existing API data only.

Important:
This is a frontend/read-model patch only.
Do not change Scout backend.
Do not change Scout DB.
Do not change source activation.
Do not add auto-approval.
Do not add memory writes.
Do not add multi-scout selector yet.

Current live evidence:

38 raw events
38 extracted artifacts
38 packets
38 verdicts
1 promoted briefing
5 active sources total
3 pollable sources
2 stored-only approved sources
18 source candidates
5 discovery jobs queued
0 budget left
daily_limit_reached
source candidates group by:
blog.python.org
github://pydantic
pydantic.dev
www.python.org

Routes to use:

GET /api/scout/overview
GET /api/scout/source-candidates?limit=200
GET /api/scout/sources
GET /api/scout/discovery-jobs?limit=50
GET /api/scout/promotions
GET /v1/scout/packets only if already available through the existing path

Files to inspect:

src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/components/dashboard/ScoutIntelligenceCenter.tsx
src/lib/scout-human-readable.ts
src/lib/scout-overview.ts
src/hooks/useScoutOverview.ts
src/app/api/scout/overview/route.ts
src/app/api/scout/source-candidates/route.ts
src/app/api/scout/sources or existing source proxy route if present
src/app/api/scout/discovery-jobs/route.ts
src/app/api/scout/promotions/route.ts
src/components/dashboard/tests/HomelabScoutIntelligenceWidget.test.tsx

Files likely touched:

src/lib/scout-human-readable.ts
src/lib/scout-overview.ts
src/hooks/useScoutOverview.ts
src/components/dashboard/tests/HomelabScoutIntelligenceWidget.test.tsx

Required read-model fields:

promotedBriefingCount
processedPacketCount
pollableSourceCount
storedOnlySourceCount
sourceCandidateGroups
sourceStatusCounts
discoveryBudgetSummary
pipelineCounts
reviewInboxCount
actionInboxCards

Candidate grouping:
Use /api/scout/source-candidates?limit=200.
Group by canonical root:

github://owner/repo -> github://owner
https://blog.python.org/path -> blog.python.org
https://www.python.org/path -> www.python.org
https://pydantic.dev/path -> pydantic.dev
Fallback to topic_anchor or unknown if URI is missing.

Candidate group shape:
type ScoutSourceCandidateGroup = {
root: string
label: string
iconKind: "github" | "python" | "pydantic" | "rss" | "web"
total: number
statuses: Record<string, number>
highestTrustLabel: string | null
candidates: ScoutSourceCandidate[]
}

Manual checks after patch:
cd ~/SpiritOS

curl -s "http://localhost:8077/v1/scout/source-candidates?limit=200" | jq '.counts'
curl -s "http://localhost:8077/v1/scout/sources" | jq '{
total: .count,
pollable: [.sources[] | select(.poller_supported == true)] | length,
stored_only: [.sources[] | select(.poller_supported == false)] | length
}'
curl -s "http://localhost:8077/v1/scout/promotions" | jq '.counts'
curl -s "http://localhost:8077/v1/scout/overview?limit=20" | jq '.counts'

npm run typecheck
npx eslint src/lib/scout-human-readable.ts src/lib/scout-overview.ts src/hooks/useScoutOverview.ts
npx vitest run src/components/dashboard/tests/HomelabScoutIntelligenceWidget.test.tsx

Expected outputs:

Candidate count remains unchanged.
Source count remains unchanged.
Promoted briefing count remains 1.
Processed packet count reads from overview counts.packets.
Pollable source count is 3.
Stored-only source count is 2.
Source candidates are grouped by canonical root in the read model.
Typecheck passes.
ESLint passes.
Widget tests pass or fail only for expected label/mock updates, which should be fixed in this increment.
No backend files changed.
No source/candidate/job state changes.

Debug if failed:

Check whether source candidate field is candidate_id or id.
Check whether URI field is canonical_uri, display_uri, or source_uri.
Check whether source field is canonical_uri or source_uri.
Check whether promotion count is counts.approved or approved.length.
Check whether overview count is counts.packets.
Check missing optional fields and null review_history.

Rollback:
Revert the touched frontend read-model/test files.
Do not touch Scout DB.
Do not change backend.

Before patching, return:

Current diagnosis from repo inspection.
Exact files you propose to touch.
Exact implementation plan.
Manual checks.
Expected outputs.
Risks.
Rollback.
Ask: "Do you want me to implement Increment 5.1A now?"