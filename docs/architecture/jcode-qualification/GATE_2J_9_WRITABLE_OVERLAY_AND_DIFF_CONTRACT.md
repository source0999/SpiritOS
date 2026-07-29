# Gate 2-J.9 Writable Overlay and Diff Contract

status: `OVERLAY_PLUS_INDEPENDENT_DIFF_SPECIFIED`

schema: `source-proxy.gate-2j-9-writable-overlay-and-diff-contract/v1`

JCode may edit files without gaining authority over the canonical repository. The canonical
repository state is Proxy-owned; JCode sees a disposable worktree with an isolated writable layer.

## 1. Construction (per task)

1. Create a disposable worktree of the sealed base commit under the run root
   (`/run/jcode-runs/<run_id>/worktree`). This is bind-mounted **read-only** at `/base` inside
   the sandbox. JCode cannot mutate the base.
2. Create a fresh empty writable upper directory (`/run/jcode-runs/<run_id>/upper`), bind-mounted
   **writable** at `/workspace` inside the sandbox. This is the only writable surface.
3. Symlink or copy the task's `allowed_paths` into the overlay so JCode can edit exactly those
   paths; protected paths are not present or are read-only.
4. Record the initial file manifest and SHA-256 of every allowed path before launch
   (`filesystem-ledger.initial.json`).

## 2. Recording (per run, Proxy-owned)

- Record every created, modified, deleted, renamed, and symlinked path in the overlay.
- Detect path traversal (`..`, absolute) and symlink escape (resolve and verify under overlay).
- Enforce protected paths independently of JCode (a protected-path write attempt is denied and
  recorded as a protected-path violation that maps to a non-`COMPLETED_VERIFIED` terminal).
- Collect the final Git diff **independently** from the Proxy side: `git -C <overlay>
  diff --no-index <base> <overlay>` semantics, or by computing the diff against the base commit.
- Collect untracked files independently.
- Refuse final verification when evidence is incomplete.
- Destroy the disposable execution environment after evidence sealing (overlay + worktree + home).
- Never `git commit` or `git push` from the JCode process. The dispatcher performs no commits;
  Proxy review/verification decide any later commit under separate authorization.

## 3. Path-class behavior

| Path class | Behavior |
|---|---|
| Binary files | diff is binary-safe; hashes recorded; not interpreted |
| Large files | size checked against file-size budget; oversized -> violation |
| Deleted files | deletion recorded; independent `git status` confirms |
| Renamed files | rename detected and recorded |
| Symlinks | symlink creation denied inside overlay (escape risk); existing symlinks resolved+checked |
| Submodules | submodule paths are protected; not writable |
| Generated files | only allowed_paths writable; generated files outside overlay are not captured as authored |
| Ignored files | `.gitignore` is Proxy-owned; ignored files are not part of the diff contract unless in allowed_paths |
| Permission changes | mode changes recorded |
| Ownership changes | not permitted (sandbox uid); attempted ownership change is a violation |
| Line-ending changes | normalized for diff hash; raw bytes also hashed |

## 4. Independent diff receipt

Output `diff-receipt.json` with: base commit, overlay root, list of changed files
(create/modify/delete/rename), per-file base SHA-256, per-file final SHA-256, symlink-escape
check result, protected-path check result, and the diff SHA-256. This receipt feeds
`evidence_hashes` and is the input to the Proxy reviewer/verifier/anti-cheat.
