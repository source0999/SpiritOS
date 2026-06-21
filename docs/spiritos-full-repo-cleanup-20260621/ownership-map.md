# Ownership Map — Stage Boundaries

Which subsystems each stage may edit, and which are protected (never edited).

## Allowed cleanup paths (task-defined)

```
source_proxy/
src/app/coding/
src/app/v1/
src/app/api/coding/
src/components/coding/
src/lib/coding/
src/lib/mac-worker/
scripts/context/
scripts/mac-worker/
scripts/source-proxy-*
scripts/headroom-proxy-dev.sh
repomix*.config.json
.repomixignore
README.md
package.json
_blueprints/
docs/spiritos-full-repo-cleanup-20260621/
docs/breakpoints/source-proxy-cleanup-preplan-20260621/
```

## Per-stage primary ownership

| Stage | Primary edit scope | Explicitly out of stage |
|---|---|---|
| F1 | `source_proxy/diagnostics/status_codes.py` (new); `decision/model_lanes.py` (qwen lane wiring); receipt serializers in `api/decision.py` (additive field only); `source_proxy/tests/test_status_codes.py` (new) | no final-status changes; no other lanes until qwen proven |
| F2 | `source_proxy/verification/anticheat/` (new, copy-from-existing); Set A runner import wiring; parity test | no legacy selftest deletion/move |
| F3 | `source_proxy/decision/escalation_contract.py` (new); `decision/model_lanes.py`; `routing/litellm_router.py`; tests | no API call path enablement |
| F4 | `source_proxy/decision/packet_templates/` (new); `decision/prompt_packet.py`; tests | no benchmark-keyed logic |
| F5 | `api/decision.py` (slim) → new `source_proxy/decision/lanes/*`; parity tests | no new engine; no receipt shape change |
| F6 | `source_proxy/tasks/long_running.py` → `tasks/{engine,apply,trace,recovery,regression}/`; tests | no state-machine rewrite |
| F7 | `src/components/coding/*`, `src/lib/coding/*`; feature flag; tests | no shell deletion; no `/coding` replacement |
| F8 | `scripts/context/headroom-check.sh`, `scripts/headroom-proxy-dev.sh`, `source_proxy/proxy_memory/` (consistency only), repomix configs, docs | no Cursor kill; no venv rebuild; no pip install |
| F9 | `decision.py`/lanes subprocess/urllib → typed adapters; `scripts/mac-worker/` contract; `src/lib/mac-worker/`; tests | no new engine; preserve timing/output |
| F10 | test gates, operator checks, runbook updates, tailoring scan tooling | no Set A/B/C; no battery prompts |

## Protected paths (NEVER edited by any stage)

```
src/app/spiritflix/
src/components/spiritflix/
src/lib/spiritflix/
src/lib/media/
scripts/media/
services/jellyfin/
Jellyfin data/config/SQLite
media storage
converter data
unrelated products
```

The media-concentration issue is deferred to a separately approved media cleanup.
SpiritFlix/media WIP present in the breakpoint baseline (anime importer) is
Britton's pre-existing work and is explicitly out of scope.

## Path-aware dirty guard (per-stage)

Before every stage, the dirty tree is compared against the breakpoint manifest.
New dirty files in cleanup-owned paths are allowed **only** if GLM created them
in the cleanup worktree as part of the current stage. Any unexpected dirty file
in a protected path halts the stage.

## Cross-cutting rules
- All edits happen in the cleanup worktree `../SpiritOS-cleanup-20260621` on
  branch `cleanup/full-repo-20260621`. The primary worktree is never edited.
- `package.json` may gain **explicitly-labeled, reversible** script entries
  (e.g. a future `check:all`); it may not have existing scripts silently
  repointed.
- New files are created, not destructively replacing tracked files, unless an
  exact-path retirement has passed its parity proof.
