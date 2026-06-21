# Stage 7 — Human Messy Prompt Review

Judging whether Set A is actually testing broad daily-driver intelligence (the prompt side), separate from how the answers were produced (covered in Stages 2-4).

## Are the prompts real messy daily-driver asks?

Yes. Reading them as Britton would phrase them:

- A1: "research open source frameworks and more ... best route not random tutorial slop" — genuine, opinionated, slangy.
- A2: "sends whatever page/text/video im on to source proxy and turns it into a task" — vague, multi-modal, real.
- A3: "start proxy tasks from my phone and check receipts" — concrete goal, loose on method.
- A4: "turn obsidian/project notes into better ai context and tell me what i should build first" — prioritization ask.
- A5: "using my dell mac and windows without wasting money" — multi-device, cost-conscious.
- A6: "...without touching jellyfin configs or media files" — user-supplied safety boundary, realistic.
- A7: "next highest leverage thing to make it closer to daily driver" — open-ended prioritization.
- A8: "...without overwhelming me" — UX-flavored constraint.
- A9: "...what is worth using for my proxy setup this month" — time-boxed currency ask.
- A10: "...what an outside ai should work on next without breaking stuff" — delegation/safety ask.

These are not scaffolded diagnostic tests. They contain no lane names, no "prove X" language, no instructions to use a specific proof path. They resemble actual messy project asks and span research/planning/architecture/handoff/delegation.

## Checks

- Not scaffolded diagnostic tests: PASS.
- Not tailored to current implementation details: PASS (prompts are stable, generic-to-Britton asks; none reference Plan numbers, file paths, or trace fields).
- Do not tell the system which lane to use: PASS.
- Trigger real work products: the prompts *would* trigger real work; the generator simply didn't run them (separate problem).
- Resemble Britton's actual messy asks: PASS — voice is consistent and informal.
- Hidden expectations kept separate and not leaked: PASS — `battery-v4.1.json` expectations did not bleed into any user prompt (Stage 1).

## Important distinction

The **prompts** are a good, hard, broad daily-driver battery. The **execution** defeats the test: because answers were generated from a hardcoded `PLANS`/`SOURCES` script, the battery did not actually exercise the proxy's intelligence on these prompts. So the test design is sound; the test was not genuinely run.

## Verdict

Human messy prompt quality: **PASS**. The prompts are clean, hard, broad, and human. This is the one dimension that is unambiguously good — but it makes the staged-answer problem worse, not better: a solid test was neutralized by canned outputs.
