# Campaign 0 Segment 0E Blocked Evidence Summary - 2026-07-26

## Status

`C0_CONTINUATION_BLOCKED_BUILD_REGRESSION`

## Source

- Worktree: `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725`
- Branch: `codex/source-proxy-campaign-0-authoritative-base-20260725`
- Current source commit: `271c9018853ff69916bf16cf578afacebae1dd20`
- Current source tree: `a8cee5f836764f0d10d65a7129d0237d4aab503c`

## Completed Proof

Segment 0D completed as `GREEN_WITH_NON_BLOCKING_CAVEAT`:

- Isolated runtime started on port `8897`.
- Process CWD matched the Campaign 0 worktree.
- Runtime source HEAD matched `271c9018853ff69916bf16cf578afacebae1dd20`.
- Route digest, config digest, dependency digest, and model inventory digest were recorded.
- Wrong-checkout, dirty-source, stale-process, controlled restart, and post-restart identity checks passed.
- Daily runtime remained separate on port `8787`, CWD `/home/source/SpiritOS`.

0D caveat:

- Isolated `/healthcheck` returned `503` because GPU VRAM metrics collection reported an NVIDIA NVML/RM mismatch. Root health and OpenAPI were healthy.

Segment 0E partial proof completed:

- First-run isolated runtime started from fresh state namespace.
- First-run backend regression passed.
- First-run frontend regression passed.
- First-run LumaCart focused regression passed.
- Clean-rerun isolated runtime started from a new state namespace.
- Clean-rerun backend regression passed.
- Clean-rerun frontend regression passed.
- Clean-rerun typecheck passed.
- Clean-rerun LumaCart focused regression passed.
- Rollback runtime started from temporary rollback worktree at `6d58031cfcf8e9f1f8f0b156a83fbd4163ec25af`.
- Roll-forward runtime restored current Campaign 0 head `271c9018853ff69916bf16cf578afacebae1dd20`.
- Rollback and roll-forward receipts were preserved.

## Blocker

`npm run build` is not reliable enough for Campaign 0 acceptance.

Observed build failures during Segment 0E:

- First-run build while isolated runtime was active: `Segmentation fault (core dumped)`.
- First-run build after stopping isolated runtime: `SyntaxError: Unexpected token '('`.
- Clean direct build after removing `.next`: reached page-data collection, then `Segmentation fault (core dumped)`.
- Final clean build with no isolated runtime active after removing `.next` and Python caches: `Segmentation fault (core dumped)`.

`npm run typecheck` passed after generated `.next` output was removed, so the remaining blocker is isolated to the Next production build lane, not Python regressions, LumaCart, route identity, or TypeScript typecheck.

## Evidence Index

- Segment 0D first runtime: `/tmp/campaign0-runtime-segment0d-20260726T000347Z/`
- Segment 0D restart runtime: `/tmp/campaign0-runtime-segment0d-restart-20260726T000749Z/`
- Segment 0E first-run runtime: `/tmp/campaign0-runtime-segment0e-first-20260726T001002Z/`
- Segment 0E clean-rerun runtime: `/tmp/campaign0-runtime-segment0e-clean-rerun-20260726T001531Z/`
- Segment 0E rollback runtime: `/tmp/campaign0-runtime-segment0e-rollback-20260726T001736Z/`
- Segment 0E roll-forward runtime: `/tmp/campaign0-runtime-segment0e-rollforward-20260726T001744Z/`

Committed evidence copies live under:

- `docs/campaign-0-authoritative-repository-runtime-truth/segment-0d-0e-runtime-evidence-20260726/`

## Daily Runtime

Daily runtime was not stopped or replaced.

- Daily PID observed: `3406614`
- Daily CWD: `/home/source/SpiritOS`
- Daily command: `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile /home/source/SpiritOS/certificates/spirit-dev.pem --ssl-keyfile /home/source/SpiritOS/certificates/spirit-dev-key.pem`

## Acceptance

Campaign 0 is not ready for operator acceptance until the required build lane has a stable passing receipt from the Campaign 0 worktree.
