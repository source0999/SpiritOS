# Dependency Audit, Phase 5

> **Historical baseline:** Source of truth was `package.json` + `grep` under `src/`, allowed docs, and **limited** `grep` on `package-lock.json`. `CURSOR_SPIRITOS_UPGRADE.md` was not read whole-file; keyword `grep` only.

## Removal applied (approved)

**Date:** 2026-05-02  

Uninstalled (zero `src/` imports; no blueprint / Cursor-rule mandate):

- `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities`
- `dexie`, `dexie-react-hooks`
- `simple-git`

**Command executed:**

```bash
npm uninstall @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities dexie dexie-react-hooks simple-git
```

**Not removed** (stack intent — reinstall when implementing features):

- `swr` — `.cursor/rules/global.mdc` telemetry guidance (NUT, Langfuse).
- `react-markdown` — `_blueprints/design_system.md` Intelligence Reader / Markdown reader.

Post-removal: `npm run lint`, `npm run typecheck`, `npm run build` — all passed.

---

## Actively used

| Package | Evidence (import or config) | Decision |
|--------|-----------------------------|----------|
| `next` | `src/app/layout.tsx` (`Metadata`); `next/dynamic`, `next/navigation`, `next/link`, `next/font/google` in `src/`; `NextResponse` in `src/proxy.ts` | **keep** — App Router core |
| `react` | Hooks and types across `src/**/*.tsx` | **keep** |
| `react-dom` | Required by Next for client surfaces | **keep** |
| `ai` | `streamText`, `convertToModelMessages` — `route.ts`; `DefaultChatTransport` — `SpiritChat`; `UIMessage` — `SpiritMessage`, `chat-utils`, `spirit-request` | **keep** |
| `@ai-sdk/react` | `useChat` — `SpiritChat.tsx` | **keep** |
| `@ai-sdk/openai` | `createOpenAI` — `src/lib/server/ollama.ts` | **keep** |
| `framer-motion` | `DashboardClient.tsx`, `HubStageCards.tsx` | **keep** |
| `lucide-react` | `stageTypes.ts`, `DashboardClient.tsx`, `QuarantineStageVisual.tsx` | **keep** |
| `clsx` | `LayoutOrchestrator.tsx`; `src/lib/cn.ts` | **keep** |
| `tailwind-merge` | `src/lib/cn.ts` | **keep** |
| `server-only` | `ollama.ts`, `spirit-request.ts`, `api-errors.ts` | **keep** |
| `typescript` | `tsc --noEmit` | **keep** (dev) |
| `@types/node` | Node typings | **keep** (dev) |
| `@types/react` | React typings | **keep** (dev) |
| `@types/react-dom` | React DOM typings | **keep** (dev) |
| `eslint` | `npm run lint` | **keep** (dev) |
| `eslint-config-next` | Next ESLint | **keep** (dev) |
| `tailwindcss` | Tailwind v4 (`globals.css`, `@import "tailwindcss"`) | **keep** (dev) |
| `@tailwindcss/postcss` | `postcss.config.mjs` | **keep** (dev) |

## Planned but not currently imported

| Package | Planning evidence | Decision |
|--------|-------------------|----------|
| `swr` | `.cursor/rules/global.mdc` — SWR for live telemetry | **keep** — add imports when NUT/Langfuse wiring lands |
| `react-markdown` | `_blueprints/design_system.md` — Markdown / Intelligence Reader | **keep** — add when that surface ships |

## Previously unused — removed (2026-05-02)

| Package | Notes |
|--------|--------|
| `@dnd-kit/core`, `@dnd-kit/sortable`, `@dnd-kit/utilities` | No `src/` usage. Re-`npm install` if drag/sort UI is scheduled. |
| `dexie`, `dexie-react-hooks` | No `src/` usage. Reinstall for IndexedDB / local thread cache if needed. |
| `simple-git` | No `src/` usage. Reinstall for server git automation if needed. |

## Build and dev tooling

| Role | Packages |
|------|----------|
| Framework / runtime | `next`, `react`, `react-dom` |
| Language | `typescript`, `@types/node`, `@types/react`, `@types/react-dom` |
| Lint | `eslint`, `eslint-config-next` |
| CSS | `tailwindcss`, `@tailwindcss/postcss` |
| Server bundle marker | `server-only` |

## Do not remove

- **`next`, `react`, `react-dom`**
- **`ai`, `@ai-sdk/react`, `@ai-sdk/openai`**
- **`framer-motion`, `lucide-react`**
- **`clsx`, `tailwind-merge`**
- **`server-only`**
- **`typescript`, `@types/*`, `eslint`, `eslint-config-next`, `tailwindcss`, `@tailwindcss/postcss`**
- **`swr`, `react-markdown`** — reserved for documented upcoming features (not dead weight by project rules)

## Future optional cleanup

If product explicitly drops SWR or Markdown reader, candidate command (not run):

```bash
npm uninstall swr react-markdown
```

## Permission checkpoint

**Phase 5 removal complete** for dnd-kit, dexie, dexie-react-hooks, and simple-git. Further cuts require another explicit approval.
