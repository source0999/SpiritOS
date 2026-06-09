# SpiritOS Local Coder Gate

This directory holds the minimal external gate for the Qwen2.5-Coder 14B upgrade plan.

The gate starts closed in `WAITING_FOR_HUMAN`. Codex must not approve its own next increment.

## Commands

```text
npm run gate:status
npm run gate:approve -- 1.1
npm run gate:start -- 1.1
npm run gate:complete -- 1.1
npm run gate:block -- "reason"
```

## States

- `WAITING_FOR_HUMAN`: no increment may run.
- `APPROVED_INCREMENT`: exactly one named increment is approved.
- `RUNNING_INCREMENT`: the approved increment is active.
- `BLOCKED`: execution is blocked until human review.

