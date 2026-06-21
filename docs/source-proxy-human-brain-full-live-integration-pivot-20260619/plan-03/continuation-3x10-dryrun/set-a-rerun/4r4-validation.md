# Stage 4R4 Validation

- py_compile: run separately by operator command sequence; expected PASS before final verdict.
- adversarial selftest: PASS
- structured packet selftest: PASS
- summary JSON parse: PASS
- Set A rerun JSON shape validation: PASS
- Set A 4R4 requested acceptance validation: FAIL
- JSON shape validation errors: none
- acceptance validation errors: ['Set A pass_count is 7, expected 10', 'A2: not PASS after 4R4', 'A5: not PASS after 4R4', 'A5: research_materially_changed_output false after 4R4', 'A5: decision_packet_validated missing/false', 'A9: not PASS after 4R4', 'A9: research_materially_changed_output false after 4R4', 'A9: decision_packet_validated missing/false']
- Plan 3 operator: PASS when run explicitly after the runner; embedded runner operator check timed out after 120s.
- focused tests: `_stage4r_runner.py` py_compile PASS.
- typecheck: not run; no frontend/runtime TypeScript touched.
