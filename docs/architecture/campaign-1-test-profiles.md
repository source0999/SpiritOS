# Campaign 1 Test Profiles

Schema: `spiritos-campaign-1-test-profiles/v1`

All commands run from `/home/source/SpiritOS-campaign-1-20260712`. Profiles inherit the Campaign-only mutable-root rule and never write protected product worktrees.

| Profile | Command / receipt | Environment and secret assumptions | Latest result | Claim ceiling |
| --- | --- | --- | --- | --- |
| authority contracts | `PYTHONPATH=. ...pytest source_proxy/tests/test_campaign_approval_authority.py -q` | Campaign Approval Authority state; no credential output | 12 passed | Cartographer/coding authority boundaries only |
| complete Cartographer API | `PYTHONPATH=. ...pytest source_proxy/tests/test_cartographer_api.py -q` | Source Proxy test app; legacy mutation assertions remain present | **36 failed, 231 passed, 4 subtests passed** | mandatory failure; legacy mutable callers require proposal-only migration |
| authority dependency enforcement | `npm run campaign-1:validate-authority` | source tree only | pass | static enforcement only |
| continuity | `npm run campaign-1:validate-continuity` | pinned protected worktrees readable | required after atomic checkpoint | continuity only |
| Design production route | `npx vitest run src/app/v1/operator/design-approval/__tests__/route.test.ts src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts src/app/v1/coding/design-studio/preview/__tests__/route.test.ts` | Node/Vitest; mocked route seams for unit coverage | 32 passed | Design unit contract only |
| Design evidence negatives | `node scripts/coding/test-validate-design-studio-receipts.mjs` | static fixtures only | 9 rejected fixtures passed | validator-negative coverage only |
| coding backend regression | `npm run test:coding-regression` | Campaign `.venv-campaign1`; 10 existing async-mock warnings | 131 passed | coding regression only |
| coding frontend regression | `npm run test:coding-frontend-regression` | Node/Vitest; existing React act warnings | 269 passed | coding frontend only |
| Source Proxy authority/task | `PYTHONPATH=. .venv-campaign1/bin/python -m pytest source_proxy/tests/test_campaign_approval_authority.py source_proxy/tests/test_long_running_tasks.py -q` | Campaign isolated Authority state | 83 passed | source task lifecycle only |
| Prompt 1 browser lifecycle | `node scripts/run-coding-e2e-loop.mjs --fixture-state=missing` | isolated HTTPS lane, operator E2E secret read server-side only | prior receipt: PASS | Prompt 1 only |
| canonical shell | canonical shell/route suites | local operator E2E session | prior receipt: 61 shell + 5 operator/session | shell only |
| authenticated SpiritFlix desktop/Fold/player | authenticated browser receipts above | dedicated least-privilege E2E identity; SPKI-only browser policy | prior receipt: pass | no-reversion browser behavior only; AR-001 remains blocked |
| ordinary SpiritFlix server-owned BFF session | session/client/BFF/admin-library/frontend plus admin baseline routes | no real credential output; normal session is opaque | 10 Vitest files, **64 passed** | ordinary-session migration only; no administrative mutation authority |
| build | `npm run build` | Campaign `.next`; no protected-service restart | pass in 166.8 s | build only |

Mandatory profile rule: a failed, skipped, stale, or narrower-than-required profile cannot claim Campaign GO. The current `NO_GO_VERIFICATION_FAILURE` ceiling remains until AR-001 is migrated and the final Cartographer/Design evidence profiles are completed.
