# Active route and trial runner evidence

- Active route file: `src/app/coding/page.tsx`
- Active component file: `src/components/coding/CodingCockpitShell.tsx`
- Evidence: the route imports and renders `CodingCockpitShell`; the visible light workspace text includes `Coding sessions`, `New chat`, `Task transcript`, `Task Composer`, `Review pane`, `Live coding runner`, and `Start coding`.
- Previous trial runner evidence: `CodingCockpitShell.tsx` still contained unreachable historical trial runner code with `Run trial`, size selection, and related state. Git history also showed `Run trial` in commit `7b1f1f2fc0f9b68b4247fac1da0cecda4b89b4d3`.
- Useful old part: the idea of a count-selected trial runner embedded in the coding workspace.
- Parts that must not come back: runner tabs, preview diagnostic mode, Live Apply Bank, Preview-only Diagnostic Bank, bank selector wording, size/view clutter, fake score/usefulness wording, and backend evidence console surfaces.
- Restoration direction: add a clean `Reversible trial runner` card to the current light workspace and source its prompts from a realistic reversible catalog instead of the old bank dashboard.
