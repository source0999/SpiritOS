# GLM Repo Explainability Secondary Review — 2026-06-23

Independent secondary audit of the SpiritOS repo-explainability cleanup pass.
**Audit-only.** No source edits, no moves, no deletes, no staging, no commits,
no push, no merge. No resume of Plan 3 / Set A–C, no Plan 4 start, no
SpiritFlix / media / Jellyfin runtime mutation.

## Executive verdict

The repo-explainability pass is **real, honest, and useful**. The README
context-pack section, the runbook, the plan index, the Headroom honesty
contract, and the targeted invariant comments are all genuine improvements,
and the Headroom `tokens_saved > 0` proof reproduces against the generated
artifact. No production Source Proxy runtime behavior was changed; the only
behavioral change is in a context-generation script (`source-context-compress.mjs`)
and it is confined to pack generation.

There are **no blockers**. There are two real quality defects worth fixing
before this is called fully closed, and a larger pre-existing repo-hygiene
debt that the explainability pass did not address (and was not scoped to
address). Verdict: **GO_WITH_MINOR_CLEANUP_NOTES**. Source-cleanup work is GO;
repo-presentation readiness is still NEEDS_WORK and is tracked separately
below.

## Repo state

- Host reality differs from the prompt's notional Linux worktree path.
  `git worktree list` reports:
  - `//10.0.0.186/SpiritOS` → `428792e5` `[master]` (this audit host's checkout)
  - `/home/source/SpiritOS-cleanup-20260621` → `eacbef81` `[cleanup/full-repo-20260621]` **prunable** (worktree dir absent on this host)
- The target commit `eacbef817f8725799fe70daa578ff491de7135f8` is present as a
  git object and is the **tip** of `cleanup/full-repo-20260621`. All review
  was performed via read-only git plumbing against that commit and by
  materializing its tree into an isolated `/z/tmp-audit/run` scratch dir
  (untracked, left in place per audit boundaries).
- **Topology caveat (INFO):** `master` has diverged from the cleanup branch.
  `master` (HEAD `428792e5`) has 2 commits not on cleanup (`a9554366`,
  `428792e5` — SpiritFlix mobile benchmark); cleanup has 18 commits not on
  master. `eacbef81` is **not** an ancestor of `master`. This is expected for
  an unmerged feature branch but means the explainability work is not yet on
  the integration branch.
- `Z:\` (master) working tree is clean (`git status` empty). No unexpected
  staged files on either branch.
- Untracked generated context XMLs exist at repo root (`*context.xml`); all are
  correctly gitignored by `.gitignore:135 /*-context.xml`. Classified as
  expected generated outputs.

## Commit reviewed

```
eacbef817f8725799fe70daa578ff491de7135f8
Improve SpiritOS repo explainability and context pack docs
source0999 <tarotni33a@gmail.com>  Mon Jun 22 21:55:47 2026 -0400
```

12 files, +428 / −2. `git show --check`: **PASS** (no whitespace errors).
`git diff --check` (working tree): **PASS**.

## Diff summary

| Status | Path | Δ | Notes |
| --- | --- | --- | --- |
| M | `README.md` | +137 | New `LLM Context Packs / Repomix + Headroom` section |
| A | `docs/context-export/llm-context-pack-runbook.md` | +84 | Pack purposes, exclusions, Headroom verify |
| A | `docs/plans/README.md` | +31 | Plan-area index (active / paused / archived) |
| A | `docs/spiritos-full-repo-cleanup-20260621/repo-explainability-secondary-review-20260623.md` | +103 | Codex self-review |
| M | `scripts/source-context-compress.mjs` | +36 / −2 | **Behavioral**: `ensureRepomixCli()` + `isNodeRepomixCli()` |
| M | `source_proxy/decision/escalation_contract.py` | +6 | Invariant comment (misplaced as docstring) |
| M | `source_proxy/decision/packet_decomposition.py` | +6 | Invariant comment (misplaced as docstring) |
| M | `source_proxy/decision/worker_tool_adapters.py` | +6 | Invariant comment (misplaced as docstring) |
| M | `source_proxy/diagnostics/status_codes.py` | +6 | Invariant comment (misplaced as docstring) |
| M | `source_proxy/tasks/engine/state.py` | +6 | Invariant comment (misplaced as docstring) |
| M | `source_proxy/verification/anticheat/registry.py` | +6 | Invariant comment (misplaced as docstring) |
| M | `src/lib/coding/shell-registry.ts` | +3 | Invariant comment (correct) |

## README / context-pack review

- README `LLM Context Packs` section is **practical and correct**: explains
  external LLMs cannot see the repo, tells the operator to upload focused XML
  packs, lists 6 named packs with intended scope, gives copy-paste single-pack
  and all-packs commands, and states the visible output root is
  `/home/source/SpiritOS/`.
- `source-proxy-min` is correctly described as the existing focused profile,
  **not** as a whole-repo pack.
- The all-packs `COMMON_IGNORE` excludes `docs/evidence/**`, `docs/handoff/**`,
  `scripts/media/*.json`, `scripts/media/model_gallery/**`, media binary
  extensions, DBs, logs, node_modules, venvs, `repomix-output*.xml`, and
  `*context.xml`. Verified against the produced packs (see Headroom section).
- Headroom honesty contract is stated correctly: active only when
  `compressed="true"` **and** `tokens_saved > 0`; Tree-sitter alone is not
  Headroom.
- Runbook mirrors README, adds first-pack guidance and the explicit warning not
  to send `docs/evidence/**` unless auditing receipts.
- Minor doc consistency note (LOW): runbook's Headroom example shows
  `tokens_saved="1"` as the minimal positive value, which is technically right
  but reads oddly; not a defect.

## Headroom / context verification

Reproduced against the generated artifact on disk (`source-proxy-min-context.xml`,
1.2M, generated 2026-06-22 21:49):

```xml
<source_context_bundle compression="tree-sitter+headroom" generator="repomix,headroom-ai">
  <headroom compressed="true"
            tokens_before="388413" tokens_after="281567"
            tokens_saved="106846"
            compression_ratio="0.7249165192720121"
            fallback_used="false" fallback_reason="unknown"
            proxy="http://127.0.0.1:8798" />
```

- `compression="tree-sitter+headroom"` ✓
- `compressed="true"` ✓
- `tokens_saved="106846"` (> 0) ✓ — arithmetic checks out (388413 − 281567 = 106846)
- `fallback_used="false"` ✓

Matches Codex's claimed `tokens_saved=106846` exactly. Headroom is honestly
proven active on the maintained `source-proxy-min` path.

All-packs outputs (`repo-map`, `source-proxy`, `frontend`, `spiritflix-media-code`,
`docs-plans`) are raw Repomix XML with **no** `<source_context_bundle>` wrapper
and therefore do **not** claim Headroom — honest. Codex correctly states
Headroom proof was on `source-proxy-min`, not the ad-hoc all-packs command.

Bloat-exclusion scan of all 6 produced packs (node_modules, .next, evidence,
media data, repomix-output, venvs, pycache, volumes, jellyfin): **clean**,
with one expected/intentional case — `spiritflix-media-code-context.xml`
includes 7 `scripts/media/` files, all of which are code
(`face_organizer.py`, `mac_videotoolbox_encode.py`, `spiritflix_anime_import.py`,
etc.), matching the pack's documented `scripts/media/**/*.{py,mjs,sh}` include.
Not a leak.

`npm run context:source-proxy-min` and `npm run context:verify` were **not**
re-executed by this audit (Headroom proxy / venvs are on the cleanup branch's
Linux host, not this Windows audit host). Instead, Headroom truth was verified
by reading the metadata of the artifact Codex produced, and the verify script
was syntax-checked (`bash -n`: OK).

## Plan duplicate / stale structure review

This is the main structural finding. The explainability pass added a useful
plan *index* but the underlying repo still carries large structural debt that
the pass did not touch (and was not scoped to touch).

**New index (`docs/plans/README.md`)** classifies 9 top-level doc areas
(source-proxy pivot, cleanup breakpoint, cleanup F1–F10, media, media-server,
media plans, backup-system, cartographer evidence/receipts). It is index-only
and explicitly forbids auto-resume of Set A/B/C, Plan 3/4, media, Jellyfin,
backup, cartographer. Good.

**Index coverage gaps (MEDIUM):** the index omits several major sibling
doc trees that clearly exist and that a reader would expect to find in a
plan index:

| Path | Files | Status classification | In index? |
| --- | --- | --- | --- |
| `docs/full-repo-system-architecture-audit-20260621/` | 14 | GLM full-repo audit + freeze shards + checksums | **no** |
| `docs/source-proxy-system-freeze-audit-20260621/` | 5 | GLM source-proxy freeze + checksums | **no** |
| `docs/breakpoints/` (only the one subfolder) | 7 | referenced ✓ | yes |
| `docs/handoff/` | 146 | historical handoffs + vendored source | **no** |
| `docs/cartographer-level-2-apply-receipts/` | 1 | receipts | **no** |
| `docs/context-export/` | 5 | the runbook's own home | **no** |
| `docs/visual-proof/`, `docs/runbooks/` | 19 | — | **no** |
| **466 loose `.md` at `docs/` root** | 466 | phase closeouts / plans | **no** |

The three parallel `*-20260621` audit folders (`full-repo-system-architecture`,
`source-proxy-system-freeze`, `spiritos-full-repo-cleanup`) are **distinct**
(glM full-repo audit vs GLM source-proxy freeze vs the active F1–F10 cleanup)
and each has its own `glm-*` artifacts and `.sha256`. They are not duplicates
of content, but they are **unified sibling audits with no cross-reference**,
and only the third is indexed. A reviewer landing in one cannot easily tell
the other two exist or how they relate.

**Duplicate / vendored source tree (MEDIUM):** `docs/handoff/spiritflix-llm-pack/stage/`
contains **141 files** that are a full vendored snapshot of source
(`next.config.ts`, `middleware.ts`, `tsconfig.json`, `package.json`,
`src/lib/spiritflix/types.ts`, `scripts/media/spiritflix_anime_import.py`,
`services/jellyfin/docker-compose.yml`, …). This is a frozen handoff snapshot,
not live source, but it duplicates live-tree paths and is exactly the kind of
artifact that confuses grep-based review and inflates context packs. Candidate
for archive/index, not delete.

**Pre-existing root clutter (MEDIUM, not introduced by this pass):**
15 loose `.md` scratch/plans at repo root plus binary/runtime junk:

| Root file | Bytes | Classification |
| --- | --- | --- |
| `Transparent-ref2.png` | 506,276 | DELETE_CANDIDATE_REQUIRES_HUMAN (loose image) |
| `spiritos-chat-demo.zip` | 26,228 | ARCHIVE_CANDIDATE (demo bundle) |
| `nohup.out` | 1,520 | DELETE_CANDIDATE_REQUIRES_HUMAN (runtime log; gitignore says ignore but it's tracked) |
| `home` | 33 | DELETE_CANDIDATE_REQUIRES_HUMAN (stray 33-byte file) |
| `basic.js` | 341 | RENAME_CANDIDATE (orphan reporter class, no owner) |
| `masterOverhual.md`, `codingAgentOverhaul.md`, `cartographerBeta.md`, `cartogrpaherPlanAuto.md` (typo), `scouUi.md`, `scout0.2-0.3.md`, `scoutRefinemint.md` (typo), `spiritBlueprinter.md`, `productionProxy.md`, `post-v1-diag.md`, `v1prepPlan.md`, `notes.md` | — | ARCHIVE_CANDIDATE / RENAME_CANDIDATE (draft plans at root; 2 filename typos) |
| `DEPENDENCY_AUDIT.md`, `REPOMIX_OUTPUTS.md` | — | INDEX_ONLY (move under docs/) |

**Tracked generated screenshots (LOW):** `.codex-smoke/` is **tracked** with
PNGs (`chat-desktop-*.png`, `chat-mobile-*.png`, …) even though `.gitignore`
says `.codex-smoke/` should be ignored — committed before the ignore rule.
DELETE_CANDIDATE_REQUIRES_HUMAN or untrack+keep-local.

**Tracked generated XMLs in docs (INFO, intentional):** 38 `.xml` files under
`docs/` — mostly prior LLM context packs and GLM freeze shards under
`docs/evidence/` and the two freeze-audit folders. These are intentional
evidence, correctly placed, and correctly excluded from new context packs.
KEEP_EVIDENCE. Noted only because they are 60% of the reason a naive
full-repo pack is huge (the runbook already warns against this).

**No duplicated plan numbers / no same-plan-in-multiple-foldets** were found
inside the active cleanup tree (`docs/spiritos-full-repo-cleanup-20260621/`)
— its F01–F10 + per-shard `codex-review-report.md` structure is clean and
consistent.

## Unneeded / generated file review

- **No tracked `*context.xml` or `repomix-output*.xml`** anywhere in the tree
  at repo root or under `src/`. Generated context XMLs are correctly untracked
  and gitignored (`.gitignore:135 /*-context.xml`, `:137 repomix-output*.xml`).
- A 314 MB `spiritos-full-repo-context.xml` sits in the repo root on disk
  (untracked, ignored). INFO only — it is exactly the "huge useless pack" the
  runbook warns against; its presence on disk is untidy but it cannot be
  committed. Operator should delete it locally at their discretion (not an
  audit action).
- **Audit scratch disclosure:** this review created `Z:\tmp-audit\`
  (untracked, `?? tmp-audit/` in `git status`) to materialize the commit tree
  and run tests. It is **not** gitignored. Per audit boundaries it is left in
  place (no delete/move); Britton may `rm -rf Z:\tmp-audit` freely.

## Comment / docstring review

**Good.** Every added comment targets a real invariant, not syntax:
- `status_codes.py`: failure-taxonomy ownership; must not silently change
  verdict vocabulary or turn unknowns into positives.
- `anticheat/registry.py`: anti-cheat is an **audit layer**, does not repair
  or upgrade the underlying verdict.
- `escalation_contract.py`: brain-switch recommendations are **advisory /
  dry-run**; provider policy authority stays outside the module.
- `packet_decomposition.py`: local decomposition; benchmark labels stripped
  before shape selection to prevent tailoring.
- `worker_tool_adapters.py`: typed subprocess probe contract; failure class
  echoed for diagnosability.
- `tasks/engine/state.py`: side-effect-free task-state predicates.
- `shell-registry.ts`: `/coding` shell canonical-vs-alternate ownership
  boundary.
- `source-context-compress.mjs`: uploadable-XML boundary + honest Headroom
  fallback labeling.

No comment spam, no `// increment i`-style noise.

**Weak / defect (MEDIUM, F-DOC-1):** all 6 Python "module docstrings" are
placed **after** the `from __future__ import annotations` and other imports.
Verified by AST: `ast.get_docstring(module)` returns `None` for all 6 — they
are bare string-expression statements, invisible to `help()`, `pydoc`, IDE
hover, and docstring tooling. The *intent* is right and the prose is good;
the *placement* is wrong. They must move to the very top of the file (before
all imports, or immediately after `from __future__`) to become real module
docstrings. The files still compile and import fine (bare string exprs are
legal), so this is a quality defect, not a runtime defect.

**Noisy additions:** none.

## June 2026 repo structure scorecard

Honest scoring. The explainability pass is a real lift, but the repo as a
whole still has presentation debt it did not touch.

| # | Category | Score | Blocking | Note |
| --- | --- | --- | --- | --- |
| 1 | Human readability | 6/10 | no | Root clutter + 466 loose docs/.md hurt orientation despite good README. |
| 2 | AI context-pack readiness | 9/10 | no | Best-in-class for this repo: 6 named packs, honest Headroom, bloat exclusions verified. |
| 3 | Active vs archived plan clarity | 5/10 | no | New index is good but covers 9 of ~25 doc areas; 3 parallel 20260621 audits ununified; 466 loose docs un-indexed. |
| 4 | Generated artifact hygiene | 8/10 | no | Context XMLs correctly gitignored & untracked; minus for tracked `.codex-smoke/` PNGs and 314MB local pack. |
| 5 | Runtime / source separation | 7/10 | no | `nohup.out`, `home`, `basic.js`, demo `.zip` at root blur the line; `docs/handoff/.../stage/` duplicates source. |
| 6 | Testability | 8/10 | no | 40/40 backend pass; typecheck pass; verify script solid. |
| 7 | Safety boundary clarity | 9/10 | no | Plan index, breakpoint, and self-review all state freeze/resume boundaries explicitly. |
| 8 | Comment / docstring quality | 6/10 | F-DOC-1 | Good semantic content; 6/6 Python docstrings misplaced (invisible to tooling). |
| 9 | Duplicate / stale file control | 4/10 | no | 466 loose docs/.md, 141-file vendored `stage/`, tracked smoke PNGs, root scratch — substantial debt. |
| 10 | Portfolio / demo walkthrough readiness | 5/10 | no | README context section is strong; root clutter and doc sprawl would embarrass a walkthrough. |

Weighted takeaway: **source-cleanup work = GO**; **repo presentation readiness =
NEEDS_WORK** (categories 1, 3, 5, 9, 10).

## Tests / checks run

| Check | Result |
| --- | --- |
| `git show --check eacbef81` | PASS (no whitespace errors) |
| `git diff --check` (working tree) | PASS |
| `python3 -m pytest test_status_codes test_anticheat_registry test_brain_switch_contract test_packet_decomposition -q` (on materialized `eacbef81` tree) | **40 passed in 9.89s** |
| `npm run typecheck` (master worktree; toolchain valid; only TS change in commit is 3 comment lines) | PASS (exit 0) |
| `bash -n verify-repomix-context.sh`, `bash -n headroom-check.sh` | PASS |
| `node --check source-context-compress.mjs` | PASS |
| Headroom metadata reproduced from `source-proxy-min-context.xml` | PASS (`tokens_saved=106846`, `fallback_used="false"`) |
| Bloat-exclusion scan of 6 produced packs | PASS (1 intentional media-code inclusion) |
| `npm run context:source-proxy-min` / `context:verify` re-run | **NOT RUN** — Headroom proxy/venvs are on the cleanup branch's Linux host, not this Windows audit host. Truth established by reading the produced artifact instead. |

## Findings table

| ID | Severity | Path | Finding | Evidence | Recommendation |
| --- | --- | --- | --- | --- | --- |
| F-DOC-1 | **MEDIUM** | `source_proxy/{diagnostics/status_codes,verification/anticheat/registry,decision/escalation_contract,decision/packet_decomposition,decision/worker_tool_adapters,tasks/engine/state}.py` | 6 "module docstrings" placed after imports → `ast.get_docstring()` returns `None` for all 6; invisible to tooling | AST check: `module __doc__ = None; first stmt: ImportFrom` for each | Move each docstring to top of file (before imports, or directly after `from __future__ import annotations`) |
| F-SCR-1 | **MEDIUM** | `scripts/source-context-compress.mjs` | Commit headline says "comments/docstrings only" but this file adds real runtime logic: `ensureRepomixCli()` can trigger `npm install repomix@1.14.0` into `/tmp` | Diff adds `ensureRepomixCli`/`isNodeRepomixCli` with `execFileSync("npm",[…,"install",…])` | Disclosure is in the self-review Caveats; just ensure merge message / changelog reflects the behavioral change. Not a Source Proxy runtime change. |
| F-IDX-1 | **MEDIUM** | `docs/plans/README.md` | Index covers 9 of ~25 doc areas; omits `docs/full-repo-system-architecture-audit-20260621/`, `docs/source-proxy-system-freeze-audit-20260621/`, `docs/handoff/`, `docs/context-export/`, `docs/visual-proof/`, `docs/runbooks/`, and the 466 loose `.md` at `docs/` root | `grep` of index vs `git ls-tree -d docs/` | Extend index table to classify the omitted areas as historical/evidence; add a one-line "loose docs/ root files are historical phase closeouts, not an active queue" note |
| F-STRUCT-1 | **MEDIUM** | `docs/handoff/spiritflix-llm-pack/stage/` | 141-file vendored source snapshot duplicates live-tree paths | `git ls-tree -r -- docs/handoff/spiritflix-llm-pack/stage/` shows `next.config.ts`, `middleware.ts`, `src/lib/spiritflix/types.ts`, … | ARCHIVE_CANDIDATE — mark as frozen snapshot in index or move under an `archive/` prefix; do not delete |
| F-STRUCT-2 | **MEDIUM** | repo root | 15 loose `.md` scratch/plans + binary junk at root: `Transparent-ref2.png` (506KB), `spiritos-chat-demo.zip`, `nohup.out`, `home`, `basic.js`, plus typo'd drafts (`cartogrpaherPlanAuto.md`, `scoutRefinemint.md`) | `git ls-tree` root; `git cat-file -s` sizes | Move docs under `docs/`, untrack+gitignore runtime junk; requires human decision per file. Pre-existing, not from this pass. |
| F-STRUCT-3 | **LOW** | `.codex-smoke/` | Tracked PNG screenshots despite `.gitignore` rule `.codex-smoke/` | `git ls-tree -r -- .codex-smoke` lists PNGs; `git check-ignore` confirms rule exists | DELETE_CANDIDATE_REQUIRES_HUMAN (untrack, keep local) |
| F-STRUCT-4 | **LOW** | `docs/{full-repo-system-architecture,source-proxy-system-freeze}-audit-20260621/` | Two sibling GLM freeze audits not cross-referenced from the active cleanup folder or index | `git ls-tree` both dirs show `glm-*` freeze shards + `.sha256` | INDEX_ONLY — add one cross-reference line each in `docs/plans/README.md` |
| F-PACK-1 | **INFO** | repo root (disk only) | 314MB `spiritos-full-repo-context.xml` local file (untracked/ignored) — the exact "huge useless pack" the runbook warns against | `ls -lh` on disk | Operator deletes locally; not an audit action |
| F-TOPO-1 | **INFO** | branch topology | `eacbef81` (cleanup tip) is not an ancestor of `master`; master has 2 SpiritFlix commits cleanup lacks | `git merge-base --is-ancestor` → NO | Expected for unmerged branch; just don't claim merge-ready |

## Recommended next cleanup pass

A focused, human-approved "repo presentation" pass (distinct from source
cleanup) could close most MEDIUMs in one sitting:

1. **Fix F-DOC-1** (5 minutes): relocate the 6 Python docstrings above imports.
2. **Extend `docs/plans/README.md`** (F-IDX-1, F-STRUCT-4): classify the
   remaining ~16 doc areas and the 466 loose root `.md` as historical/evidence
   with a one-line "not an active queue" note. Index only; no moves.
3. **Archive/index the vendored `stage/` tree** (F-STRUCT-1).
4. **Root cleanup (F-STRUCT-2, F-STRUCT-3)** under human sign-off: untrack
   `.codex-smoke/` PNGs, `nohup.out`, `home`, `Transparent-ref2.png`,
   `spiritos-chat-demo.zip`; relocate or archive the 15 root `.md`.

None of these block the explainability verdict. All are presentation-layer.

## Hard no-go issues

**None.** No production runtime behavior changed, no merge/push performed, no
Plan 3/4 / Set A–C touched, no SpiritFlix/media/Jellyfin mutation, no falsified
Headroom proof, no generated XMLs committed.

## Final verdict

**GO_WITH_MINOR_CLEANUP_NOTES.**

The repo-explainability objectives (context-pack docs, Headroom honesty,
plan index, invariant comments) are met and verified. The two real defects
(F-DOC-1 misplaced docstrings, F-SCR-1 under-disclosed script behavior change)
are minor, do not change Source Proxy runtime behavior, and are fixable in
minutes. The larger structural debt (F-IDX-1, F-STRUCT-1/2/3) is pre-existing,
out of scope for this pass, and does not block secondary-review acceptance of
the explainability work itself. Merge-readiness is **not** claimed here (see
F-TOPO-1).
