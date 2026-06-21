# GLM Full-Repo Mobile Index — Fold 7

**Audit:** GLM Full-Repo Second Audit against supplied 2026 benchmark · **Date:** 2026-06-21
**HEAD:** `927055e4` · **Branch:** `master` · **Host:** Spirit
**Folder:** `docs/full-repo-system-architecture-audit-20260621/`

How to use on Britton's Samsung Fold 7 (mobile Codex): open the audit `.md` first for human reading, use the shard `.xml`s as compact AI context (one shard per area), keep checksums beside all files, and compare GLM's findings with the **prior** source-proxy-min GLM audit and any future Codex audit before approving cleanup.

---

## Files

### 1. `glm-full-repo-audit-20260621.md` — READ FIRST
- **Purpose:** Human-readable full-repo audit (18 sections: verdict, system map, OS-brain alignment, coding-loop readiness, clean-architecture, commenting, debugging/taxonomy, anti-cheat, brain-switch, context/Headroom, Blueprint/Cartographer, SpiritFlix/media boundary, vs prior audit, top risks, F0–F10 cleanup roadmap, review checklist).
- **Repo path:** `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-audit-20260621.md`
- **Size:** see checksums.
- **SHA-256:** see `glm-full-repo-checksums.sha256`.
- **How to use on Fold 7:** Open in a Markdown viewer (Codex mobile, Obsidian, Markor). Short sections + compact tables, designed for fold-screen reading. Read §1 (verdict), §9 (taxonomy gap), §11 (A2/A5/A9 brain-switch), §15 (vs prior audit), §16 (top risks) first.

### 2. `glm-full-repo-freeze-20260621-shard-001.xml` — CORE OS CODE
- **Purpose:** Source Proxy + Coding UI + SpiritFlix code + media code + spirit/dashboard/chat — the OS brain + human face.
- **Repo path:** `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-freeze-20260621-shard-001.xml`
- **Size:** 1,769,609 bytes · 816 files.
- **SHA-256:** `fbe676b55f4a4ceb550cea3f0f73567d605ace25c06f1a18cd5c1cf4efc8b82b`
- **How to use on Fold 7:** Upload/paste into another AI chat (Codex, Claude) for a second opinion on Source Proxy architecture, `decision.py`, the Coding UI shells, or the durable engine. Primary shard for coding-loop questions.

### 3. `glm-full-repo-freeze-20260621-shard-002.xml` — TOOLING
- **Purpose:** Scout (read-only intel) + scripts (ops, mac-worker, context, media tooling code) + root configs (package.json, repomix configs, tsconfig, etc.).
- **Repo path:** `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-freeze-20260621-shard-002.xml`
- **Size:** 550,807 bytes · 189 files.
- **SHA-256:** `4666eb61e8a396130011af03f5ab70325299395dd04765c38c7a8e063adff530`
- **How to use on Fold 7:** Use for Scout bounded-contract questions, Mac worker bridge, context/Headroom tooling, ops scripts. Includes the exemplary `scout/SCOPE.md` (Permitted/Prohibited/Kill-Switch) — a model Source Proxy could learn from.

### 4. `glm-full-repo-freeze-20260621-shard-003.xml` — ARCHITECTURE DOCS
- **Purpose:** `_blueprints/**` + top-level plan `.md` docs + source-proxy-human-brain pivot + context-export + cartographer-live-receipts docs.
- **Repo path:** `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-freeze-20260621-shard-003.xml`
- **Size:** 1,883,468 bytes · 431 files.
- **SHA-256:** `2f18e3b1d51f3f177684b162263f812ef750e51e89bd22f073f5a8c2a33db34e`
- **How to use on Fold 7:** Use for Blueprint/Cartographer intent questions, plan history, contracts. Compare intent (docs) vs implementation (shard-001).

### 5. `glm-full-repo-freeze-20260621-shard-index.md`
- **Purpose:** Shard map (which shard covers what, sizes, hashes, how-made).
- **Repo path:** `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-freeze-20260621-shard-index.md`
- **How to use on Fold 7:** Keep open as the shard navigator.

### 6. `glm-full-repo-mobile-index.md` (this file)
- **Purpose:** File list, paths, sizes, hashes, how-to for mobile review.
- **Repo path:** `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-mobile-index.md`

### 7. `glm-headroom-repair-log.md`
- **Purpose:** Honest log of the Headroom BLOCKED_ENV diagnosis (Cursor on 8797, Linux venv, bounded 12s repair attempt, no service killed).
- **Repo path:** `docs/full-repo-system-architecture-audit-20260621/glm-headroom-repair-log.md`
- **How to use on Fold 7:** Read if Headroom token-savings matter; explains why shards are tree-sitter-only (no Headroom compression) and what to fix on the Dell Linux side.

### 8. `glm-full-repo-metadata.json`
- **Purpose:** Machine-readable freeze identity (HEAD, dirty/staged by subsystem, shard table, excluded categories, commands run/not-run, caveats).
- **Repo path:** `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-metadata.json`
- **How to use on Fold 7:** Open as JSON. Confirms read-only, no source mutation, no commit/push, Headroom BLOCKED_ENV.

### 9. `glm-full-repo-checksums.sha256`
- **Purpose:** SHA-256 of the audit MD, mobile index, metadata JSON, headroom log, and the 3 shards. Integrity verification.
- **Repo path:** `docs/full-repo-system-architecture-audit-20260621/glm-full-repo-checksums.sha256`
- **How to use on Fold 7:** After download, run `sha256sum <file>` (Termux) or a checksum app and compare. Mismatch = corrupted transfer.

---

## Fold 7 Review Workflow

1. **Open `glm-full-repo-audit-20260621.md` first.** Read §1, §9, §11, §15, §16.
2. **Use shard-001 as primary AI context** for Source Proxy / coding-loop second opinions.
3. **Use shard-002** for Scout / Mac worker / ops; **shard-003** for Blueprint/Cartographer intent.
4. **Keep `glm-full-repo-checksums.sha256`** beside all files and verify after transfer.
5. **Compare with the prior source-proxy-min GLM audit** (`docs/source-proxy-system-freeze-audit-20260621/`). Does Codex agree the taxonomy gap + decision.py concentration are the top two risks?
6. **Compare with any future Codex full-repo audit.**
7. **Do NOT approve F1–F10 cleanup implementation** until both GLM + Codex reviewed and Britton signs off per-stage.

---

## Safety Confirmations (what this audit did NOT do)

- No source code patched, refactored, moved, or deleted.
- No files staged, committed, or pushed.
- No services killed (Cursor on 8797 was left alone — unrelated editor service).
- No SpiritFlix / media / Jellyfin files touched. (2 dirty + 1 new SpiritFlix file are Britton's pre-existing WIP, recorded not modified.)
- No Set B/C, Stage 5, Plan 4, new engine, or new route.
- No packages installed. No venv rebuilt. No secrets printed.
- Headroom: bounded 12s repair attempted and honestly logged as BLOCKED_ENV; documented tree-sitter fallback used. No data lost.

## Freeze Identity (quick reference)

- **HEAD:** `927055e489eb1dc9a263bf3a80cde53869e274ce`
- **Branch:** `master`
- **Dirty paths:** 2 (SpiritFlix WIP) · **Staged:** 0 · **Untracked:** 4 (1 temp, 1 SpiritFlix WIP, 2 GLM audit dirs)
- **Shards:** 3 · **Total size:** 4.20 MB · **Total files:** 1,436
- **Headroom:** BLOCKED_ENV (Cursor on 8797 + Linux venv; documented fallback used)
- **Verdict:** PARTIALLY_HEALTHY · OS-BRAIN-MODEL-IS-REAL · CONCENTRATED-AND-TAXONOMY-WEAK · ANTI-CHEAT-STRONG · MEDIA-BOUNDARY-CLEAN
