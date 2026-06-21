# SpiritOS Full-Repo Cleanup — P0 Breakpoint Readback

**Date:** 2026-06-21
**Operator:** GLM (cleanup planning owner; NOT acceptance authority)
**Verdict:** `BLOCKED_HUMAN` — frozen audit evidence checksums fail; see §3.

This readback records exactly what was verified during P0 and the discrepancy
that halts the cleanup *before* any planning or source edits. No source was
modified. No branch or worktree was created. The primary worktree was only read.

> **Re-verification (turn 2):** The cleanup task was re-issued with the same
> request. P0 was re-run from scratch. The blocker is **unchanged and stable**.
> `sha256sum -c glm-full-repo-checksums.sha256` (run from `Z:\` repo root)
> still exits 1 with the same three shards failing:
> shard-001 (`fbe676…` recorded vs `d1e6f7…` actual),
> shard-002 (`4666eb…` recorded vs `bff9c9…` actual),
> shard-003 (`2f18e3…` recorded vs `04c831…` actual).
> Shard byte content is identical to the first P0 run, so the evidence was
> **not reconciled** between turns. breakpoint-state.json still parses;
> `cleanup_roadmap.implementation_started` is still `False`; approved HEAD is
> still `927055e4`. Branch `master`, current HEAD `728a7c82`, working tree
> clean apart from this untracked readback dir. No branch/worktree created.
> The decision in §5 is still required before P1 can begin.

---

## 1. Repository identity and path discrepancies (recorded, per "use the evidence")

The task body names the primary repo as `~/SpiritOS`. The harness environment
names the primary working directory as `Z:\`. Evidence resolves the conflict:

| Field | Task body | Harness / git reality | Evidence |
|---|---|---|---|
| Primary working dir | `~/SpiritOS` | `Z:\` | harness env header |
| `Z:\` resolves to | — | `//10.0.0.186/SpiritOS` (SMB share) | `git -C /z rev-parse --show-toplevel` |
| `~/SpiritOS` (Dell local) | primary | a *different* clone | `C:/Users/smith/SpiritOS`, branch `main`, HEAD `563dd79`, sparse checkout, dirty |

**Decision:** The repo matching the task's git snapshot
(branch `master`, HEAD `728a7c82`, recent commit `728a7c82 docs: preserve
proxy freeze and cleanup breakpoints`) is `Z:\` (the share). That is the
evidence-bearing primary repo and was used for all reads. `~/SpiritOS` on the
Dell is a divergent clone (`main`/`563dd79`) and was **not** used as the
primary; it was only inspected enough to confirm it is a separate checkout.

Additional path-format discrepancy (cosmetic, recorded only):
- breakpoint-state.json records `repo.path = "/home/source/SpiritOS"` and
  `repo.host = "source-server"` (Linux path), while the reachable share is
  `//10.0.0.186/SpiritOS` (`Z:\`). Same logical repo; the JSON used the
  Linux-side mount path. Not a blocker by itself.

## 2. P0 verification that PASSED

| Check | Command | Result |
|---|---|---|
| breakpoint-state.json parses | `python3 -c "json.load(open(...))"` | PASS |
| breakpoint required files exist | ls of README/breakpoint-state.{json,md}/resume-map/evidence-index/validation | all OK |
| full-repo metadata.json parses | `json.load` | PASS |
| prior source-proxy audit dir exists | ls `docs/source-proxy-system-freeze-audit-20260621/` | exists (6 files) |
| audit HEAD reachable | breakpoint metadata `head = 927055e4…` | reachable; `927055e4` is ancestor of `728a7c82` (linear) |
| breakpoint HEAD ancestry | `git merge-base --is-ancestor 927055e4 728a7c82` | YES (linear descendant) |
| Expected state per breakpoint | F0 complete; F1–F10 not started; Plan 3 NEEDS_FIX; A2/A5/A9 unresolved; Set B/C not run | matches breakpoint-state.json exactly |

### 2a. Commit gap (breakpoint HEAD `927055e4` → current `728a7c82`)

Two commits past the breakpoint, both by `source0999`, both docs/SpiritFlix:

```
728a7c82 2026-06-21 15:23:42 -0400  docs: preserve proxy freeze and cleanup breakpoints
1f1d3e81 2026-06-21 15:23:07 -0400  feat: add anime series playback and dual-audio import
```

Files changed across the gap: breakpoint docs, the three audit dirs, and
SpiritFlix/media (anime importer — a **protected** path). Classification:

- **Cleanup-owned source touched: NONE.** Verified by
  `git diff --name-only 927055e4..728a7c82 -- <every cleanup-owned path>`
  → empty.
- The gap merely *committed* the previously-untracked breakpoint/audit docs
  and the protected SpiritFlix WIP. No source_proxy / coding loop change.

Current working tree of `Z:\`: **clean** (0 dirty files).

## 3. P0 verification that FAILED — the blocker

### Audit shard checksums do NOT verify.

Run from repo root:
```
$ cd /z
$ sha256sum -c docs/full-repo-system-architecture-audit-20260621/glm-full-repo-checksums.sha256
docs/.../glm-full-repo-audit-20260621.md:      OK
docs/.../glm-full-repo-mobile-index.md:        OK
docs/.../glm-full-repo-metadata.json:          OK
docs/.../glm-headroom-repair-log.md:           OK
docs/.../glm-full-repo-freeze-20260621-shard-001.xml: FAILED
docs/.../glm-full-repo-freeze-20260621-shard-002.xml: FAILED
docs/.../glm-full-repo-freeze-20260621-shard-003.xml: FAILED
docs/.../glm-full-repo-freeze-20260621-shard-index.md: OK
sha256sum: WARNING: 3 computed checksums did NOT match
EXIT=1
```

The mismatch is corroborated by **three independent records** disagreeing with
the on-disk bytes:

| Shard | Recorded bytes (checksums.sha256, metadata.json, shard-index.md all agree) | Recorded SHA-256 | Actual on-disk bytes | Actual on-disk SHA-256 |
|---|---|---|---|---|
| shard-001.xml | 1,769,609 | `fbe676b55f4a4ceb550cea3f0f73567d605ace25c06f1a18cd5c1cf4efc8b82b` | 1,769,550 | `d1e6f74e2059aaafbee537be5348c92082d1547fd0e7edd0145c41dae8f143fd` |
| shard-002.xml | 550,807 | `4666eb61e8a396130011af03f5ab70325299395dd04765c38c7a8e063adff530` | 550,808 | `bff9c938755a69ec3f7290f1c506ef9854a08089bc98a5f73eadc12286b57d19` |
| shard-003.xml | 1,883,468 | `2f18e3b1d51f3f177684b162263f812ef750e51e89bd22f073f5a8c2a33db34e` | 1,883,447 | `04c831ce91e7959a9cb62b54665d9e59ad2cce8bb8b67eb910119626cecc6130` |

Both **byte size and hash** disagree, for all three shards, in the same
direction. This is not a CRLF/encoding artifact (that would not also move the
byte counts by tens to hundreds of bytes).

### Root cause (evidence-backed timeline)

| File | mtime | role |
|---|---|---|
| `glm-full-repo-metadata.json` | 14:47:01 | records shard hashes `fbe676/4666eb/2f18e3` |
| `glm-full-repo-checksums.sha256` | 14:49:15 | records the *same* three hashes |
| shard-001/002/003 .xml | **15:23:35** | current bytes hash to `d1e6f7/bff9c9/04c831` |
| commit `728a7c82` ("preserve proxy freeze…") | **15:23:42** | committed shards + the stale checksum file together |

The three shard XMLs were **regenerated at 15:23:35**, ~34 minutes after the
checksum file was written (14:49), and were committed 7 seconds later in
`728a7c82`. The checksum file was committed **as-is** with the pre-regeneration
hashes. Result: the "frozen audit evidence" the cleanup must build on is
internally inconsistent — the committed bytes are not the bytes that were
hashed and recorded as the freeze.

## 4. Why this halts the cleanup (constitutional mapping)

- **Source-of-truth order:** "If audit checksums fail, stop with NEEDS_FIX."
- **Human-only blockers:** "failed audit/breakpoint integrity checks."
- **Non-cheating constitution J (No evidence fabrication):** a cleanup plan
  that treats shards as verified ground-truth when they fail their own recorded
  hashes would be relying on unverified evidence. The task explicitly forbids
  "claim raw evidence exists unless the path exists" in a verified state.
- **I must not self-repair the evidence.** Re-running `sha256sum` to overwrite
  `glm-full-repo-checksums.sha256` with the new hashes, or regenerating the
  shards to match the old hashes, would itself be an undocumented mutation of
  frozen audit evidence by the very operator who is supposed to consume it —
  exactly the kind of integrity violation the constitution exists to prevent.
  The evidence files are not in my approved cleanup edit paths in any case.

The blocker is **narrow**: the cleanup-owned source is untouched by the gap,
and the *conclusions* in `glm-full-repo-audit-20260621.md` (which hashes OK)
are not implicated. Only the three shard `.xml` files fail to verify. But the
shards are named as **required** source-of-truth inputs ("all three shards
exist"), and F8/F10 in particular lean on the freeze evidence, so the
inconsistency cannot be silently ignored or worked around.

## 5. Exact decision requested from Britton

Reconcile the frozen-audit checksum contract. Specifically, choose one:

1. **Accept the current on-disk shards as canonical** and have Britton (not
   GLM) re-issue `glm-full-repo-checksums.sha256`, `glm-full-repo-metadata.json`
   `shards[]`, and the shard-index.md table with the *actual* hashes
   (`d1e6f7…` / `bff9c9…` / `04c831…`) and byte sizes, in a new evidence
   commit. This re-freezes the audit against the bytes that actually shipped.
2. **Restore the originally-hashed shards** (`fbe676…` / `4666eb…` / `2f18e3…`,
   1,769,609 / 550,807 / 1,883,468 bytes) from wherever they were before the
   15:23:35 regeneration, so the committed checksums verify again.
3. **Re-run the full-repo freeze cleanly** (regenerate shards + write a fresh
   checksum file in the same atomic step) under Britton's authority and record
   it as a new audit event.

After one of these, the frozen-audit checksums will verify, P0 can complete,
and GLM can proceed to P1 (write the durable cleanup packet) without touching
the evidence.

## 6. What was NOT done (held at the gate)

- No cleanup branch or worktree created.
- No acceptance contracts or holdout manifests frozen.
- No P1 plan packet written.
- No source edits of any kind, on any path.
- No git add/commit/push/branch/reset.
- Primary worktree (`Z:\`) read only; protected paths untouched.
- `~/SpiritOS` (Dell local clone) left exactly as found.

## 7. Files written by this P0 pass

- `docs/spiritos-full-repo-cleanup-20260621/breakpoint-readback.md` (this file)
- `docs/spiritos-full-repo-cleanup-20260621/baseline-manifest.json`

Both are new, untracked, documentation-only. They are **not** committed (the
gate stops before any commit). They exist only to hand the evidence to Britton.
