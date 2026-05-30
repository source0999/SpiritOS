# Increment 2.3.1 Scout Research Packet Inspection

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Inspect Mac worker implementation for `scout_research_packet`.
- Inspect Source Proxy and Scout intake/search code that might consume or resemble the packet.
- Identify whether the job requires internet, local Scout files, SearXNG, external browser tooling, or only repo context.

No implementation files were changed.

## Files inspected

- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `src/lib/mac-worker/types.ts`
- `src/lib/mac-worker/contract.ts`
- `src/lib/mac-worker/client.ts`
- `src/app/api/coding/mac-worker/route.ts`
- `source_proxy/api/scout_intake.py`
- `source_proxy/proxy_memory/scout_intake.py`
- `source_proxy/decision/scout_research.py`
- `scout/src/scout/sources/search.py`
- `scout/src/scout/sources/search_candidates.py`
- `scout/src/scout/api/discovery_jobs.py`
- `scout/docs/V0_3_PHASE2_CONTROLLED_SEARCH_PROVIDER.md`

## Current Mac worker behavior

`scout_research_packet` is listed as a supported job type in:

- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `src/lib/mac-worker/types.ts`

However, it does not currently have a dedicated handler.

In both worker implementations, the dispatcher handles only:

- `system_status`
- `run_safe_check`
- `browser_design_check`

All other supported job types, including `scout_research_packet`, fall through to the generic context search handler.

Current effective behavior:

- Searches tracked repo files through `git ls-files`.
- Scores candidate file paths against prompt/query tokens.
- Reads snippets from safe in-repo files only.
- Returns `summary`, `snippets`, `candidate_files`, and `recommended_checks`.
- Does not call internet.
- Does not call SearXNG.
- Does not call Scout API.
- Does not write Scout production storage.
- Does not promote or import packets.

## Source Proxy and Scout boundary

`source_proxy/api/scout_intake.py` exposes signed Scout promotion intake only. It requires:

- `SCOUT_PROMOTION_SIGNING_KEY`
- `approved: true`
- a promote verdict
- packet/verdict match

It writes through `source_proxy/proxy_memory/scout_intake.py`, which appends to `SOURCE_PROXY_SCOUT_INTAKE_LOG`.

The Mac worker does not call this intake path.

`source_proxy/decision/scout_research.py` can read Scout packets as advisory research sources only when:

- `SOURCE_PROXY_SCOUT_RESEARCH_ENABLED=1`
- a configured Scout research URL is reachable

It returns evidence-only results with:

- `can_apply: false`
- `can_approve: false`
- `can_mutate_proxy_memory: false`
- `authority: evidence_only`

The Mac worker does not currently call this path.

## Scout search boundary

`scout/src/scout/sources/search.py` implements SearXNG search through `run_searxng_search`.

Dependency requirements:

- `SCOUT_SEARXNG_URL`
- HTTP access to the configured SearXNG endpoint
- timeout and max-result bounds

`scout/src/scout/api/discovery_jobs.py` has two related flows:

- `search-preview`: bounded preview, `candidate_effect: "none"`, no candidate write.
- `extract-candidates`: converts search results into candidates and writes Scout storage.

The Mac worker must not use `extract-candidates` for advisory packet proof.

## Dependency classification

Current `scout_research_packet` implementation requires:

- real Mac repo checkout
- `git ls-files`
- readable tracked repo files
- local worker script

Current `scout_research_packet` implementation does not require:

- internet
- SearXNG
- local Scout database
- Source Proxy Scout intake
- external browser tooling
- Playwright

A future web-capable packet mode would require a bounded, local-first provider such as SearXNG and must remain preview/advisory-only.

## Result shape assessment

Current shape is too generic for A+ Scout advisory proof.

It lacks dedicated fields required by Plan 2:

- `query`
- `mode`
- `sources`
- `confidence`
- `limitations`
- `unsafe_or_untrusted_content_warning`

It does return:

- a summary
- candidate files
- snippets
- recommended checks

## Safety confirmation

- No implementation files were changed.
- No Scout production storage was mutated.
- No Scout promotion or intake endpoint was called.
- No SearXNG or external internet search was called.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Cartographer data, provider routing, secrets, or protected files were changed.

## GO / NO-GO

GO for Increment 2.3.1 complete.

Next authorized increment: Increment 2.3.2, run a no-internet/local-only `scout_research_packet` smoke.
