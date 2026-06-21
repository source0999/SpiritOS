# Stage 3 — Prompt Integrity Review

Reviewer: GLM (independent, review-only).
Date: 2026-06-20.

## Comparison method

Compared `battery-v4.1.md` and `battery-v4.1.json` (approved prompt set) against every `set-a-rerun/A*.json` `user_prompt` field via an automated byte-equality check across all 10 prompts.

## Result: PASS

```
A1 OK | A2 OK | A3 OK | A4 OK | A5 OK
A6 OK | A7 OK | A8 OK | A9 OK | A10 OK
ALL_PROMPT_MATCH = true
```

Every A1-A10 `user_prompt` in the rerun records is **byte-identical** to the approved battery-v4.1 text. Examples:
- A2: `look into how i could build a browser extension that sends whatever page/text/video im on to source proxy and turns it into a task` ✓
- A5: `make me a plan for a local ai workstation setup using my dell mac and windows without wasting money` ✓
- A9: `research current local llm tools and tell me what is worth using for my proxy setup this month` ✓

## Sub-checks

- **User prompts match approved battery text:** YES, all 10 byte-identical.
- **No hidden expectations leaked into the user prompt:** YES. The user-visible prompt carries no diagnostic/lane/materiality language. (The hidden expectations live in `battery-v4.1.json` fields like `internet_likely_required`, `must_inspect_repo_context`, `mac_likely_required`, `expected_work_product` — correctly kept out of the user prompt.)
- **No diagnostic/lane language inserted into the user prompt:** YES. Terms like "research_materially_changed_output", "consumer", "trace", "lane", "MV3", "system_status" do NOT appear in any user prompt.
- **No prompt rewritten for the A2/A5 fix:** YES. A2 and A5 user prompts are unchanged from battery. The fix changed the *model worker prompt* (`model_prompt()` in the runner) and the *grader*, not the user-facing ask. That is the correct place to fix — the user ask is intact.

## Important distinction (prompt integrity vs. model-prompt scaffolding)

Prompt integrity is clean. Separately (covered in Stage 2), the *internal* model worker prompt pre-shapes the answer into fixed sections and hands the model the exact `Finding:/Source:/How it changed the plan:` bullets that the grader then keys on. That is an internal scaffolding/grading concern, **not** a corruption of the user-facing battery prompt. The user prompt integrity gate itself is fully met.

## Verdict

**prompt_integrity: PASS.** The messy human asks are preserved verbatim; no tailoring, no leaking, no rewriting for the fix.
