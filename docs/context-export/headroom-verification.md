# Headroom verification

| Field | Value |
|---|---|
| `headroom_present` | **true** (`headroom-ai` package, `.venv-headroom`, `scripts/headroom-proxy-dev.sh`) |
| `headroom_called_by_readme_command` | **true** (`compress()` invoked in `source-context-compress.mjs` on every `context:source-proxy-min` run) |
| `headroom_output_used_by_repomix` | **false** at test time — proxy unreachable; Tree-sitter profile used as honest fallback |
| `fallback_profile_used` | **true** — `repomix.source-proxy-min.config.json` tight include/exclude |
| `before_size_bytes` | 336,592,896 (321 MB — `repomix-output.xml` pre-patch) |
| `after_size_bytes` | 1,586,028 (1.6 MB — `repomix-output.source-proxy-min.xml`) |
| `before_file_count` | thousands (full-tree pack) |
| `after_file_count` | 412 (approx, from verify script) |
| `verdict` | **GO with fallback** — uploadable context achieved via profile compression; Headroom adds further token savings when `npm run headroom:proxy` is running |

## How to prove Headroom active

```bash
npm run context:headroom:check          # proxy health
npm run headroom:proxy                  # terminal 1
npm run context:source-proxy-min        # terminal 2
grep -o 'compressed="[^"]*"' repomix-output.source-proxy-min.xml
```

Expect `compression="tree-sitter+headroom"` and `compressed="true"` with `tokens_saved > 0` when proxy is up.
