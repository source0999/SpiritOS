# Repomix / Headroom test results

**Date:** 2026-06-20  
**PASS**

## Exact command run

```bash
rm -f repomix-output.source-proxy-min*.xml
npm run context:source-proxy-min
npm run context:verify
```

## Output

| Field | Value |
|---|---|
| Output path | `repomix-output.source-proxy-min.xml` |
| Output size | **1.5 MB** (1,577,xxx bytes after soak-logs exclusion) |
| Included file count | 439 (Repomix) / 430 (verify approx) |
| Compression | `tree-sitter` (Headroom proxy down) |

## Largest included files

1. `src/components/coding/CodingCommandCenterShell.tsx`
2. `source_proxy/api/decision.py`
3. `source_proxy/tasks/long_running.py`
4. `source_proxy/cartographer/service.py`
5. `source_proxy/tests/test_coding_regression_pack.py`

## Excluded bloat proof

Verify script confirms no included **paths** under:

- `node_modules/`, `.next/`, `dist/`
- `scripts/media/`
- `docs/evidence/`
- `repomix-output*`

## Headroom proof / fallback proof

- `npm run context:headroom:check` → proxy **not reachable** (exit 1)
- Bundle shows `compression="tree-sitter"`, `headroom compressed="false"`
- Fallback: `repomix.source-proxy-min.config.json` whitelist reduced output from **321 MB → 1.5 MB**

## Result

**PASS** — `npm run context:verify` exit 0
