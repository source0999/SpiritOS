# Anti-Cheat Recheck

Status: CONCERN

## Sets Compared

| Set | Behavior PASS | Scaffold | Fallback | Backend content | Real app touched | Cloud/API fallback | Failed behavior marked PASS | Missing transcript/probe | Hidden second repair |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random 10 | 7/10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| random 10b | 5/10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| random 10c | 4/10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| random 10d | 6/10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

10d used one bounded repair attempt and no row exceeded one repair attempt.

## Verdict

CONCERN.

The evidence does not show scaffold/fallback/backend-created content or failed behavior marked PASS, but 10d remains below the 8/10 behavior threshold. CLEAN is not supported.
