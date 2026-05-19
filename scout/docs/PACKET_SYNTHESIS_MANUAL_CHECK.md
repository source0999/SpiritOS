# Packet Synthesis Manual Check

Use this smoke after rebuilding Scout to verify the full raw event to verdict path.

```bash
cd ~/SpiritOS
docker compose --profile cpu -f scout/docker-compose.scout.yml up -d --build --force-recreate
curl -s http://localhost:8077/v1/scout/status | jq
curl -s -X POST http://localhost:8077/v1/scout/_debug/poll \
  -H "Content-Type: application/json" \
  -d '{"kind":"rss","url":"https://blog.python.org/feeds/posts/default"}' | jq
```

Wait for the extractor, packet synthesis, and debugger jobs to run, then inspect counts:

```bash
docker exec -i scout_v0_1 python - <<'PY'
from scout.config import get_settings
from scout.storage.db import open_connection

settings = get_settings()
conn = open_connection(settings.database_path)

for table in [
    "raw_event_index",
    "extracted_artifacts",
    "packets",
    "verdicts",
    "packet_embeddings",
]:
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count}")
    except Exception as e:
        print(f"{table}: ERROR {e}")
PY
```

Expected sequence:

- The forced RSS poll creates `raw_event_index > 0`.
- The extractor job creates `extracted_artifacts > 0`.
- `packets:synthesize_pending_artifacts` creates `packets > 0`.
- The debugger job later creates `verdicts > 0`.
- `packet_embeddings` may remain `0` unless Tier 3 embedding storage runs.

## Troubleshooting: Scout-to-Ollama Route Verification

Use this section when packet synthesis logs repeat `packet_synthesis_model_failed` or `litellm.APIConnectionError` for Ollama. These commands diagnose the route only. They do not fix Docker, compose, networks, services, or code.

### Host probe

Check whether the host can reach an Ollama API on port 11434:

```bash
curl -sS --max-time 5 http://localhost:11434/api/tags | jq . 2>/dev/null || true
```

Interpretation:

- Pass: the host has an Ollama API reachable at `localhost:11434`.
- Fail: the host route is not available, so Scout cannot use `host.docker.internal:11434` unless that route is created later.
- A host pass does not prove the Scout container can reach the same endpoint.

### Docker network inspection

Inspect Scout and Ollama network membership:

```bash
docker inspect scout_v0_1 --format '{{json .NetworkSettings.Networks}}' 2>/dev/null | jq . || true
docker inspect spirit-ollama --format '{{json .NetworkSettings.Networks}}' 2>/dev/null | jq . || true
```

Interpretation:

- Pass for container DNS: both containers share a Docker network and the Ollama container has a usable DNS name on that network.
- Fail for container DNS: Scout is on a different network from `spirit-ollama`, or `spirit-ollama` has no inspectable network membership.
- If Scout is only on `scout_default` and Ollama is not, `http://spirit-ollama:11434` should not be assumed to work from Scout.

### Ollama published port check

Check whether the `spirit-ollama` container publishes port 11434:

```bash
docker port spirit-ollama 2>/dev/null || true
```

Interpretation:

- Pass: Docker reports a host port mapping for the Ollama container.
- Fail: no container port is published. Scout may still reach another host-level Ollama, but the `spirit-ollama` container is not exposed through `docker port`.

### Scout container probes

First check which probe tool exists inside the Scout container:

```bash
docker exec scout_v0_1 sh -lc 'command -v curl || command -v wget || command -v python || true'
```

If `curl` exists:

```bash
docker exec scout_v0_1 sh -lc '
  echo "-- host.docker.internal --"
  curl -sS --max-time 5 http://host.docker.internal:11434/api/tags || true
  echo
  echo "-- spirit-ollama --"
  curl -sS --max-time 5 http://spirit-ollama:11434/api/tags || true
  echo
  echo "-- localhost from scout container --"
  curl -sS --max-time 5 http://localhost:11434/api/tags || true
'
```

If `wget` exists:

```bash
docker exec scout_v0_1 sh -lc '
  echo "-- host.docker.internal --"
  wget -qO- --timeout=5 http://host.docker.internal:11434/api/tags 2>&1 || true
  echo
  echo "-- spirit-ollama --"
  wget -qO- --timeout=5 http://spirit-ollama:11434/api/tags 2>&1 || true
  echo
  echo "-- localhost from scout container --"
  wget -qO- --timeout=5 http://localhost:11434/api/tags 2>&1 || true
'
```

If only `python` exists:

```bash
docker exec scout_v0_1 python - <<'PY'
from urllib.request import urlopen

for label, url in [
    ("host.docker.internal", "http://host.docker.internal:11434/api/tags"),
    ("spirit-ollama", "http://spirit-ollama:11434/api/tags"),
    ("localhost from scout container", "http://localhost:11434/api/tags"),
]:
    print(f"-- {label} --")
    try:
        with urlopen(url, timeout=5) as response:
            print(response.read().decode("utf-8")[:1000])
    except Exception as exc:
        print(type(exc).__name__, exc)
PY
```

Interpretation:

- Host route pass from inside Scout: `host.docker.internal:11434` is viable for Scout's model base URL.
- Container DNS route pass from inside Scout: `spirit-ollama:11434` is viable for Scout's model base URL.
- Localhost fail from inside Scout is expected unless Ollama runs inside the Scout container itself.
- If all Scout container probes fail, packet synthesis is not model-backed ready.
- Repeated `packet_synthesis_model_failed` after a successful route probe points to model configuration, credentials, payload, or application-level errors rather than basic routing.

Do not apply a code or Docker fix from this checklist. Record the route evidence, then request explicit approval for the chosen repair path.
