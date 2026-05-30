# Active `/coding` Route Evidence

- Active route file: `src/app/coding/page.tsx`.
- Active component file: `src/components/coding/CodingCockpitShell.tsx`.
- Why this is the light simplified page: `src/app/coding/page.tsx` imports and renders `CodingCockpitShell`; the simplified-screen search finds the active task-composer/review/transcript copy in `CodingCockpitShell.tsx`, including `Task Composer`, `Task transcript`, `Review pane`, and the current prompt placeholder.
- `CodingCommandCenterShell` active: no. It is present in the repository and tests, but `src/app/coding/page.tsx` does not import or render it.
- `CodingAgentInterface` active: no. It is present in the repository and tests, but `src/app/coding/page.tsx` does not import or render it.
- Old wrong surfaces user-facing: no evidence from the active route. The backend evidence console and old command center shell remain dormant code/test surfaces, not the `/coding` route.

