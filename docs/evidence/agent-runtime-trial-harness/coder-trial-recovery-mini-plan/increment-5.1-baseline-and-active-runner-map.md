# Increment 5.1 - Baseline and Active Runner Map

Status: complete with preserved dirty tree.

Baseline commands:

- `git status --short`
- `git diff --stat`
- `rg -n "coding|CodingCockpitShell|Agent Trials|reversible|trial" src\app src\components\coding src\lib\coding tests\ui-agent-trials -g "*.ts" -g "*.tsx" -g "*.json"`
- `rg -n "<<<<<<<|=======|>>>>>>>" src\app src\components\coding src\lib\coding tests\ui-agent-trials`

Findings:

- Active `/coding` route is `src/app/coding/page.tsx`, which renders `CodingCockpitShell`.
- Active shell is `src/components/coding/CodingCockpitShell.tsx`.
- Existing focused shell test is `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.
- Existing prompt-bank files include `src/lib/coding/reversible-trial-prompts.ts` and `tests/ui-agent-trials/fixtures/coding-agent-prompts.json`.
- Dirty tree already included Source Proxy, coding shell, durable run, reversible runner, and SpiritFlix files before Gate 5 edits. These were preserved.
- Conflict-marker search found no active source conflict markers in the inspected source/test paths.

No trial run was executed.
