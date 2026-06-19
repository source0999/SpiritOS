# Live API Smoke

Command output is saved at `raw/live-api-smoke.txt`.

## Result

Live API smoke: `PARTIAL-GO/BLOCKED`.

The currently running Source Proxy process was not restarted, per the task boundary. Therefore the live process has not loaded the code changes yet.

Observed live responses:

- `GET https://127.0.0.1:8787/health`: HTTP `404`
- `GET https://127.0.0.1:8787/v1/health`: HTTP `404`
- `GET https://127.0.0.1:8787/v1/runtime/status`: HTTP `404`
- OpenAPI still lists `/healthcheck` and existing status routes, but not the new runtime-health routes.

## Interpretation

Code tests prove the new routes in-process. The live service needs a restart/reload to expose them, but no restart was approved and none was performed.
