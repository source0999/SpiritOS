# SpiritOS Progress Tracker / Project Tracker Roadmap

> **Extracted from:** End-of-night product checkpoint — we need a first-class “what projects exist, what’s on fire, what’s next” surface inside SpiritOS.  
> **Design language:** **Read-only first**, approval-gated later. No drive-by `fs` access, no secret sprawl in summaries.

## Purpose

A built-in tracker so SpiritOS can know **what projects exist**, what phase each is in, what was worked on last, what tests passed, what broke, what needs attention next, and what commits/checkpoints exist — without living in a separate tool forever.

**Status:** **Not implemented** — this file is the contract for when we start.

---

## Planned capabilities

### Phase 0 — Manual tracker

- User-entered **project cards** (title, path/repo link, notes).
- Fields: **status**, **priority**, **next action**, freeform notes.
- **Tags** (e.g. `ui`, `backend`, `oracle`, `telemetry`, `mobile`, `personality`).

### Phase 1 — Read-only project discovery

- Parse **`SPIRIT_PROJECT_PATH`** (or equivalent allowlist env).
- Scan **allowed roots only** — no arbitrary filesystem wandering.
- Detect **`package.json`**, **`README`**, **`.git`**, app routes (heuristics), **tests** directories.
- **No file modification.**

### Phase 2 — Git-aware tracking

- **Branch**, **dirty** status, **last commit**, optional **test status** (from CI/local commands later).
- Surfacing **uncommitted files** and suggested **commit checkpoints** (suggestions only until approvals exist).

### Phase 3 — AI-assisted planning

- Summarize what changed (from git + allowed scans).
- Generate next-step plans; surface **stale TODOs**; suggest **test commands** (read-only until execution is approved).

### Phase 4 — Approval-gated actions

- Create issues/tasks (external or internal).
- Run tests, commit changes, and later **file edit/move** with **diff preview** — all behind explicit user approval and audit.

---

## Safety (non-negotiable)

- **Read-only** paths and registry first; **no** arbitrary browsing outside **allowed roots**.
- **No writes** (disk, git, issue APIs) without **explicit approval** and later **audit log**.
- **No secrets** in generated summaries (strip env files, keys, token-like strings by policy).

---

## Related: personality / profile hygiene (feeds the same product story)

Not the tracker’s job alone, but **blockers** if we ignore them:

- **Clear personality settings** — what applies in `/chat` vs `/oracle`, and how modes interact.
- **Memory hygiene / test mode** — ability to run “test” sessions that **do not** poison long-term personalization.
- **Review what Spirit thinks it knows** — user-visible, editable, resettable.
- **Refine Oracle vs chat tone** — practical, social, warm, not over-clinical; still within safety policy.

---

## See also

- `_blueprints/chat_workspace_roadmap.md` — chat workspace phases and deferred work.
- `README.md` — **Next Work Order** (P1–P3) aligns P2–P3 with this roadmap.
