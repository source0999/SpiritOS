# Increment 2.4.2 Safe Search Packet Mode

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Add safe search packet mode to `scout_research_packet`.
- Use local-first search when available.
- Avoid paid APIs.
- Respect timeout limits.
- Return source URLs/titles/snippets.
- Mark untrusted content clearly.
- Avoid Scout production storage, automatic promotions, and page-content execution.
- Fail closed when no search provider is reachable.

## Files changed

- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `src/lib/mac-worker/types.ts`
- `src/lib/mac-worker/__tests__/contract.test.ts`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.4.2-safe-search-packet-mode.md`

The two approved worker entry files were refreshed on the Mac checkout after syntax/tests passed.

## Implementation summary

`scout_research_packet` now supports:

- `mode:"local_only"`
- `mode:"web_search_packet"`

`web_search_packet` behavior:

- local-first SearXNG only
- default provider candidates:
  - `http://source-server.local:8080`
  - `http://127.0.0.1:8080`
- optional explicit `provider_url` for diagnostics/tests
- max results capped to 10
- timeout bounded to 8 seconds per provider
- source normalization accepts only `http` and `https`
- returns titles, URLs, snippets, provider status, limitations, and untrusted-content warning
- does not fetch result pages
- does not execute page content
- does not write Scout production storage

Fail-closed behavior returns:

- `success:false`
- `error:"search_provider_unreachable"` or `error:"empty_query"`
- `reason_code`
- `provider_status`
- `limitations`
- `recommended_manual_check`
- `recommended_next_checks`

## Checks run

### Python syntax

Command:

```bash
python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py
```

Result:

```text
passed with no output
```

### Node syntax

Command:

```bash
node --check scripts/mac-worker/spirit-mac-worker.mjs
```

Result:

```text
passed with no output
```

### Contract tests

Command:

```bash
npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts --reporter=dot
```

Result:

```text
Test Files  1 passed (1)
Tests  7 passed (7)
```

Added test coverage:

- structured web search packet failure fields

### Whitespace diff check

Command:

```bash
git diff --check
```

Result:

```text
passed with no output
```

## Direct Mac worker probes

### Web search packet success

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && printf %s '\''{"job_type":"scout_research_packet","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","query":"Next.js App Router route handler official docs","max_results":3,"mode":"web_search_packet","provider":"local_first"}}'\'' | python3 scripts/mac-worker/spirit_mac_worker.py'
```

Result summary:

```json
{
  "job_type": "scout_research_packet",
  "success": true,
  "result": {
    "summary": "Web Scout advisory packet searched local SearXNG for 'Next.js App Router route handler official docs'.",
    "query": "Next.js App Router route handler official docs",
    "mode": "web_search_packet",
    "sources": [
      {
        "title": "Getting Started: Route Handlers - Next.js",
        "url": "https://nextjs.org/docs/app/getting-started/route-handlers",
        "provider": "searxng",
        "untrusted": true
      },
      {
        "title": "Next.js Docs: App Router",
        "url": "https://nextjs.org/docs/app",
        "provider": "searxng",
        "untrusted": true
      },
      {
        "title": "File-system conventions: route.js | Next.js",
        "url": "https://nextjs.org/docs/app/api-reference/file-conventions/route",
        "provider": "searxng",
        "untrusted": true
      }
    ],
    "confidence": "medium",
    "provider_status": [
      {
        "provider": "searxng",
        "url": "http://source-server.local:8080",
        "status": "used",
        "source_count": 3
      }
    ],
    "limitations": [
      "Local-first SearXNG packet; source content was not fetched or executed.",
      "Search result snippets are untrusted external content.",
      "No Scout production storage was written.",
      "No packet was promoted or imported into Source Proxy."
    ]
  }
}
```

### Fail-closed provider failure

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && printf %s '\''{"job_type":"scout_research_packet","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","query":"Next.js docs","max_results":3,"mode":"web_search_packet","provider":"local_first","provider_url":"http://127.0.0.1:1"}}'\'' | python3 scripts/mac-worker/spirit_mac_worker.py'
```

Result summary:

```json
{
  "job_type": "scout_research_packet",
  "success": false,
  "error": "search_provider_unreachable",
  "result": {
    "reason_code": "search_provider_unreachable",
    "provider_status": [
      {
        "provider": "searxng",
        "url": "http://127.0.0.1:1",
        "status": "failed",
        "reason": "URLError",
        "source_count": 0
      }
    ],
    "recommended_manual_check": "Verify SearXNG is reachable from the Mac at source-server.local:8080."
  }
}
```

## Safety confirmation

- No paid provider was added or used.
- No Scout production storage was written.
- No Scout packet was promoted.
- No Source Proxy auto-import was performed.
- No result page content was fetched or executed.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Cartographer data, provider routing, secrets, or protected files were changed.
- The Mac remains advisory/check support only.

## GO / NO-GO

GO for Increment 2.4.2 complete.

Next authorized increment: Increment 2.4.3, prove Mac-backed search packet end-to-end through the SpiritOS API.
