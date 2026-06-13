# Memory And Context Status

Final Obsidian trust grade: READ-ONLY ONLY

## Obsidian Usage

Obsidian appears as a real read-only context adapter, not only as docs. The local default vault is `data/design-vault` when present. Current files found there include `README.md`, `token-model-v0.1.md`, design pack notes/tokens, and source-card metadata.

## Obsidian Discovery Logic

`source_proxy/context/obsidian.py` resolves configuration from:

- `OBSIDIAN_CONTEXT_ENABLED`
- `OBSIDIAN_VAULT_PATH`
- `OBSIDIAN_INCLUDE_GLOBS`
- `OBSIDIAN_EXCLUDE_GLOBS`
- `OBSIDIAN_MAX_NOTES`
- `OBSIDIAN_MAX_CHARS_PER_NOTE`

If no explicit path is set, it walks from cwd/module parents looking for `data/design-vault`.

## APIs, Scripts, Routes, Components

Code/routes:

- `source_proxy/context/obsidian.py`
- `source_proxy/context/source_readiness.py`
- `source_proxy/api/obsidian_context.py`
- `/v1/context/obsidian/query`
- `source_proxy/self_status.py`
- `source_proxy/decision/prompt_packet.py`
- `source_proxy/tasks/long_running.py`

Tests:

- `source_proxy/tests/test_obsidian_context.py`
- `source_proxy/tests/test_context_source_readiness.py`
- `source_proxy/tests/test_self_status.py`
- `source_proxy/tests/test_prompt_packet_context_metadata.py`

## Read/Write Mode

Current mode: read-only. Diagnostics expose `obsidian_read_only: True`. Authority packets set `can_write_memory: False`, `can_apply: False`, `can_commit: False`, `can_push: False`, `can_start_worker: False`, and `can_call_provider: False`.

No automatic Obsidian write-back path was found.

## Manual, Automatic, Or Documented

Obsidian is automatic only as an optional context source and diagnostics provider. It is not automatic as an authoritative planner memory or write-back layer. It is also referenced in docs/evidence as intended memory direction.

## Search, Summary, Indexing, Prompt Injection

Search is simple: Markdown files are globbed, excluded paths are skipped, query terms are extracted from task text, notes are scored by term presence, and safe excerpts are returned. There is no durable index, vector store, graph, semantic ranking, freshness score, or metadata-aware resolver.

Prompt injection status:

- Dedicated Obsidian query returns selected safe excerpts.
- Context-source readiness packet includes selected note excerpts.
- Baseline prompt-packet metadata includes diagnostics only.
- Coder diagnostics currently include `obsidian_context_used_in_prompt: false`.

## Metadata And Reliability

No required frontmatter schema for Obsidian notes was found. `_blueprints` has schema/frontmatter conventions, but Obsidian notes are not yet governed as trusted memory. Reliability is therefore partial and content-dependent.

## Freshness, Duplication, Trust

No staleness/freshness handling was found for Obsidian notes. No conflict resolver was found between Obsidian, evidence docs, durable run store, Cartographer state, and blueprints. No automatic evidence link requirement was found for notes.

## Permission Boundaries And Audit

Reads are bounded by include/exclude globs and safe excerpts. Writes are absent. There is no Obsidian-specific write approval, audit ledger, or rollback path because the system does not currently write notes.

## Connections To Evidence And Preferences

Evidence docs are the strongest current proof memory. Durable runner rows store live runner diagnostics. Blueprints capture architecture/component intent. Cartographer has audit/evidence/trust modules. Obsidian is not yet tightly linked to these as a curated Hippocampus.

## Cartographer, Repo Map, Vector/Search

Cartographer can build repo map, component map, dirty-tree status, and blueprint truth. `source_proxy/vector/visual_index.py` exists with tests. Scout/search paths exist. These are adjacent memory/context systems, but there is no single memory orchestrator.

## Queried By Source Proxy Today

Actually queried:

- `/v1/context/obsidian/query`
- `build_obsidian_context_packet()`

Diagnostics only:

- `/v1/self/status`
- prompt-packet context metadata
- coder diagnostics

Not proven:

- route choice
- model/worker selection
- planner authority
- automatic learning/write-back

## Needed For Hippocampus v0.1

- Promote Obsidian only as read-only advisory memory first.
- Define note frontmatter: `memory_id`, `project`, `source`, `created_at`, `updated_at`, `confidence`, `freshness`, `evidence_links`, `owner`, `scope`, `deprecated`.
- Add evidence links from notes to `docs/evidence/**` or durable run IDs.
- Add freshness/staleness and conflict rules.
- Add approved write-back endpoint or CLI that produces a diff/preview before writing.
- Add tests proving selected notes appear in context packets and are either used or explicitly ignored by route/planner.
- Keep evidence docs and durable run store as proof-of-record, not Obsidian alone.

## Obsidian Readiness Matrix

| Capability | Status | Notes |
|---|---|---|
| Discovery | PARTIAL | Env path or `data/design-vault` auto-discovery. |
| Read access | PARTIAL | Markdown excerpts with excludes and redaction. |
| Search quality | WEAK | Simple term scoring only. |
| Context ranking | WEAK | Score count and path sort; no semantic or recency ranking. |
| Freshness/staleness handling | MISSING | No note freshness policy found. |
| Write safety | READ-ONLY ONLY | No writes; safe for now, not a write-back memory. |
| User approval boundaries | PARTIAL | Reads are bounded; writes absent; future writes need approval. |
| Evidence linking | WEAK | Not required by adapter. |
| Source Proxy integration | PARTIAL | Query endpoint and readiness packet; not proven in route decisions. |
| Future memory suitability | PARTIAL TRUST | Suitable as curated read-only context, not authoritative memory yet. |
