# Plan 2 Phase 2.3 - Scout/Mac/Search Readiness

Status: GO

## Increment 2.3.1 - Real search packet or hard blocked reason

`build_scout_search_context_packet` wraps the existing local-first research path. It returns:

- `used` when repo/Scout/search sources are selected
- `skipped` when no sources are available
- `blocked` only for adapter exceptions

Live read-only check against `/home/source/SpiritOS`:

- `scout_search`: `used`
- reason: `research_sources_selected`

Decision: GO.

## Increment 2.3.2 - Source/citation metadata

Each source includes evidence metadata:

- `source`
- `freshness`
- `trust_status`
- `review_status`
- `packet_summary`
- `why_relevant`

Test:

`test_scout_search_sources_include_citations_and_no_write_authority`

Decision: GO.

## Increment 2.3.3 - Mac advisory boundary

The packet declares:

`advisory_boundary: evidence_only_no_code_or_memory_writes`

Authority flags are read-only and advisory-only.

Decision: GO.

## Increment 2.3.4 - No hidden memory writes

Diagnostics include:

- `hidden_memory_writes: false`
- `can_write_memory: false`

Decision: GO.

## Increment 2.3.5 - No hidden code writes

Diagnostics include:

- `hidden_code_writes: false`
- `can_apply: false`
- `can_commit: false`
- `can_push: false`

Decision: GO.

## Phase Closeout

Phase 2.3 GO. Scout/Search can advise visibly with citations or skip/block honestly, and the packet denies memory/code/write authority.

