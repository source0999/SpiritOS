# Context Packet Truth

## Current Included Context

For repo coder paths, Source Proxy can build Coder packets with:

- target file path and existence
- allowed/forbidden files
- protected paths
- context slices from repo files
- task spec and verification plan
- model route/provider summary
- Obsidian diagnostics summary
- trial flags and output format contract

For recent Level 3/4 artifact runs, evidence focused on:

- prompt
- generic artifact behavior contract
- task shape
- model-authored file targets/content
- disposable workspace path
- browser behavior probe results
- repair/retest evidence

## Included / Not Included

| Context type | Included today | Recent Level 3/4 artifact use | Notes |
| --- | --- | --- | --- |
| Repo context | YES for repo coder packet paths | mostly NO | artifacts are disposable, model chooses files |
| Obsidian context | diagnostics only | NO | `obsidian_context_used_in_prompt: False` |
| Search results | conditional route research | NO | no Level 3/4 invocation found |
| Cartographer context | preview/advisory code exists | NO | not route owner |
| Model lane recommendations | metadata/observability | YES as metadata | sidecars not called |
| Verifier feedback | deterministic/browser evidence | YES | model verifier not called |
| Behavior contract | YES | YES | central to artifact levels |

## Are Packets Enough for Qwen?

They are enough for disposable artifact generation and some simple repo edits. They are not yet enough for full SpiritOS context-orchestrated coding because context source selection is not a live router and receipts do not prove non-Qwen subsystem participation.

## Missing

- context-needed decision
- source-specific receipts
- search/Obsidian/Cartographer injected context with evidence refs
- verifier feedback as structured input before repair/final verdict
- privacy/cost/approval record per context source
- explicit negative receipts for skipped integrations
