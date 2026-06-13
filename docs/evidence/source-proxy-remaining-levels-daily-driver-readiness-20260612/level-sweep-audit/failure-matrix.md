# Failure Matrix

Status labels used here are sub-check labels only. They do not promote Level 3 or any higher level.

| Level/gate | Check attempted | Status | Evidence path | Root failure class | Failure type | Patch required before promotion | Britton approval required |
|---|---|---|---|---|---|---|---|
| Level 3 Phase 3A | Read existing closeout/operator receipt | PASS_SUBCHECK | `level-3/operator-receipt.md` | approval boundary mostly proven for Phase 3A | safety gate/reporting | Yes, for full Level 3 continuation | Yes |
| Level 3 Task B | Read inventory only; did not run preview | BLOCKED | `level-3/manual-review-packet.md` | level dependency and explicit approval required | safety gate | Unknown until run | Yes |
| Level 3 Phase 3B | Read phase plan only; did not run diff preview | BLOCKED | `level-3/phase-plan.md` | level dependency violated if run now | safety gate | Yes | Yes |
| Level 3 Phase 3C | Read phase plan only; did not apply/revert mutation | BLOCKED | `level-3/phase-plan.md` | requires real mutation and revert proof | safety gate | Yes | Yes |
| Disposable random 10 | Read existing repaired rerun results | NO-GO | `../../source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-results.json` | model-authored UI lacks real behavior; repair output targetless | model capability / repair loop | Yes | Yes |
| Disposable random 10b | Read existing repaired rerun results | NO-GO | `../../source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10b-results.json` | repair output targetless; missing behavior contract/probe metadata | repair loop / behavior probe / contract parser | Yes | Yes |
| Disposable random 10c | Read existing fresh repaired run results | NO-GO | `../../source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10c-results.json` | behavior contract gaps; repair metadata gaps; static control behavior | behavior probe / contract parser / model capability | Yes | Yes |
| Level 4 context/planner traceability | Read relevant planner/intake/contract files only | BLOCKED_BY_LEVEL_3_NO_GO | `source_proxy/decision/task_spec_intake.py`, `source_proxy/decision/artifact_behavior_contract.py` | planner criteria not fully traced into final behavior proof | context/planner gap | Yes | Yes |
| Level 5 verifier critic | Read verifier/model-lane files; no live verifier | VERIFIER_PREVIEW_ONLY | `source_proxy/decision/verifier_lane.py`, `source_proxy/decision/model_lanes.py` | verifier lane not active as independent critic | verifier gap | Yes | Yes |
| Level 6 Cartographer/model routing | Read routing preview files only | BLOCKED_BY_LEVEL_3_NO_GO | `source_proxy/decision/cartographer_routing.py` | routing ownership preview-only; sidecars not live | context/planner gap / safety gate | Yes | Yes |
| Level 7 autonomy | No check run | SKIPPED | `baseline-check.md` | autonomy forbidden; prior gates red | level dependency violated | Yes | Yes |
| Level 8 daily-driver activation/expanded benchmark | No check run | SKIPPED | `baseline-check.md` | daily-driver activation and benchmark expansion forbidden | safety gate / reporting gap | Yes | Yes |

## Failure Buckets From Existing Random Evidence

| Evidence set | Behavior failures | Bucket | Count |
|---|---:|---|---:|
| random 10 | 3 | repair rejected: free-floating code without path/action | 3 |
| random 10b | 5 | repair rejected: free-floating code without path/action | 3 |
| random 10b | 5 | repair handoff: missing behavior contract/probe metadata | 2 |
| random 10c | 6 | repair rejected: free-floating code without path/action | 2 |
| random 10c | 6 | repair handoff: missing behavior contract/probe metadata | 3 |
| random 10c | 6 | theme/control did not change computed state | 1 |

## Broad Root Classes Evaluated

| Root class | Evidence status | Notes |
|---|---|---|
| model-authored UI lacks real behavior | CONFIRMED | All three random sets contain browser-openable artifacts with failing behavior probes. |
| repair output rejected as free-floating/no path/action | CONFIRMED | 8 failed rows across random 10/10b/10c ended in this bucket. |
| behavior contract missing or stale despite behavior probe evidence | CONFIRMED | 5 failed rows hand off before repair because behavior contract/probe metadata is missing. |
| behavior probe metadata not passed into repair packet | CONFIRMED | Same handoff bucket shows repair packet lacks needed metadata for some rows. |
| static artifact vs interactive artifact classification ambiguity | CONCERN | Some prompts route/open but fail interactive behavior; classification alone is insufficient proof. |
| intake synonym gaps for messy human wording | CONCERN | Random 10c includes wording that produced lower reliability; exact intake miss rate was not separately rerun in this audit. |
| final verdict/reason code mismatch | IMPROVED_WITH_RISK | Refreshed result JSONs no longer contain stale `behavior_required_but_unverified`, but continued reporting discipline is required. |
| verifier lane not active as independent critic | CONFIRMED | Verifier files are preview/advisory only and `model_calls_enabled` is false. |
| planner criteria not traced into final behavior proof | CONCERN | Contracts exist, but failed repair packets prove criteria/probe metadata does not always arrive. |
| anti-cheat/scaffold/fallback guard incomplete or unclear | CONCERN | Current evidence reports no scaffold/fallback flags, but absence of deeper code-level provenance proof leaves unknowns. |
| reporting surface hides or softens failure | IMPROVED_WITH_RISK | HTML reports now show failure buckets; older hub wording still says Phase 3A fixed/review without random-set NO-GO context. |
| real-repo mutation safety unresolved | CONFIRMED | Level 3 Task B/3B/3C remain unrun and require approval. |
| level dependency violated | BLOCKED | Higher levels cannot promote while Level 3 is red. |
