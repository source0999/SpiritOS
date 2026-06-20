# Repomix / Headroom preflight

**Date:** 2026-06-20T04:43:56-04:00  
**Host:** source-server  
**Repo:** /home/source/SpiritOS  
**HEAD:** 1b94053604eace0d70aab7b3597c06dfafcc459b

## README command (before patch)

```bash
npx repomix --config repomix.config.json .
# equivalent: npm run context:pack
```

## Existing config / scripts

| Path | Role |
|---|---|
| `repomix.config.json` | Legacy full-tree include `**/*` with ignore list |
| `scripts/repomix-llm.mjs` | Shim replacing `npx repomix` bin |
| `scripts/source-context-compress.mjs` | Tree-sitter Repomix + Headroom wrap |
| `scripts/headroom-proxy-dev.sh` | Headroom proxy on :8797 |
| `.venv-headroom/bin/headroom` | Local Headroom CLI venv |
| `.repomixignore` | Additional ignore patterns |

No `.headroom*` config file at repo root. Headroom is invoked via `headroom-ai` npm package `compress()`.

## Output size (before patch)

| File | Size |
|---|---|
| `repomix-output.xml` | **321 MB** |
| `repomix-output.ast.xml` | 321 MB |
| `repomix-output.headroom.xml` | 321 MB |

Headroom proxy on `http://127.0.0.1:8797` was **down**. README claimed ~1 MB but actual output matched full-tree bloat.

## Obvious bloat sources

- `repomix.config.json` `include: ["**/*"]` pulled nearly entire repo
- `docs/evidence/` (~2 GB on disk)
- `scripts/media/` (~13 GB generated face-organizer artifacts)
- `docs/handoff/spiritflix-llm-pack/spiritflix-only-repomix.xml` (33 MB packed handoff)
- Prior `repomix-output*.xml` at repo root
- `node_modules/`, `.next/`, caches, venvs
- Pivot plan `artifacts/`, `codex-review/`, `continuation-*` folders
