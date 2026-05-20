# Internal Dashboard Demo v4 Design Notes

Status: raw inventory, not normalized

Source card: `data/design-vault/source-cards/internal-dashboard-demo-v4.json`

## Source Scope

Approved internal source files:

- `src/components/dashboard/demo-v4/`
- `src/styles/dashboard-demo-v4.css`
- `src/styles/spirit-demo.tokens.css`
- `src/theme/spiritPalettes.ts`

No source files were modified during this extraction increment.

## Design Language Observations

- Isolated dashboard namespace through `.dashboard-demo-v4-*`.
- Glass and pearl surface system with light and smoke variants.
- Theme switching rides the existing `html[data-theme="..."]` contract from Spirit palettes.
- The dashboard uses a direct `<main className="dashboard-demo-v4-root">` surface rather than a decorative outer wrapper.
- Primary patterns include atmosphere layer, shell, header, oracle hero, project tracker, system stats, storage, briefing, Scout, Cartographer, blueprint review, test runner, floating nav, desktop rail, mobile nav, and theme picker.
- Motion language includes atmospheric drift, glow breathing, badge sheen, subtle text glow, oracle standby bars, widget floating, and mobile scroll reveal.

## Raw Token Families Observed

- `--ddv4-*`: dashboard-demo-v4 local surface, atmosphere, shell, navigation, widget, badge, and light/smoke surface variables.
- `--demo-*`: older Spirit design-demo local tokens for colors, semantic accents, glow, radius, blur, spacing, typography, z-index, and motion.
- `--spirit-*`: global Spirit theme variables applied by the palette registry.

## Known Limits

- This is not a normalized token file.
- No screenshots were captured in this increment.
- No Playwright visual verification was run in this increment.
- No preview route, Storybook story, or production UI import was added.

## Next Step

Phase 4.1 normalized `tokens.raw.json` into primitive, semantic, component, motion, responsive, and accessibility token groups.

Future Style Alchemist use:

- This pack may be used as an internal-approved blend source.
- Influence notes must reference `internal-dashboard-demo-v4`.
- Any blended output should remain clearly SpiritOS-owned and should not introduce external protected assets.
