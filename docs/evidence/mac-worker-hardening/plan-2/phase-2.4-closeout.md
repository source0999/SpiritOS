# Phase 2.4 Closeout

Date: 2026-05-28

## Increments completed

- Increment 2.4.1: `docs/evidence/mac-worker-hardening/plan-2/increment-2.4.1-search-provider-boundary.md`
- Increment 2.4.2: `docs/evidence/mac-worker-hardening/plan-2/increment-2.4.2-safe-search-packet-mode.md`
- Increment 2.4.3: `docs/evidence/mac-worker-hardening/plan-2/increment-2.4.3-web-search-packet-proof.md`

Evidence exists for all increments.

## Web/search grade

A+

Rationale:

- Local SearXNG provider exists on Linux.
- Mac can reach the provider at `source-server.local:8080`.
- `scout_research_packet` supports bounded `mode:"web_search_packet"`.
- End-to-end proof started from SpiritOS API.
- Mac worker handled the job.
- Local SearXNG returned structured data.
- Result packet included sources, provider status, limitations, recommended checks, and untrusted-content warning.
- No paid provider was used.
- No Scout production storage was written.

## Checks and proof

Checks run in this phase:

- Linux SearXNG HTML probe: passed.
- Linux SearXNG JSON probe: passed, with provider engine limitations visible.
- Mac TCP provider reachability probe: passed for `source-server.local:8080`.
- Mac JSON provider probe: passed.
- `python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py`: passed.
- `node --check scripts/mac-worker/spirit-mac-worker.mjs`: passed.
- `npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts --reporter=dot`: passed, 7 tests.
- `git diff --check`: passed.
- Direct Mac `web_search_packet`: passed.
- Direct Mac forced bad provider URL: failed closed with `search_provider_unreachable`.
- API `web_search_packet`: passed with 5 sources.

## Forbidden action review

- No hidden writes occurred.
- No paid provider was used.
- No Scout production storage was mutated.
- No Scout packet was promoted.
- No Source Proxy auto-import was performed.
- No result page content was fetched or executed.
- No private account was browsed.
- No Cartographer data, provider routing, secrets, or protected files were changed.
- The Mac remains advisory/check support only.

## Process note

An explicit temporary Next HTTPS dev server is currently running on port 3000 for API/browser proof. It is not hidden. It must be stopped before final Plan 2 closeout if no longer needed.

## GO / NO-GO

GO for Phase 2.4 complete.

GO to Phase 2.5.

Next authorized increment: Increment 2.5.1, inspect browser/design dependency boundary.
