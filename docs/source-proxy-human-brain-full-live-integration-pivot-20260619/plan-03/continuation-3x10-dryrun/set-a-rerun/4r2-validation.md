# Stage 4R2 Validation

- py_compile: PASS
- adversarial selftest: PASS
- summary JSON parse: PASS
- Set A 4R2 requested acceptance validation: FAIL
- JSON shape validation: PASS
- validation errors:
  - Set A pass_count is 7, expected 10
  - A2: not PASS after 4R2
  - A2: research_materially_changed_output false after 4R2
  - A5: not PASS after 4R2
  - A5: research_materially_changed_output false after 4R2
  - A9: not PASS after 4R2
  - A9: research_materially_changed_output false after 4R2
- Plan 3 operator: PASS
- focused tests: `_stage4r_runner.py` py_compile.
- typecheck: not run; no frontend/runtime TypeScript touched.
