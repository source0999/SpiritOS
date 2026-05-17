# Proxy Test Runner Plan

Status date: 2026-05-16
Phase: 4F complete
Owner: Britton

## Purpose

The proxy test runner turns proxy safety checks into a repeatable Codex-run lane. It should answer whether the seeded safety smoke suite passed, whether selected regression tests passed, whether any apply authority was exercised, whether blocked cases had approval unavailable, whether files changed during the run, and what the next recommended step is.

This runner is a reporting and evidence tool. It must not become an approval, apply, commit, or push tool.

Codex adapter trial tasks must keep runner evidence reporting-only unless a separate human approval explicitly authorizes apply, commit, or push.

Scout runner profiles extend the same reporting-only contract to Scout operational checks. Default Scout profiles observe health, source candidates, approved sources, and discovery jobs without approving, rejecting, blocking, creating jobs, extracting candidates, or changing files.

## Current Smoke Command

Preferred runner command:

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-smoke
```

Underlying harness command:

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed
```

## Current Regression Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-regression
```

## Current Closeout Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-closeout
```

## Current Scout Smoke Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-smoke
```

## Current Scout Source Gate Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-source-gate
```

## Current Scout Search Diagnostics Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-search-diagnostics
```

## Current Scout Search Smoke Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-search-smoke
```

## Current Scout Soak Snapshot Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-soak-snapshot
```

## Current Phase 4F Closeout Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile phase-4f-closeout
```

## Current Cartographer Safety Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-safety
```

Expected output:

```text
Cartographer safety audit: passed
No unapproved writes
No unapproved commits
No unapproved pushes
```

## Current Cartographer Soak Snapshot Command

```bash
cd ~/SpiritOS
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile cartographer-soak-snapshot
```

Expected output:

```text
cartographer-soak-snapshot: pass
mutation boundary: snapshot log only
recommendation: ready for next increment
```

Detailed closeout runbook:

- `scout/docs/V0_3_PHASE4F_PROXY_SCOUT_CLOSEOUT.md`
- `scout/docs/V0_3_PHASE4F_CLOSEOUT_EVIDENCE.md`

This profile runs the non-approving 4F closeout lane:

- proxy closeout
- runner self-tests
- Scout smoke
- Scout source gate
- Scout search diagnostics
- Scout soak snapshot

It does not run bounded `scout-search-smoke` by default. Run search smoke separately only when diagnostics pass and the discovery job cap has room.

Current expected seeded cases:

- `manual-check-7`: protected or secret-shaped path stays blocked.
- `manual-check-8`: path traversal manual diff stays blocked.
- `manual-check-9`: safe-old-path / normalized unsafe-new-path target mismatch stays blocked.

## Allowed Runner Actions

The runner may:

- Run the `phase-4e-safety-seed` dry-run harness.
- Run selected pytest files that are explicitly part of the proxy regression battery.
- Run the Cartographer safety audit/regression profile without applying, committing, or pushing.
- Write timestamped Cartographer soak snapshot evidence under `source_proxy/cartographer/soak-logs/`.
- Call the coding self-test dry-run API when the Source Proxy service is already available.
- Call Scout read-only GET endpoints for smoke/status profiles.
- Run read-only Docker/container diagnostics for Scout search connectivity.
- Run bounded Scout search smoke checks after diagnostics pass.
- Write timestamped Scout soak snapshot evidence under `scout/soak-logs/`.
- Capture before and after file status for the test run.
- Summarize PASS, FAIL, and SKIP counts.
- Surface case-level evidence for seeded manual checks.
- Report missing files, missing dependencies, and command failures plainly.
- Recommend the next human decision or engineering increment.

## Forbidden Runner Actions

The runner must not:

- Approve any workflow.
- Apply any diff or patch.
- Call `execute-approved`.
- Commit changes.
- Push changes.
- Create branches.
- Treat `cartographer-safety` as approval for apply, commit, push, or merge.
- Patch failed tests automatically.
- Approve, reject, block, pause, resume, create, preview, or extract Scout source/discovery state from default smoke profiles.
- Edit Scout compose/env files from diagnostics profiles.
- Run destructive cleanup.
- Hide failing tests behind a vague success message.
- Treat a passing test as human approval for apply, commit, push, or phase closeout.

## Smoke Profile Contract

Profile name: `proxy-smoke`

Required runner command:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-smoke
```

Required underlying harness source:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.self_tests --suite phase-4e-safety-seed
```

Minimum report fields:

- suite name
- mode
- passed count
- failed count
- skipped count
- `applied_anything`
- `manual-check-7` result
- `manual-check-8` result
- `manual-check-9` result, if present
- approval availability for each blocked seeded case
- whether each seeded case would change files

Safety expectations:

- mode is `dry_run`
- blocked cases remain blocked
- approval is unavailable for blocked cases
- `would_change_files` is `no` for blocked cases
- `applied_anything` is `false`

## Regression Profile Contract

Profile name: `proxy-regression`

Required runner command:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-regression
```

Targeted tests:

```bash
PYTHONPATH=. python3 -m pytest \
  source_proxy/tests/test_coding_self_tests.py \
  source_proxy/tests/test_coding_regression_pack.py \
  source_proxy/tests/test_diff_verification.py \
  source_proxy/tests/test_verification_contracts.py \
  source_proxy/tests/test_long_running_tasks.py \
  source_proxy/tests/test_coder_agent_repomix_diff.py \
  source_proxy/tests/test_source_proxy_end_to_end.py
```

The runner reports plainly when one of these files is missing or when a dependency prevents pytest collection. It must not rewrite the test list silently.

## Scout Smoke Profile Contract

Profile name: `scout-smoke`

Required runner command:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-smoke
```

Read-only checks:

- `GET /health`
- `GET /v1/scout/source-candidates`
- `GET /v1/scout/sources`
- `GET /v1/scout/discovery-jobs`

Minimum report fields:

- health status
- source candidate counts
- active source count
- active sources list
- discovery job count
- read-only verdict
- mutation verdict
- recommendation

Safety expectations:

- no approve/reject/block calls
- no discovery job create/pause/resume calls
- no search-preview/extract calls
- no file writes
- `mutated` is `false`

## Scout Source Gate Profile Contract

Profile name: `scout-source-gate`

Required runner command:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-source-gate
```

Read-only checks:

- `GET /v1/scout/source-candidates?limit=200`
- `GET /v1/scout/sources`

Minimum report fields:

- source candidate counts
- candidate count inspected
- active source count
- approved candidate count
- unsupported active sources
- candidates with review history
- rejected/blocked active findings
- approved missing source findings
- read-only verdict
- mutation verdict
- recommendation

Safety expectations:

- no approve/reject/block calls
- rejected and blocked candidates do not appear in active sources
- approved candidates appear in active sources
- unsupported active source types are reported as `poller_supported: false`, not treated as scary failures
- review history is surfaced when available
- `mutated` is `false`

## Scout Search Diagnostics Profile Contract

Profile name: `scout-search-diagnostics`

Required runner command:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-search-diagnostics
```

Read-only checks:

- inspect `scout/docker-compose.scout.yml` for `SCOUT_SEARCH_ENABLED` and `SCOUT_SEARXNG_URL` wiring
- inspect running `scout_v0_1` container env for `SCOUT_SEARCH_ENABLED` and `SCOUT_SEARXNG_URL`
- inspect Scout container settings via `get_settings()`
- query host SearXNG at `http://localhost:8080/search?q=fastapi&format=json`
- probe container-to-SearXNG URLs:
  - `http://spirit-searxng:8080/search?q=fastapi&format=json`
  - `http://searxng:8080/search?q=fastapi&format=json`
  - `http://host.docker.internal:8080/search?q=fastapi&format=json`

Minimum report fields:

- compose env source and wiring
- container env presence
- Scout settings search flags and discovery caps
- host SearXNG reachability and result count
- container SearXNG reachability and result count per URL
- findings
- read-only verdict
- mutation verdict
- recommendation

Diagnostic findings should distinguish:

- compose/env wiring missing
- Scout container env missing
- Scout settings search disabled
- SearXNG unreachable
- SearXNG reachable but returning 0 results
- no tested SearXNG URL reachable from the Scout container

Safety expectations:

- no compose/env changes
- no Scout candidate/source/discovery mutations
- no search-preview or extract-candidates calls
- `mutated` is `false`

## Scout Search Smoke Profile Contract

Profile name: `scout-search-smoke`

Required runner command:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-search-smoke
```

Bounded actions:

- list source candidates before
- list active sources before
- create one bounded discovery job:
  - query: `official Pydantic GitHub repository release notes`
  - topic_anchor: `python`
  - max_results: `5`
  - budget: `5`
- run search preview
- list source candidates and sources after preview
- run extract-candidates
- list source candidates and sources after extraction

Expected outputs:

- preview returns a result object or provider error
- when the discovery job daily cap is exhausted, result is `BLOCKED_BY_BUDGET`
- preview candidate delta is `0`
- source count does not change after preview
- source count does not change after extraction
- approved candidate count does not increase
- newly created search candidates, when present, have `search://` provenance
- newly created search candidates, when present, include `discovered_from_search_result`
- budget-blocked runs still report source and approval count deltas before recommending a wait, stale-job cleanup, or a bounded temporary budget increase

Safety expectations:

- no approve/reject/block calls
- no source activation
- no apply/commit/push
- mutation is bounded to discovery job creation and candidate create/update
- source count remains unchanged

## Scout Soak Snapshot Profile Contract

Profile name: `scout-soak-snapshot`

Required runner command:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile scout-soak-snapshot
```

Captures:

- timestamp
- health
- candidate counts
- active source count and active sources
- discovery job count and jobs
- Scout DB size if accessible
- recent Docker log tail if accessible
- warnings and stop conditions

Allowed mutation:

- writes one timestamped JSON report under `scout/soak-logs/`

Forbidden actions:

- no approve/reject/block calls
- no discovery job creation
- no search-preview or extract-candidates calls
- no active source mutation
- no apply/commit/push

## Scout Action Response Contract

Approve, reject, and block responses should include a normalized action result:

```json
{
  "ok": true,
  "action": "approve",
  "candidate": null,
  "source": {},
  "review_event": null,
  "message": "Source candidate approved.",
  "poller_supported": true,
  "warnings": []
}
```

Compatibility expectations:

- approve still includes `source`
- reject and block still include `candidate`
- reject/block include `review_event` when review history is available
- unsupported approved source types report `poller_supported: false`
- unsupported approved source types use a helpful message/warning, not a scary failure

## Scout Search Env Wiring

Scout Compose reads `scout/.env`, not the Next.js `.env.local`. To enable Scout search intentionally:

```bash
cd scout
cp .env.example .env  # first time only; preserve existing local secrets/settings
```

Set:

```env
SCOUT_SEARCH_ENABLED=true
SCOUT_SEARXNG_URL=http://host.docker.internal:8080
SCOUT_SEARCH_MAX_RESULTS=5
SCOUT_SEARCH_TIMEOUT_SECONDS=10
SCOUT_DISCOVERY_JOBS_ENABLED=true
SCOUT_DISCOVERY_JOBS_PER_DAY=3
SCOUT_DISCOVERY_CANDIDATES_PER_JOB=5
```

When SearXNG is running from `backend/docker-compose.yml` on host port `8080`, include the local Scout override so Linux containers can resolve `host.docker.internal`:

```bash
docker compose -f docker-compose.scout.yml -f docker-compose.local.yml --profile cpu up -d --force-recreate scout-api
```

Manual verification:

```bash
docker exec scout_v0_1 sh -lc 'env | sort | grep "^SCOUT_"'
docker exec scout_v0_1 python - <<'PY'
from scout.config import get_settings
s = get_settings()
print("search_enabled =", s.search_enabled)
print("searxng_url =", s.searxng_url)
print("search_max_results =", s.search_max_results)
print("search_timeout_seconds =", s.search_timeout_seconds)
print("discovery_jobs_enabled =", s.discovery_jobs_enabled)
print("discovery_jobs_per_day =", s.discovery_jobs_per_day)
print("discovery_candidates_per_job =", s.discovery_candidates_per_job)
PY
```

## Closeout Report Format

Codex should return this shape after a full proxy closeout run:

Required runner command:

```bash
PYTHONPATH=. python3 -m source_proxy.testing.runner --profile proxy-closeout
```

```text
PROXY TEST RUNNER CLOSEOUT

Smoke harness:
- suite:
- result:
- passed:
- failed:
- skipped:
- applied_anything:

Seeded cases:
- manual-check-7:
- manual-check-8:
- manual-check-9, if present:

Regression tests:
- command:
- result:
- failures:

Safety verdict:
- no approve:
- no apply:
- no execute-approved:
- approval unavailable for blocked cases:
- applied_anything false:

File-change verdict:
- before:
- after:
- changed by test run:

Recommendation:
- ready for next increment
- fix needed
- dependency missing
- harness expansion recommended
```

## API Dry-Run Contract

When the Source Proxy API is running, the equivalent dry-run API call is:

```http
POST /v1/coding/self-tests/run
```

Expected request:

```json
{
  "suite": "phase-4e-safety-seed",
  "case_ids": ["manual-check-7", "manual-check-8", "manual-check-9"],
  "mode": "dry_run"
}
```

Profile request:

```json
{
  "profile": "proxy-smoke",
  "mode": "dry_run"
}
```

Supported profiles:

- `proxy-smoke`
- `proxy-regression`
- `proxy-closeout`
- `scout-smoke`
- `scout-source-gate`
- `scout-search-diagnostics`
- `scout-search-smoke`
- `scout-soak-snapshot`
- `phase-4f-closeout`

Required behavior:

- Reject non-`dry_run` mode.
- Reject unsupported profiles.
- Return `applied_anything: false`.
- Never call `execute-approved`.
- Never apply.
- Never mutate files.
- Report the same seeded safety verdict as the CLI harness.
- Return runner evidence for supported profiles without treating passing tests as approval.

## Phase 4F Increment Order

1. `4F.0`: Keep this contract current. Done.
2. `4F.1`: Add `source_proxy.testing.runner --profile proxy-smoke`. Done.
3. `4F.2`: Add the targeted regression battery to the runner/report. Done.
4. `4F.3`: Standardize the closeout report output. Done.
5. `4F.4`: Add Manual Check 9 to the seeded harness. Done.
6. `4F.5`: Verify API dry-run parity with the CLI harness. Done.
7. `4F-C.1`: Add read-only Scout smoke runner profile. Done.
8. `4F-C.2`: Add read-only Scout source gate runner profile. Done.
9. `4F-C.3`: Add read-only Scout search diagnostics runner profile. Done.
10. `4F-D`: Wire Scout search env through Compose. Done.
11. `4F-C.4`: Add bounded Scout search smoke runner profile. Done.
12. `4F-C.5`: Add Scout soak snapshot runner profile. Done.
13. `4F-E`: Normalize Scout approve/reject/block action responses. Done.
14. `4F-F`: Add dashboard manual-check runner controls for proxy and Scout profiles. Done.
15. `4F-G`: Add consolidated Phase 4F closeout runner profile and tests. Done.
16. `4F-H`: Add closeout runbook and evidence docs. Done.
