# Final A2/A5/A9 Bounded Fix Analysis - 2026-06-24

## Current Evidence

| Prompt | Remaining failure | Current source refs / action intent | Correct bounded fix | Why this is not contract weakening |
| --- | --- | --- | --- | --- |
| A2 | `research_change_source_not_from_raw_sources` | The packet is valid and uses code-owned `research:*` evidence refs. The rendered work has five raw research source lines, but `research_change_blocks()` keeps parsing after `Repo/Mac evidence that changed the plan`; repo snippet text containing `Source:` overwrites the final research block source as a repo path. | Stop research-change parsing at the `Repo/Mac evidence that changed the plan` section and require parsed `Source:` lines to match raw source hosts/URLs only. | This tightens source provenance by preventing repo snippet text from counting as research provenance. It does not accept fake URLs or lower validation requirements. |
| A5 | `research_materially_changed_output`, `research_change_source_not_from_raw_sources` | The packet is valid and uses code-owned `research:*` refs. The rendered work has raw research source lines, then the same parser bleed lets repo evidence text overwrite the final research block source. | Same parser boundary fix as A2. The output may still fail if fewer than three valid raw-source research-change blocks remain; that is an honest grader result. | The fix preserves the existing three-block materiality threshold and only prevents non-research repo text from corrupting source linkage. |
| A9 | `model_decision_body_invalid_action_intent:test later` | The model emitted exact `action_intent: "test later"`; the controlled enum already has `defer`, which is the safe equivalent for a later test rather than a present action. | Normalize the exact phrase `test later` to existing controlled intent `defer`; record original, normalized value, and reason in the shell/debugger status. Keep unrelated invalid intents failing. | This uses an existing enum value and records the normalization. It does not add a new intent, broaden acceptance, or hide invalid unrelated verbs. |

## Source-Linkage Path

- Raw source facts enter the runner through `build_generation_evidence_digest()` and `build_packet_evidence_items()`.
- Code-owned packet assembly inserts `research:*` evidence IDs and source URLs from that digest.
- `render_work_from_decision_packet()` emits research-change blocks from `source_fact_by_ref()`.
- `grade()` calls `research_change_blocks()` over the rendered work and raw research sources.
- The bug is in `research_change_blocks()`: it keeps parsing beyond the research section and treats later repo evidence lines containing `Source:` as research source lines.

## Action-Intent Path

- `decision_packet_prompt()` asks the model for bounded `action_intent`.
- `normalize_action_intent()` maps model action intent text to the controlled enum.
- `model_decision_body_status()` and `assemble_code_owned_decision_packet()` surface invalid action errors.
- The bounded change belongs in `normalize_action_intent()` with diagnostic metadata surfaced by the shell status.
