# Campaign 0 Acceptance Matrix

Date: 2026-07-26

Scope: Source Proxy Campaign 0 acceptance only. This authorizes Campaign 1 and
does not authorize deployment to the dirty daily runtime, Campaign 2, or any
merge to main/master.

Accepted token:

```text
CAMPAIGN_0_AUTHORITATIVE_REPOSITORY_RUNTIME_TRUTH_ACCEPTED
```

## Source Identity

| Check | Observed proof | Status |
|---|---|---|
| Worktree | `/home/source/SpiritOS-source-proxy-campaign-0-authoritative-base-20260725` | PASS |
| Branch | `codex/source-proxy-campaign-0-authoritative-base-20260725` | PASS |
| Accepted head before addendum | `f0994d1e865bd934189ef7ca113f9c2eed0a2395` | PASS |
| Verified source/runtime proof commit | `ab68745c` | PASS |
| Source code unchanged from `ab68745c` through `f0994d1e` | `git diff --name-only ab68745c..HEAD -- source_proxy src scripts package.json package-lock.json next.config.ts tsconfig.json` returned no paths | PASS |
| Worktree-local `.venv-campaign1` binding | Ignored symlink to `/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy` | PASS |
| Daily runtime separation | PID `3406614`, CWD `/home/source/SpiritOS`, port 8787 unchanged | PASS |

## Runtime And Fresh-State Evidence

| Check | Observed proof | Status |
|---|---|---|
| Segment 0D first runtime identity | `segment-0d-0e-green-evidence-20260726/segment0d-first-runtime-identity.json` | PASS_WITH_CAVEAT |
| Segment 0D restart identity | `segment-0d-0e-green-evidence-20260726/segment0d-restart-runtime-identity.json` | PASS_WITH_CAVEAT |
| Segment 0E first run | `segment0e-first-runtime-identity.json` plus command logs | PASS |
| Segment 0E clean rerun | `segment0e-clean-rerun-runtime-identity.json` plus command logs | PASS |
| Rollback proof | Clean temporary rollback branch at `6d58031cfcf8e9f1f8f0b156a83fbd4163ec25af` | PASS |
| Roll-forward proof | Campaign 0 branch returned to current accepted head | PASS |

The repeated caveat is `/healthcheck` returning 503 because Dell GPU metrics
report an NVML/RM version mismatch. Root service and OpenAPI identity were
healthy; this caveat did not modify or involve the daily runtime.

## Reproducibility Fix

| Required condition | Observed proof | Status |
|---|---|---|
| Registered backend command runs from checkout | `npm run test:coding-regression` executed from Campaign 0 checkout | PASS |
| Registered backend command is green | `139 passed, 46 subtests passed in 36.99s`, exit 0 | PASS |
| Exact setup documented | `campaign-0-reproducibility-addendum-20260726.md` | PASS |
| Commands and selected test nodes preserved | `source_proxy/tests/test_coding_regression_pack.py`; no fabricated prior 99/2 selection | PASS |
| Worktree-local environment documented | `.venv-campaign1 -> /home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy` | PASS |
| Symlink not committed | `.venv-campaign1` ignored by git info exclude | PASS |
| Frontend/build lane green | Frontend 193 passed, typecheck exit 0, build exit 0 | PASS |
| Production behavior unchanged | Evidence/docs-only changes after `ab68745c`; reproducibility fix is local symlink plus docs | PASS |

## Conditional Acceptance

All operator-authorized Campaign 0 acceptance conditions are satisfied:

- registered backend regression command runs from the checkout;
- backend regression is green;
- exact setup and commands are documented;
- Campaign 0 worktree can return clean after evidence commit;
- local and remote HEAD are verified as matching after publication;
- no production behavior changed during the reproducibility fix;
- previously verified 0D/0E evidence remains valid;
- no Campaign 0 P0/P1 blocker remains.

Campaign 0 is accepted with:

```text
CAMPAIGN_0_AUTHORITATIVE_REPOSITORY_RUNTIME_TRUTH_ACCEPTED
```
