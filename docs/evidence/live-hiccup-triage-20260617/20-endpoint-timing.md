# Endpoint Timing

Raw output: `raw/20-endpoint-timing.txt`.

- Source Proxy `/health`: HTTP 404 in 0.0046s.
- Source Proxy `/v1/health`: HTTP 404 in 0.0049s.
- Source Proxy `/docs`: HTTP 200 in 0.0050s.
- Source Proxy `/openapi.json`: HTTP 200 in 0.2653s.
- Next HTTP `/spiritflix/admin`: HTTP 000/empty reply in 0.0011s because this lane is HTTPS.
- Next HTTPS `/spiritflix/admin`: HTTP 200 in 0.1005s.
- Ollama `/api/tags`: HTTP 200 in 0.0013s.

Interpretation: Source Proxy and Next were responsive when sampled. The Source Proxy health path names are not valid liveness endpoints here, but docs/openapi responded quickly.
