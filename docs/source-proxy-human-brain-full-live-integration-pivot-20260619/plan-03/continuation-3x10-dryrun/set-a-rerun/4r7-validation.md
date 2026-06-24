# Stage 4R7 Validation

- py_compile: run separately by operator command sequence; expected PASS before final verdict.
- adversarial selftest: PASS
- structured packet selftest: PASS
- roundtrip selftest: PASS
- structured output selftest: PASS
- model escalation selftest: PASS
- summary JSON parse: PASS
- Set A rerun JSON shape validation: PASS
- Set A 4R7 requested acceptance validation: FAIL
- JSON shape validation errors: none
- acceptance validation errors: ['Set A pass_count is 3, expected 9 with A9 blocked or 10']
- Plan 3 operator: FAIL
- focused tests: `_stage4r_runner.py` py_compile.
- typecheck: not run; no frontend/runtime TypeScript touched.
