# Integration Risk And Priority

## Priority 0: Truth Receipts

Goal: every prompt records what integrations were actually used.

Files likely touched later:

- `source_proxy/api/decision.py`
- `source_proxy/tasks/long_running.py`
- artifact runner/report builders under `docs/evidence/*/tools` or promoted runtime equivalents
- evidence schema/report files

Tests/evidence:

- unit tests for skipped and used subsystem fields
- one prompt receipt with all booleans false except Qwen/browser/repair as applicable

Stop condition: receipt exists for every prompt path and cannot silently omit a subsystem.

Risk: low. Needs user approval before implementation.

## Priority 1: Context Packet Router

Goal: choose no context, repo context, Obsidian, search/web, Cartographer, verifier, or Mac worker.

Risk: medium because privacy and prompt bloat matter.

Stop condition: router can skip safely and records why.

Needs approval: yes.

## Priority 2: Wire One Integration At A Time

Likely first choices:

- Obsidian for read-only local context if a relevant note exists.
- Search/SearXNG for prompts requiring current/external facts.
- Cartographer context after receipt and ownership boundaries are clear.

Risk: medium. Each integration needs one deliberately designed proof prompt.

Stop condition: one integration produces transcript/receipt proof and Qwen prompt includes bounded context.

Needs approval: yes.

## Priority 3: Integrated Test Run

Goal: future levels test the real SpiritOS system, not only Qwen artifact mode.

Run shape:

- prompt requires a context source
- context source is invoked
- model receives the context
- action/result is evaluated
- receipt proves all of the above

Risk: high if multiple systems are turned on at once. Integrate incrementally.
