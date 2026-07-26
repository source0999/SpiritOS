# Campaign 1 Operator Review Packet

Status: `C1_CAMPAIGN_READY_FOR_OPERATOR_ACCEPTANCE`

Campaign 1 implements Source Proxy terminal truth and legacy-path lockdown.
It was created from accepted Campaign 0 parent
`bbe195111e202afe8610cd02adf528f0e92857c7`, whose authorization token is
`CAMPAIGN_0_AUTHORITATIVE_REPOSITORY_RUNTIME_TRUTH_ACCEPTED`.

## Outcome

- A versioned terminal vocabulary and sealed transition payload now exist.
- Only canonical finalization can produce `completed_verified`.
- Fallback/pre-Coder paths preserve `not_attempted` or `blocked_environment`.
- Verification failure and cancellation are sealed with provenance.
- Legacy `/advance` remains available only as a pending-finalization compatibility path.
- Extended-lane recovery remains attributed advisory evidence and cannot mutate canonical task status.
- No daily runtime process or checkout was modified.

## Validation

| Command | Result |
| --- | --- |
| `.venv-campaign1/bin/python -m pytest -q source_proxy/tests/test_coding_orchestrator.py` | `44 passed` |
| `.venv-campaign1/bin/python -m pytest -q source_proxy/tests/test_coding_proof.py` | `56 passed` |
| `.venv-campaign1/bin/python -m pytest -q source_proxy/tests/test_long_running_tasks.py` | `81 passed` |
| `npm run test:coding-regression` | `139 passed, 46 subtests passed` |
| `npm run test:coding-frontend-regression` | `193 passed` |
| `npm run typecheck` | passed |
| `CI=1 NEXT_TELEMETRY_DISABLED=1 npm run build` | passed |

The Campaign 1 worktree-local `.venv-campaign1` and `node_modules` bindings
are ignored setup links. The latter points to the accepted Campaign 0 worktree
dependency tree only so the existing TypeScript preview verifier can resolve
its parser; it is not committed product state.

## Failure injection and regressions

| Scenario | Observed disposition |
| --- | --- |
| Report asks to upgrade a weaker producer result | `report_upgrade_rejected` |
| Verified completion lacks artifact or verifier receipt | rejected before state persistence |
| Late success after verifier failure | sealed-terminal transition rejected |
| Fallback blocks before Coder dispatch | `not_attempted` with no implied Coder invocation |
| Fallback/model failure | `blocked_environment` with invocation lineage |
| Post-apply checks without terminal proof | `coding_production_proof_not_terminal` |
| Operator cancellation | `cancelled` with `operator_cancelled` provenance |
| Legacy debugger return code | `verification_passed_pending_participants` |
| Extended-lane `BLOCKED_ENV` | advisory receipt; core task state unchanged |

## Anti-overfitting scan

The Campaign 1 production diff was scanned for BT labels, LumaCart/fixture
coupling, benchmark/scorer code, expected-answer fragments, private-oracle
references, Campaign 3.5-only behavior, and commit `6616846d`. There were no
matches in the Campaign 1 additions. Existing unrelated fixture and Campaign
3.5 references in `long_running.py` and `orchestrator.py` predate this diff and
were not copied or widened.

## Remaining boundaries

BT05 and BT06 functional success is intentionally not claimed: Campaign 1
only makes their no-attempt and verification-failure outcomes truthful.
Campaign 2 has not begun. It will build the authoritative full-pipeline
benchmark, require causal participation from each applicable layer, and
replace the Basic Backend 10 acceptance contract only after operator acceptance
of Campaign 1.

## Rollback

The rollback parent is `bbe195111e202afe8610cd02adf528f0e92857c7`. Revert the
Campaign 1 commit on its isolated branch; do not touch the dirty daily runtime
or merge this work without separate authorization.
