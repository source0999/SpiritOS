# Runtime Liveness

Generated from `raw/30-runtime-liveness.txt`, `raw/60-no-code-probes.txt`, and `raw/openapi-paths.txt`.

## Listeners

- Source Proxy: `0.0.0.0:8787`, `python` pid `35581`
- Next: `0.0.0.0:3000`, `next-server` pid `939993`
- Ollama: `127.0.0.1:11434`
- Jellyfin: `:8096`

Tmux sessions include `source-proxy-lan`, `spiritos-lan`, and `face-organizer-8765`.

## Source Proxy

- `https://127.0.0.1:8787/docs`: HTTP `200`, about `0.004s`
- `https://127.0.0.1:8787/openapi.json`: HTTP `200`, about `0.007s`
- `https://127.0.0.1:8787/health`: HTTP `404`
- `https://127.0.0.1:8787/v1/health`: HTTP `404`
- `https://127.0.0.1:8787/healthcheck`: HTTP `200`
- `https://127.0.0.1:8787/v1/self/status`: HTTP `200`
- `https://127.0.0.1:8787/v1/models`: HTTP `200`
- `https://127.0.0.1:8787/v1/cartographer/status`: HTTP `200`

Valid liveness proof is `/docs`, `/openapi.json`, `/healthcheck`, `/v1/self/status`, `/v1/models`, and Cartographer read-only status. `/health` and `/v1/health` remain invalid health endpoints.

## Next

- `https://127.0.0.1:3000/spiritflix/admin`: HTTP `200`, about `0.056s`

## Ollama

- `http://127.0.0.1:11434/api/tags`: HTTP `200`, about `0.140s`
- `http://127.0.0.1:11434/api/ps`: HTTP `200`, no loaded models

## Latency and noise

Status endpoints are fast. A full proxy/model test would still be noisy right now because no Ollama models are loaded, swap is in use, and prior evidence shows local rows can take tens to hundreds of seconds under contention.

## Verdict

- Source Proxy: `GO`
- Next: `GO`
- Ollama: `GO`
- Full proxy test now: noisy; not run.
