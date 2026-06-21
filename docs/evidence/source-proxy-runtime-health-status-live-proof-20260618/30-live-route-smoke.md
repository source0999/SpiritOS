# Stage 3 Live Route Smoke

Raw smoke: `raw/30-live-route-smoke.txt`. OpenAPI JSON: `raw/openapi.json`.

## Route Results

| Route | HTTP | Result |
| --- | ---: | --- |
| `/health` | 200 | GO |
| `/v1/health` | 200 | GO |
| `/v1/runtime/status` | 200 | GO |

`/docs` also returned HTTP 200.

## OpenAPI

OpenAPI lists the new routes: `true`.

## Runtime Payload Truth

The runtime payload includes `status`, `service`, `timestamp`, `checks`, `valid_liveness_endpoints`, `invalid_legacy_health_endpoints`, and `notes`. The observed top-level runtime status was `NO_GO`. This is truthful rather than blindly green: it reports live routes working while also surfacing dirty authority and recent crash-signal checks.

Runtime check groups observed: `api, failed_units, git_authority, next, ollama, recent_crash_signals, watchers`.

Live route proof: `GO`. Runtime status truth: `GO`.
