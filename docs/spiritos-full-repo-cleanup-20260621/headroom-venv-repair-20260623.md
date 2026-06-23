# Headroom Venv Repair - 2026-06-23

## Scope

Full-authority Headroom tooling repair only. No Source Proxy cleanup implementation, Set A/B/C, Plan 3/4, push, merge, SpiritFlix, media, or Jellyfin work was performed.

## Environment

- Worktree: `/home/source/SpiritOS-cleanup-20260621`
- Branch: `cleanup/full-repo-20260621`
- Venv path: `/home/source/SpiritOS/.venv-headroom`
- Headroom binary: `/home/source/SpiritOS/.venv-headroom/bin/headroom`
- Headroom version after repair: `0.27.0`
- Python: `3.12.3`

## Installed / Upgraded Packages

Installed into the existing Headroom venv with pip:

- `headroom-ai[code,ml,proxy]` upgraded from `0.26.0` to `0.27.0`
- `torch` installed as `2.12.1+cu130`
- `tree_sitter` installed as `0.25.2`
- `tree_sitter_languages` installed as `1.10.2`
- `tree-sitter-language-pack` installed as `0.13.0`
- `transformers` present as `5.12.1`
- `tokenizers` present as `0.22.2`
- `setuptools` and `wheel` refreshed for venv build/runtime support

Caveat: The pip resolver pulled CUDA-tagged `torch` dependencies even though CPU-safe runtime was preferred. No CUDA system stack was installed separately.

## Runtime Repair

`scripts/headroom-proxy-dev.sh` now honors `HEADROOM_BIN` when provided, so the cleanup worktree can launch the known Linux-native Headroom binary without requiring a local `.venv-headroom` copy.

Confirmed old Headroom test listeners on ports `8798` and `8799` were killed only after their command lines were verified as Headroom processes. A fresh Headroom proxy was started on `127.0.0.1:8798` with:

```bash
HEADROOM_PORT=8798 HEADROOM_HOST=127.0.0.1 HEADROOM_BASE_URL=http://127.0.0.1:8798 HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom HEADROOM_CODE_AWARE_ENABLED=1 HEADROOM_TARGET_RATIO=0.5 HEADROOM_COMPRESS_USER_MESSAGES=1 bash scripts/headroom-proxy-dev.sh
```

Health proof:

- `/health`: healthy
- Version: `0.27.0`
- Code-aware: enabled
- `compress_user_messages`: true
- `target_ratio`: `0.5`
- Port: `127.0.0.1:8798`

## Direct Compression Proof

Direct `/v1/compress` payload shape that works:

```json
{
  "messages": [{"role": "user", "content": "...large code/text payload..."}],
  "model": "gpt-4o",
  "token_budget": 1000,
  "config": {
    "compress_user_messages": true,
    "protect_recent": 0,
    "target_ratio": 0.5,
    "force_kompress": true
  }
}
```

Proof result:

- `tokens_before`: `11208`
- `tokens_after`: `5294`
- `tokens_saved`: `5914`
- `compression_ratio`: `0.47234118486795146`
- transform: `router:kompress:0.50`

The endpoint rejects bare `text` or `content` payloads with HTTP 400; the supported path is `messages`.

## Context Pipeline Repair

The context pipeline previously sent the full XML repository context as one very large user message. Headroom compressed normal code/text, but returned `router:noop` for that monolithic XML-shaped payload.

`scripts/source-context-compress.mjs` now:

- sends repository context to Headroom in chunks (`HEADROOM_CONTEXT_CHUNK_CHARS`, default `100000`)
- extends context compression timeout (`HEADROOM_CONTEXT_TIMEOUT_MS`, default `180000`)
- passes explicit Headroom config for user-message compression, target ratio, and analysis-context protection
- reassembles compressed Headroom message chunks into the final context XML
- labels Headroom active only when content changes and `tokens_saved > 0`
- preserves honest fallback metadata when savings are absent

## Context Pipeline Proof

Command:

```bash
HEADROOM_PORT=8798 HEADROOM_BASE_URL=http://127.0.0.1:8798 HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom npm run context:source-proxy-min

HEADROOM_PORT=8798 HEADROOM_BASE_URL=http://127.0.0.1:8798 HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom npm run context:verify
```

Result:

- `context:headroom:check`: PASS
- `context:source-proxy-min`: PASS
- `context:verify`: PASS
- bundle compression: `tree-sitter+headroom`
- Headroom active label: `compressed="true"`
- `fallback_used`: `false`
- `tokens_before`: `386311`
- `tokens_after`: `289522`
- `tokens_saved`: `96789`
- output size: `1.2M` / `1212507 bytes`
- verifier result: `PASS`, including positive Headroom token savings

Representative metadata:

```xml
<source_context_bundle compression="tree-sitter+headroom" generator="repomix,headroom-ai">
<headroom compressed="true" tokens_before="386311" tokens_after="289522" tokens_saved="96789" compression_ratio="0.7494531607953178" fallback_used="false" fallback_reason="unknown" proxy="http://127.0.0.1:8798" />
```

## Remaining Caveats

- The generated `repomix-output.*` files remain ignored artifacts and were not committed.
- The Python venv is intentionally not committed.
- Git still reports the pre-existing loose-object/gc maintenance warning during commits; no prune/gc cleanup was performed.
- The installed Torch wheel is CUDA-tagged because pip selected that wheel; no separate CUDA OS/runtime stack was installed.
