# Baseline

Generated from `raw/00-baseline.txt`.

## Repo

- Host: `source-server`
- Path: `/home/source/SpiritOS`
- Branch: `master`
- Latest HEAD: `179e60ea Document cleanup finish readiness`

## Git state

- Staged files at baseline: `0`
- Dirty tracked files: existing unrelated SpiritFlix/media/package/runtime helper work
- Dirty `source_proxy/` files at baseline: none visible in `git status --short --untracked-files=normal`
- Evidence folder: `docs/evidence/source-proxy-runtime-health-status-patch-20260618/`

Because there were no staged files at baseline, this patch can continue. The broad dirty tree remains out of scope and must not be staged.

## Prior source-of-truth

The return checkpoint recommended exactly this patch: runtime health/status/liveness truth. The checkpoint also established that Source Proxy, Next, Ollama, and watchers were reachable, no fresh OOM was found, and dirty-tree authority remained `PARTIAL-GO` because non-Source-Proxy package/config/runtime helper files were dirty.
