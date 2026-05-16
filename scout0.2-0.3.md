Scout v0.2 and v0.3 Master Plan
1. Executive Summary

Scout v0.2 should not become a full autonomous web research agent yet. It should become a Source Registry + Candidate Queue system.

In simple terms:

v0.1 = Scout watches sources you manually configured.
v0.2 = Scout can notice possible new sources from approved sources, score them, and queue them for your approval.
v0.3 = Scout can perform controlled web/search discovery to find new source candidates, still behind strict review gates.

The key rule:

Scout can discover sources.
Scout can score sources.
Scout can recommend sources.
Scout cannot activate new sources without you.

That keeps Scout intelligent without letting it become messy, expensive, or dangerous.

2. Current Repo Reality Check

Your current Scout already has the right foundation. The repo contains Scout API modules for overview, packets, promotions, source trust, and human-readable labels; pollers for GitHub and RSS; extractors; debugger tiers; packet storage/synthesis; migrations; and tests. It also has dashboard and Next API surfaces under src/app/api/scout, useScoutOverview, scout-overview.ts, and HomelabScoutIntelligenceWidget.

Current source config is static:

scout/config/sources.yaml
  github_repos:
    anthropics/anthropic-sdk-python
    fastapi/fastapi
  rss_feeds:
    https://blog.python.org/feeds/posts/default
  web_pages: []

The current topic anchors are also static and coding-focused: Python, FastAPI, TypeScript, local LLMs, agents, SQLite, Docker, security, embeddings, and developer tools.

So v0.2 should extend these parts:

source_trust.py
storage/migrations.py
pollers/
extractors/
overview.py
promotions.py
packets.py
HomelabScoutIntelligenceWidget
src/app/api/scout/

It should not create a whole parallel Scout system.

3. Architecture Inspiration From Open Source

Huginn is useful because it models sources as agents that create and consume events through a directed graph. Scout should borrow the idea of scheduled watchers producing structured events, but not copy Huginn’s Rails stack.

OpenCTI is useful because it separates source reliability from information confidence. Scout needs that distinction: a source can be reliable, but a particular claim or packet can still be weak.

MISP is useful because of taxonomies, warninglists, and the Admiralty Scale idea for ranking source reliability and information credibility. Scout should borrow the taxonomy/warninglist style, not the whole threat-intel platform.

GPT Researcher is useful for source gathering and citation workflow patterns, but Scout should not become a fully autonomous report generator yet.

LangChain Open Deep Research is useful for later v0.3 style configurable research workflows across model providers, search tools, and MCP servers. Scout should borrow the idea of configurable discovery jobs, not automatic trust.

Node-RED is useful as visual pipeline inspiration. It is a flow-based, low-code system for collecting, transforming, and visualizing data. Scout can borrow the visual “source → candidate → score → review” mental model, without moving its core logic into Node-RED.

4. Final Architecture Target

Scout should have two gates:

Source Gate
Should Scout be allowed to watch this source?

Packet Gate
Should this specific packet be promoted after Scout watched the source?

Today you already have most of the Packet Gate.

v0.2 builds the Source Gate.

v0.3 makes source discovery stronger.

5. Source Lifecycle

Use this lifecycle:

Active
Approved by you. Scout can poll it.

Recommended
Scout thinks it is high-trust and relevant, but it still needs your approval.

Needs Review
Possibly useful, but not enough confidence.

Stored Candidate
Low priority. Kept for record, not shown aggressively.

Rejected
You rejected it.

Blocked
Known bad, spammy, unsafe, impersonating, or explicitly blocked.

No source becomes Active automatically.

6. Scout v0.2 Scope

Scout v0.2 should deliver:

Source Registry
Source Candidate table/model
Candidate discovery from approved extracted artifacts only
Canonical URI dedupe
Rule-based trust scorer
Manual approve/reject/block source workflow
Minimal Source Management dashboard section
APIs for source candidates
No web search yet
No coding integration
No proxy memory writes

v0.2 is not “Scout searches the internet.”
v0.2 is “Scout learns how to manage and review sources safely.”

7. Scout v0.2 Data Model

Add these tables through scout/src/scout/storage/migrations.py.

source_registry

Stores active approved sources.

Fields:

source_id
canonical_uri
display_uri
source_kind: github_repo | rss_feed | docs_page | blog | changelog | release_feed | unknown
trust_label
trust_tier
status: active | paused | disabled
poll_interval_minutes
approved_at
approved_by
created_at
updated_at
metadata_json

Indexes:

unique(canonical_uri)
index(status)
index(source_kind)
source_candidates

Stores discovered source candidates.

candidate_id
canonical_uri
display_uri
source_kind
status: recommended | needs_review | stored | rejected | blocked | approved
confidence_score
trust_label
trust_tier
recommendation
discovered_from_uri
discovered_from_event_id
discovered_from_packet_id
reason_codes_json
explanation
first_seen_at
last_seen_at
reviewed_at
reviewed_by
rejection_reason
blocked_reason
metadata_json

Indexes:

unique(canonical_uri)
index(status)
index(confidence_score)
index(discovered_from_uri)
source_discovery_events

Audit trail.

event_id
candidate_id
discovery_kind
source_uri
artifact_path
raw_url
canonical_uri
created_at
metadata_json
blocked_sources

Hard blocks.

canonical_uri
reason
blocked_at
blocked_by
metadata_json
8. Scout v0.2 API Plan

Keep APIs under Scout, not Source Proxy.

GET /v1/scout/sources

Extend existing sources endpoint to include active registry sources and current static config sources.

GET /v1/scout/source-candidates

Query params:

status=recommended | needs_review | stored | rejected | blocked | approved
limit=50

Response:

{
  "counts": {
    "recommended": 2,
    "needs_review": 4,
    "stored": 10,
    "rejected": 1,
    "blocked": 3
  },
  "candidates": []
}
POST /v1/scout/source-candidates/{candidate_id}/approve

Approves candidate and adds it to source_registry.

POST /v1/scout/source-candidates/{candidate_id}/reject

Rejects candidate with reason.

POST /v1/scout/source-candidates/{candidate_id}/block

Blocks candidate and prevents requeue.

POST /v1/scout/source-discovery/run-debug

Manual one-shot discovery from existing approved artifacts only. No web search.

9. Scout v0.2 Phases
v0.2 Phase 0: Repo Audit and Blueprint Alignment

Goal
Confirm exact current Scout structures before code.

Files likely touched
Docs only:

_blueprints/scout-v0.2-source-registry-plan.md

Small increments

Document current static source flow.
Document new source lifecycle.
Document migration names and API shape.
Confirm no Source Proxy changes.

Manual tests

grep -R "source_trust\|promotion\|source_tracking\|sources.yaml" scout/src scout/config -n

Expected outcome
A repo-specific v0.2 blueprint.

Debug if failed
If files differ from assumptions, adjust the plan before implementation.

Rollback
Delete docs file.

Next step
Permission to start schema.

v0.2 Phase 1: Source Registry Schema

Goal
Add database support for approved sources and candidate sources.

Files likely touched

scout/src/scout/storage/migrations.py
scout/src/scout/storage/db.py
scout/src/scout/tests/test_migrations.py

Small increments

Add source_registry.
Add source_candidates.
Add source_discovery_events.
Add blocked_sources.
Add indexes and uniqueness constraints.
Add tests that migrations are idempotent.

Manual tests

cd ~/SpiritOS
python -m pytest scout/src/scout/tests/test_migrations.py
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
docker exec -i scout_v0_1 python - <<'PY'
from scout.config import get_settings
from scout.storage.db import open_connection
settings = get_settings()
conn = open_connection(settings.database_path)
for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(row[0])
PY

Expected outcome
New tables exist, old tables are untouched.

Debug if failed

Check migration version order.
Check SQLite syntax.
Check table name collisions.
Check Docker image rebuild.

Rollback

Restore DB backup.
Revert migration file.

Next step
Permission to add models/storage helpers.

v0.2 Phase 2: Source Candidate Models and Storage Helpers

Goal
Add typed helpers for source registry and candidates.

Files likely touched

scout/src/scout/sources/
scout/src/scout/sources/models.py
scout/src/scout/sources/storage.py
scout/src/scout/api/source_trust.py
scout/src/scout/tests/test_source_candidates.py

If you do not want a new folder, use:

scout/src/scout/storage/source_registry.py

But I would allow scout/src/scout/sources/ for source-specific logic, while still extending existing source_trust.py.

Small increments

Define SourceCandidate.
Define SourceRegistryEntry.
Add canonical_uri.
Add upsert_candidate.
Add list_candidates.
Add approve_candidate.
Add reject_candidate.
Add block_candidate.

Manual tests

python -m pytest scout/src/scout/tests/test_source_candidates.py

Expected outcome
Candidates can be inserted, deduped, listed, approved, rejected, and blocked.

Debug if failed

Print canonical URI.
Check duplicate constraint.
Check timestamp handling.
Check JSON serialization of reason codes.

Rollback

Revert new files and tests.
Keep migration only if unused, or roll DB backup.

Next step
Permission to add candidate API.

v0.2 Phase 3: Candidate API

Goal
Expose source candidate workflow.

Files likely touched

scout/src/scout/api/sources.py
scout/src/scout/main.py
scout/src/scout/api/overview.py
scout/src/scout/tests/test_sources_api.py
src/app/api/scout/source-candidates/route.ts
src/app/api/scout/source-candidates/[candidateId]/approve/route.ts
src/app/api/scout/source-candidates/[candidateId]/reject/route.ts
src/app/api/scout/source-candidates/[candidateId]/block/route.ts

Small increments

Add GET /v1/scout/source-candidates.
Add approve/reject/block endpoints.
Mount router in main.py.
Add Next API proxies.
Keep all actions Scout-only.

Manual tests

curl -s http://localhost:8077/v1/scout/source-candidates | jq .
curl -s -X POST http://localhost:8077/v1/scout/source-candidates/<ID>/reject \
  -H "Content-Type: application/json" \
  -d '{"reason":"Not relevant"}' | jq .

Expected outcome
Candidate queue is visible and reviewable.

Debug if failed

Check router prefix.
Check Docker rebuild.
Check main.py includes router.
Check Next proxy URL.

Rollback

Remove router include and Next routes.

Next step
Permission to add discovery.

v0.2 Phase 4: Discovery From Approved Artifacts Only

Goal
Scout can discover candidate links from artifacts it already extracted from approved sources.

Files likely touched

scout/src/scout/sources/discovery.py
scout/src/scout/extractors/
scout/src/scout/packets/orchestrator.py
scout/src/scout/storage/jsonl.py
scout/src/scout/tests/test_source_discovery.py

Discovery mechanics

Read extracted markdown artifacts.
Extract URLs with strict parser.
Ignore mailto, javascript, fragments, social share URLs, tracking URLs, anchors, image URLs unless explicitly allowed.
Normalize canonical URI.
Check against approved registry and blocked list.
Upsert candidate.
Store discovery event.

Important
Do not fetch discovered URLs yet.

Small increments

Build URL extractor.
Build canonicalizer.
Build deny patterns.
Add artifact scanner.
Add manual debug runner.
Add tests with good, duplicate, noisy, and blocked URLs.

Manual tests

python -m pytest scout/src/scout/tests/test_source_discovery.py

curl -s -X POST http://localhost:8077/v1/scout/source-discovery/run-debug \
  -H "Content-Type: application/json" \
  -d '{"limit":10}' | jq .

curl -s http://localhost:8077/v1/scout/source-candidates | jq .

Expected outcome
Candidates appear from existing approved artifacts, but none become active.

Debug if failed

Print artifact paths scanned.
Print raw URLs found.
Print canonical URI output.
Check denylist filtering.
Check candidate upsert.

Rollback

Disable debug runner.
Keep tables.

Next step
Permission to add scoring.

v0.2 Phase 5: Deterministic Trust Scoring

Goal
Score candidates using explainable non-LLM rules.

Files likely touched

scout/src/scout/api/source_trust.py
scout/src/scout/sources/scoring.py
scout/src/scout/tests/test_source_trust.py

Tier 1 deterministic checks

HTTPS
canonical URI valid
duplicate
approved source
blocked source
obvious spam pattern
tracking-heavy URL
GitHub repo format
known official domain pattern

Tier 2 structural checks

discovered from approved source
topic anchor match
official docs/repo/blog/changelog hint
source metadata quality
freshness if known
content type if known without fetching
safe domain shape

Score bands

0.90 to 1.00 = recommended
0.70 to 0.89 = needs_review
0.50 to 0.69 = stored
below 0.50 = ignored
hard safety issue = blocked

Small increments

Add score_candidate.
Add reason codes.
Add confidence band mapping.
Add tests for official GitHub, official docs, random blog, spammy URL, duplicate, blocked.

Manual tests

python -m pytest scout/src/scout/tests/test_source_trust.py
curl -s http://localhost:8077/v1/scout/source-candidates?status=recommended | jq .

Expected outcome
Every candidate has score, trust label, recommendation, and reasons.

Debug if failed

Inspect reason codes.
Check canonical domain extraction.
Check topic anchor matching.

Rollback

Set all candidate scores to needs_review until scorer fixed.

Next step
Permission to add dashboard.

v0.2 Phase 6: Minimal Dashboard Source Management

Goal
Add source candidate review to the current Scout dashboard surface without bloating it.

Files likely touched

src/components/dashboard/HomelabScoutIntelligenceWidget.tsx
src/lib/scout-overview.ts
src/hooks/useScoutOverview.ts
src/app/api/scout/source-candidates/*
src/components/dashboard/__tests__/

Small increments

Add a Source Queue or Sources sub-tab.
Show Active, Recommended, Needs Review, Rejected, Blocked.
Show confidence score and reason codes.
Add approve/reject/block buttons.
Add calm empty states.
Refresh after action.

Manual tests

npx eslint src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/lib/scout-overview.ts
npx vitest run src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
npx tsc --noEmit

Expected outcome
You can review source candidates in the dashboard.

Debug if failed

Check Next proxy routes.
Check API shape.
Check missing optional fields.
Check UI state after action.

Rollback

Hide Source Queue tab.
Keep backend API.

Next step
Permission to activate approved sources.

v0.2 Phase 7: Source Activation Flow

Goal
Approved candidates become active sources.

Files likely touched

scout/src/scout/pollers/registry.py
scout/src/scout/main.py
scout/src/scout/storage/source_tracking.py
scout/src/scout/sources/storage.py
scout/src/scout/tests/test_registry.py

Small increments

Load static YAML sources as bootstrap active sources.
Load DB active sources.
Merge and dedupe.
Register jobs from merged registry.
Keep static sources working.
Pause/disable DB sources if needed.

Manual tests

docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api
docker logs --since 5m scout_v0_1
curl -s http://localhost:8077/v1/scout/sources | jq .

Expected outcome
Approved source appears in Active Sources and gets a scheduled polling job only after approval.

Debug if failed

Check scheduler registered jobs.
Check canonical URI dedupe.
Check source kind mapping to poller.
Check unsupported source type handled safely.

Rollback

Set SCOUT_DB_SOURCE_REGISTRY_ENABLED=false if added.
Fall back to YAML only.

Next step
Permission for soak and audit.

v0.2 Phase 8: Soak Test and Safety Audit

Goal
Prove v0.2 does not spam, bloat DB, or affect coding.

Small increments

Run overnight with only approved static sources.
Run candidate discovery manually.
Approve one safe candidate.
Confirm it polls.
Reject/block noisy candidates.
Confirm /coding untouched.

Manual tests

curl -s http://localhost:8077/v1/scout/overview?limit=5 | jq .
curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
curl -s http://localhost:8077/v1/scout/sources | jq '.sources[] | {source_uri, status, health_label}'
docker logs --since 24h scout_v0_1 | tail -n 200

Expected outcome

No unapproved candidate is polled.
Active sources stay explainable.
Candidate counts stay bounded.
Dashboard works.
Source Proxy behavior unchanged.

Debug if failed

Check discovery limits.
Check duplicate candidate growth.
Check blocked source matching.
Check scheduler.

Rollback

Disable discovery scheduler.
Keep manual review data.
10. Scout v0.2 Manual Test Matrix
Test	Expected
Duplicate candidate	One canonical candidate only
Known official docs candidate	Recommended or Needs Review with reasons
Spammy/tracking candidate	Ignored or Blocked
Candidate discovered from artifact	Stored with discovered_from info
Approve candidate	Moves to Active
Reject candidate	Stays rejected, not active
Block candidate	Cannot be requeued
Unapproved candidate	Not polled
Approved candidate	Gets scheduled only after approval
Dashboard counts	Match API counts
/coding	No behavior change
Proxy memory	No writes
11. Scout v0.3 Scope

Scout v0.3 is where controlled web/search discovery begins.

v0.3 should deliver:

Discovery job planner
Controlled search provider integration
Search result candidate extraction
Canonical URI hardening
Dedupe hardening
Tier 2 structural scoring upgrades
Optional Tier 3 LLM scorer
Budgets and rate limits
Dashboard discovery controls
Audit trail and review history
Long-running soak tests

Still no automatic activation.

Still no /coding integration.

12. Scout v0.3 Phases
v0.3 Phase 0: v0.2 Stabilization Checkpoint

Goal
Do not start search discovery until source registry works.

Manual tests

curl -s http://localhost:8077/v1/scout/source-candidates | jq '.counts'
curl -s http://localhost:8077/v1/scout/sources | jq '.count'

Expected outcome
Source registry, candidate queue, dashboard, and approval flow stable.

v0.3 Phase 1: Discovery Job Planner

Goal
Create search/discovery jobs without executing broad search yet.

Files likely touched

scout/src/scout/sources/discovery_jobs.py
scout/src/scout/storage/migrations.py
scout/src/scout/tests/test_discovery_jobs.py

Data model

discovery_jobs
  job_id
  query
  topic_anchor
  status
  max_results
  budget
  created_at
  started_at
  finished_at
  error

Manual tests

python -m pytest scout/src/scout/tests/test_discovery_jobs.py

Expected outcome
Jobs can be created, paused, resumed, and listed.

v0.3 Phase 2: Controlled Search Provider Integration

Goal
Integrate search in a controlled way.

Your repo already has backend SearXNG config and Next web-search code paths, so search should reuse existing local-search concepts when practical, not invent a totally new provider. The repo includes SearXNG configuration and web-search server/provider files under src/lib/server/web-search/.

Small increments

Add Scout search provider abstraction.
Add local/SearXNG provider first.
Add strict result limit.
Add timeout and failure handling.
Store result candidates only.

Manual tests

curl -s -X POST http://localhost:8077/v1/scout/discovery-jobs \
  -H "Content-Type: application/json" \
  -d '{"query":"official FastAPI release notes","max_results":5}' | jq .

Expected outcome
Search creates candidates, not active sources.

v0.3 Phase 3: Search Result Candidate Extraction

Goal
Turn search results into source candidates.

Small increments

Normalize result URLs.
Remove ads/tracking.
Deduplicate.
Classify source kind.
Score with Tier 1/Tier 2.
Queue.

Expected outcome
Official docs beat random blogs.

v0.3 Phase 4: Canonical URI and Dedupe Hardening

Goal
Stop source bloat.

Rules:

strip utm params
normalize trailing slash
lowercase host
preserve meaningful path
collapse http to https where safe
dedupe GitHub repo URLs
dedupe docs aliases only with explicit rules

Manual tests
Use a list of messy URLs and confirm one candidate.

v0.3 Phase 5: Tier 2 Structural Scoring Upgrades

Goal
Improve source quality without LLM calls.

Signals:

official domain match
GitHub org/repo verification
docs/changelog/release path
linked from approved source
topic anchor density
freshness
known ecosystem match
metadata quality

Expected outcome
More useful ranking, no token burn.

v0.3 Phase 6: Optional Tier 3 LLM Scoring

Goal
Use LLM only for borderline or high-potential candidates.

Rules:

Do not call LLM for blocked candidates.
Do not call LLM for obvious low score.
Do not activate source.
Require reason codes.
Cap batch size.
Cap tokens.

Expected outcome
Better explanations for hard cases.

v0.3 Phase 7: Discovery Budgets, Rate Limits, and Backoff

Goal
Prevent Scout from burning resources.

Controls:

max jobs per day
max candidates per job
max candidates per source
max LLM scorer calls
domain cooldown
failure backoff
global pause

Manual tests
Trigger repeated jobs and verify caps.

v0.3 Phase 8: Dashboard Discovery Controls

Goal
Add UI controls for discovery jobs.

UI:

Run discovery
Pause discovery
Budget remaining
Recent jobs
Candidate counts
Recommended
Needs Review
Blocked

Keep it simple.

v0.3 Phase 9: Audit Trail and Review History

Goal
Make source trust decisions explainable.

Every candidate should show:

where it came from
why it scored that way
who approved/rejected
when it changed state
what job found it
v0.3 Phase 10: Long-Running Soak Test

Goal
Run for 24 to 72 hours with strict budgets.

Expected:

No DB explosion
No runaway logs
No uncontrolled source activation
No /coding influence
Useful candidates appear
Spam gets blocked/ignored
13. Scout v0.3 Manual Test Matrix
Test	Expected
Search official FastAPI docs	Official docs candidate ranks high
Search vague coding topic	Mixed candidates go to Needs Review
Duplicate result URLs	One canonical candidate
Spam result	Ignored or blocked
Rate cap reached	Discovery stops gracefully
Scout search provider down	Job fails soft
Discovery paused	No new jobs run
Approve search candidate	Becomes active only after approval
/coding	Still untouched
Proxy memory	Still untouched
14. Scoring Plan
Tier 1: Deterministic

Reason codes:

canonical_uri_valid
duplicate_candidate
already_active
blocked_source
https_required
github_repo_detected
tracking_url_stripped
spam_pattern_detected
unsafe_scheme
Tier 2: Structural

Reason codes:

linked_from_active_source
matches_topic_anchor
official_docs_pattern
official_repo_pattern
release_notes_pattern
metadata_sufficient
fresh_source
known_ecosystem_match
low_evidence
Tier 3: LLM assisted

Reason codes:

llm_official_source_likely
llm_topic_relevant
llm_low_trust_warning
llm_source_impersonation_risk
llm_needs_human_review

Tier 3 is for explanation and borderline calls, not authority.

15. Safety and Threat Model
Risk	Mitigation
SEO spam	Deterministic spam filters, low trust by default
Source impersonation	Domain/org matching, manual approval
GitHub repo squatting	Known org checks, age/stars optional later, manual approval
Typosquatting	Canonical domain checks, edit-distance warnings
Prompt injection	Existing debugger patterns, never treat source text as instruction
Token burn	LLM only for candidates above threshold
DB bloat	canonical URI dedupe, candidate caps, pruning
Accidental source activation	manual approve only
Candidate content entering coding	no /coding integration in v0.2/v0.3
Proxy memory contamination	no proxy memory writes
Rate-limit hits	backoff, floors, budgets
16. Operational Plan

Budgets:

v0.2:
manual discovery only
max 50 candidates per run
no candidate deep-fetch by default
no LLM scoring unless explicitly run in debug

v0.3:
max search jobs per day
max results per job
max candidates per domain
max LLM scorer calls per day

Logs:

source_discovery_events
candidate review audit
scorer reason codes
job status logs

Pruning:

delete ignored candidates after 30 to 90 days
keep approved/rejected/blocked audit longer
compact duplicate discovery events

Rollback:

disable discovery jobs
disable DB source registry loading
fall back to sources.yaml
restore scout/data backup
17. Integration Boundaries

v0.2 and v0.3 are Scout-only.

They do not:

connect Scout to /coding
feed Scout packets to Architect
write proxy memory
change Approval Gate
change approved execution
change Source Proxy behavior

They prepare the intelligence supply chain.

The Skill Mediator and Architect Context Preview come later.

18. Recommended Next Patch

Do v0.2 Phase 1: Source Registry Schema + Storage Helpers.

But keep it small:

Add tables
Add storage helpers
Add tests
Do not add dashboard yet
Do not add discovery yet
Do not add web search yet

First patch target:

scout/src/scout/storage/migrations.py
scout/src/scout/sources/models.py
scout/src/scout/sources/storage.py
scout/src/scout/tests/test_source_registry.py
scout/src/scout/tests/test_migrations.py

Manual verification:

python -m pytest scout/src/scout/tests/test_migrations.py scout/src/scout/tests/test_source_registry.py

docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate scout-api

docker exec -i scout_v0_1 python - <<'PY'
from scout.config import get_settings
from scout.storage.db import open_connection

settings = get_settings()
conn = open_connection(settings.database_path)
for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(row[0])
PY

Expected:

source_registry exists
source_candidates exists
source_discovery_events exists
blocked_sources exists
old Scout tables still exist
existing Scout tests still pass
19. Done Criteria
v0.2 is done when:
Approved source registry exists
Candidate queue exists
Approved artifacts can emit source candidates
Candidates are deduped
Candidates are scored with reason codes
Recommended / Needs Review / Rejected / Blocked states work
Dashboard can approve/reject/block candidates
Approved candidates can become active sources
Unapproved candidates are never polled
No /coding integration exists
No proxy memory writes exist
v0.3 is done when:
Controlled search jobs exist
Search creates candidates only
Canonical URI dedupe is strong
Budgets and rate limits work
Tier 2 structural scoring is solid
Optional Tier 3 scoring is capped
Dashboard can run/pause discovery
Audit trail explains source decisions
Long-running soak does not bloat DB
No /coding integration exists
No proxy memory writes exist