# Set A Rerun Test Results

- summary JSON parse: PASS
- adversarial selftest: PASS
- structured packet selftest: PASS
- roundtrip selftest: PASS
- structured output selftest: PASS
- model escalation selftest: PASS
- Set A rerun JSON shape validation: PASS
- Set A 4R7 requested acceptance validation: FAIL
- JSON shape validation errors: none
- acceptance validation errors: ['A2: not PASS after 4R7', 'A5: not PASS after 4R7', 'A5: research_materially_changed_output false after 4R7', 'A9: expected PASS or BLOCKED_ENV, got NEEDS_FIX']
- Plan 3 operator: FAIL
- focused tests: `_stage4r_runner.py` py_compile PASS.
- typecheck: not run; no frontend touched.

```text
Plan 3/6 operator check


TimeoutExpired after 120s
```
