# Scout Scope

Scout v0.1 is a Dell-local, read-only intelligence service for SpiritOS. It watches a small allowlist of public technical sources, extracts structured observations, and exposes those observations through a local REST API for later human-reviewed use.

Scout is not an agent loop, a code runner, a proxy memory writer, or a general web crawler. It does not execute fetched code, does not push into `source_proxy/`, and does not make autonomous promotion decisions on behalf of SpiritOS.

## Permitted Activities

1. Respectful polling of allowlisted GitHub repositories, RSS feeds, and named web pages.
2. Structured extraction from fetched content under bounded timeout and size limits.
3. Structured intelligence packet emission into Scout-owned storage.
4. Read-only REST serving on localhost for health, status, and packet retrieval.

## Prohibited Activities

1. Writing outside `scout/data/`.
2. Writing to the SpiritOS workspace, `source_proxy/`, or proxy databases.
3. Calling out to the proxy. Bridge calls are proxy-initiated only.
4. Executing fetched repository code or extracted snippets.
5. Auto-promoting intelligence into proxy memory.
6. Making unbounded external HTTP calls.
7. Sending unwrapped external content to an LLM.

## CPU-Only v0.1

Scout v0.1 runs CPU-only. GPU scheduling is deferred so Scout does not contend with the proxy's local LLM for VRAM on the Dell workstation. GPU profiles belong to the portability phase once the basic local service is stable.

## Kill Switch

Stop Scout:

```bash
docker compose -f scout/docker-compose.scout.yml stop
```

Disable scheduling without stopping the container:

```bash
curl -X POST http://localhost:8077/v1/scout/scheduler/pause
```
