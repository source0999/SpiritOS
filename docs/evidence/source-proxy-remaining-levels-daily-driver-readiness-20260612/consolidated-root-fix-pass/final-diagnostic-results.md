# Final Diagnostic Results

Status: NO-GO

## Results

| Set | Old result | New result in this pass | Verdict |
|---|---:|---:|---|
| random 10 | 7/10 PASS, 3 FAIL | Not rerun after 10d stop rule | NO-GO |
| random 10b | 5/10 PASS, 5 FAIL | Not rerun after 10d stop rule | NO-GO |
| random 10c | 4/10 PASS, 6 FAIL | Not rerun after 10d stop rule | NO-GO |
| random 10d | Fresh set | 6/10 PASS, 4 FAIL | NO-GO |

Fresh 10d evidence:

- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d.html`
- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-results.json`
- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-browser-behavior-results.json`
- `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-post-behavior-repair-summary.json`

## Fresh 10d Counts

- Behavior PASS: 6
- Behavior FAIL: 4
- Threshold: 8/10 behavior PASS
- Repair attempts: 1
- Handoff before repair: 2

## Remaining Failure Buckets

- `01-build-me-a-snack-break-countdown`: behavior failed; repair handed off because probe metadata was incomplete.
- `03-make-a-day-night-color-flipper`: missing preview / not eligible for behavior repair.
- `09-make-a-login-safety-gauge`: behavior failed; repair handed off because probe metadata was incomplete.
- `10-make-a-scribble-sketch-pad`: repair attempted once; model returned free-floating code without a path/action.

## Anti-Cheat Recheck Verdict

CONCERN.

No evidence of deterministic scaffold, fallback, backend-created content, real app touch, cloud/API fallback, missing transcript, missing behavior evidence, hidden second repair, or failed behavior marked PASS was found in 10d. The verdict is still CONCERN, not CLEAN, because 10d remains below threshold and several behavior failures remain.

## Level 3 Status

NO-GO.

Do not claim Level 3 GREEN. Do not promote Level 4 or higher.
