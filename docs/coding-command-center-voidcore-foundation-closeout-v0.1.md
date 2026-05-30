# Coding Command Center VoidCore Foundation Closeout v0.1

Status: foundation implemented
Status date: 2026-05-22
Scope: close out the first `/coding` VoidCore command-center foundation pass without changing Source Proxy safety contracts.

## What Changed

`/coding` now renders the new VoidCore-inspired command-center shell through `src/app/coding/page.tsx` and `src/components/coding/CodingCommandCenterShell.tsx`.

The foundation includes:

- Left rail with workspace controls, chat list, and start-new-chat action.
- Current SpiritOS repo selected by default.
- Gated `C:\Projects` future workspace option.
- Honest disabled `Start new project` placeholder.
- Local LLM default provider intent and GPT/cloud unavailable/configured status display.
- Per-chat provider intent switching without claiming a provider call ran.
- New-chat creation and visible two-chat switching.
- Desktop and mobile composers kept distinct.
- Mobile command composer region with compact fixed layout.
- Compact Source Proxy safety/status panel.
- Coding mode entry point.
- Preview-only request path through existing BFF routes.
- Approval button shown only after preview evidence is ready.
- Apply button shown only after explicit local approval.
- Verification remains required after apply; the shell does not claim verification passed.

## What Stayed Protected

The Source Proxy safety model remains the authority:

- Draft before preview.
- Preview before approval.
- Human approval before apply.
- Apply through approved route only.
- Verify after apply.
- Honest blocked/error states.

No hidden autonomy was added. No commit, push, merge, branch creation, worktree creation, cleanup, stash, self-approval, background mutation, or unsafe Windows write behavior was added.

## Intentional Non-Goals

These remain intentionally unwired or gated:

- Full autonomous coding.
- Auto project creation.
- Unsafe Windows mutation.
- Fake local/cloud execution claims.
- Cloud/GPT execution when not configured.
- Treating a successful apply as verified.
- Replacing Source Proxy backend contracts.

## Guardrails Added

Tests now cover:

- `/coding` renders the VoidCore command-center shell.
- The command-center shell renders without live coding authority.
- Workspace, provider, and safety status remain visible without implying execution.
- Mobile and desktop composer controls remain distinct.
- Compact Source Proxy safety panel remains visible.
- Coding mode does not enable actions by itself.
- Preview request does not enable apply.
- Apply only appears after preview evidence and explicit approval.
- Preview-blocked state keeps approval/apply locked.
- Provider intent can switch without claiming a provider call ran.
- New chat creation works.
- Two chats can be created and swapped.

## Manual Check

```bash
cd /home/source/SpiritOS
git diff --check
npm run typecheck
npx vitest run src/app/coding/__tests__/page.test.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx
npm run test:coding-frontend-regression
curl -k -I https://127.0.0.1:3000/coding
git status --branch --short
```

Expected outcome:

- `git diff --check` is clean.
- `typecheck` passes.
- Route + shell tests pass.
- Coding frontend regression passes.
- `/coding` returns `HTTP/1.1 200 OK` over HTTPS.
- Git status still shows the expected working tree changes and unrelated untracked Cartographer files.

Next increment title: Increment 8.8: Operator Visual Review Before Additional Polish

## Stop Point

Stop here unless the operator gives specific visual notes or a specific next workflow target. The command-center foundation is now wired and guarded enough for manual visual review.
