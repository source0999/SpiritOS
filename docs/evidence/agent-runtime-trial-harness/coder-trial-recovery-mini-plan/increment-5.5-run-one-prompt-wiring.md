# Increment 5.5 - Run-One Prompt Wiring

Status: complete.

Implemented:

- Added `handleRunDummyCoder10Prompt` in `CodingCockpitShell`.
- The action posts only the selected prompt to `/v1/decisions/prompt-packet`.
- Payload includes submitted prompt, fixture root, allowed write root, primary targets, forbidden files, expected result state, project contract, factual summary, and trial-mode ban flags.
- No full Coder 10 loop is called.
- No Coder 25/50/100 path is called.
- No apply endpoint is called by this new action.

Focused test intent:

- `coding-cockpit-shell.test.tsx` includes a test that selects Prompt 009, clicks the run-one button, and asserts exactly one prompt-packet call with dummy-root boundaries.

Verification:

- `npx --no-install tsc --noEmit --pretty false` passed.
- `git diff --check` passed.
- Focused Vitest blocked before import with the local Vitest resolver failure.
