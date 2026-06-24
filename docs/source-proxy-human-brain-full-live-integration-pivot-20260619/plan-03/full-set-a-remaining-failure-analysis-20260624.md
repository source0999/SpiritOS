# Full Set A Remaining Failure Analysis - 2026-06-24

## Scope

- Branch: `integration/cleanup-plan3-debug-20260623`
- Starting HEAD: `836d8707f55a9ee0baf0d33b3a7bdf984cb1fe6e`
- Failed prompts in scope: A1, A3, A4, A6, A7, A8, A10
- Out of scope: A2, A5, A9 except regression verification through shared helper changes
- Set B/C: not run
- Plan 4: not started

## Failure Table

| Prompt | Failure class | Validator/debugger evidence | Shared root cause group | Proposed bounded fix |
| --- | --- | --- | --- | --- |
| A1 | `PRODUCTIVE_OUTPUT_GRADE_FAILURE` | `research_materially_changed_output`, `research_change_no_specific_decision`; selected `gemma3n:e4b`; raw research sources exist. | `RESEARCH_MATERIALITY` | Treat concrete planning verbs such as narrow/prioritize/implement/consider as specific decision verbs only when the block is still tied to raw source evidence. |
| A3 | `PRODUCTIVE_OUTPUT_GRADE_FAILURE` | `research_materially_changed_output`, `repo_context_used`, `limitations_stated`, `handoff_created`, `research_change_no_specific_decision`, `research_change_source_not_from_raw_sources`; raw source titles exist but source lines may omit host/URL. | `RESEARCH_SOURCE_LINKAGE`, `RESEARCH_MATERIALITY`, `PROMPT_TEMPLATE_UNCLEAR` | Match source lines to raw source objects by exact normalized title, URL, or host. Clarify prompt requirement for source lines and decision verbs. |
| A4 | `PRODUCTIVE_OUTPUT_GRADE_FAILURE` | `research_materially_changed_output`, `research_change_no_specific_decision`; raw source sources exist and source lines are mostly valid. | `RESEARCH_MATERIALITY` | Recognize concrete planning verbs while preserving raw source linkage checks. |
| A6 | `PRODUCTIVE_OUTPUT_GRADE_FAILURE` | `research_materially_changed_output`, `research_change_no_specific_decision`; raw sources exist. | `RESEARCH_MATERIALITY` | Recognize concrete planning verbs while preserving raw source linkage checks. |
| A7 | `PRODUCTIVE_OUTPUT_GRADE_FAILURE` | `research_change_source_not_from_raw_sources`; `internet_required=false`, `source_count=0`, repo context used. | `VERIFIER_EXPECTATION_MISMATCH` | Do not append research materiality/source-linkage errors for prompts where live research is not required and no sources exist. |
| A8 | `PRODUCTIVE_OUTPUT_GRADE_FAILURE` | `research_change_source_not_from_raw_sources`; `internet_required=false`, `source_count=0`, repo context used. | `VERIFIER_EXPECTATION_MISMATCH` | Same as A7. |
| A10 | `PRODUCTIVE_OUTPUT_GRADE_FAILURE` | `research_change_source_not_from_raw_sources`; `internet_required=false`, `source_count=0`, repo context used. | `VERIFIER_EXPECTATION_MISMATCH` | Same as A7. |

## Strategy

Two shared source changes are justified:

1. `RESEARCH_SOURCE_LINKAGE` / `VERIFIER_EXPECTATION_MISMATCH`: make raw source matching use raw source host, URL, or exact normalized title, and only apply research materiality parser errors when research was required or sources exist.
2. `RESEARCH_MATERIALITY` / `PROMPT_TEMPLATE_UNCLEAR`: recognize concrete planning verbs already used by the live model as specific decisions, and clarify the prompt to make the expected decision/source line shape explicit.

This is not contract weakening because fake/model-owned sources still do not match raw source objects, missing source evidence is not promoted to GO for internet-required prompts, and non-internet prompts are no longer penalized for not producing research-source provenance.
