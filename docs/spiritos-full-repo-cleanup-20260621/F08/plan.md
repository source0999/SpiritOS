# F08 — Context / Memory / Headroom / Repomix Consistency

## Goal
Make port/config/start scripts for context, memory, Headroom, and repomix
internally consistent, and document the audited Headroom environmental truth
honestly. **No claim of Headroom active without proof.**

## Why
Audit §17/G + headroom-repair-log: Headroom is BLOCKED_ENV (Cursor on 8797; the
installed Headroom was a Linux venv Windows Git Bash can't run). Scripts
reference ports/configs inconsistently, which obscures the real environmental
block. F8 makes the inconsistency honest and explicit.

## Audited truth to preserve (immutable documentation)
- Cursor occupied port 8797 during the audit.
- The installed Headroom binary belonged to a Linux venv (shebang
  `#!/home/source/...`); Windows Git Bash could not execute it.
- Cursor must NOT be killed (unrelated editor service).
- Tree-sitter (repomix --compress) is an honest fallback, not Headroom.

## Primary targets
`scripts/context/headroom-check.sh`, `scripts/headroom-proxy-dev.sh`,
`source_proxy/proxy_memory/` (consistency only), repomix configs
(`repomix*.config.json`, `.repomixignore`), and docs.

## Increments (≤12 source files each)
1. **8.1** — make `HEADROOM_PORT` / port references consistent across
   `headroom-check.sh`, `headroom-proxy-dev.sh`, and repomix LLM config;
   document the Cursor/8797 collision explicitly in comments + a runbook note.
   No behavior that would kill Cursor or rebuild the venv.
2. **8.2** — context/memory digest consistency (proxy_memory): ensure the context
   pack shape is unchanged; add an honest `headroom_status` probe that reports
   BLOCKED_ENV when health fails / compressed!=true / tokens_saved<=0.

## Invariants
- **Headroom may not be reported active** unless: health success AND
  `compressed=true` AND `tokens_saved > 0`.
- Tree-sitter fallback keeps work moving but **cannot make Headroom GO**.
- Context pack shape unchanged (compatibility).
- No Cursor kill, no venv rebuild, no pip install, no package install.

## Stop conditions
- Context pack shape changes → NEEDS_FIX.
- Headroom reported active without the three proofs → NEEDS_FIX (constitution §F).

## Environmental outcome
If config/docs are fixed but runtime remains externally blocked, record a **minor
environment caveat** and `BLOCKED_ENV` for Headroom itself. This is an allowed
minor caveat (see minor-caveat policy) — it does not weaken any contract.

## Rollback
Revert env var / port references; restore prior probe. Documentation additions
may stay (they record truth).

## Approval
Britton. (Real Headroom enablement is a separate Britton decision — not in F8.)
