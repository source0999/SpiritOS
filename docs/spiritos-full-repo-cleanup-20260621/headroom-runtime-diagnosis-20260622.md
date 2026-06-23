# Headroom Runtime Diagnosis - 2026-06-22

## Scope

Environment/tooling repair only. No Source Proxy cleanup implementation, Set A/B/C, Plan 3/4, push, merge, media, SpiritFlix, or Jellyfin work was performed.

## Initial State

- Cleanup worktree: `/home/source/SpiritOS-cleanup-20260621`
- Branch: `cleanup/full-repo-20260621`
- Git status before repair: clean
- CLI in PATH: not found
- Cleanup venv CLI: not found at `.venv-headroom/bin/headroom`
- Primary venv CLI: found at `/home/source/SpiritOS/.venv-headroom/bin/headroom`
- Old Z venv CLI: not found at `/z/.venv-headroom/bin/headroom`
- Port 8797: no listener; health failed
- Port 8798: no listener initially; health failed

## Repair Attempt

No package install was performed. No persistent service was created. No editor or unrelated process was killed.

The existing Linux-native Headroom CLI from `/home/source/SpiritOS/.venv-headroom/bin/headroom` was used by prepending that venv to PATH and launching the cleanup worktree script on port 8798:

```bash
env PATH="/home/source/SpiritOS/.venv-headroom/bin:$PATH" HEADROOM_PORT=8798 HEADROOM_HOST=127.0.0.1 bash scripts/headroom-proxy-dev.sh
```

The proxy became healthy after startup:

- `/health`: HTTP 200
- `/livez`: HTTP 200
- `/readyz`: HTTP 200
- `npm run context:headroom:check` with `HEADROOM_PORT=8798`: pass

A local ignored dependency shim was also repaired without install: `node_modules/repomix/bin/repomix.cjs` in the cleanup worktree had been replaced by a shell wrapper, which caused Node to throw `SyntaxError: Unexpected identifier 'node'`. It was backed up to `/tmp/cleanup-repomix.cjs.broken-20260622` and restored from the existing primary repo Repomix package at `/home/source/SpiritOS/node_modules/repomix/bin/repomix.cjs`.

## Compression Proof

The context pack was rerun with the healthy local proxy:

```bash
HEADROOM_PORT=8798 HEADROOM_BASE_URL=http://127.0.0.1:8798 npm run context:source-proxy-min
HEADROOM_PORT=8798 HEADROOM_BASE_URL=http://127.0.0.1:8798 npm run context:verify
```

The pack completed and produced `repomix-output.source-proxy-min.xml`, but it did not prove Headroom token savings:

- Bundle compression: `tree-sitter`
- Headroom metadata: `tokens_before="386058"`, `tokens_after="386058"`, `tokens_saved="0"`, `compression_ratio="1"`
- Wrapper output: `Headroom pass skipped or had no savings - Tree-sitter payload only (http://127.0.0.1:8798)`
- Verifier result: FAIL, because `compressed="true"` appears with non-positive `tokens_saved`
- Headroom `/stats`: zero API requests, zero requests compressed, zero total tokens saved

## Verdict

`BLOCKED_ENV_TREE_SITTER_FALLBACK_OK`

Headroom CLI and proxy runtime are usable on Linux at port 8798, but the required GO condition is not met because no positive `tokens_saved` or equivalent compression evidence was produced. Future context packs must be labeled as tree-sitter fallback only until the Headroom compression path returns positive savings or the metadata contract is repaired with approval.
