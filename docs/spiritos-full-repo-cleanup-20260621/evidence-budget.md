# Evidence Budget — F1–F10

What evidence each stage must produce and retain. Raw logs live **outside Git**
under the evidence root recorded in `cleanup-state.json`. Git holds
*evidence summaries* + hashes, not raw-log forests.

## Evidence root

- **Preferred:** `/home/source/spiritos-evidence/full-repo-cleanup-20260621/`
- **Fallback:** `/tmp/spiritos-full-repo-cleanup-20260621/`
- Chosen root is recorded in `cleanup-state.json` and `baseline-manifest.json`.
- If fallback is used: record why; do not claim the preferred root is available;
  do not count fallback storage as proof of the preferred path.

## Per-command record (constitution §10)

Every reported command in a stage's `evidence-summary.md` must include:
- exact command
- start time
- exit code
- decisive output excerpt
- raw evidence location (path under evidence root)
- SHA-256 of raw evidence (when retained)
- conclusion derived from the command

Forbidden: summarizing a command not run; claiming a raw-evidence path exists
when it doesn't.

## Per-stage evidence artifacts (in Git, in `Fxx/evidence-summary.md`)

- baseline command outputs + hashes (captured before source edits)
- per-increment focused-check results
- compatibility parity comparison (before/after)
- `operator-check.sh` run output
- holdout-check results
- fallback records (if any): primary path, failure class, fallback path,
  `fallback_used=true`, verdict effect, evidence ref
- stage verdict derivation

## Per-stage raw artifacts (outside Git, under evidence root)

- `Fxx/raw/` — full stdout/stderr of the baseline + operator-check + focused
  runs, retained with SHA-256.
- Naming: `<stage>/<increment>/<command-slug>.<out|err|json>` with a sibling
  `.sha256`.

## Retention vs. summarization

- **Retain raw** for: baseline, operator-check, holdout checks, any fallback,
  parity comparison, the terminal F10 battery.
- **Summarize (with excerpt + hash)** for: verbose intermediate test output
  where the decisive line is the pass/fail summary.
- Never retain secrets. Test commands that would print secrets are not run.

## F10 special: terminal battery evidence

F10 retains raw output for every battery item listed in its acceptance contract,
plus a single `f10-battery-manifest.json` mapping each item → exit code → raw
path → SHA-256 → conclusion. This is the primary artifact Codex reviews.

## Size discipline
- Shard XML freezes are excluded from cleanup evidence (they are audit artifacts).
- No re-dumping of source files into evidence; reference paths + hashes instead.
- If a stage's raw evidence exceeds ~50 MB, summarize more aggressively and keep
  the decisive excerpts + hashes.
