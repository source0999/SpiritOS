# Final Set A Stability Readback - 2026-06-25

## Preflight

- repo: `/home/source/SpiritOS`
- branch: `integration/cleanup-plan3-debug-20260623`
- current HEAD: `08fd309f741452748def4871e40cdebee7ba3581`
- current HEAD subject: `docs: record Plan 3 Stage 4R GO verdict`
- required provider config commit present: yes, `b591dc0a fix: disable unstable SearXNG research engines`
- required diagnostics commit present: yes, `877f51fd Stabilize Plan 3 research provider diagnostics`
- staged files at preflight: none observed
- current dirty state: pre-existing Plan 3 Set A rerun receipt/report churn under `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/`; no source-code dirty files were observed in preflight
- active mutation check: no active `_stage4r_runner` process observed; SearXNG, Ollama, and Next dev processes were running

## SearXNG Engine Config Summary

`backend/searxng.yml` uses the default SearXNG settings with JSON output enabled and local service binding on `0.0.0.0:8080`.

The current engine override disables the unstable engines that previously returned CAPTCHA, rate-limit, or access-denied metadata during the A3 provider probe:

- `brave`: disabled
- `duckduckgo`: disabled
- `karmasearch`: disabled

The config keeps live search enabled through the remaining default engines and does not add fallback, cached, or fabricated sources.

## Last Known A3 Result

The latest recorded provider-stability rerun before this final verification reported:

- A3 run 1: `PASS`, source count `6`, retry count `0`, provider classification `SOURCES_AVAILABLE`, run id `run-20260625T104710Z`
- A3 run 2: `BLOCKED_ENV`, source count `0`, retry count `2`, provider classification `PROVIDER_ZERO_RESULTS`, run id `run-20260625T105325Z`
- A3 run 3: `PASS`, source count `6`, retry count `0`, provider classification `SOURCES_AVAILABLE`, run id `run-20260625T105845Z`

That result was not stable `PASS / PASS / PASS`, so full Set A was not run in that prior attempt.

## What This Verification Will Check

This final verification checks whether disabling unstable SearXNG engines makes Plan 3 Set A stable enough to proceed to a human decision:

1. Direct SearXNG 10x check for query `Android Jetpack Compose share intent local task app receipt polling`.
2. A3-only stability 3x, only if direct SearXNG returns usable live sources consistently enough.
3. Full Set A stability 2x, only if A3 is `PASS / PASS / PASS`.
4. Requested validation commands.
5. Exact-doc staging and commit only for final verification reports, with latest receipt churn left unstaged unless explicitly required as final evidence.

## Forbidden Scope

- Do not start Set B/C.
- Do not start Plan 4.
- Do not push.
- Do not merge.
- Do not touch SpiritFlix, media, or Jellyfin.
- Do not modify the model contract unless a fresh failure proves a tiny diagnostic/report correction is required.
- Do not loosen validation.
- Do not accept zero-source research as `PASS`.
- Do not fabricate sources.
- Do not use stale cached sources as live proof.
- Do not use `git add .`.
