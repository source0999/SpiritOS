# Headroom Compression Debug - 2026-06-22

## Scope

Environment/tooling debugger only. This did not run Source Proxy cleanup, Set A/B/C, Plan 3/4, push, merge, or media/Jellyfin work.

## Pipeline Map

`npm run context:source-proxy-min` runs `node ./scripts/repomix-llm.mjs --profile source-proxy-min .`.

`repomix-llm.mjs` calls `buildRepositoryContextBundle()` from `scripts/source-context-compress.mjs`.

`source-context-compress.mjs` does this sequence:

1. Run Repomix with `--compress` into `repomix-output.source-proxy-min.ast-inner.xml`.
2. Extract the `<repository_context>` payload.
3. Probe `HEADROOM_BASE_URL` or default `http://127.0.0.1:8797` at `/health`.
4. Call `headroom-ai.compress()` with the repository context as a single `user` message.
5. Write `repomix-output.source-proxy-min.xml`, `.ast.xml`, and `.headroom.xml`.

## Proxy State

- Existing proxy on 8798: healthy.
- Headroom version: 0.26.0.
- Compression endpoint identified: `/v1/compress`, via the installed `headroom-ai` SDK and direct curl.
- `/health` exposes proxy readiness, not proof of compression.

## Root Cause

The context pipeline does call Headroom and uses the requested URL when `HEADROOM_BASE_URL=http://127.0.0.1:8798` is set.

The zero-savings behavior is caused by Headroom returning unchanged content:

- Default 8798 proxy config reports `compress_user_messages: false`.
- The context pack sends the repo context as one huge `user` message.
- Direct `/v1/compress` and SDK probes returned either `router:protected:user_message` or `router:noop`.
- `tokens_saved` stayed `0` and content stayed unchanged.
- The primary Headroom venv lacks `torch` and `tree_sitter`; proxy startup reports `Code-Aware: DISABLED (install headroom-ai[code] to enable)` and `[transformers] PyTorch was not found`.

There was also a metadata issue in the local context script: the `headroom-ai` SDK reports `compressed: true` after any successful `/v1/compress` call, even when `tokens_saved=0`. The script previously propagated that field into XML metadata. The verifier correctly rejected this as a false Headroom-compression claim.

## Fix Applied

`scripts/source-context-compress.mjs` now:

- Passes explicit context-compression config to Headroom: `compressUserMessages`, `protectRecent`, `targetRatio`, optional `forceKompress`, and optional `minTokensToCompress`.
- Labels Headroom as compressed only when all are true: Headroom says compressed, `tokens_saved > 0`, and output content differs from input content.
- Records `fallback_used` and `fallback_reason` in the XML metadata.
- Keeps tree-sitter fallback honest when Headroom health passes but no positive savings are produced.

## Current Classification

- A. context pipeline never calls Headroom: false.
- B. context pipeline calls wrong URL/port: false when `HEADROOM_BASE_URL` is set.
- C. Headroom proxy returns unchanged content: true.
- D. metadata detection is wrong but compression happened: false; metadata detection was wrong, but compression did not happen.
- E. context:verify is stale/wrong: false; it correctly rejected zero-savings Headroom claims.
- F. cleanup worktree lacks dependency/symlink expected by script: partially true for the previous Repomix shim repair; current compression blocker is Headroom dependency/capability, not the Repomix shim.

## Verdict

`BLOCKED_ENV_TREE_SITTER_FALLBACK_OK`

The health and routing path are repaired enough to produce honest context packs, but Headroom-active GO is still blocked because the current venv/proxy returns `tokens_saved=0`. Installing or rebuilding Headroom with the optional compression/code dependencies may be required, but that was not approved in this task.
