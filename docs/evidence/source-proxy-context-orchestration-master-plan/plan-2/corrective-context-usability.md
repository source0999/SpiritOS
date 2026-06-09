# Plan 2 Corrective - Context Source Usability

Status: GO

## Why This Corrective Pass Exists

The first Plan 2 pass normalized context-source statuses, but Obsidian was only reported as skipped and the result was not useful enough inside the actual Source Proxy packet flow.

This corrective pass makes the local Obsidian-style markdown vault usable by default and proves the combined Source Proxy context packet can return real context from all four sources.

## Increment C2.1 - Enable local Obsidian context by default

Change:

- `obsidian_context_config_from_env` now auto-detects `data/design-vault` when Obsidian env vars are unset.
- If the vault exists, Obsidian is enabled read-only by default.
- Diagnostics now include:
  - `obsidian_default_vault`
  - `obsidian_vault_path`
  - `obsidian_read_only`

Config documentation:

- `.env.example`
- `config/source-proxy.example.env`

Both now document:

- `OBSIDIAN_CONTEXT_ENABLED=true`
- `OBSIDIAN_VAULT_PATH=data/design-vault`
- include/exclude globs

Decision: GO.

## Increment C2.2 - Prove Obsidian returns real context

Test:

- `test_obsidian_defaults_to_local_design_vault_when_env_unset`

Result:

- env unset
- temp `data/design-vault` detected
- Obsidian enabled
- note selected
- safe excerpt returned

Decision: GO.

## Increment C2.3 - Prove Obsidian inside combined Source Proxy packet flow

Test:

- `test_combined_packet_uses_default_obsidian_vault_without_explicit_config`

Result:

- combined packet status for Obsidian: `used`
- note path: `README.md`
- no explicit `obsidian_config` argument was passed

Decision: GO.

## Increment C2.4 - Live Source Proxy context packet proof

Command:

Ran `build_context_source_readiness_packet` against `/home/source/SpiritOS` with `OBSIDIAN_CONTEXT_ENABLED` and `OBSIDIAN_VAULT_PATH` unset.

Result:

- `ready_for_source_proxy_packet: true`
- `cartographer: used`
- `obsidian: used`
- `scout_search: used`
- `design: used`
- Obsidian vault path: `/home/source/SpiritOS/data/design-vault`
- Obsidian note count: `5`
- Obsidian paths:
  - `README.md`
  - `packs/internal-dashboard-demo-v4/README.md`
  - `token-model-v0.1.md`
  - `packs/internal-dashboard-demo-v4/notes.md`
  - `source-cards/approval-checklist.md`
- authority flags:
  - `can_apply: false`
  - `can_commit: false`
  - `can_push: false`
  - `can_write_memory: false`
  - `can_start_worker: false`
  - `can_call_provider: false`

Decision: GO.

## Increment C2.5 - Verify other sources are usable packets

Live packet proof:

- Cartographer returned a used packet with repo map data.
- Scout/Search returned used research sources.
- Design returned used refs from the design context surface.

Focused and adjacent tests:

- `source_proxy/tests/test_context_source_readiness.py`
- `source_proxy/tests/test_research_preview.py`
- `source_proxy/tests/test_scout_research_bridge.py`
- `source_proxy/tests/test_self_status.py`

Decision: GO.

## Verification

Command:

`cd ~/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_context_source_readiness.py`

Result:

`8 passed in 0.19s`

Command:

`cd ~/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_ollama_route.py source_proxy/tests/test_coder_agent_repomix_diff.py source_proxy/tests/test_context_source_readiness.py source_proxy/tests/test_research_preview.py source_proxy/tests/test_scout_research_bridge.py source_proxy/tests/test_self_status.py`

Result:

`106 passed in 11.10s`

Command:

`git diff --check` on the corrective Plan 1/2 surface.

Result:

passed.

## Phase Closeout

Corrective Plan 2 GO. Obsidian is now enabled by default when the local vault exists and returns real context inside the combined Source Proxy packet flow. Cartographer, Scout/Search, and Design also return usable packets, not just status labels.
