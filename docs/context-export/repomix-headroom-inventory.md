# Repomix / Headroom inventory

## Where is the README command?

`README.md` § "Repository context bundles" (line ~674). **Updated** to `npm run context:source-proxy-min`.

## Does a repomix config exist?

Yes:

| Config | Purpose |
|---|---|
| `repomix.config.json` | Legacy full-tree (debug / `context:pack:full`) |
| `repomix.source-proxy-min.config.json` | **Canonical** Source Proxy + coding lane |
| `repomix.repo-map.config.json` | High-level repo map |

## Does Headroom exist?

**Yes.** `headroom-ai` npm dep, `.venv-headroom/`, `scripts/headroom-proxy-dev.sh`, `compress()` in `source-context-compress.mjs`.

## Is Headroom actually called?

**Yes, when proxy is reachable.** `buildRepositoryContextBundle()` always calls `compress()` from `headroom-ai`. When proxy is down, Headroom returns uncompressed fallback and `<headroom compressed="false" />`.

## Bloat directories (excluded from source-proxy-min)

| Path | On-disk size (approx) | In old 321 MB export? |
|---|---|---|
| `docs/evidence/` | 2.0 GB | Yes (markdown closeouts) |
| `scripts/media/` | 13 GB | Partial (HTML/JSON reports) |
| `node_modules/` | 1.2 GB | No (ignored) |
| `.next/` | 50 MB | No |
| `docs/handoff/` | 3.7 MB | Yes |
| Prior `repomix-output*.xml` | 321 MB each | Self-referential risk |

## Output formats

Per profile:

- `repomix-output.<profile>.xml` — LLM handoff (Tree-sitter ± Headroom)
- `repomix-output.<profile>.ast.xml` — mirror
- `repomix-output.<profile>.headroom.xml` — Headroom review copy
- `repomix-output.<profile>.full.xml` — raw Repomix (`--full`)

## Canonical command

```bash
npm run context:source-proxy-min
npm run context:verify
```

Larger map only when needed:

```bash
npm run context:repo-map
```
