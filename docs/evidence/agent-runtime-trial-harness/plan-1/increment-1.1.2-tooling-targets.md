# Increment 1.1.2 Tooling Targets

Date: 2026-05-28

Findings:

- Existing browser tooling: `playwright.config.mjs`, `tests/e2e/coding-ui.spec.mjs`.
- Existing test tooling: `vitest.config.mjs`, `npm run typecheck`, `npm run test:coding-frontend-regression`.
- Real route: `/coding` renders `src/components/coding/CodingCommandCenterShell.tsx`.
- Real desktop composer: `#coding-command-composer`, placeholder `Ask for a plan, start a coding task, or gather repo context.`
- Real desktop controls: buttons labeled `Desktop submit task`, `Desktop preview safely`, `Desktop clear task`.
- Existing proof pattern: `docs/evidence/...` for concise terminal/result notes.

Implementation target:

- Add a Playwright UI trial harness under `tests/e2e`.
- Drive `/coding` through the real composer and controls.
- Store screenshots/results under `docs/evidence/agent-runtime-trial-harness/plan-1/artifacts`.
- Keep trials preview-only and guard repo mutation around the run.

Result: GO for Increment 1.1.2.
