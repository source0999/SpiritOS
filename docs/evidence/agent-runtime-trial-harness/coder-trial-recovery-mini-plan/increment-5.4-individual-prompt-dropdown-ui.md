# Increment 5.4 - Individual Prompt Dropdown UI

Status: complete.

Implemented:

- Added a `LumaCart prompt runner` panel to `src/components/coding/CodingCockpitShell.tsx`.
- Added dropdown for Coder 001-010.
- Selecting a prompt updates title, submitted prompt, fixture root, allowed write root, expected result state, forbidden file summary, project summary, and primary expected targets.
- Added focused shell test coverage in `src/components/coding/__tests__/coding-cockpit-shell.test.tsx`.

Safety:

- Selecting a prompt does not run anything.
- Existing manual composer remains present.
- Older suite runner remains separate; it is not used as the source of truth for this LumaCart bank.

Verification:

- `npx --no-install tsc --noEmit --pretty false` passed.
- `git diff --check` passed.
- Browser smoke was attempted against `http://localhost:3000/coding` and `http://127.0.0.1:3000/coding`; the in-app browser returned `net::ERR_BLOCKED_BY_CLIENT`.
