# Scout v0.4 Polish Closeout

Date: 2026-05-16

Scout v0.4 turns Scout from a working backend feed into a clearer intelligence control center with explicit gates, visible safety boundaries, and regression evidence.

## What Scout Does Now

Scout now separates work into three human-readable gates:

- Source Gate: review candidate sources before activation.
- Packet Gate: inspect, recheck, queue, and promote individual intelligence packets.
- Discovery Gate: inspect search jobs, budget state, stale jobs, duplicate jobs, noisy jobs, and safe next actions.

Scout can:

- show discovery budget usage and daily limit state
- classify queued discovery jobs as duplicate, stale, noisy, blocked by budget, or normal queued
- preview search results without creating candidates
- extract candidates without activating sources
- rank source candidates for review
- group candidates into review bundles
- manually approve selected low-risk sources after strict confirmation
- report auto-approval dry-run eligibility without approving anything
- explain packet usefulness and recommended action
- show promotion queue metadata
- show semantic memory safety state
- write timestamped soak snapshots

Scout still must not:

- auto-approve sources
- auto-reject or auto-block sources
- activate a source without human approval
- write to proxy memory automatically
- write to coding context automatically
- apply, commit, push, or execute code changes

## Final Commands

Focused Scout backend regression:

```bash
cd ~/SpiritOS
PYTHONPATH=scout/src scout/.venv/bin/python -m pytest \
  scout/src/scout/tests/test_source_registry.py \
  scout/src/scout/tests/test_sources_api.py \
  scout/src/scout/tests/test_discovery_jobs.py \
  scout/src/scout/tests/test_search_candidate_extraction.py \
  scout/src/scout/tests/test_search_provider.py \
  scout/src/scout/tests/test_v03_soak_safety.py
```

Observed result:

```text
43 passed in 71.50s
```

Dashboard Scout UI, typecheck, and targeted lint:

```bash
cd ~/SpiritOS
npx vitest run src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx
npm run typecheck
npx eslint src/components/dashboard/HomelabScoutIntelligenceWidget.tsx src/lib/scout-overview.ts src/hooks/useScoutOverview.ts
```

Observed result:

```text
24 tests passed
tsc --noEmit passed
targeted ESLint passed with no output
```

Baseline soak snapshot:

```bash
cd ~/SpiritOS
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-soak-snapshot
```

Observed result:

```text
SCOUT SOAK SNAPSHOT
Result: PASS
Snapshot: scout/soak-logs/scout-soak-snapshot-2026-05-16T194610Z.json
warnings: none
Recommendation: ready for next increment
```

## Live Evidence

Baseline live counts after the soak snapshot:

```text
active source count: 5
candidate counts: approved 2, recommended 12, stored 0, blocked 1, needs_review 2, rejected 1
discovery job count: 5
```

Discovery budget and queue state:

```text
daily_limit: 3
used_today: 4
remaining_today: 0
can_create_job: false
blocked_reason: daily_limit_reached
queued_jobs: 5
running_jobs: 0
completed_jobs: 0
failed_jobs: 0
```

Queued job classifications:

- duplicate Pydantic jobs: `duplicate_queued`, next action `cancel_duplicate_or_wait`
- spam/noise test job: `spam_test`, next action `cancel_or_keep_for_test_evidence`
- old FastAPI job: `stale_queued`, next action `cancel_stale_or_investigate_worker`

## Dashboard Controls

Source Gate:

- shows candidate counts
- shows review bundle counts
- shows trust tier, confidence, source kind, poller support, provenance, review history, auto-rank, suggested action, and auto-approval dry-run state
- supports individual approve, reject, and block
- supports manual batch approval only for explicitly selected low-risk recommended sources
- shows exact selected URIs and poller support before batch approval

Packet Gate:

- shows queued packet promotions
- shows queued by, queued at, promotion reason, promoted by, and promoted at
- supports Promote Packet and Reject Packet on queued promotions
- does not promote anything automatically

Discovery Gate:

- shows daily budget, used count, remaining count, and reset hint
- shows manual-controlled execution state
- shows Preview Search and Extract Candidates as separate actions
- preview does not create candidates
- extraction creates or updates candidates only
- no source becomes active from preview or extraction

Diagnostics:

- points operators to manual runner checks and soak snapshots
- does not run destructive workflows

## Safety Boundaries

Memory:

- current live state: `Semantic memory inactive`
- `write_enabled` is false in the v0.4 read model
- Scout stores packets and source decisions, but does not write into proxy memory or coding context automatically

Auto approval:

- auto-rank is active as read-only labels
- review bundles are active as read-only grouping
- auto-approval dry-run is active as a report field
- real auto-approval is not built
- batch approval remains manual and requires selected candidates plus confirmation

Search and discovery:

- search smoke respects daily discovery job budget
- budget-blocked smoke is reported as budget-blocked, not as provider failure
- queued jobs are saved controlled search plans
- no background worker automatically advances queued discovery jobs

## Known Limitations

- The live discovery budget is currently exhausted until the next UTC reset.
- The live queue still contains duplicate, stale, and noisy test jobs.
- Baseline soak is clean, but a full 24 to 72 hour soak has not elapsed yet.
- Auto-approval dry-run may show no eligible candidates when live candidates do not meet every strict rule.
- Batch approval is intentionally limited to low-risk recommended candidates.
- Unsupported source types can be manually approved, but they report `poller_supported: false`.

## Stability Evidence

The following passed after the v0.4 polish work:

- source registry tests
- source candidate API tests
- discovery job budget/state tests
- search candidate extraction tests
- search provider tests
- soak safety test
- Scout dashboard widget tests
- TypeScript typecheck
- targeted ESLint
- baseline soak snapshot

The baseline soak snapshot reported:

- health: PASS
- source candidates: PASS
- sources: PASS
- discovery jobs: PASS
- mutated: false
- wrote snapshot: true
- warnings: none

## Next Recommended Phase

Do not enable real auto-approval yet.

Recommended next step:

Run the long soak routine from `scout/docs/V0_3_PHASE10_LONG_RUNNING_SOAK.md` for 24 to 72 hours:

```bash
cd ~/SpiritOS
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-smoke
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-source-gate
PYTHONPATH=. .venv/bin/python -m source_proxy.testing.runner --profile scout-soak-snapshot
```

Proceed only if:

- source count changes only after explicit manual approval
- candidate counts remain bounded
- rejected and blocked decisions stay durable
- discovery jobs remain explainable
- logs do not show repeated errors
- search smoke only runs when budget allows

After soak, choose the next project priority:

- Scout-to-Proxy context bridge, still read-only/manual-import first
- Cartographer/Blueprinter integration
- Discovery queue cleanup controls for stale and duplicate jobs
