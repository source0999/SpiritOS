# Self-Check Matrix

| Patch | Expected fix | Files changed | Tests run | Manual check | Evidence path | Status |
|---|---|---|---|---|---|---|
| 1 | Preserve contract/probe metadata and derive repair packets from failed probe evidence when safe | `artifact_repair_contract.py`, `test_artifact_repair_loop.py` | 34 focused tests, py_compile, diff check | Before/after packet inspected | `patch-1-contract-probe-metadata.md` | PASS_SUBCHECK |
| 2 | Accept valid model-authored path-bound `.html/.css/.js` repair output and reject unsafe/free-floating output | `artifact_repair_loop.py`, `tool_action_executor.py`, `test_artifact_repair_loop.py` | 44 focused tests, 1 skipped, py_compile, diff check | Accepted/rejected examples inspected | `patch-2-path-bound-repair-output.md` | PASS_SUBCHECK |
| 3 | Trace planner criteria through final verdict rows | `artifact_final_verdict.py`, `artifact_retest_result.py`, tests | 28 focused tests, py_compile, diff check | Sample row inspected | `patch-3-planner-to-verdict-trace.md` | PASS_SUBCHECK |
| 4 | Add generic visible-state mutation criteria without templates | `artifact_behavior_contract.py`, tests | 40 focused tests, 1 skipped, py_compile, diff check | Static mockup allowance checked | `patch-4-generic-interactive-reliability.md` | PASS_SUBCHECK |
| 5 | Keep verifier preview no-glaze and evidence-blocking | `verifier_lane.py`, tests | 24 focused tests, py_compile, diff check | Failed-browser preview packet inspected | `patch-5-verifier-no-glaze-preview.md` | PASS_SUBCHECK |

Final diagnostic: fresh 10d is 6/10 behavior PASS, so Level 3 remains NO-GO.
