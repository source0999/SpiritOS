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
- acceptance validation errors: ['A2: not PASS after 4R7', 'A2: research_materially_changed_output false after 4R7', 'A2: decision_packet_validated missing/false', 'A5: not PASS after 4R7', 'A5: research_materially_changed_output false after 4R7', 'A5: decision_packet_validated missing/false', 'A9: expected PASS or BLOCKED_ENV, got NEEDS_FIX']
- Plan 3 operator: PASS
- focused tests: `_stage4r_runner.py` py_compile.
- typecheck: not run; no frontend/runtime TypeScript touched.
