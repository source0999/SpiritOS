# Campaign 1 Test Profiles

Schema: `spiritos-campaign-1-test-profiles/v1`

The canonical registry is [campaign-1-test-profiles.json](campaign-1-test-profiles.json). The table reconciles its profile IDs to the accepted receipt; it does not expand any profile's claim ceiling. All paths are redacted references and contain no credential values.

| Profile ID | Command / suite | Latest result | Source / receipt | Freshness | Claim ceiling |
| --- | --- | --- | --- | --- | --- |
| `source-proxy-authority` | `PYTHONPATH=. .venv-campaign1/bin/python -m pytest source_proxy/tests/test_campaign_approval_authority.py source_proxy/tests/test_long_running_tasks.py -q` | **85 passed** | source `e35f8a11`; final closeout receipt | 2026-07-15 | task lifecycle only |
| `coding-backend` | `npm run test:coding-regression` | **133 passed** | source `e35f8a11`; final closeout receipt | 2026-07-15 | coding backend only |
| `coding-frontend` | `npm run test:coding-frontend-regression` | **193 passed** | source `e35f8a11`; final closeout receipt | 2026-07-15 | canonical production coding frontend only |
| `canonical-shell` | `npm exec vitest run src/components/coding/__tests__/coding-cockpit-shell.test.tsx` | **61 passed** | source `e35f8a11`; final closeout receipt | 2026-07-15 | canonical shell only |
| `cartographer-api` | `PYTHONPATH=. .venv-campaign1/bin/python -m pytest source_proxy/tests/test_cartographer_api.py -q` | **263 passed** | source `e35f8a11`; final closeout receipt | 2026-07-15 | proposal boundary only |
| `design-route` | `npm exec vitest run src/app/v1/operator/design-approval/__tests__/route.test.ts` | **3 passed** | source `e35f8a11`; final closeout receipt | 2026-07-15 | Design route only |
| `spiritflix-operator` | `PYTHONPATH=. .venv-campaign1/bin/python -m pytest source_proxy/tests/test_spiritflix_admin_authority.py source_proxy/tests/test_operator_session_assertion.py -q` | **3 passed** | source `e35f8a11`; final closeout receipt | 2026-07-15 | admin issuance only |
| `build` | `NODE_OPTIONS=--max-old-space-size=4096 npm run build` | pass | source `e35f8a11`; final closeout receipt | 2026-07-15 | build only |
| `continuity` | `npm run campaign-1:validate-continuity` | pass | source `e35f8a11`; final closeout receipt | 2026-07-15 | continuity only |
| `authority` | `npm run campaign-1:validate-authority` | pass | source `e35f8a11`; final closeout receipt | 2026-07-15 | static authority only |
| `test-profile-registry` | `npm run campaign-1:validate-test-profiles` | pass | source `e35f8a11`; final closeout receipt | 2026-07-15 | registry only |
| `target-adapter` | focused target-adapter parser and authority tests | pass | `630b6632`; final closeout receipt | 2026-07-15 | canonical target identity only |
| `evidence-validator` | `python3 scripts/validate-campaign-1-evidence.py` | pass | final closeout receipt | 2026-07-15 | redacted evidence index only |
| `secret-scan` | scoped changed-file secret scan | pass | final closeout receipt | 2026-07-15 | disclosure detection only |
| `prompt1-browser` | `node scripts/run-coding-e2e-loop.mjs --fixture-state=missing` | pass / authoritative GO | `docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json` | 2026-07-15T23:36:28Z | authenticated Prompt 1 lifecycle only |
| `anti-cheat` | accepted E2E anti-cheat stage | pass | `docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json` | 2026-07-15T23:36:28Z | harness integrity only |
| `undo-reset-rerun` | accepted E2E manifest Undo/reset, clean baseline, and clean rerun stages | pass | `docs/evidence/e2e-loop/2026-07-15T23-36-28-866Z/result.json` | 2026-07-15T23:36:28Z | lifecycle recovery only |
| `labs-command-center` | `npm exec vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx` | not an acceptance gate | source `007bb4ea` | 2026-07-15 | labs-only; excluded from Campaign production acceptance |

Historical counts of 83, 131, 258, and Design 32 are superseded runs and are not current acceptance claims. A failed, skipped, stale, or narrower-than-required mandatory profile cannot claim Campaign GO. The accepted `GO_CAMPAIGN_1_COMPLETE` verdict does not start Campaign 2; Campaign 2 is not started.
