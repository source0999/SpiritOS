# Phase 2.2 Closeout

Date: 2026-05-28

## Increments completed

- Increment 2.2.1: `docs/evidence/mac-worker-hardening/plan-2/increment-2.2.1-overlay-decision.md`
- Increment 2.2.2: `docs/evidence/mac-worker-hardening/plan-2/increment-2.2.2-worker-overlay-formalized.md`

Evidence exists for both increments.

## Overlay decision

`scripts/mac-worker/` should be normal tracked repo content.

The required worker entry files were staged as tracked additions:

- `scripts/mac-worker/spirit-mac-worker.mjs`
- `scripts/mac-worker/spirit_mac_worker.py`

The operator contract was added:

- `docs/mac-worker-operator-contract.md`

Excluded from tracked content:

- `scripts/mac-worker/__pycache__/`
- secrets
- `.env.local`
- machine-specific private keys
- local caches
- generated runtime state

## Checks

Required checks from Increment 2.2.2:

- `git status --branch --short --untracked-files=normal`: passed and showed the worker files as staged additions.
- `python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py`: passed.
- `node --check scripts/mac-worker/spirit-mac-worker.mjs`: passed.
- `git diff --check`: passed.

Additional Mac execution check:

- Direct SSH `system_status` through `python3 scripts/mac-worker/spirit_mac_worker.py`: passed with `success:true` and `repo_present:true`.

## Forbidden action review

- No secrets were added.
- No `.env.local` file was added.
- No local cache file was added.
- No Mac write authority was changed.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No Scout production data was mutated.
- No Cartographer data, provider routing, secrets, or protected files were mutated.
- The Mac worker remains advisory/check support only.

## Phase result

Worker files are now formalized as tracked repo content, with the operator contract documenting the checkout and safety boundary.

## GO / NO-GO

GO for Phase 2.2 complete.

GO to Phase 2.3.

Next authorized increment: Increment 2.3.1, inspect current `scout_research_packet` implementation.
