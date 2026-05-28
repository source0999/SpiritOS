# Mac Mini Internet Search And Scout Intake Node Plan 4/24

Date: 2026-05-27

Roadmap: `docs/masterKeyProxyProduction.md`
Plan: Plan 4/24, Mac Mini Internet Search And Scout Intake Node
Mode: MAC SUPPORT NODE / ADVISORY ONLY

## Scope

This packet records a read-only search routing contract, provider decision, and advisory packet format. It does not start services, schedule discovery, run Scout extraction, call Scout intake, write proxy memory, mutate Source Proxy, mutate Cartographer, auto-promote, create hidden workers, stage, commit, push, branch, create worktrees, clean, stash, reset, checkout, or start Plan 5/24.

Baseline inputs:

- Plan 2/24 Mac Mini baseline: `docs/mac-mini-support-node-plan-2-24-baseline-safety-boundary-v0.1.md`
- Plan 3/24 workload placement: `docs/mac-mini-workload-placement-matrix-plan-3-24-v0.1.md`
- Proven Mac primitives: SSH alias `spirit-mac-mini`, Python `3.9.6`, curl `8.7.1`, `osascript`, telemetry online.
- Unproven Mac primitives: Docker and Homebrew command paths.

## Phase 4.1 Search Boundary

### Increment 4.1.1 Read-Only Search Jobs

Search jobs are read-only.

Allowed operations after explicit search scope:

- Query approved search providers.
- Fetch provider result metadata.
- Produce bounded summaries.
- Produce citation lists.
- Produce candidate URLs.
- Produce blocked-reason notes when provider or policy blocks.

Forbidden operations:

- Repo writes.
- Proxy memory writes.
- Scout intake writes.
- Discovery job creation.
- Source candidate extraction into Scout state.
- Cartographer, map, live evidence, runtime, queue, worker, approval-token, or trust-tier mutation.
- Hidden scheduled discovery.

Increment result: GO for advisory policy; NO-GO for execution authority.

### Increment 4.1.2 Allowed Output

Allowed output is limited to:

- `search_summary`
- `citations`
- `candidate_sources`
- `research_packet`
- `blocked_reason`
- `manual_decision_needed`

Every output must include:

- source query
- provider used
- timestamp
- result count
- cited URLs
- confidence
- allowed use
- forbidden use

Increment result: GO.

### Increment 4.1.3 Direct Repo Mutation Forbidden

Mac search jobs must not write files directly into `/home/source/SpiritOS`, Scout state, Source Proxy memory, Cartographer evidence, or application routes. If a search result should become repo evidence, Source Proxy or Britton must approve the exact file/action scope separately.

Increment result: GO.

### Phase 4.1 Closeout

- Evidence exists for increments 4.1.1 through 4.1.3.
- Forbidden scope avoided: no repo mutation from Mac, no Scout intake/extraction, no Cart mutation, no Source Proxy mutation, no service start, no hidden worker, no branch, no worktree, no commit, no push, no cleanup, no stash, no reset, no checkout, and no Plan 5 start.
- Phase result: GO to Phase 4.2.

## Phase 4.2 Search Provider Decision

### Increment 4.2.1 Provider Choice

Provider options:

| Provider path | Decision | Reason |
| --- | --- | --- |
| Existing SearXNG from Mac via `http://10.0.0.186:8080/search?...&format=json` | Preferred for next scoped advisory search | Proven reachable from Mac with JSON results; local/free; already documented in repo search guidance. |
| Plain Python/curl scripts on Mac | Preferred execution wrapper later | Proven available; simple to audit; no service install required. |
| Browser automation / Safari checks | Later | `osascript` exists, but browser automation needs explicit scope and should not be hidden. |
| API search | Fallback later | Requires provider and credential policy. |
| Docker on Mac | NO-GO | Docker command path not proven on Mac. |
| Homebrew service on Mac | NO-GO | Homebrew command path not proven on Mac. |

Provider capability proof:

```json
{
  "ok": true,
  "provider": "searxng",
  "url": "http://10.0.0.186:8080/search?q=fastapi&format=json",
  "result_count": 19,
  "first_title": "FastAPI - FastAPI",
  "first_url_present": true
}
```

General HTTPS egress proof:

```json
{
  "ok": true,
  "url": "https://example.com/",
  "status": 200,
  "server": "cloudflare"
}
```

Increment result: GO for advisory SearXNG routing; NO-GO for autonomous search execution.

### Increment 4.2.2 Docker Versus Script Decision

Decision: scripts are safer than Docker for the next scoped plan.

Reason:

- Mac Python and curl are proven.
- Existing SearXNG endpoint is reachable from Mac.
- Docker is not proven on Mac.
- A script wrapper is easier to bound by query, timeout, result count, and output-only packet.

Increment result: GO.

### Increment 4.2.3 Fallback

Fallback policy:

- If SearXNG is unavailable, return a blocked packet with `provider_unavailable`.
- If Docker is unsupported or too heavy, do not install or start Docker; use scripts or defer.
- If provider credentials are required, stop and request explicit provider/credential scope.
- If results are too broad, stop and request narrower query/source allowlist.

Increment result: GO.

### Phase 4.2 Closeout

- Evidence exists for increments 4.2.1 through 4.2.3.
- Forbidden scope avoided: no Docker start/install, no Homebrew install/service, no browser automation, no hidden schedule, no Scout extraction, no Source Proxy mutation, no Cart mutation, no branch, no worktree, no commit, no push, no cleanup, no stash, no reset, no checkout, and no Plan 5 start.
- Phase result: GO to Phase 4.3.

## Phase 4.3 Proxy Integration

### Increment 4.3.1 Source Proxy Request Model

Source Proxy asks Mac for search by creating an explicit advisory request packet. Minimum fields:

```json
{
  "request_id": "mac-search-YYYYMMDD-NNN",
  "requested_by": "source_proxy_or_britton",
  "mode": "advisory_search_only",
  "query": "example query",
  "provider": "searxng",
  "max_results": 5,
  "timeout_sec": 8,
  "allowed_outputs": ["search_summary", "citations", "candidate_sources"],
  "forbidden_outputs": ["repo_write", "scout_intake_write", "cart_mutation", "source_proxy_mutation"],
  "manual_decision_required": true
}
```

Increment result: GO.

### Increment 4.3.2 Mac Research Packet Return Model

Mac returns a research packet only. Packet example:

```json
{
  "packet_type": "mac_search_advisory_packet",
  "request_id": "mac-search-YYYYMMDD-NNN",
  "provider": "searxng",
  "query": "fastapi",
  "result_count": 5,
  "summary": "Bounded provider results for operator review.",
  "citations": [
    {
      "title": "FastAPI - FastAPI",
      "url": "https://fastapi.tiangolo.com/",
      "source": "searxng"
    }
  ],
  "candidate_sources": [],
  "allowed_use": "operator review and possible later approved Scout/Source Proxy packet",
  "forbidden_use": "no direct repo write, no Scout intake write, no Cart mutation, no Source Proxy mutation",
  "manual_decision_needed": true
}
```

Increment result: GO.

### Increment 4.3.3 Source Proxy Remains Gate

Source Proxy remains the approval/write gate. Mac output is advisory evidence only. No Mac packet can authorize code edits, Scout intake, proxy memory writes, Cartographer mutation, provider/model calls, queue execution, worker execution, staging, commits, pushes, branches, worktrees, cleanup, stash, reset, or checkout.

Increment result: GO.

### Phase 4.3 Closeout

- Evidence exists for increments 4.3.1 through 4.3.3.
- Forbidden scope avoided: no repo mutation, no Scout intake/extraction, no Source Proxy mutation, no Cart mutation, no service start, no hidden worker, no branch, no worktree, no commit, no push, no cleanup, no stash, no reset, no checkout, and no Plan 5 start.
- Search routing contract is recorded.
- Phase result: GO to Plan 4/24 closeout.

## Plan 4/24 Closeout

- All phases reviewed: Phase 4.1, Phase 4.2, Phase 4.3.
- All increments reviewed: 4.1.1 through 4.3.3.
- Evidence exists: yes.
- Forbidden actions occurred: no.
- Provider capability proof exists: yes.
- Packet example exists: yes.
- Advisory search routing: GO for future scoped use.
- Direct Scout intake: NO-GO.
- Direct Source Proxy mutation: NO-GO.
- Direct Cart mutation: NO-GO.
- Hidden scheduled discovery: NO-GO.
- Docker/Homebrew Mac provider path: NO-GO until proven and approved.
- Final Plan 4/24 result: GO for advisory search routing contract; NO-GO for execution, intake, mutation, or hidden scheduling.
- Next roadmap plan only: `Plan 5/24: Mac Mini Subagent Host Feasibility`.
- Plan 5 started by this packet: `false`.

## Manual Verification Block

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
ssh -o BatchMode=yes spirit-mac-mini 'command -v python3; python3 --version; command -v curl; curl --version | head -1; command -v osascript || true; command -v docker || true; command -v brew || true'
ssh -o BatchMode=yes spirit-mac-mini 'python3 - <<'"'"'PY'"'"'
import json, urllib.parse, urllib.request
url = "http://10.0.0.186:8080/search?" + urllib.parse.urlencode({"q":"fastapi","format":"json"})
with urllib.request.urlopen(url, timeout=8) as r:
    payload = json.loads(r.read(200000).decode("utf-8"))
results = payload.get("results") or []
print(json.dumps({"ok": True, "provider": "searxng", "result_count": len(results), "first_url_present": bool(results and results[0].get("url"))}, indent=2))
PY'
grep -nE "Plan 4/24|read-only search|SearXNG|Provider capability proof|packet_type|mac_search_advisory_packet|Source Proxy remains|NO-GO|Plan 5/24" docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md
git diff --check -- docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md
```

## Expected Output

- `git status` shows existing untracked roadmap/evidence files plus this Plan 4 packet.
- `git rev-parse HEAD` prints `caeccea45b18d39f94c463a3376a6eb911256ea8`.
- SSH capability check shows Python, curl, and `osascript`; Docker/Homebrew may print nothing.
- SearXNG proof prints JSON with `ok: true`, provider `searxng`, positive result count, and `first_url_present: true`.
- `grep` shows search boundary, provider proof, packet contract, Source Proxy gate, NO-GO boundaries, and next plan title.
- `git diff --check` exits cleanly with no output.

## Rollback Guidance

If rollback is required, remove only `docs/mac-mini-internet-search-scout-intake-node-plan-4-24-v0.1.md` after explicit Britton approval.

Do not reset, checkout, stash, clean up, broadly restore files, mutate branches or worktrees, push, or force push.
