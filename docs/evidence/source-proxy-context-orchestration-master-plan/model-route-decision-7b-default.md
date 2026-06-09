# Model Route Decision: 7B Default, 14B Comparison Lane

Status: decision record for planning. This does not execute any model route change.

## Current Decision

Use `qwen2.5-coder:7b` as the default coder route for the Source Proxy coding workflow for now.

## Reason

Recent messy-prompt diagnostics showed `qwen2.5-coder:7b` followed the file-block/output contract better than the 14B route. The immediate readiness blocker is not ambition; it is reliable, parseable, safe output under messy Britton-style prompts.

## 14B Boundary

The 14B route remains a controlled upgrade/comparison lane. It is not abandoned, but it cannot become default until:

- the parser and repair discipline are stable,
- the 7B baseline passes the basic messy-prompt output contract,
- the 14B route passes the same output-contract tests,
- comparison evidence shows no regression in malformed tags, markdown fences, unsafe paths, empty diffs, or out-of-scope edits,
- Britton approves a default-route switch after reviewing evidence.

## Required Route Truth Evidence

Plan 0 must record:

- configured coder alias
- provider backing that alias
- actual model called for generation
- route shown in `/coding`
- Source Proxy `/v1/models` or equivalent route truth
- any mismatch between UI-selected model, backend alias, and provider model

## GO/NO-GO

GO for planning with 7B as default.

NO-GO for switching 14B to default before the parser gauntlet and Britton approval.
