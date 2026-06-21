# No-Code Probes

Generated from `raw/openapi.json`, `raw/openapi-paths.txt`, and `raw/60-no-code-probes.txt`.

## OpenAPI

OpenAPI parsed successfully. Safe read-only/status endpoints found include:

- `/healthcheck`
- `/v1/self/status`
- `/v1/models`
- `/v1/cartographer/status`
- `/v1/cartographer/live-state`

`/v1/decisions/model-lanes/preview` exists as `POST`, not `GET`, so it was not called because this checkpoint avoided preview calls with ambiguous request bodies.

## Probes called

- `/healthcheck`: HTTP `200`
- `/v1/cartographer/status`: HTTP `200`
- `/v1/cartographer/live-state`: HTTP `200`
- `/v1/models`: HTTP `200`
- `/v1/self/status`: HTTP `200`

No coding task execution, apply/execute endpoint, benchmark battery, model generation request, or mutating endpoint was called.

## Key findings

- Source Proxy exposes valid read-only status and model inventory routes.
- Cartographer is observing/read-only with write actions disabled.
- Cartographer's live truth packet reports package/config dirty files as a blocker for authority gates.
- `/v1/models` confirms local Hermes and Qwen coder availability, but classifier is missing `phi4-mini:latest`.
