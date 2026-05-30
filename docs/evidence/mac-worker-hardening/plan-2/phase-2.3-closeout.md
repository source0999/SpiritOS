# Phase 2.3 Closeout

Date: 2026-05-28

## Increments completed

- Increment 2.3.1: `docs/evidence/mac-worker-hardening/plan-2/increment-2.3.1-scout-research-packet-inspection.md`
- Increment 2.3.2: `docs/evidence/mac-worker-hardening/plan-2/increment-2.3.2-scout-research-local-smoke.md`
- Increment 2.3.3: `docs/evidence/mac-worker-hardening/plan-2/increment-2.3.3-scout-research-result-shape.md`
- Increment 2.3.4: `docs/evidence/mac-worker-hardening/plan-2/increment-2.3.4-scout-research-api-proof.md`

Evidence exists for all increments.

## Scout research packet status

`scout_research_packet` is proven through the SpiritOS API for:

- `mode:"local_only"`

It returns structured advisory data:

- `summary`
- `query`
- `mode`
- `sources`
- `candidate_files`
- `snippets`
- `confidence`
- `limitations`
- `recommended_next_checks`
- `unsafe_or_untrusted_content_warning`

`scout_research_packet` is not yet proven for:

- `mode:"web_search_packet"`

Unsupported modes currently fail closed with:

- `success:false`
- `error:"unsupported_scout_research_mode"`
- `reason_code:"unsupported_scout_research_mode"`
- explicit limitations and recommended next checks

## Checks

Checks run in this phase:

- `python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py`: passed.
- `node --check scripts/mac-worker/spirit-mac-worker.mjs`: passed.
- `npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts --reporter=dot`: passed, 6 tests.
- `git diff --check`: passed.
- Direct Mac `scout_research_packet` local-only probe: passed.
- Direct Mac `scout_research_packet` unsupported web mode probe: failed closed as expected.
- API `scout_research_packet` local-only proof: passed.

## Forbidden action review

- No Scout production storage was mutated.
- No Scout packet was promoted.
- No Source Proxy auto-import was performed.
- No web/search provider was called in Phase 2.3.
- No paid provider was used.
- No hidden worker, daemon, launch agent, or persistent process was started by this phase.
- No Cartographer data, provider routing, secrets, or protected files were changed.
- The Mac remains advisory/check support only.

## Phase result

GO for local-only `scout_research_packet`.

NO-GO for web-capable `scout_research_packet` until Phase 2.4 proves or honestly blocks the web/search provider boundary.

## GO / NO-GO

GO for Phase 2.3 complete.

GO to Phase 2.4.

Next authorized increment: Increment 2.4.1, inspect available search providers and network boundary.
