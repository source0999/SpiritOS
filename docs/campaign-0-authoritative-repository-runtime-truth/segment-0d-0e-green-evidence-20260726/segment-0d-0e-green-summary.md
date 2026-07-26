# Campaign 0 Segment 0D/0E Green Evidence

Date: 2026-07-26

Scope: Source Proxy Campaign 0 only. Campaign 1 was not started.

## Result

Segment 0D and Segment 0E are ready for Campaign 0 operator acceptance.

Current authoritative Campaign 0 checkout:

- Worktree: `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725`
- Branch: `codex/source-proxy-campaign-0-authoritative-base-20260725`
- Head: `ab68745cc9e5dccf1e3d67024e7a6a1c911cb3e8`
- Tree: `cad80959fc2e10e6ff64c1f4b297169c49b70dc3`
- Scoped status during receipts: clean
- Local/remote branch match during current-checkout receipts: true

## Segment 0D Runtime Identity

The isolated Campaign 0 runtime was started on port 8897 from the authoritative Campaign 0 checkout, then stopped and restarted from the same checkout.

- First runtime receipt: `segment0d-first-runtime-identity.json`
- First verification receipt: `segment0d-first-tests.json`
- Restart runtime receipt: `segment0d-restart-runtime-identity.json`
- Restart verification receipt: `segment0d-restart-tests.json`
- OpenAPI route count: 172
- OpenAPI route digest: `e9ec1931f64c22e82465478fb3a0a9052d8d2fc4a1602e74ce54fc1b0dffdec7`
- Configuration digest: `f2631f803d42eac232f87b5c96db05388462421e3ada8cd09b499bf43d5982f9`
- Dependency digest: `09492e174b3d70d41cf9ae147387d97c6e77c6b962952cd54be12b8a52216280`

Verification status for both 0D starts: `GREEN_WITH_NON_BLOCKING_CAVEAT`.

The caveat is limited to `/healthcheck` returning 503 because Dell GPU metrics report an NVML/RM version mismatch. The root service endpoint and OpenAPI route inventory were healthy, process identity matched the Campaign 0 checkout, and the daily runtime on port 8787 remained untouched.

## Segment 0E Fresh-State Proof

Segment 0E was run twice from isolated runtime state:

- First run runtime receipt: `segment0e-first-runtime-identity.json`
- Clean rerun runtime receipt: `segment0e-clean-rerun-runtime-identity.json`

Both runs passed the focused proof commands with exit status 0:

- `npm run test:coding-regression`
- `npm run test:coding-frontend-regression`
- `npm run typecheck`
- `CI=1 NEXT_TELEMETRY_DISABLED=1 npm run build`
- LumaCart focused pytest

The current checkout uses a physical ignored `node_modules` directory at `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725/node_modules`, replacing the earlier shared live symlink into the daily worktree. This corrected the build lane while leaving the daily runtime and daily worktree unchanged.

## Rollback And Roll-Forward

Rollback proof:

- Worktree: `/tmp/campaign0-rollback-worktree-6d58031c-branch-clean-20260726T003857Z`
- Temporary branch: `codex/campaign0-rollback-proof-6d58031c-clean-20260726T003857Z`
- Head: `6d58031cfcf8e9f1f8f0b156a83fbd4163ec25af`
- Scoped status: clean
- Runtime receipt: `segment0e-rollback-clean-runtime-identity.json`

Roll-forward proof:

- Worktree: `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725`
- Branch: `codex/source-proxy-campaign-0-authoritative-base-20260725`
- Head: `ab68745cc9e5dccf1e3d67024e7a6a1c911cb3e8`
- Scoped status: clean
- Runtime receipt: `segment0e-rollforward-runtime-identity.json`

The rollback receipt has `local_remote_match: false` by design because it runs from a temporary rollback branch at the earlier accepted commit while the remote authoritative branch remains at the current Campaign 0 head. Process identity still matched the rollback worktree, and scoped status was clean.

## Daily Runtime

Daily Source Proxy runtime was observed and left unchanged:

- Port: 8787
- PID: 3406614
- CWD: `/home/source/SpiritOS`
- Command: `/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile /home/source/SpiritOS/certificates/spirit-dev.pem --ssl-keyfile /home/source/SpiritOS/certificates/spirit-dev-key.pem`

The Campaign 0 proof runtime on port 8897 was stopped after evidence collection.

## Evidence Index

- `campaign0-green-proof-summary.json`
- `segment0d-first-runtime-identity.json`
- `segment0d-first-tests.json`
- `segment0d-restart-runtime-identity.json`
- `segment0d-restart-tests.json`
- `segment0e-first-runtime-identity.json`
- `segment0e-clean-rerun-runtime-identity.json`
- `segment0e-rollback-clean-runtime-identity.json`
- `segment0e-rollforward-runtime-identity.json`
- `commands/first_backend_regression.log`
- `commands/first_frontend_regression.log`
- `commands/first_typecheck.log`
- `commands/first_build.log`
- `commands/first_lumacart_focus.log`
- `commands/clean_backend_regression.log`
- `commands/clean_frontend_regression.log`
- `commands/clean_typecheck.log`
- `commands/clean_build.log`
- `commands/clean_lumacart_focus.log`

Acceptance token:

`C0_SEGMENT_0E_CAMPAIGN_0_READY_FOR_OPERATOR_ACCEPTANCE`
