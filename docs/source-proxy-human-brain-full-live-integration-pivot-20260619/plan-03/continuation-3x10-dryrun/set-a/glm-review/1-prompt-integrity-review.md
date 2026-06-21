# Stage 1 — Prompt Integrity Review

Goal: confirm the user-facing prompts in `A1-A10` match the approved battery text verbatim, contain no diagnostic/hidden-expectation language, and were not rewritten or lane-tailored.

## Method

Compared `user_prompt` strings in `battery-v4.1.md`, `battery-v4.1.json`, and each `A{n}.json` / `A{n}.md` "Exact user prompt" block.

## Per-prompt comparison

All ten A-record `user_prompt` values are byte-identical to the approved battery text in both `battery-v4.1.md` and `battery-v4.1.json` (and `PROMPTS` in the generator script). No rewording detected.

| Prompt | A.json == battery.json | A.md == battery.md | Diagnostic/tailored language? | Verdict |
|-------:|:--:|:--:|:--|:--|
| A1 | match | match | none — "best route not random tutorial slop" is the user's own voice | PROMPT_CLEAN |
| A2 | match | match | none | PROMPT_CLEAN |
| A3 | match | match | none | PROMPT_CLEAN |
| A4 | match | match | none | PROMPT_CLEAN |
| A5 | match | match | none | PROMPT_CLEAN |
| A6 | match | match | none; user supplies the no-mutation boundary ("without touching jellyfin configs or media files") | PROMPT_CLEAN |
| A7 | match | match | none | PROMPT_CLEAN |
| A8 | match | match | none | PROMPT_CLEAN |
| A9 | match | match | none | PROMPT_CLEAN |
| A10 | match | match | none | PROMPT_CLEAN |

## Checks

- Hidden expectations leaked into user prompts: none. The diagnostic expectations live only in `battery-v4.1.json` (`internet_likely_required`, `mac_likely_required`, etc.) and were not copied into any user-facing prompt.
- Forbidden diagnostic phrases searched for and absent in all A prompts: "prove Mac", "test Qwen", "show consumer_event_id", "run verifier", "simulate recovery", "check if search is lying".
- No prompt names a lane (qwen/verifier/repair/recovery) or tells the system which proof path to use.
- Set A stays research/planning/architecture; none of the prompts demand a code patch, so Qwen/verifier/repair being "not required" is consistent with the prompt type.

## Caveat on integrity vs. execution

The prompts themselves are clean and un-tailored. The integrity problem is *not* in the prompt text — it is in how the answers were produced (Stage 2). The prompt layer is honest; the generation/grading layer is the issue.

## Verdict

Prompt integrity: **PASS** (10/10 PROMPT_CLEAN). Prompts are genuine messy human asks and were preserved verbatim.
