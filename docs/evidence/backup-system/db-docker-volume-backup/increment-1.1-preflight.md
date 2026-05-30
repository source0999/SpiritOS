# Increment 1.1 Preflight

Date: 2026-05-29

Checks run:

- `restic snapshots`: PASS
- `docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'`: PASS
- `docker volume ls`: PASS
- `git diff --check`: PASS

Observed restic:

- Existing file-level snapshot: `12865b16`

Observed Docker containers:

- `scout_v0_1`: `scout-scout-api`, healthy
- `spirit-ollama`: `ollama/ollama:latest`, healthy
- `spirit-searxng`: `searxng/searxng:latest`, healthy
- `source-postgres`: `postgres:16-alpine`, healthy
- `spirit-openedai-speech`: `ghcr.io/matatonic/openedai-speech-min:latest`, healthy
- `spirit-whisper`: `fedirz/faster-whisper-server:0.6.0-rc.3-cuda`, unhealthy
- `spirit-xtts`: `ghcr.io/coqui-ai/xtts-streaming-server:latest-cpu`, healthy

Observed Docker volumes:

- `backend_ollama_data`
- `backend_openedai_voices`
- `backend_searxng_data`
- `backend_source_postgres_data`
- `backend_whisper_cache`
- `backend_xtts_speakers`
- `bec52709bce0ff802788ac729cd59520aee08d81777d317b7cec6aa550d42dde`

Result: GO. Docker is available and no secret contents were printed.
