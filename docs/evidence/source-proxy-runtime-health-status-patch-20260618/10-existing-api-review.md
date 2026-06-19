# Existing API Review

## Existing routes

Source Proxy uses FastAPI in `source_proxy/main.py` and includes routers from `source_proxy/api/*`.

Relevant current routes before this patch:

- `/`: root service metadata.
- `/healthcheck`: legacy GPU/budget healthcheck in `source_proxy/api/healthcheck.py`.
- `/v1/self/status`: read-only Source Proxy manifest in `source_proxy/api/self_status.py`.
- `/v1/models`: model route status via the decision API.
- `/v1/cartographer/status`: read-only Cartographer status.
- `/docs` and `/openapi.json`: FastAPI docs/OpenAPI liveness surfaces.

Before this patch, `/health` and `/v1/health` returned 404 in live checkpoint evidence.

## Existing status/health behavior

`/healthcheck` is not a broad runtime status endpoint. It tries to collect VRAM and budget data and may return 503 if either diagnostic source is unavailable. It should remain untouched because callers may already depend on that narrow meaning.

`/v1/self/status` is a static-ish read-only manifest and does not summarize Next, Ollama loaded models, watchers, failed units, crash signals, dirty-tree authority, or valid/invalid health endpoints.

## Test conventions

Tests use both `unittest` and pytest style. FastAPI route tests commonly build a small `FastAPI()` app, include the router under test, and use `fastapi.testclient.TestClient`.

## Files likely to touch

- `source_proxy/main.py`
- `source_proxy/api/runtime_status.py`
- `source_proxy/decision/runtime_health.py`
- `source_proxy/tests/test_runtime_health_status.py`

## Files explicitly not touched

- Frontend/Next files.
- Browser verifier, repair loop, Qwen coder behavior, model lane logic, media/Jellyfin files, Docker/systemd files, and existing `/healthcheck` behavior.
