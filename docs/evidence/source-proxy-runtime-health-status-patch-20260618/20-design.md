# Design

## Endpoint paths

Add a new runtime health router with:

- `GET /health`
- `GET /v1/health`
- `GET /v1/runtime/status`

`/healthcheck` remains unchanged.

## Status schema

The endpoint returns a dictionary shaped like:

```json
{
  "status": "GO",
  "service": "source-proxy",
  "timestamp": "2026-06-19T00:00:00Z",
  "checks": {
    "api": {},
    "next": {},
    "ollama": {},
    "watchers": {},
    "git_authority": {},
    "failed_units": {},
    "recent_crash_signals": {}
  },
  "valid_liveness_endpoints": ["/health", "/v1/health", "/v1/runtime/status", "/docs", "/openapi.json"],
  "invalid_legacy_health_endpoints": [],
  "notes": []
}
```

Statuses are one of `GO`, `PARTIAL_GO`, `NO_GO`, `BLOCKED`, or `UNKNOWN`.

## Secret safety

The endpoint does not expose environment variables, process args, raw logs, journal lines, headers, tokens, or secret-shaped values. It returns only sanitized URLs, HTTP status codes, latency, model names from Ollama APIs, systemd unit names, watcher log paths/timestamps, and aggregate counts.

## Degradation behavior

All external checks degrade instead of throwing. Missing `systemctl`, `journalctl`, `git`, inaccessible watcher paths, HTTP timeouts, and JSON parse errors become `UNKNOWN`, `PARTIAL_GO`, or `NO_GO` check objects with concise details.

## Timeouts

- Next probe: 2 seconds.
- Ollama tags/ps probes: 2 seconds each.
- `git`: 3 seconds.
- `systemctl`: 2 seconds.
- `journalctl`: 3 seconds.

## Watcher logs

Watcher logs are summarized by file metadata only. The implementation scans the watcher directory tree shallowly, sorts recent files by mtime, and returns a small latest-log list. It does not read full log bodies.

## Dirty-tree status

Dirty-tree authority uses `git status --porcelain=v1 -z --untracked-files=all`.

- Any staged files are counted.
- Any dirty `source_proxy/` file makes `git_authority` `NO_GO`.
- Unrelated dirty files make `git_authority` `PARTIAL_GO`.
- Package/config/runtime helper dirty files are counted separately because they affect authority confidence.

## Failed units

Failed units use `systemctl --failed --no-legend --no-pager` with a short timeout. Only unit names are returned. Known unrelated failed units, including `mnt-spirit\x2dprojects.mount`, are notes and do not make the whole Source Proxy liveness status `NO_GO`.

## Scope boundary

This is not a model, benchmark, browser verifier, repair loop, Qwen coder, Docker, systemd, media, or Jellyfin patch. It only adds a truthful low-cost read-only runtime status surface.

## Test plan

- Route tests for `/health`, `/v1/health`, and `/v1/runtime/status`.
- Unit tests for Next success and timeout/refused behavior.
- Unit tests for Ollama tags/ps parsing.
- Unit tests for watcher active/log and missing-systemctl behavior.
- Unit tests for failed unit summarization without full logs.
- Unit tests for git authority `NO_GO` on dirty Source Proxy and `PARTIAL_GO` on unrelated dirt.
- Unit tests that status is not always GO.
- Secret-safety test to ensure env/token/secret/password-shaped content is not exposed.
