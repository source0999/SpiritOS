# SpiritOS Design Visual Verification v0.1

Status: planning and scaffold only, no screenshots captured

This document defines how Design Vault packs should use Playwright, screenshots, and match reports for future visual capture and regression checks. It does not add an e2e test, start a browser, change app routes, or import Design Vault files into production UI.

## Scope

Phase 5.1 covers:

- capture plan documentation
- screenshot folder conventions
- match-report shape
- safe Playwright detection
- optional `npx playwright test --list` smoke check when config exists

Phase 5.1 does not cover:

- visual baseline approval
- pixel comparison gates
- screenshot generation
- preview route implementation
- Storybook setup
- app UI changes
- Source Proxy, Scout, or Cartographer behavior changes

## Current Repo Fit

Observed visual verification support:

- Playwright config exists at `playwright.config.mjs`.
- Existing e2e tests live under `tests/e2e/`.
- The first Design Vault pack is `data/design-vault/packs/internal-dashboard-demo-v4/`.
- No Storybook setup was found during the v0.1 repo audit, so Storybook remains proposed only.

## Capture Targets

First approved internal target:

- Source card: `data/design-vault/source-cards/internal-dashboard-demo-v4.json`
- Pack: `data/design-vault/packs/internal-dashboard-demo-v4/`
- Internal source path: `src/components/dashboard/demo-v4/`
- Source style path: `src/styles/dashboard-demo-v4.css`

Future capture should use a stable local route only after a later approved implementation increment confirms the route and server command. Until then, this plan records the capture shape without running it.

## Screenshot Folders

For each design pack:

```text
data/design-vault/packs/<pack-id>/
  reference/
  generated/
  match-report.json
```

Use `reference/` for approved source screenshots. Use `generated/` for generated previews or implementation captures.

Recommended screenshot naming:

```text
<pack-id>--<source-or-generated>--<viewport>--<theme>--<state>.png
```

Examples:

```text
internal-dashboard-demo-v4--reference--desktop--frozen-water--default.png
internal-dashboard-demo-v4--generated--mobile--deep-sky--default.png
```

## Viewports

Initial viewport set should mirror the existing Playwright projects when practical:

- Desktop Chrome
- Mobile Safari
- Pixel 5
- iPad

Future screenshots should record viewport width, height, device scale factor, browser project, theme, state, and route.

## Match Report Shape

`match-report.json` should record:

- pack id
- source card
- status
- capture date
- Playwright config detected
- reference screenshots
- generated screenshots
- compared pairs
- threshold policy
- known deviations
- reviewer notes

Phase 5.1 creates a not-run report only. Later increments may replace it with real capture evidence after approval.

## Threshold Policy

The first comparison threshold should be informational, not blocking. Suggested later policy:

- `pass`: visible structure, color roles, spacing, and state treatment match the approved target within accepted variance.
- `review`: meaningful visual drift or missing state, but no protected asset or safety problem.
- `fail`: wrong source, missing required UI, unreadable layout, inaccessible state, or unapproved protected material.

No threshold in this document grants authority to write app UI.

## Safe Playwright Check

Use this pattern before any Playwright command:

```bash
cd /home/source/SpiritOS
if ls playwright.config.* >/dev/null 2>&1 && node -e "require.resolve('@playwright/test/package.json')" >/dev/null 2>&1; then
  npx playwright test --list
elif ls playwright.config.* >/dev/null 2>&1; then
  echo "Playwright config found, but @playwright/test is not installed locally. Skipping Playwright check for this increment."
else
  echo "Playwright config not found, skipping Playwright check for this increment."
fi
```

## Future Capture Rules

- Capture only approved source cards.
- Do not crawl websites.
- Do not follow arbitrary links.
- Do not capture external references without source-card approval.
- Do not promote screenshots or design packs into coding context automatically.
- Do not write app UI without Source Proxy approval.
- Keep reference and generated screenshots separated.
- Keep match reports tied to a design pack.

## Phase 5.1 Output

Phase 5.1 should leave:

- this visual verification doc
- empty `reference/` and `generated/` placeholders for the internal dashboard demo v4 pack
- a `match-report.json` with `status: not-run`
- no runtime changes
