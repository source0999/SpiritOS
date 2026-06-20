# Stage 6 Verifier-Driven Repair Loop

Result: `INTEGRATED_LIVE`.

Implementation:
- `run_plan3_verifier_driven_repair`
- repair writes only inside a provided disposable workspace
- repair is triggered by verifier failure
- final result requires re-verification

Proof:
- task: `task_938dad74a7d9`
- trace: `trace_31500112a69a42bf`
- failing verifier: file contained `<main>broken</main>`
- repair action: wrote `<main>fixed</main>` to disposable `proof.html`
- repair_attempt_count: 1
- re-verification: passed
- final status: `verified`
- verification_result: `VERIFIED`
- repair_result: `repair_applied_and_reverified`
- causal events include: `verification`, `repair`

Raw evidence:
- `/home/source/spiritos-evidence/plan-03/plan3-disposable-proof.json`
