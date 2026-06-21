# Stage 4R Fix Runner Change

Patched `_stage4r_runner.py` only inside the approved Set A rerun artifact path.

Changes:
- Added `PLAN3_STAGE4R_ONLY` so the fix run can rerun only A2 and A5 while preserving existing A1/A3/A4/A6-A10 records for validation.
- Strengthened the live work-product prompt to require a `Research findings that changed the plan` section with `Finding`, `Source`, and `How it changed the plan` fields.
- Kept `run_current_research_for_task`, raw provider evidence, live Ollama work-product generation, task/readback evidence, same-trace consumer extraction, computed `fake_go_detected`, and grader-derived `final_status`.
- Tightened materiality grading to require explicit structured research-use text and source/domain/title hits in the actual generated output.

No hardcoded A2/A5 final answers, hardcoded SOURCES, hardcoded PLANS, or forced `research_materially_changed_output=true` were added.
