# What Level Tests Actually Tested

## Level 3 Gate B

Evidence inspected:

- `docs/evidence/source-proxy-level-3-semantic-generalization-gate-b-20260613/index.md`
- `final-clean-10-gate-b-results.json`
- `final-clean-10-gate-b-run-receipt.json`
- per-run `receipt.json`
- `mini-context-pack.json`
- `anti-cheat-integrity.md`
- `anti-tailoring-audit.md`

Level 3 Gate B tested:

- Qwen/local artifact generation through `qwen2.5-coder:7b`.
- Generic artifact resolver/product route.
- Disposable workspace writes.
- Tool/action parsing into `WriteFile` actions.
- Browser/open and behavior probes.
- Repair/retest evidence for failed behaviors.
- Anti-tailoring and anti-cheat reporting in searched scopes.

Level 3 Gate B did not test:

- Gemma live invocation: NOT_INVOKED.
- Hermes live verifier invocation: NOT_INVOKED.
- Cartographer live route ownership: NOT_INVOKED.
- Obsidian context injection: NOT_INVOKED.
- Web/search/SearXNG/xersearch/Scout context: NOT_INVOKED.
- Mac worker: NOT_INVOKED.
- Continue/Cursor lanes: NOT_INVOKED.

Accepted status: Gate B was GO, with 9/10 behavior PASS and one theme/palette failure backlog item.

## Level 4

Evidence inspected:

- `docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/index.md`
- `level-4-results.json`
- `level-4-run-receipt.json`
- `per-prompt-traces/*.json`
- per-run `receipt.json` and `score.json`
- `mini-context-pack.json`
- `anti-cheat-integrity.md`
- `anti-tailoring-audit.md`

Level 4 tested:

- Same Qwen/local artifact lane as Level 3.
- Stricter evidence-only behavior wrapper requiring at least two observations.
- Disposable workspaces.
- Route traces as sidecar evidence.
- Browser behavior observation and strict final scoring.
- Bounded model-authored repair attempts for selected failures.

Level 4 did not test:

- Gemma live invocation: NOT_INVOKED.
- Hermes live verifier invocation: NOT_INVOKED.
- Cartographer live route ownership: NOT_INVOKED.
- Obsidian context injection: NOT_INVOKED.
- Web/search/SearXNG/xersearch/Scout context: NOT_INVOKED; per-score fields observed `web_search_used: false` on inspected runs.
- Mac worker: NOT_INVOKED.
- Continue/Cursor lanes: NOT_INVOKED.

Level 4 status: NO-GO, 5/10 PASS under strict two-observation behavior scoring.

## Core Answer

The recent levels tested Source Proxy artifact mode, not the full SpiritOS proxy system. They are valid evidence for Qwen artifact generation and behavior probing. They are not evidence that Cartographer, Obsidian, Search, Scout, Gemma, Hermes, Mac worker, Continue, or Cursor are part of the live prompt -> context -> model -> action loop.
