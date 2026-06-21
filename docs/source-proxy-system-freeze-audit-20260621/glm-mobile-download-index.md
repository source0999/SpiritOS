# GLM Mobile Download Index — Fold 7

**Audit:** GLM Independent Source Proxy Freeze + Audit · **Date:** 2026-06-21
**HEAD:** `927055e4` · **Branch:** `master` · **Host:** Spirit
**Folder:** `docs/source-proxy-system-freeze-audit-20260621/`

How to use on Britton's Samsung Fold 7 (mobile Codex): open the `.md` first for human reading, use the `.xml` as compact AI context, keep checksums beside both, and compare GLM's audit with Codex's before approving any cleanup.

---

## Files

### 1. `glm-source-proxy-audit-20260621.md`
- **Purpose:** Human-readable independent GLM audit (15 sections: verdict, system map, code-quality, debugging, anti-cheat, brain-switch, Blueprint/Cartographer, vs-Codex comparison, cleanup roadmap C0–C9).
- **Repo path:** `docs/source-proxy-system-freeze-audit-20260621/glm-source-proxy-audit-20260621.md`
- **Size:** see checksums line below (computed at freeze time).
- **SHA-256:** see `glm-checksums.sha256`.
- **How to use on Fold 7:** Open in any Markdown viewer (Codex mobile, Obsidian, Markor). Short sections + compact tables, designed for fold-screen reading. Read sections 1 (verdict), 7 (debugging gap), 9 (brain-switch), 12 (vs Codex) first.

### 2. `glm-source-proxy-freeze-20260621.xml`
- **Purpose:** Compact Source Proxy context bundle (tree-sitter Repomix, 414 files, ~380k tokens). Source-proxy-min profile — excludes node_modules, media, SpiritFlix, evidence bloat, secrets.
- **Repo path:** `docs/source-proxy-system-freeze-audit-20260621/glm-source-proxy-freeze-20260621.xml`
- **Size:** 1,600,235 bytes (1.6 MB, under the 2 MB target).
- **SHA-256:** `a46936756a0caa8343e7ae65477b7a7523b4515907a9035c6d025d79b16d6241`
- **How to use on Fold 7:** Upload/paste into another AI chat (Codex, Claude, etc.) as compact repo context for an independent second opinion on Source Proxy. Or open as text to grep for specific files/lanes. Do **not** treat it as full repo — it is the source-proxy-min subset only.

### 3. `glm-mobile-download-index.md` (this file)
- **Purpose:** File list, paths, sizes, hashes, and how-to for mobile review.
- **Repo path:** `docs/source-proxy-system-freeze-audit-20260621/glm-mobile-download-index.md`
- **Size:** see checksums.
- **SHA-256:** see `glm-checksums.sha256`.
- **How to use on Fold 7:** Keep open as the index while reviewing the other files.

### 4. `glm-checksums.sha256`
- **Purpose:** SHA-256 of the XML, audit MD, this index, and metadata JSON. Integrity verification.
- **Repo path:** `docs/source-proxy-system-freeze-audit-20260621/glm-checksums.sha256`
- **How to use on Fold 7:** After download, run `sha256sum <file>` (Termux) or a checksum app and compare to the lines in this file. Mismatch = corrupted/transferred file.

### 5. `glm-freeze-metadata.json`
- **Purpose:** Machine-readable freeze identity (HEAD, branch, dirty/staged counts, XML size+hash, headroom status, commands run/not-run, caveats).
- **Repo path:** `docs/source-proxy-system-freeze-audit-20260621/glm-freeze-metadata.json`
- **Size:** see checksums.
- **SHA-256:** see `glm-checksums.sha256`.
- **How to use on Fold 7:** Open as JSON. Confirms the freeze was read-only, no source mutation, no commit/push, headroom-fallback used.

---

## Fold 7 Review Workflow

1. **Open `glm-source-proxy-audit-20260621.md` first.** Read §1 (verdict), §7 (debugging/taxonomy gap), §9 (A2/A5/A9 brain-switch), §12 (vs Codex).
2. **Use `glm-source-proxy-freeze-20260621.xml` as compact AI context** if you want a second AI's view on the same Source Proxy subset GLM audited.
3. **Keep `glm-checksums.sha256` beside both files** and verify after any transfer.
4. **Compare GLM audit with Codex audit** before approving cleanup. Key points to reconcile:
   - Does Codex agree `decision.py` (7,971 lines) is the top concentration risk?
   - Does Codex agree the failure taxonomy has no `MODEL_CAPABILITY_LIMIT` / `API_ESCALATION_RECOMMENDED` codes?
   - Does Codex agree A2 escalation is reasonable but A5/A9 should be local-capable after decomposition?
5. **Do NOT approve C1–C9 cleanup implementation** until both GLM and Codex views are reviewed and Britton signs off per-stage.

---

## Safety Confirmations (what this audit did NOT do)

- No source code patched, refactored, moved, or deleted.
- No files staged, committed, or pushed.
- No services restarted. No runtime state mutated.
- No SpiritFlix / media / Jellyfin files touched.
- No Set B/C, Stage 5, Plan 4, new engine, or new route.
- No packages installed. No secrets printed.
- Headroom proxy was down; the documented tight-profile fallback was used and verified PASS.

## Freeze Identity (quick reference)

- **HEAD:** `927055e489eb1dc9a263bf3a80cde53869e274ce`
- **Branch:** `master`
- **Dirty paths:** 0 · **Staged:** 0 · **Untracked:** 1 (0-byte `NDH6SA~M` temp artifact, outside scope)
- **Source-proxy dirty paths:** 0 · **SpiritFlix/media dirty paths:** 0
- **XML size:** 1,600,235 bytes · **XML files:** 414 · **XML SHA-256:** `a4693675…b16d6241`
- **Verdict:** PARTIALLY_HEALTHY · STRUCTURALLY_STRAINED · ANTI-CHEAT_STRONG · BRAIN-SWITCH_INCOMPLETE
