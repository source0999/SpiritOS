# Campaign 0 Segment 0D Runtime Identity Checkpoint - 2026-07-26

## Status

`GREEN_WITH_NON_BLOCKING_CAVEAT`

## Isolated Runtime Identity

- Worktree: `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725`
- Branch: `codex/source-proxy-campaign-0-authoritative-base-20260725`
- Runtime source commit: `271c9018853ff69916bf16cf578afacebae1dd20`
- Runtime tree: `a8cee5f836764f0d10d65a7129d0237d4aab503c`
- Isolated port: `8897`
- First PID: `560829`
- Restart PID: `563629`
- Process CWD: `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725`
- Python executable: `/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python`
- Route count: `172`
- Route digest: `e9ec1931f64c22e82465478fb3a0a9052d8d2fc4a1602e74ce54fc1b0dffdec7`
- Config digest: `f2631f803d42eac232f87b5c96db05388462421e3ada8cd09b499bf43d5982f9`
- Dependency digest: `4f2840a7c1e2835182b5386a917dc8a2dafc25cb3ec8e3110203e2c1ab8b975c`
- Model inventory digest: `48a6077dab18fa78f5dbced797c361e942920bc67a81235f6ad9879de9986707`

## Tests

Passed:

- Fresh isolated startup.
- Root health check.
- Route-surface verification.
- Runtime identity verification.
- Configuration digest verification.
- Dependency/environment digest verification.
- Model inventory verification.
- Wrong-checkout rejection.
- Dirty-source rejection.
- Stale-process detection.
- Controlled restart.
- Post-restart identity re-verification.
- Daily runtime unchanged.

Non-blocking caveat:

- `/healthcheck` returns `503` in the isolated runtime because GPU VRAM metrics collection reports an NVIDIA NVML/RM version mismatch. The runtime root endpoint, OpenAPI route surface, process identity, and restart identity are healthy. This is recorded as a healthcheck metrics caveat, not as source/runtime identity drift.

## Evidence Paths

- First runtime receipt: `/tmp/campaign0-runtime-segment0d-20260726T000347Z/evidence/segment0d-runtime-identity.json`
- First runtime tests: `/tmp/campaign0-runtime-segment0d-20260726T000347Z/evidence/segment0d-tests.json`
- First startup log: `/tmp/campaign0-runtime-segment0d-20260726T000347Z/logs/uvicorn-startup.log`
- Restart runtime receipt: `/tmp/campaign0-runtime-segment0d-restart-20260726T000749Z/evidence/segment0d-runtime-identity.json`
- Restart runtime tests: `/tmp/campaign0-runtime-segment0d-restart-20260726T000749Z/evidence/segment0d-tests.json`
- Restart startup log: `/tmp/campaign0-runtime-segment0d-restart-20260726T000749Z/logs/uvicorn-startup.log`

## Daily Runtime

Daily runtime remained separate and unchanged:

- Daily PID: `3406614`
- Daily CWD: `/home/source/SpiritOS`
- Daily command: `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile /home/source/SpiritOS/certificates/spirit-dev.pem --ssl-keyfile /home/source/SpiritOS/certificates/spirit-dev-key.pem`

## Readiness For 0E

Proceed to Segment 0E automatically.
