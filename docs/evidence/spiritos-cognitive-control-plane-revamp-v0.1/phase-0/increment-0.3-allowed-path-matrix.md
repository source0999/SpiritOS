# Increment 0.3 - Allowed Path Matrix and Anti-Scaffold Rules

## Preflight

- Repo path: `Z:\`
- Allowed files: `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/**`
- Inspected existing code/docs read-only through file discovery and text search.
- Forbidden: production source edits, provider calls, workers, Obsidian writes, git mutation.

## Implement

Created:

- `allowed-paths.json`
- `anti-scaffold-rules.md`
- `phase-0/increment-0.3-allowed-path-matrix.md`

## Verify

- Future implementation paths are marked not authorized yet: PASS
- Read-only inspection paths are separated from write paths: PASS
- Forbidden routes/actions are named: PASS
- Anti-scaffold rules include mentor refinements: PASS

## Observe

Commands run:

- `rg --files ...`
- `rg -n ... source_proxy src tests ...`

Skipped/unverified checks: none.

## Triage

Verdict: GO

Next authorized increment: Increment 0.4 - Current test baseline, no fixes.

