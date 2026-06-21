# Source-of-Truth Review

## Local Search: Ollama / 8TB / Model Path

```
config/backup.env.example:8:RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server
config/backup.env.example:12:SPIRIT_MAC_RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-mac-mini
config/backup.env.example:17:SPIRIT_WINDOWS_RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows
config/source-proxy.example.env:16:# 8TB drive, prove `OLLAMA_MODELS` or the Ollama home symlink/service path
config/source-proxy.example.env:17:# resolves to `/mnt/spirit-8tb/ollama-models`.
config/source-proxy.example.env:18:SOURCE_PROXY_OLLAMA_MODEL=hermes4
config/source-proxy.example.env:19:SOURCE_PROXY_CODER_OLLAMA_MODEL=qwen2.5-coder:7b
config/source-proxy.example.env:20:SOURCE_PROXY_CLASSIFIER_OLLAMA_MODEL=phi4-mini:latest
config/source-proxy.example.env:27:# Host-run proxy: http://127.0.0.1:11434. Docker same-network: http://spirit-ollama:11434
config/source-proxy.example.env:28:SOURCE_PROXY_OLLAMA_BASE_URL=http://127.0.0.1:11434
config/source-proxy.example.env:30:SOURCE_PROXY_OLLAMA_KEEP_ALIVE=-1
config/source-proxy.example.env:35:OLLAMA_KEEP_ALIVE=-1
./README.md:16:- `/mnt/spirit-8tb/converter/authorized-imports`
./README.md:17:- `/mnt/spirit-8tb/converter/audio`
./README.md:18:- `/mnt/spirit-8tb/converter/transcripts`
./README.md:19:- `/mnt/spirit-8tb/converter/knowledge`
./README.md:20:- `/mnt/spirit-8tb/converter/logs`
./README.md:43:ollama pull hermes4
./README.md:71:Hermes 4 is the default local intelligence model for SpiritOS chat and Source Proxy local routing. The expected local IDs are `hermes4:latest` and `hf.co/bartowski/NousResearch_Hermes-4-14B-GGUF:Q4_K_M`; keep `hermes3:8b-abliterated` available as the fast `/oracle`/voice-friendly fallback and keep `qwen2.5-coder:7b` selectable for explicit coding experiments. If Ollama models are intended to live on the 8TB drive, verify `OLLAMA_MODELS` or the Ollama service/home symlink resolves to `/mnt/spirit-8tb/ollama-models` before calling storage configured.
./README.md:338:**Brain vs TTS (do not conflate them):** `/api/spirit` uses `OLLAMA_MODEL` for `/chat` text generation. `/oracle` can use `ORACLE_OLLAMA_MODEL` when set. Voice is synthesized via same-origin **`/api/tts`** (`TTS_PROVIDER=piper` or `elevenlabs`); the browser never sees `ELEVENLABS_API_KEY`. Optional `ELEVENLABS_VOICE_SPEED` (default 1.12, clamped 0.7–1.2) sets ElevenLabs cadence; Voice settings can send a per-request `speed` override. **`GET /api/tts/voices`** feeds the Voice picker. **`ELEVENLABS_VOICE_ALLOWLIST`** supports **`Clarice:voice_id`** (recommended, no catalog read) or comma-separated **names only** (needs catalog + `voices_read`; if the catalog fails, switch to `Name:voice_id`). When any allowlist is set, the API returns **only** those voices - never the full catalog. Defaults prefer **`ELEVENLABS_DEFAULT_VOICE_ID`**, then **Clarice** by name, then **`ELEVENLABS_VOICE_ID`**. Response **`X-Spirit-TTS-Voice-Name-Encoded`** keeps display names ASCII-safe for Tailscale.
./README.md:400:SPIRIT_OLLAMA_SUPPORTS_TOOLS=false
./scoutRefinemint.md:2211:- `spirit-ollama` is not attached to `scout_default` in the observed Docker inspect output.
./scoutRefinemint.md:2212:- `docker port spirit-ollama` reports no published port.
./scoutRefinemint.md:2269:docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Networks}}' | grep -E 'scout|ollama|searxng|spirit' || true
./scoutRefinemint.md:2271:docker inspect spirit-ollama --format '{{json .NetworkSettings.Networks}}' 2>/dev/null | jq . || true
./scoutRefinemint.md:2272:docker port spirit-ollama 2>/dev/null || true
./scoutRefinemint.md:2275:docker logs --tail=300 scout_v0_1 2>&1 | grep -E 'packet_synthesis_model_failed|ollama|11434|model' || true
./scoutRefinemint.md:2287:- `http://spirit-ollama:11434/api/tags`
docs/hermes4-full-integration-closeout.md:20:8TB model storage is proven GO. `/mnt/spirit-8tb` is mounted and `/usr/share/ollama/.ollama` resolves to `/mnt/spirit-8tb/ollama-models`. Direct running-process `OLLAMA_MODELS` proof was blocked by `/proc` permissions, so the accepted proof is the mounted drive plus active Ollama home symlink.
docs/hermes4-full-integration-closeout.md:26:- Source Proxy local model: `ollama_chat/hermes4:latest`.
docs/hermes4-full-integration-closeout.md:34:- Ollama service/storage/model path checks.
docs/hermes4-full-integration-closeout.md:57:- Frontend chat: set `OLLAMA_MODEL=hermes3:8b-abliterated` or `OLLAMA_MODEL=qwen2.5-coder:7b` in the live frontend environment and restart Next when approved.
docs/hermes4-full-integration-closeout.md:58:- Source Proxy local route: set `SOURCE_PROXY_OLLAMA_MODEL=hermes3:8b-abliterated` or `SOURCE_PROXY_OLLAMA_MODEL=qwen2.5-coder:7b` and restart Source Proxy when approved.
docs/hermes4-full-integration-closeout.md:59:- Keep `ORACLE_OLLAMA_MODEL=hermes3:8b-abliterated` for fast oracle/voice-friendly use.
docs/hermes4-full-integration-closeout.md:66:- No `/mnt/spirit-8tb` ownership or symlink changes were made.
./productionProxy.md:1877:symlink-like path patterns if relevant
./productionProxy.md:2029:docs/local-ollama-provider-study.md
./productionProxy.md:2037:git diff -- docs/local-ollama-provider-study.md
./productionProxy.md:2054:git restore docs/local-ollama-provider-study.md source_proxy/agents source_proxy/tests
./services/jellyfin/docker-compose.yml:14:      - /mnt/spirit-8tb/services/jellyfin/config:/config
./services/jellyfin/docker-compose.yml:15:      - /mnt/spirit-8tb/services/jellyfin/cache:/cache
./services/jellyfin/docker-compose.yml:16:      - /mnt/spirit-8tb/services/jellyfin/transcodes:/transcodes
./services/jellyfin/docker-compose.yml:17:      - /mnt/spirit-8tb/services/jellyfin/web-overrides/index.html:/jellyfin/jellyfin-web/index.html:ro
./services/jellyfin/docker-compose.yml:18:      - /mnt/spirit-8tb/services/jellyfin/web-overrides/spirit-player-enhancer.js:/jellyfin/jellyfin-web/spirit-player-enhancer.js:ro
./services/jellyfin/docker-compose.yml:19:      - /mnt/spirit-8tb/services/jellyfin/web-overrides/spirit-player-enhancer.css:/jellyfin/jellyfin-web/spirit-player-enhancer.css:ro
./services/jellyfin/docker-compose.yml:20:      - /mnt/spirit-8tb/services/jellyfin/web-overrides/spiritos-mobile-swipes.js:/jellyfin/jellyfin-web/spiritos-mobile-swipes.js:ro
./services/jellyfin/docker-compose.yml:21:      - /mnt/spirit-8tb/media/movies:/media/movies:ro
./services/jellyfin/docker-compose.yml:22:      - /mnt/spirit-8tb/media/tv:/media/tv:ro
./services/jellyfin/docker-compose.yml:23:      - /mnt/spirit-8tb/media/music:/media/music:ro
./services/jellyfin/docker-compose.yml:24:      - /mnt/spirit-8tb/media/anime:/media/anime:ro
./services/jellyfin/docker-compose.yml:25:      - /mnt/spirit-8tb/media/other:/media/other:ro
./services/jellyfin/docker-compose.yml:26:      - /mnt/spirit-8tb/media/optimized-test:/media/optimized-test:ro
./services/jellyfin/sync_folder_playlists.py:22:JELLYFIN_DB = "/mnt/spirit-8tb/services/jellyfin/config/data/jellyfin.db"
source_proxy/tasks/long_running.py:30:from source_proxy.routing.ollama_route import (
source_proxy/tasks/long_running.py:33:    ollama_route_status_entry,
source_proxy/tasks/long_running.py:34:    resolve_classifier_ollama_model_name,
source_proxy/tasks/long_running.py:35:    resolve_coder_ollama_model_name,
source_proxy/tasks/long_running.py:36:    resolve_ollama_route,
source_proxy/tasks/long_running.py:3554:    classifier_model = route_model_for_alias("classifier") or f"ollama_chat/{resolve_classifier_ollama_model_name(probe=False)}"
source_proxy/tasks/long_running.py:3570:        "classifier_provider": route_provider_for_alias("classifier") or "ollama",
source_proxy/tasks/long_running.py:4318:                        f"(host={payload['api_base_host']}, model={payload['ollama_model']})"
source_proxy/tasks/long_running.py:5176:    provider = route_provider_for_alias(selected_alias) or ("ollama" if selected_alias == "local" else "")
source_proxy/tasks/long_running.py:5209:    local_route_status = ollama_route_status_entry() if provider == "ollama" else {}
source_proxy/tasks/long_running.py:5211:        "providerId": "local" if provider == "ollama" else provider or "unknown",
source_proxy/tasks/long_running.py:5212:        "providerLabel": "Local / Ollama" if provider == "ollama" else provider or "unknown",
source_proxy/tasks/long_running.py:5214:        "modelLabel": model.removeprefix("ollama_chat/") if model else "Unknown local model",
source_proxy/tasks/long_running.py:5215:        "family": "local/ollama/hermes" if provider == "ollama" else "unknown",
source_proxy/tasks/long_running.py:5220:        "externalCallAvailable": False if provider == "ollama" else bool(provider),
source_proxy/tasks/long_running.py:5231:        "configuredOllamaModel": local_route_status.get("ollama_model"),
source_proxy/tasks/long_running.py:5772:    ollama_route = resolve_ollama_route(probe=False)
source_proxy/tasks/long_running.py:5773:    coder_ollama_model = resolve_coder_ollama_model_name(probe=False)
source_proxy/tasks/long_running.py:5794:        ollama_base=ollama_route.api_base,
source_proxy/tasks/long_running.py:5795:        coder_ollama_model=coder_ollama_model,
scripts/media/import_extension_downloads.ps1:6:  [string]$RemoteInboxRoot = "/mnt/spirit-8tb/media-inbox/anime",
scripts/media/import_extension_downloads.ps1:83:  $remoteStageDir = "/mnt/spirit-8tb/media-processing/extension-import-stage"
scripts/backups/spiritos-backup-manifest.sh:41:ollama_data
scripts/media/recover_media_ingest_failures.mjs:5:const ROOT = process.env.MEDIA_INGEST_ROOT || "/mnt/spirit-8tb";
scripts/backups/spiritos-backup-docker-volumes.sh:20:  [ollama_data]="large runtime/model state"
scripts/backups/spiritos-backup-docker-volumes.sh:32:for volume in source_postgres_data ollama_data whisper_cache openedai_voices searxng_data; do
scripts/backups/spiritos-backup-docker-volumes.sh:34:  print_command docker run --rm -v "${volume}:/volume:ro" -v /mnt/spirit-8tb/spiritos-backups/docker-volumes:/backup alpine tar -C /volume -cf "/backup/${volume}.tar" .
scripts/backups/spiritos-backup-windows.ps1:19:$ResticRepository = if ($env:RESTIC_REPOSITORY) { $env:RESTIC_REPOSITORY } else { "/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-windows" }
scripts/backups/spiritos-backup-mac.sh:18:MAC_RESTIC_REPOSITORY="${SPIRIT_MAC_RESTIC_REPOSITORY:-/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-mac-mini}"
source_proxy/routing/ollama_route.py:12:_DEFAULT_OLLAMA_MODEL = "hermes4"
source_proxy/routing/ollama_route.py:13:_DEFAULT_OLLAMA_BASE = "http://127.0.0.1:11434"
source_proxy/routing/ollama_route.py:14:_DEFAULT_OLLAMA_HOME = "/usr/share/ollama/.ollama"
source_proxy/routing/ollama_route.py:15:_SPIRIT_8TB_ROOT = "/mnt/spirit-8tb"
source_proxy/routing/ollama_route.py:34:def ollama_base_url_candidates() -> list[str]:
source_proxy/routing/ollama_route.py:38:        "SOURCE_PROXY_OLLAMA_BASE_URL",
source_proxy/routing/ollama_route.py:39:        "OLLAMA_BASE_URL",
source_proxy/routing/ollama_route.py:40:        "OLLAMA_URL",
source_proxy/routing/ollama_route.py:48:        ordered.append(_DEFAULT_OLLAMA_BASE)
source_proxy/routing/ollama_route.py:52:def resolve_ollama_model_name() -> str:
source_proxy/routing/ollama_route.py:54:        os.getenv("SOURCE_PROXY_OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:55:        or os.getenv("OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:59:    return _DEFAULT_OLLAMA_MODEL
source_proxy/routing/ollama_route.py:77:def resolve_coder_ollama_model_name(*, probe: bool = True) -> str:
source_proxy/routing/ollama_route.py:79:    explicit = os.getenv("SOURCE_PROXY_CODER_OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:82:    route = resolve_ollama_route(probe=probe)
source_proxy/routing/ollama_route.py:87:    return resolve_ollama_model_name()
source_proxy/routing/ollama_route.py:90:def resolve_classifier_ollama_model_name(*, probe: bool = True) -> str:
source_proxy/routing/ollama_route.py:92:    explicit = os.getenv("SOURCE_PROXY_CLASSIFIER_OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:95:    route = resolve_ollama_route(probe=probe)
source_proxy/routing/ollama_route.py:103:def _ollama_model_available(model: str, available_models: tuple[str, ...]) -> bool | None:
source_proxy/routing/ollama_route.py:115:def _first_available_ollama_model(available_models: tuple[str, ...]) -> str | None:
source_proxy/routing/ollama_route.py:131:def _ollama_missing_model_reason(model: str, available_models: tuple[str, ...]) -> str:
source_proxy/routing/ollama_route.py:133:        return "ollama_models_unavailable"
source_proxy/routing/ollama_route.py:135:    return f"ollama_model_missing:{model}; available={sample}"
source_proxy/routing/ollama_route.py:138:def safe_ollama_host_label(api_base: str) -> str:
source_proxy/routing/ollama_route.py:147:def clear_ollama_route_cache() -> None:
source_proxy/routing/ollama_route.py:152:def resolve_ollama_route(*, probe: bool = True) -> OllamaRouteResolution:
source_proxy/routing/ollama_route.py:153:    candidates = ollama_base_url_candidates()
source_proxy/routing/ollama_route.py:154:    model = resolve_ollama_model_name()
source_proxy/routing/ollama_route.py:156:        os.getenv("SOURCE_PROXY_OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:157:        or os.getenv("OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:178:        requested_model=resolve_ollama_model_name(),
source_proxy/routing/ollama_route.py:180:        litellm_model=f"ollama_chat/{model}",
source_proxy/routing/ollama_route.py:207:        "ollama_chatexception",
source_proxy/routing/ollama_route.py:208:        "ollamaexception",
source_proxy/routing/ollama_route.py:221:    route = resolve_ollama_route(probe=False)
source_proxy/routing/ollama_route.py:222:    host = safe_ollama_host_label(route.api_base)
source_proxy/routing/ollama_route.py:226:        "provider": "ollama",
source_proxy/routing/ollama_route.py:228:        "ollama_model": route.model,
source_proxy/routing/ollama_route.py:239:def ollama_coder_route_status_entry() -> dict[str, str | bool | None]:
source_proxy/routing/ollama_route.py:240:    chat_route = resolve_ollama_route(probe=True)
source_proxy/routing/ollama_route.py:241:    coder_model = resolve_coder_ollama_model_name(probe=True)
source_proxy/routing/ollama_route.py:242:    model_available = _ollama_model_available(coder_model, chat_route.available_models)
source_proxy/routing/ollama_route.py:249:    storage = _ollama_model_storage_proof()
source_proxy/routing/ollama_route.py:252:        "provider": "ollama",
source_proxy/routing/ollama_route.py:253:        "model": f"ollama_chat/{coder_model}",
source_proxy/routing/ollama_route.py:254:        "requested_ollama_model": os.getenv("SOURCE_PROXY_CODER_OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:256:        "ollama_model": coder_model,
source_proxy/routing/ollama_route.py:257:        "api_base_host": safe_ollama_host_label(chat_route.api_base),
source_proxy/routing/ollama_route.py:262:        "available_ollama_model_fallback": fallback_model,
source_proxy/routing/ollama_route.py:270:            else "ollama_unreachable"
source_proxy/routing/ollama_route.py:272:            else _ollama_missing_model_reason(coder_model, chat_route.available_models)
source_proxy/routing/ollama_route.py:277:def ollama_classifier_route_status_entry() -> dict[str, str | bool | None]:
source_proxy/routing/ollama_route.py:278:    chat_route = resolve_ollama_route(probe=True)
source_proxy/routing/ollama_route.py:279:    classifier_model = resolve_classifier_ollama_model_name(probe=True)
source_proxy/routing/ollama_route.py:280:    model_available = _ollama_model_available(classifier_model, chat_route.available_models)
source_proxy/routing/ollama_route.py:287:    storage = _ollama_model_storage_proof()
source_proxy/routing/ollama_route.py:290:        "provider": "ollama",
source_proxy/routing/ollama_route.py:291:        "model": f"ollama_chat/{classifier_model}",
source_proxy/routing/ollama_route.py:292:        "requested_ollama_model": os.getenv("SOURCE_PROXY_CLASSIFIER_OLLAMA_MODEL", "").strip()
source_proxy/routing/ollama_route.py:294:        "ollama_model": classifier_model,
source_proxy/routing/ollama_route.py:295:        "api_base_host": safe_ollama_host_label(chat_route.api_base),
source_proxy/routing/ollama_route.py:300:        "available_ollama_model_fallback": fallback_model,
source_proxy/routing/ollama_route.py:308:            else "ollama_unreachable"
source_proxy/routing/ollama_route.py:310:            else _ollama_missing_model_reason(classifier_model, chat_route.available_models)
source_proxy/routing/ollama_route.py:315:def ollama_route_status_entry() -> dict[str, str | bool | None]:
source_proxy/routing/ollama_route.py:316:    route = resolve_ollama_route(probe=True)
source_proxy/routing/ollama_route.py:317:    model_available = _ollama_model_available(route.model, route.available_models)
source_proxy/routing/ollama_route.py:319:    fallback_model = _first_available_ollama_model(route.available_models)
source_proxy/routing/ollama_route.py:320:    storage = _ollama_model_storage_proof()
source_proxy/routing/ollama_route.py:323:        "provider": "ollama",
source_proxy/routing/ollama_route.py:325:        "requested_ollama_model": route.requested_model,
source_proxy/routing/ollama_route.py:326:        "ollama_model": route.model,
source_proxy/routing/ollama_route.py:327:        "api_base_host": safe_ollama_host_label(route.api_base),
source_proxy/routing/ollama_route.py:332:        "available_ollama_model_fallback": fallback_model,
source_proxy/routing/ollama_route.py:340:            else "ollama_unreachable"
source_proxy/routing/ollama_route.py:342:            else _ollama_missing_model_reason(route.model, route.available_models)
source_proxy/routing/ollama_route.py:347:def _ollama_model_storage_proof() -> dict[str, str]:
source_proxy/routing/ollama_route.py:348:    env_path = os.getenv("OLLAMA_MODELS", "").strip()
source_proxy/routing/ollama_route.py:354:                "proof": "OLLAMA_MODELS",
source_proxy/routing/ollama_route.py:360:            "proof": "OLLAMA_MODELS",
source_proxy/routing/ollama_route.py:363:    real_home = os.path.realpath(_DEFAULT_OLLAMA_HOME)
source_proxy/routing/ollama_route.py:364:    if real_home != _DEFAULT_OLLAMA_HOME:
source_proxy/routing/ollama_route.py:368:            "proof": f"{_DEFAULT_OLLAMA_HOME} symlink",
source_proxy/routing/ollama_route.py:374:        "proof": "default_ollama_home",
source_proxy/routing/ollama_route.py:388:        if _ollama_model_names_equivalent(candidate, selected_model):
source_proxy/routing/ollama_route.py:390:        if _ollama_model_available(candidate, available_models):
source_proxy/routing/ollama_route.py:395:def _ollama_model_names_equivalent(left: str, right: str) -> bool:
source_proxy/routing/ollama_route.py:415:        ok, models = _probe_ollama_tags(candidate)
source_proxy/routing/ollama_route.py:418:                "SOURCE_PROXY_OLLAMA_BASE_URL"
source_proxy/routing/ollama_route.py:419:                if index == 0 and os.getenv("SOURCE_PROXY_OLLAMA_BASE_URL", "").strip()
source_proxy/routing/ollama_route.py:421:                    "OLLAMA_BASE_URL"
source_proxy/routing/ollama_route.py:422:                    if candidate == os.getenv("OLLAMA_BASE_URL", "").strip().rstrip("/")
source_proxy/routing/ollama_route.py:424:                        "OLLAMA_URL"
source_proxy/routing/ollama_route.py:425:                        if candidate == os.getenv("OLLAMA_URL", "").strip().rstrip("/")
source_proxy/routing/ollama_route.py:444:def _probe_ollama_tags(api_base: str) -> tuple[bool, tuple[str, ...]]:
scripts/backups/spiritos-backup-dell.sh:16:RESTIC_REPOSITORY="${RESTIC_REPOSITORY:-/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server}"
scripts/backups/spiritos-backup-dell.sh:23:findmnt /mnt/spirit-8tb >/dev/null 2>&1 || warn "/mnt/spirit-8tb is not mounted or not visible"
scripts/backups/spiritos-restore-drill.sh:16:RESTIC_REPOSITORY="${RESTIC_REPOSITORY:-/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server}"
scripts/backups/spiritos-restore-drill.sh:19:DRILL_ROOT="${SPIRIT_RESTORE_DRILL_ROOT:-/mnt/spirit-8tb/spiritos-backups/restore-drills/$(date +%F)/$(date -u +%H%M%SZ)}"
scripts/backups/spiritos-restore-drill.sh:26:require_path_under "${resolved_target}" "/mnt/spirit-8tb/spiritos-backups/restore-drills"
scripts/backups/spiritos-backup-inventory.sh:26:  findmnt /mnt/spirit-8tb 2>&1 || true
scripts/backups/spiritos-backup-inventory.sh:27:  df -h /mnt/spirit-8tb 2>&1 || true
source_proxy/routing/litellm_router.py:8:from source_proxy.routing.ollama_route import (
source_proxy/routing/litellm_router.py:9:    clear_ollama_route_cache,
source_proxy/routing/litellm_router.py:10:    ollama_coder_route_status_entry,
source_proxy/routing/litellm_router.py:11:    ollama_classifier_route_status_entry,
source_proxy/routing/litellm_router.py:12:    ollama_route_status_entry,
source_proxy/routing/litellm_router.py:13:    resolve_classifier_ollama_model_name,
source_proxy/routing/litellm_router.py:14:    resolve_coder_ollama_model_name,
source_proxy/routing/litellm_router.py:15:    resolve_ollama_model_name,
source_proxy/routing/litellm_router.py:16:    resolve_ollama_route,
source_proxy/routing/litellm_router.py:30:    ollama_resolution = resolve_ollama_route(probe=True)
source_proxy/routing/litellm_router.py:31:    ollama_model = ollama_resolution.model
source_proxy/routing/litellm_router.py:32:    coder_ollama_model = resolve_coder_ollama_model_name(probe=True)
source_proxy/routing/litellm_router.py:33:    classifier_ollama_model = resolve_classifier_ollama_model_name(probe=True)
source_proxy/routing/litellm_router.py:34:    local_status = ollama_route_status_entry()
source_proxy/routing/litellm_router.py:35:    coder_status = ollama_coder_route_status_entry()
source_proxy/routing/litellm_router.py:36:    classifier_status = ollama_classifier_route_status_entry()
source_proxy/routing/litellm_router.py:46:            provider="ollama",
source_proxy/routing/litellm_router.py:47:            model=f"ollama_chat/{ollama_model}",
source_proxy/routing/litellm_router.py:53:            provider="ollama",
source_proxy/routing/litellm_router.py:54:            model=f"ollama_chat/{coder_ollama_model}",
source_proxy/routing/litellm_router.py:60:            provider="ollama",
source_proxy/routing/litellm_router.py:61:            model=f"ollama_chat/{classifier_ollama_model}",
source_proxy/routing/litellm_router.py:105:        if route_model.provider == "ollama":
source_proxy/routing/litellm_router.py:106:            litellm_params["api_base"] = resolve_ollama_route(probe=True).api_base
source_proxy/routing/litellm_router.py:107:            litellm_params["keep_alive"] = _parse_ollama_keep_alive(
source_proxy/routing/litellm_router.py:109:                    "SOURCE_PROXY_OLLAMA_KEEP_ALIVE",
source_proxy/routing/litellm_router.py:110:                    os.getenv("OLLAMA_KEEP_ALIVE", "-1"),
source_proxy/routing/litellm_router.py:165:    local_status = ollama_route_status_entry()
source_proxy/routing/litellm_router.py:174:        if route_model.alias == "local" and route_model.provider == "ollama":
source_proxy/routing/litellm_router.py:176:        if route_model.alias == "coder" and route_model.provider == "ollama":
source_proxy/routing/litellm_router.py:177:            item.update(ollama_coder_route_status_entry())
source_proxy/routing/litellm_router.py:178:        if route_model.alias == "classifier" and route_model.provider == "ollama":
source_proxy/routing/litellm_router.py:179:            item.update(ollama_classifier_route_status_entry())
source_proxy/routing/litellm_router.py:186:    clear_ollama_route_cache()
source_proxy/routing/litellm_router.py:189:def configured_local_ollama_model() -> str:
source_proxy/routing/litellm_router.py:190:    return resolve_ollama_model_name()
source_proxy/routing/litellm_router.py:193:def configured_local_ollama_base_url() -> str:
source_proxy/routing/litellm_router.py:194:    return resolve_ollama_route(probe=False).api_base
source_proxy/routing/litellm_router.py:197:def _parse_ollama_keep_alive(value: str) -> int | str:
scripts/media-ingest-worker.mjs:6:const ROOT = process.env.MEDIA_INGEST_ROOT || "/mnt/spirit-8tb";
scripts/agent-trials/run-aider-goose-local-agent-smoke.py:247:    shell_capture("ollama list || true", ENV_DIR / "ollama-list.txt")
scripts/agent-trials/run-aider-goose-local-agent-smoke.py:248:    shell_capture("ollama ps || true", ENV_DIR / "ollama-ps-before.txt")
scripts/agent-trials/run-aider-goose-local-agent-smoke.py:301:    result = run_cmd(["timeout", "30s", "ollama", "run", model, "say MODEL_READY in one line"], cwd=REPO, timeout=35)
scripts/agent-trials/run-aider-goose-local-agent-smoke.py:311:        ps = run_cmd(["ollama", "ps"], cwd=REPO, timeout=10)
scripts/agent-trials/run-aider-goose-local-agent-smoke.py:313:            second = run_cmd(["timeout", "60s", "ollama", "run", model, "say MODEL_READY in one line"], cwd=REPO, timeout=65)
scripts/agent-trials/run-aider-goose-local-agent-smoke.py:385:        cmd = ["aider", "--model", f"ollama_chat/{model}", "--yes", "--no-gitignore", "--no-auto-commits", "--message", PROMPT]
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:20:ROOT = REPO / "docs/evidence/source-proxy-context-orchestration-master-plan/plan-3/qwen-ollama-runtime-diagnostic"
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:25:CLEAN_COMMAND = "python3 scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py --clean"
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:70:        "env_ollama": shell("env | grep -E 'OLLAMA|CUDA|NVIDIA' || true", ENV / "env-ollama.txt"),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:71:        "docker_ollama": shell("docker ps | grep -i ollama || true", ENV / "docker-ollama.txt"),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:72:        "system_ollama": shell("systemctl status ollama --no-pager || true", ENV / "system-ollama.txt"),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:73:        "ps_before": shell("ps -ef | grep -E 'ollama|cn|aider|goose|continue|node' | grep -v grep || true", ENV / "ps-ollama-before.txt"),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:74:        "ollama_list": shell("ollama list || true", ENV / "ollama-list.txt"),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:75:        "ollama_ps_before": shell("ollama ps || true", ENV / "ollama-ps-before.txt"),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:78:        "disk": shell("df -h / /mnt/spirit-8tb || true", ENV / "disk.txt"),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:80:    ollama_list = captures["ollama_list"]["stdout"]
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:81:    docker_text = captures["docker_ollama"]["stdout"]
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:82:    system_text = captures["system_ollama"]["stdout"] + captures["system_ollama"]["stderr"]
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:90:        "qwen_installed": MODEL in ollama_list,
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:91:        "docker_ollama_running": "ollama" in docker_text.lower(),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:92:        "spirit_ollama_container": "spirit-ollama" in docker_text,
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:93:        "system_ollama_exists": "ollama.service" in system_text,
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:94:        "system_ollama_running": "Active: active (running)" in system_text,
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:95:        "duplicate_ollama_warning": ("ollama" in docker_text.lower()) and ("Active: active (running)" in system_text),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:96:        "qwen_loaded_before": MODEL in captures["ollama_ps_before"]["stdout"],
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:97:        "gpu_runner_before": "ollama" in nvidia_text.lower(),
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:99:        "stale_runner_processes": any(token in ps_text for token in ["ollama runner", "ollama_llama_server"]) and MODEL not in captures["ollama_ps_before"]["stdout"],
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:113:    before = run(["ollama", "ps"], timeout=20)
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:115:        ["timeout", "120s", "ollama", "run", MODEL, PROMPT],
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:122:    during_ps = run(["bash", "-lc", "ps -ef | grep -E 'ollama|cn|aider|goose|continue|node' | grep -v grep || true"], timeout=20)
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:125:        (ENV / "ps-ollama-during.txt").write_text(during_ps["stdout"] + during_ps["stderr"])
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:139:    after = run(["ollama", "ps"], timeout=20)
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:142:        "command": f'timeout 120s ollama run {MODEL} "{PROMPT}"',
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:148:        "ollama_ps_before": before["stdout"],
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:149:        "ollama_ps_after": after["stdout"],
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:245:        status = "BLOCKED_OLLAMA_UNREACHABLE"
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:246:    elif env["duplicate_ollama_warning"]:
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:258:    if env["duplicate_ollama_warning"]:
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:264:    if env["gpu_runner_before"] or any("ollama" in r.get("nvidia_smi_during", "").lower() for r in [cli_cold, cli_warm]):
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:271:    recommendation = "OPERATOR_DECISION_REQUIRED" if env["duplicate_ollama_warning"] else "NO_CHANGE_NEEDED"
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:278:            "systemctl status ollama --no-pager",
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:279:            "docker ps | grep -i ollama",
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:287:        "clean_duplicate_ollama": recommendation == "OPERATOR_DECISION_REQUIRED",
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:302:Duplicate Ollama should be cleaned first: {summary['clean_duplicate_ollama']}
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:329:<tr><th>Duplicate Ollama warning</th><td>{yesno(manifest['environment']['duplicate_ollama_warning'])}</td></tr>
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:370:    shell("ps -ef | grep -E 'ollama|cn|aider|goose|continue|node' | grep -v grep || true", ENV / "ps-ollama-after.txt")
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:371:    shell("ollama ps || true", ENV / "ollama-ps-after.txt")
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:401:Duplicate Ollama warning: {env['duplicate_ollama_warning']}
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:402:System Ollama running: {env['system_ollama_running']}
scripts/agent-trials/run-qwen-ollama-runtime-diagnostic.py:403:Docker Ollama running: {env['docker_ollama_running']}
scripts/agent-trials/run-lane-plumbing-repair.py:43:OLLAMA_API = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
scripts/agent-trials/run-lane-plumbing-repair.py:106:    raw_trace = load_json(ROUND1_ROOT / "lanes/raw-ollama-qwen/path-trace.json")
scripts/agent-trials/run-lane-plumbing-repair.py:110:    raw_text = read(ROUND1_ROOT / "lanes/raw-ollama-qwen/raw-transcript.txt")
scripts/agent-trials/run-lane-plumbing-repair.py:163:    qwen_smoke = ollama_generate("say READY in one line", timeout=30, num_predict=8)
scripts/agent-trials/run-lane-plumbing-repair.py:210:    result = ollama_generate(prompt, timeout=240, num_predict=1200)
scripts/agent-trials/run-lane-plumbing-repair.py:216:        "selected_model_call": "ollama /api/generate",
scripts/agent-trials/run-lane-plumbing-repair.py:518:    provider: ollama
scripts/agent-trials/run-lane-plumbing-repair.py:519:    apiBase: {OLLAMA_API}
scripts/agent-trials/run-lane-plumbing-repair.py:530:def ollama_generate(prompt: str, timeout: int, num_predict: int) -> CmdResult:
scripts/agent-trials/run-lane-plumbing-repair.py:531:    command = ["ollama-api-generate", OLLAMA_API, TARGET_MODEL]
scripts/agent-trials/run-lane-plumbing-repair.py:534:    request = urllib.request.Request(f"{OLLAMA_API}/api/generate", data=payload, headers={"Content-Type": "application/json"}, method="POST")
scripts/agent-trials/run-continue-qwen-real-env-debug.py:33:OLLAMA_API = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
scripts/agent-trials/run-continue-qwen-real-env-debug.py:183:        ["ollama", "list"],
scripts/agent-trials/run-continue-qwen-real-env-debug.py:184:        ["ollama", "ps"],
scripts/agent-trials/run-continue-qwen-real-env-debug.py:193:    write(ENV_DIR / "ollama-list.txt", results[7].text)
scripts/agent-trials/run-continue-qwen-real-env-debug.py:194:    write(ENV_DIR / "ollama-ps-before.txt", results[8].text)
scripts/agent-trials/run-continue-qwen-real-env-debug.py:222:    result = ollama_generate_smoke(
scripts/agent-trials/run-continue-qwen-real-env-debug.py:228:    write(ENV_DIR / "ollama-ps-during.txt", run_capture(["ollama", "ps"], timeout=20, missing_ok=True).text)
scripts/agent-trials/run-continue-qwen-real-env-debug.py:237:        "model_observed": TARGET_MODEL in read(ENV_DIR / "ollama-ps-during.txt") or TARGET_MODEL in output,
scripts/agent-trials/run-continue-qwen-real-env-debug.py:286:        "model_observed": TARGET_MODEL if TARGET_MODEL in read(ENV_DIR / "ollama-ps-during.txt") or "qwen" in (result.stdout + result.stderr).lower() else "unknown",
scripts/agent-trials/run-continue-qwen-real-env-debug.py:458:def ollama_generate_smoke(
scripts/agent-trials/run-continue-qwen-real-env-debug.py:467:    command = ["ollama-api-generate", OLLAMA_API, TARGET_MODEL]
scripts/agent-trials/run-continue-qwen-real-env-debug.py:478:        f"{OLLAMA_API}/api/generate",
scripts/agent-trials/run-continue-qwen-real-env-debug.py:486:        events.write(json.dumps({"ts": utc_now(), "event": "OLLAMA_API_GENERATE_START", "model": TARGET_MODEL}) + "\n")
```

## Local Search: Watchers / Monitors / Runtime

```
config/source-proxy.example.env:2:SOURCE_PROXY_PORT=8787
config/source-proxy.example.env:5:SOURCE_PROXY_DATA_DIR=data/source-proxy
scripts/spiritdesktop-windows/agent.js:12:// (or whatever path you launch from) and **restart** the Node process (`node agent.js`).
scripts/spiritdesktop-windows/agent.js:14://   http://<spiritdesktop-lan-ip>:3000/api/telemetry/self
scripts/spiritdesktop-windows/agent.js:25:const PORT = Number.parseInt(process.env.PORT || "3000", 10);
scripts/spiritdesktop-windows/agent.js:84:  if (s === "healthy" || s === "ok") return "Healthy";
scripts/spiritdesktop-windows/agent.js:86:  if (s === "critical" || s === "unhealthy" || s === "failed" || s === "pred fail") return "Critical";
scripts/spiritdesktop-windows/agent.js:148:  $health = $null
scripts/spiritdesktop-windows/agent.js:158:            try { $health = $disk.HealthStatus.ToString() } catch {}
scripts/spiritdesktop-windows/agent.js:172:              if ($vdHealth) { $health = $vdHealth }
scripts/spiritdesktop-windows/agent.js:182:            if (-not $health) {
scripts/spiritdesktop-windows/agent.js:187:                if ($poolHealth.Count -eq 1) { $health = $poolHealth[0] }
scripts/spiritdesktop-windows/agent.js:193:        if (-not $media -or $media -eq 'Unspecified' -or -not $health) {
scripts/spiritdesktop-windows/agent.js:199:              if (-not $health) { try { $health = $pd.HealthStatus.ToString() } catch {} }
scripts/spiritdesktop-windows/agent.js:229:    PhysicalHealthStatus = $health
scripts/source_proxy_today_handoff_bundle.py:16:    / "source-proxy-full-integration-pivot"
scripts/source_proxy_today_handoff_bundle.py:19:FIP_ROOT = ROOT / "docs" / "evidence" / "source-proxy-full-integration-pivot"
scripts/source_proxy_today_handoff_bundle.py:143:- Source Proxy URL: `https://127.0.0.1:8787`
scripts/source_proxy_today_handoff_bundle.py:144:- Latest receipt: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest`
scripts/source_proxy_today_handoff_bundle.py:145:- Latest trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace`
scripts/source_proxy_today_handoff_bundle.py:146:- By-run trace: `https://127.0.0.1:8787/v1/decisions/fip0-receipts/<run_id>/trace`
scripts/source_proxy_today_handoff_bundle.py:205:        "    <current_runtime>/home/source/SpiritOS via npm run proxy:https:lan on https://127.0.0.1:8787</current_runtime>",
scripts/source_proxy_today_handoff_bundle.py:337:        "zip_name": "britton-spiritos-source-proxy-handoff-2026-06-15.zip",
scripts/fip7_gauntlet_runner.py:10:BASE_URL = "https://127.0.0.1:8787"
scripts/fip7_gauntlet_runner.py:11:OUT_DIR = Path("docs/evidence/source-proxy-full-integration-pivot/fip-7R-gauntlet")
scripts/fip7_gauntlet_runner.py:41:        "target": "docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/repo-context-note.txt",
scripts/fip7_gauntlet_runner.py:62:        "target": "docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/design-context-note.txt",
scripts/fip7_gauntlet_runner.py:79:        "target": "docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/cartographer-note.txt",
scripts/fip7_gauntlet_runner.py:99:        "target": "docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/search-note.txt",
scripts/fip7_gauntlet_runner.py:117:        "target": "docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/scout-note.txt",
scripts/fip7_gauntlet_runner.py:151:        "target": "docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/skipped-lane-note.txt",
scripts/fip7_gauntlet_runner.py:167:        "target": "docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/repair-note.txt",
scripts/fip7_gauntlet_runner.py:187:                "docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/protected-trap.txt"
scripts/fip7_gauntlet_runner.py:201:        "target": "docs/evidence/source-proxy-full-integration-pivot/fip-7-targets/noop-note.txt",
./v1prepPlan.md:83:  curl -k -s https://localhost:3000/v1/cartographer/v1-proof-validation | jq .
./v1prepPlan.md:84:  curl -k -s https://localhost:3000/v1/cartographer/v1-combined-readiness-dry-run | jq .
./v1prepPlan.md:85:  curl -k -s https://localhost:3000/v1/cartographer/v1-readiness | jq .
./v1prepPlan.md:111:  curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-proposal | jq .
./v1prepPlan.md:112:  curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
./v1prepPlan.md:140:  curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
./v1prepPlan.md:141:  curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq .
scripts/integrated_level5r2_runner.py:38:    level5.level3.OUT_DIR = Path("docs/evidence/source-proxy-full-integration-pivot/integrated-level-5R2")
scripts/source-proxy-bootstrap.ps1:35:$VenvDir = if ($env:SOURCE_PROXY_VENV) { $env:SOURCE_PROXY_VENV } else { ".venv-source-proxy-windows" }
scripts/repomix-llm.mjs:26:Headroom proxy (port 8797 — not Source Proxy on 8787):
scripts/runtime-port-guard.sh:3:# tmux-managed production dev ports. Agents/smoke scripts must not kill these.
scripts/runtime-port-guard.sh:5:PROTECTED_RUNTIME_PORTS=(3000 8787 3001)
scripts/runtime-port-guard.sh:22:  [[ "$args" == *"next dev"* ]] && [[ "$args" == *"3000"* ]] && [[ "$args" == *"experimental-https"* ]]
scripts/runtime-port-guard.sh:34:    port_line="$(ss -ltnp 2>/dev/null | grep "pid=$pid" | grep ':3000 ' || true)"
scripts/runtime-port-guard.sh:81:      printf 'refusing to kill protected runtime port %s (tmux-managed; use npm run lan:restart)\n' "$port" >&2
scripts/runtime-port-guard.sh:114:  port_pids="$(listener_pids_on_port 3000)"
scripts/runtime-port-guard.sh:121:      printf 'refusing to kill foreign listener on :3000 pid=%s\n' "$pid" >&2
scripts/runtime-port-guard.sh:124:  # Orphaned next dev parents can survive listener-only kills and block restarts.
scripts/runtime-port-guard.sh:125:  pkill -TERM -f "next dev -H 0.0.0.0 --webpack -p 3000 --experimental-https" 2>/dev/null || true
scripts/runtime-port-guard.sh:130:  port_pids="$(listener_pids_on_port 3000)"
scripts/runtime-port-guard.sh:138:  pkill -KILL -f "next dev -H 0.0.0.0 --webpack -p 3000 --experimental-https" 2>/dev/null || true
./README.md:7:The active Source Proxy plan is `docs/source-proxy-production-hardening-plan.md`.
./README.md:48:# Terminal 1: Next HTTPS visual app on 0.0.0.0:3000
./README.md:52:# Terminal 2: Source proxy HTTPS API on 0.0.0.0:8787
./README.md:62:curl -k -sS https://localhost:3000/api/spirit/health
./README.md:65:**Source proxy health check (VRAM diagnostics):**
./README.md:68:curl -k -sS https://localhost:8787/healthcheck
./README.md:75:SpiritOS uses two local HTTPS LAN dev servers during normal development.
./README.md:82:- Port: `3000`
./README.md:85:- URL: `https://10.0.0.186:3000/coding`
./README.md:90:- Session: `source-proxy-lan`
./README.md:92:- Port: `8787`
./README.md:93:- Log: `~/source-proxy-https-lan.log`
./README.md:95:Use detached tmux sessions so the servers survive Cursor Remote or SSH disconnects. Normal code edits usually hot reload and do not require restarting either server. Restart mainly after `.env.local`, config, certificates, server scripts, dependency/package changes, or when compile/cache state gets stuck.
./README.md:104:tmux kill-session -t spiritos-lan 2>/dev/null || true
./README.md:105:tmux kill-session -t source-proxy-lan 2>/dev/null || true
./README.md:107:tmux new -d -s source-proxy-lan 'cd ~/SpiritOS && npm run proxy:https:lan 2>&1 | tee -a ~/source-proxy-https-lan.log'
./README.md:108:tmux new -d -s spiritos-lan 'cd ~/SpiritOS && npm run dev:https:lan:watch'
./README.md:112:tmux ls || true
./README.md:113:ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
./README.md:114:curl -k -I --max-time 10 https://localhost:3000/coding || true
./README.md:122:tmux kill-session -t spiritos-lan 2>/dev/null || true
./README.md:123:tmux kill-session -t source-proxy-lan 2>/dev/null || true
./README.md:125:lsof -ti tcp:3000 2>/dev/null | xargs -r kill -TERM
./README.md:126:lsof -ti tcp:8787 2>/dev/null | xargs -r kill -TERM
./README.md:130:lsof -ti tcp:3000 2>/dev/null | xargs -r kill -KILL
./README.md:131:lsof -ti tcp:8787 2>/dev/null | xargs -r kill -KILL
./README.md:133:tmux ls || true
./README.md:134:ss -ltnp | grep -E ':3000|:8787' || true
./README.md:137:Clean restart both servers:
./README.md:142:tmux kill-session -t spiritos-lan 2>/dev/null || true
./README.md:143:tmux kill-session -t source-proxy-lan 2>/dev/null || true
./README.md:145:lsof -ti tcp:3000 2>/dev/null | xargs -r kill -TERM
./README.md:146:lsof -ti tcp:8787 2>/dev/null | xargs -r kill -TERM
./README.md:150:lsof -ti tcp:3000 2>/dev/null | xargs -r kill -KILL
./README.md:151:lsof -ti tcp:8787 2>/dev/null | xargs -r kill -KILL
./README.md:155:tmux new -d -s source-proxy-lan 'cd ~/SpiritOS && npm run proxy:https:lan 2>&1 | tee -a ~/source-proxy-https-lan.log'
./README.md:156:tmux new -d -s spiritos-lan 'cd ~/SpiritOS && npm run dev:https:lan:watch'
./README.md:160:tmux ls || true
./README.md:161:ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
./README.md:162:curl -k -I --max-time 10 https://localhost:3000/coding || true
./README.md:165:Clean restart kills tmux sessions and any orphan processes on ports `3000` and `8787` before starting fresh tmux sessions. Plain `tmux kill-session` is not always enough because the frontend can leave orphan Next processes on port `3000`.
./README.md:167:Restart frontend only (leaves Source Proxy `:8787` and SpiritFlix `:3001` untouched):
./README.md:171:npm run lan:restart
./README.md:179:tmux kill-session -t spiritos-lan 2>/dev/null || true
./README.md:181:lsof -ti tcp:3000 2>/dev/null | xargs -r kill -TERM
./README.md:183:lsof -ti tcp:3000 2>/dev/null | xargs -r kill -KILL
./README.md:187:tmux new -d -s spiritos-lan 'cd ~/SpiritOS && npm run dev:https:lan:watch'
./README.md:191:tmux ls || true
./README.md:192:ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
./README.md:193:curl -k -I --max-time 10 https://localhost:3000/coding || true
./README.md:201:tmux kill-session -t source-proxy-lan 2>/dev/null || true
./README.md:203:lsof -ti tcp:8787 2>/dev/null | xargs -r kill -TERM
./README.md:205:lsof -ti tcp:8787 2>/dev/null | xargs -r kill -KILL
./README.md:207:tmux new -d -s source-proxy-lan 'cd ~/SpiritOS && npm run proxy:https:lan 2>&1 | tee -a ~/source-proxy-https-lan.log'
./README.md:211:tmux ls || true
./README.md:212:ss -ltnp | grep -E ':8787|:22|:11434' || true
./README.md:213:curl -k --max-time 10 https://localhost:8787/v1/self/status | head -c 800
./README.md:222:echo "== tmux =="
./README.md:223:tmux ls || true
./README.md:227:ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
./README.md:231:curl -k -I --max-time 10 https://localhost:3000/ || true
./README.md:232:curl -k -I --max-time 10 https://localhost:3000/coding || true
./README.md:236:curl -k -s --max-time 10 https://localhost:3000/v1/self/status | head -c 800
./README.md:241:curl -k -s --max-time 10 https://localhost:8787/v1/self/status | head -c 800
./README.md:254:tail -f ~/source-proxy-https-lan.log
./README.md:257:Attach to frontend tmux session:
./README.md:260:tmux attach -t spiritos-lan
./README.md:263:Attach to proxy tmux session:
./README.md:266:tmux attach -t source-proxy-lan
./README.md:269:Detach from tmux without killing the server:
./README.md:278:https://10.0.0.186:3000/
./README.md:279:https://10.0.0.186:3000/coding
./README.md:282:If the browser shows a white page after restart, hard refresh:
./README.md:291:ssh spirit "tmux ls || true"
./README.md:292:ssh spirit "ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true"
./README.md:293:curl.exe -k -I https://10.0.0.186:3000/coding
./README.md:294:Test-NetConnection 10.0.0.186 -Port 3000
./README.md:295:Test-NetConnection 10.0.0.186 -Port 8787
./README.md:300:- `tmux` shows `spiritos-lan` and `source-proxy-lan`.
./README.md:301:- `ss` shows `0.0.0.0:3000` for the frontend.
./README.md:302:- `ss` shows `0.0.0.0:8787` for the proxy.
./README.md:303:- `curl` to `https://localhost:3000/` returns `HTTP/1.1 200 OK` (watchdog health probe).
./README.md:304:- `curl` to `https://localhost:3000/coding` returns `HTTP/1.1 200 OK`.
./README.md:305:- The browser opens `https://10.0.0.186:3000/coding` after a hard refresh if needed.
./README.md:307:### Runtime lane audit (when :3000 / :8787 / :3001 feel down or slow)
./README.md:318:- **Watchdog restart churn** on `:3000` when Next is still compiling or swap is full. The LAN watchdog now probes `https://127.0.0.1:3000/` (not `/coding`), waits longer before health checks, and only clears `.next` cache every 3rd restart instead of every loop.
./README.md:322:Per-lane restarts (safe, tmux-managed):
./README.md:325:npm run lan:restart                 # SpiritOS HTTPS UI :3000 only
./README.md:326:npm run proxy:lan:restart           # Source Proxy :8787 only (now watchdog-wrapped)
./README.md:327:npm run spiritflix:stable:restart   # SpiritFlix stable sidecar :3001 only
./README.md:334:~/source-proxy-lan-watchdog.log
./README.md:352:If the curl response is HTML instead of JSON, check `backend/searxng.yml` and confirm `search.formats` includes `json`, then restart SearXNG.
./README.md:386:$env:PORT="3000"
./README.md:402:SPIRIT_WINDOWS_FS_BASE_URL=http://REPLACE_WITH_WINDOWS_LAN_IP:3000
./README.md:405:SPIRITDESKTOP_TELEMETRY_URL=http://REPLACE_WITH_WINDOWS_LAN_IP:3000/api/telemetry/self
./README.md:412:curl -H "Authorization: Bearer 3399" http://REPLACE_WITH_WINDOWS_LAN_IP:3000/api/telemetry/self
./README.md:426:- `filesystem endpoint missing` means the Windows machine is running an older copied `agent.js`; copy the updated agent and restart `node .\agent.js`.
./README.md:428:- `unreachable` means the Dell cannot reach the Windows LAN IP or port `3000`.
./README.md:524:### Source proxy start (`8787`)
./README.md:530:npm run proxy:bootstrap   # first run only, creates .venv-source-proxy
./README.md:531:npm run proxy:https:lan   # HTTPS API on 0.0.0.0:8787
./README.md:534:The proxy launcher loads `.env`, `.env.local`, and `config/source-proxy.env` before starting Python. Restart `npm run proxy:https:lan` after adding or changing API keys.
./README.md:539:curl -k https://127.0.0.1:8787/healthcheck
./README.md:545:curl -k https://10.0.0.186:8787/healthcheck
./README.md:551:curl -k https://127.0.0.1:8787/v1/models
./README.md:557:curl -k https://127.0.0.1:8787/v1/chat/completions \
./README.md:564:For Increment 1.2, start PostgreSQL before restarting the proxy:
./README.md:584:curl -k https://127.0.0.1:8787/v1/chat/completions \
./README.md:600:curl -k https://127.0.0.1:8787/v1/chat/completions \
./README.md:610:curl -k https://127.0.0.1:8787/v1/decisions/route \
./README.md:620:curl -k https://127.0.0.1:8787/v1/decisions/prompt-packet \
./README.md:630:curl -k https://127.0.0.1:8787/v1/decisions/recommend-model \
./README.md:640:curl -k https://127.0.0.1:8787/v1/decisions/api-vs-manual-preview \
./README.md:657:### Visual app start (`3000`)
./README.md:659:The browser UI is the Next dev server. Run it in a separate terminal from the proxy:
./README.md:669:https://10.0.0.186:3000
./README.md:672:The common mix-up: `npm run proxy:https:lan` starts only the API on **8787**. It does not start the visual site on **3000**.
./README.md:692:**Headroom** (extra token savings) needs the Python proxy on **8797** — not Source Proxy on 8787:
./README.md:728:Next.js 16 exposes runtime diagnostics at `/_next/mcp` while the dev server is running. The local bridge keeps a persistent WebSocket open for JSON-RPC tool calls and forwards `get_errors` / `get_page_metadata` through `next-devtools-mcp`.
./README.md:739:NEXT_MCP_PORT=3000 npm run next:mcp:ws
./README.md:750:Next blocks cross-origin dev assets unless the browser `Origin` hostname is allowlisted. Defaults live in `allowed-dev-origins.ts` and merge with **`NEXT_ALLOWED_DEV_ORIGINS`** (comma-separated hostnames in `.env.local`, no `http://` or ports). **Restart the dev server** after edits - `next.config.ts` only sees env at startup.
./README.md:756:- **`npm run dev:https`** - same `-H 0.0.0.0` bind as `npm run dev`, plus Next **`--experimental-https`** (self-signed cert). Fine for **this machine** via `https://localhost:3000`.
./README.md:759:  then **`npm run dev:https:lan`** or **`npm run dev:all:https:lan`**. Then open **`https://10.0.0.186:3000/oracle`** from another device.
./README.md:767:1. **Firewall on the Spirit host** - allow inbound TCP **3000** for the visual app and **8787** for the proxy: e.g. `sudo ufw allow 3000/tcp`, `sudo ufw allow 8787/tcp`, then `sudo ufw reload`. Confirm listen: `ss -tlnp | grep -E ':3000|:8787'` shows `0.0.0.0:3000` and/or `0.0.0.0:8787`.
./README.md:770:4. From the client, sanity-check: `curl -vk https://10.0.0.186:3000/` - if TCP fails before TLS, it is network/firewall, not Oracle.
./README.md:774:- **Port / HTTPS:** default local dev is **`npm run dev:https:lan`** (port **3000**, `0.0.0.0` bind). For **Oracle mic from another machine**, use **`dev:https:lan`** + **`scripts/gen-dev-cert.sh`**, and open the firewall for **3000/tcp**. Use `npm run dev -- -p 3000` only if you need plain HTTP on a fixed port.
scripts/restart-spiritos-lan.sh:8:printf 'Restarting SpiritOS HTTPS LAN app on :3000 only. Source proxy :8787 and SpiritFlix sidecar :3001 are left untouched.\n'
scripts/restart-spiritos-lan.sh:14:tmux kill-session -t spiritos-lan 2>/dev/null || true
scripts/restart-spiritos-lan.sh:17:port_pids="$(lsof -ti tcp:3000 2>/dev/null || true)"
scripts/restart-spiritos-lan.sh:19:  printf 'terminating stale port 3000 pid(s): %s\n' "${port_pids//$'\n'/ }"
scripts/restart-spiritos-lan.sh:23:  if [[ -z "$(lsof -ti tcp:3000 2>/dev/null || true)" ]]; then
scripts/restart-spiritos-lan.sh:28:port_pids="$(lsof -ti tcp:3000 2>/dev/null || true)"
scripts/restart-spiritos-lan.sh:30:  printf 'killing stale port 3000 pid(s): %s\n' "${port_pids//$'\n'/ }"
scripts/restart-spiritos-lan.sh:34:  if [[ -z "$(lsof -ti tcp:3000 2>/dev/null || true)" ]]; then
scripts/restart-spiritos-lan.sh:41:tmux new-session -d -s spiritos-lan "cd '$ROOT' && npm run dev:https:lan:watch"
scripts/restart-spiritos-lan.sh:44:tmux ls || true
scripts/restart-spiritos-lan.sh:45:ss -ltnp | grep -E ':3000|:8787|:22|:11434' || true
scripts/restart-spiritos-lan.sh:46:curl -k -I --max-time 25 https://localhost:3000/coding || true
./cartographerBeta.md:148:- inspect project-health output
./cartographerBeta.md:169:curl -k -s https://localhost:3000/v1/cartographer/project-health | jq .
./cartographerBeta.md:170:curl -k -s https://localhost:3000/v1/cartographer/push-queue | jq .
./cartographerBeta.md:171:curl -k -s https://localhost:3000/v1/cartographer/audit-trail | jq .
./cartographerBeta.md:174:- project-health says merge_ready false until push audit is resolved
./cartographerBeta.md:182:- If project-health cannot distinguish bootstrap warning from current push audit, plan a future patch.
./cartographerBeta.md:327:curl -k -s https://localhost:3000/v1/cartographer/git | jq .
./cartographerBeta.md:364:curl -k -s https://localhost:3000/v1/cartographer/change-scribe | jq .
./cartographerBeta.md:396:curl -k -s https://localhost:3000/v1/cartographer/components | jq .
./cartographerBeta.md:437:curl -k -s https://localhost:3000/v1/cartographer/drift | jq .
./cartographerBeta.md:438:curl -k -s https://localhost:3000/v1/cartographer/proposals | jq .
./cartographerBeta.md:463:curl -k -s https://localhost:3000/v1/cartographer/proposals | jq .
./cartographerBeta.md:504:- source_proxy/cartographer/project_health.py
./cartographerBeta.md:510:curl -k -s https://localhost:3000/v1/cartographer/branch-recommendations | jq .
./cartographerBeta.md:511:curl -k -s https://localhost:3000/v1/cartographer/project-health | jq .
./cartographerBeta.md:540:curl -k -s https://localhost:3000/v1/cartographer/commit-proposals | jq .
./cartographerBeta.md:569:- source_proxy/cartographer/project_health.py
./cartographerBeta.md:575:curl -k -s https://localhost:3000/v1/cartographer/push-queue | jq .
./cartographerBeta.md:576:curl -k -s https://localhost:3000/v1/cartographer/project-health | jq .
./cartographerBeta.md:727:If HEAD changes without Cartographer’s commit_created event, project-health must report:
./cartographerBeta.md:731:- source_proxy/cartographer/project_health.py
./cartographerBeta.md:775:- source_proxy/cartographer/project_health.py
./cartographerBeta.md:801:- project-health no longer reports push audit missing for that pushed commit.
./cartographerBeta.md:816:Inspect project-health on a freshly created branch and on current branch.
./cartographerBeta.md:821:- Project-health explains the difference.
./cartographerBeta.md:1064:curl -k -s https://localhost:3000/v1/cartographer/sub-cartographers | jq .
scripts/runtime-lanes-audit.sh:13:printf '== tmux ==\n'
scripts/runtime-lanes-audit.sh:14:tmux ls 2>&1 || true
scripts/runtime-lanes-audit.sh:18:ss -ltnp 2>/dev/null | grep -E ':3000|:3001|:8787|:3020|:3030' || printf '(no lane listeners found)\n'
scripts/runtime-lanes-audit.sh:29:printf '== health probes ==\n'
scripts/runtime-lanes-audit.sh:30:curl -k -sS -o /dev/null -w '  :3000 root -> %{http_code} in %{time_total}s\n' --max-time 20 https://127.0.0.1:3000/ || printf '  :3000 root -> FAIL\n'
scripts/runtime-lanes-audit.sh:31:curl -k -sS -o /dev/null -w '  :3000 coding -> %{http_code} in %{time_total}s\n' --max-time 20 https://127.0.0.1:3000/coding || printf '  :3000 coding -> FAIL\n'
scripts/runtime-lanes-audit.sh:32:curl -k -sS -o /dev/null -w '  :8787 health -> %{http_code} in %{time_total}s\n' --max-time 25 https://127.0.0.1:8787/healthcheck || printf '  :8787 health -> FAIL\n'
scripts/runtime-lanes-audit.sh:38:  rg -c 'frontend health check failed|frontend is hung|frontend exited' "$HOME/spiritos-dev-lan-watchdog.log" 2>/dev/null | head -1 || true
./next.config.ts:8: * Tailscale / LAN: set `NEXT_ALLOWED_DEV_ORIGINS` (comma-separated hostnames), restart dev.
scripts/source-proxy-lan-watchdog.sh:8:LOG="${SOURCE_PROXY_LAN_WATCHDOG_LOG:-$HOME/source-proxy-lan-watchdog.log}"
scripts/source-proxy-lan-watchdog.sh:9:HEALTH_URL="${SOURCE_PROXY_LAN_HEALTH_URL:-https://127.0.0.1:8787/healthcheck}"
scripts/source-proxy-lan-watchdog.sh:19:health_check() {
scripts/source-proxy-lan-watchdog.sh:26:log "Source Proxy LAN watchdog starting (health=$HEALTH_URL)"
scripts/source-proxy-lan-watchdog.sh:29:  port_pids="$(listener_pids_on_port 8787)"
scripts/source-proxy-lan-watchdog.sh:35:    wait_for_port_free 8787 8 || true
scripts/source-proxy-lan-watchdog.sh:39:  npm run proxy:https:lan 2>&1 | tee -a ~/source-proxy-https-lan.log &
scripts/source-proxy-lan-watchdog.sh:44:    if health_check; then
scripts/source-proxy-lan-watchdog.sh:48:      log "proxy :8787 health failed $failures/$HEALTH_FAILURE_LIMIT"
scripts/source-proxy-lan-watchdog.sh:50:        log "proxy :8787 unreachable; restarting"
scripts/source-proxy-lan-watchdog.sh:52:        wait_for_port_free 8787 5 || true
scripts/source-proxy-lan-watchdog.sh:53:        pkill -f "uvicorn source_proxy.main:app.*8787" 2>/dev/null || true
scripts/source-proxy-lan-watchdog.sh:62:    log "proxy :8787 exited; restarting in ${RESTART_DELAY}s"
scripts/headroom-proxy-dev.sh:5:# Source Proxy owns 8787. Headroom gets its own lane so compress() stops
scripts/next-mcp-ws-bridge.mjs:20:const nextPort = readIntEnv("NEXT_MCP_PORT", 3000);
scripts/next-mcp-ws-bridge.mjs:30:        port: { type: "number", description: "Next.js dev server port." },
scripts/next-mcp-ws-bridge.mjs:41:        port: { type: "number", description: "Next.js dev server port." },
scripts/next-mcp-ws-bridge.mjs:48:    description: "Discover running Next.js dev servers and their MCP tools.",
scripts/next-mcp-ws-bridge.mjs:52:        port: { type: "number", description: "Optional Next.js dev server port." },
scripts/source-context-compress.mjs:184:    const response = await fetch(`${baseUrl}/health`, {
scripts/spiritos-lan-watchdog.sh:11:HEALTH_URL="${SPIRITOS_LAN_HEALTH_URL:-https://127.0.0.1:3000/}"
scripts/spiritos-lan-watchdog.sh:28:    echo "-- tmux --"
scripts/spiritos-lan-watchdog.sh:29:    tmux ls 2>&1 || true
scripts/spiritos-lan-watchdog.sh:31:    ss -ltnp 2>/dev/null | grep -E ':3000|:8787|:3001|:22|:11434' || true
scripts/spiritos-lan-watchdog.sh:56:  wait_for_port_free 3000 8 || true
scripts/spiritos-lan-watchdog.sh:62:  wait_for_port_free 3000 5 || true
scripts/spiritos-lan-watchdog.sh:64:  foreign_pids="$(listener_pids_on_port 3000)"
scripts/spiritos-lan-watchdog.sh:68:      log "warning: foreign listener still on :3000 pid=$foreign_pid (watchdog will not kill it)"
scripts/spiritos-lan-watchdog.sh:74:health_check() {
scripts/spiritos-lan-watchdog.sh:89:log "watchdog starting in $ROOT (health=$HEALTH_URL grace=${HEALTH_STARTUP_GRACE}s)"
scripts/spiritos-lan-watchdog.sh:93:restart_count=0
scripts/spiritos-lan-watchdog.sh:99:    log "skipping cache clear after fast-fail restart"
scripts/spiritos-lan-watchdog.sh:102:  elif (( restart_count % CACHE_CLEAR_EVERY == 0 )); then
scripts/spiritos-lan-watchdog.sh:120:    if health_check; then
scripts/spiritos-lan-watchdog.sh:122:        log "frontend health recovered after $failures failed check(s)"
scripts/spiritos-lan-watchdog.sh:127:      log "frontend health check failed $failures/$HEALTH_FAILURE_LIMIT for $HEALTH_URL"
scripts/spiritos-lan-watchdog.sh:129:        log "frontend is hung or unreachable; restarting"
scripts/spiritos-lan-watchdog.sh:144:      log "frontend failed fast (likely EADDRINUSE); force-clearing :3000 listeners"
scripts/spiritos-lan-watchdog.sh:146:      wait_for_port_free 3000 15 || true
scripts/spiritos-lan-watchdog.sh:153:  restart_count=$((restart_count + 1))
scripts/spiritos-lan-watchdog.sh:158:  log "restarting frontend in ${RESTART_DELAY}s (restart_count=$restart_count)"
source_proxy/tasks/long_running.py:1763:            "persists_across_restart": True,
./tests/agent-lab-demo/messy-prompt-comparison-results.json:34:        "raw_model_response":  "\u003cfile path=\"tests/agent-lab-demo/7b/init-experimental-repo-homepage/.gitignore\"\u003e\nnode_modules/\ndist/\n*.log\n\u003c/file\u003e\n\n\u003cfile path=\"tests/agent-lab-demo/7b/init-experimental-repo-homepage/package.json\"\u003e\n{\n  \"name\": \"experimental-repo\",\n  \"version\": \"1.0.0\",\n  \"description\": \"Experimental features and homepage for the new repo\",\n  \"main\": \"index.js\",\n  \"scripts\": {\n    \"start\": \"node index.js\"\n  },\n  \"dependencies\": {\n    \"express\": \"^4.17.1\"\n  }\n}\n\u003c/file\u003e\n\n\u003cfile path=\"tests/agent-lab-demo/7b/init-experimental-repo-homepage/index.js\"\u003e\nconst express = require(\u0027express\u0027);\nconst app = express();\nconst port = 3000;\n\napp.get(\u0027/\u0027, (req, res) =\u003e {\n  res.send(\u0027\u003ch1\u003eWelcome to the Experimental Repo Homepage\u003c/h1\u003e\u0027);\n});\n\napp.listen(port, () =\u003e {\n  console.log(`App listening at http://localhost:${port}`);\n});\n\u003c/file\u003e",
./tests/agent-lab-demo/messy-prompt-comparison-results.json:48:                                       "content":  "const express = require(\u0027express\u0027);\nconst app = express();\nconst port = 3000;\n\napp.get(\u0027/\u0027, (req, res) =\u003e {\n  res.send(\u0027\u003ch1\u003eWelcome to the Experimental Repo Homepage\u003c/h1\u003e\u0027);\n});\n\napp.listen(port, () =\u003e {\n  console.log(`App listening at http://localhost:${port}`);\n});",
./tests/agent-lab-demo/messy-prompt-comparison-results.json:52:        "diff_preview":  "diff --git a/tests/agent-lab-demo/7b/init-experimental-repo-homepage/.gitignore b/tests/agent-lab-demo/7b/init-experimental-repo-homepage/.gitignore\nnew file mode 100644\n--- /dev/null\n+++ b/tests/agent-lab-demo/7b/init-experimental-repo-homepage/.gitignore\n@@ -0,0 +1,3 @@\n+node_modules/\n+dist/\n+*.log\n\ndiff --git a/tests/agent-lab-demo/7b/init-experimental-repo-homepage/package.json b/tests/agent-lab-demo/7b/init-experimental-repo-homepage/package.json\nnew file mode 100644\n--- /dev/null\n+++ b/tests/agent-lab-demo/7b/init-experimental-repo-homepage/package.json\n@@ -0,0 +1,12 @@\n+{\n+  \"name\": \"experimental-repo\",\n+  \"version\": \"1.0.0\",\n+  \"description\": \"Experimental features and homepage for the new repo\",\n+  \"main\": \"index.js\",\n+  \"scripts\": {\n+    \"start\": \"node index.js\"\n+  },\n+  \"dependencies\": {\n+    \"express\": \"^4.17.1\"\n+  }\n+}\n\ndiff --git a/tests/agent-lab-demo/7b/init-experimental-repo-homepage/index.js b/tests/agent-lab-demo/7b/init-experimental-repo-homepage/index.js\nnew file mode 100644\n--- /dev/null\n+++ b/tests/agent-lab-demo/7b/init-experimental-repo-homepage/index.js\n@@ -0,0 +1,11 @@\n+const express = require(\u0027express\u0027);\n+const app = express();\n+const port = 3000;\n+\n+app.get(\u0027/\u0027, (req, res) =\u003e {\n+  res.send(\u0027\u003ch1\u003eWelcome to the Experimental Repo Homepage\u003c/h1\u003e\u0027);\n+});\n+\n+app.listen(port, () =\u003e {\n+  console.log(`App listening at http://localhost:${port}`);\n+});",
./tests/agent-lab-demo/messy-prompt-comparison-results.json:201:        "id":  "server-health",
./tests/agent-lab-demo/messy-prompt-comparison-results.json:202:        "prompt":  "check server health",
./tests/agent-lab-demo/messy-prompt-comparison-results.json:204:        "raw_model_response":  "\u003cfile path=\"tests/agent-lab-demo/7b/server-health/health.js\"\u003e\nconst express = require(\u0027express\u0027);\nconst router = express.Router();\n\nrouter.get(\u0027/health\u0027, (req, res) =\u003e {\n  res.status(200).json({ status: \u0027UP\u0027 });\n});\n\nmodule.exports = router;\n\u003c/file\u003e",
./tests/agent-lab-demo/messy-prompt-comparison-results.json:207:                                       "path":  "tests/agent-lab-demo/7b/server-health/health.js",
./tests/agent-lab-demo/messy-prompt-comparison-results.json:208:                                       "content":  "const express = require(\u0027express\u0027);\nconst router = express.Router();\n\nrouter.get(\u0027/health\u0027, (req, res) =\u003e {\n  res.status(200).json({ status: \u0027UP\u0027 });\n});\n\nmodule.exports = router;",
./tests/agent-lab-demo/messy-prompt-comparison-results.json:212:        "diff_preview":  "diff --git a/tests/agent-lab-demo/7b/server-health/health.js b/tests/agent-lab-demo/7b/server-health/health.js\nnew file mode 100644\n--- /dev/null\n+++ b/tests/agent-lab-demo/7b/server-health/health.js\n@@ -0,0 +1,8 @@\n+const express = require(\u0027express\u0027);\n+const router = express.Router();\n+\n+router.get(\u0027/health\u0027, (req, res) =\u003e {\n+  res.status(200).json({ status: \u0027UP\u0027 });\n+});\n+\n+module.exports = router;",
./tests/agent-lab-demo/messy-prompt-comparison-results.json:217:                            "isolated_root":  "tests/agent-lab-demo/7b/server-health/",
source_proxy/diagnostics/gpu.py:20:    def as_healthcheck_payload(self) -> dict[str, str]:
./tests/ui-agent-trials/run-ui-agent-trials.test.ts:29:    const error = new Error("page.goto: net::ERR_CONNECTION_REFUSED at https://localhost:3000/coding");
./tests/ui-agent-trials/run-ui-agent-trials.test.ts:30:    const classified = classifyRouteAvailabilityError(error, "https://localhost:3000/coding");
./tests/ui-agent-trials/run-ui-agent-trials.test.ts:34:    expect(classified.next_recommended_action).toContain("Start or repair the dev server");
./tests/ui-agent-trials/run-ui-agent-trials.test.ts:39:      error: new Error("page.goto: net::ERR_CONNECTION_REFUSED at https://localhost:3000/coding"),
./tests/ui-agent-trials/run-ui-agent-trials.test.ts:55:    expect(result.next_recommended_action).toContain("Start or repair the dev server");
./tests/ui-agent-trials/run-ui-agent-trials.test.ts:62:        error: new Error("page.goto: net::ERR_CONNECTION_REFUSED at https://localhost:3000/coding"),
source_proxy/cartographer/project_health.py:16:def build_project_health() -> list[ProjectHealth]:
source_proxy/cartographer/project_health.py:47:    health: list[ProjectHealth] = []
source_proxy/cartographer/project_health.py:51:        health.append(
source_proxy/cartographer/project_health.py:57:                blueprint_health="missing_starter_blueprints",
source_proxy/cartographer/project_health.py:88:        health.append(
source_proxy/cartographer/project_health.py:98:                blueprint_health=_blueprint_health(
source_proxy/cartographer/project_health.py:153:    return sorted(health, key=lambda item: (item.status != "active", item.name.lower()))
source_proxy/cartographer/project_health.py:171:def _blueprint_health(*, blueprint_count: int, pending_drift: int) -> str:
source_proxy/cartographer/project_health.py:176:    return "healthy"
source_proxy/cartographer/level_14_autonomy_runtime.py:208:def build_level_14_recurring_health_check_dry_run(
source_proxy/cartographer/level_14_autonomy_runtime.py:215:        reasons += ["unsupported_health_check_class"]
source_proxy/cartographer/level_14_autonomy_runtime.py:221:        status="recurring-health-check-dry-run-only",
source_proxy/cartographer/models.py:409:    blueprint_health: str
source_proxy/cartographer/v1_readiness.py:56:        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-evidence | jq .",
source_proxy/cartographer/v1_readiness.py:61:        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-evidence | jq .",
source_proxy/cartographer/v1_readiness.py:66:        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-recording-proposal | jq .",
source_proxy/cartographer/v1_readiness.py:71:        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-recording-proposal | jq .",
source_proxy/cartographer/v1_readiness.py:76:        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
source_proxy/cartographer/v1_readiness.py:81:        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
source_proxy/cartographer/v1_readiness.py:86:        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
source_proxy/cartographer/v1_readiness.py:91:        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
source_proxy/cartographer/v1_readiness.py:96:        "manual_check": "curl -k -s https://localhost:3000/v1/cartographer/v1-proof-contract | jq .",
source_proxy/cartographer/v1_readiness.py:374:            "curl -k -s https://localhost:3000/v1/cartographer/v1-readiness | jq .",
./post-v1-diag.md:50:curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
./post-v1-diag.md:51:curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq .
./post-v1-diag.md:217:curl -k -s https://localhost:3000/v1/cartographer/v1-freeze-marker-validation | jq .
./post-v1-diag.md:218:curl -k -s https://localhost:3000/v1/cartographer/v1-closeout-dashboard | jq .
source_proxy/cartographer/component_mapper.py:47:        component_id="source-proxy",
./source_proxy/tasks/long_running.py:1763:            "persists_across_restart": True,
source_proxy/cartographer/runbook_scribe.py:115:                "Open the affected dashboard or API route through the local dev server.",
./source_proxy/diagnostics/gpu.py:20:    def as_healthcheck_payload(self) -> dict[str, str]:
source_proxy/cartographer/repo_map.py:43:    ".venv-source-proxy",
source_proxy/cartographer/repo_map.py:44:    ".venv-source-proxy-windows",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:664:    "messy_prompt": "add quick health thing for node npm git model endpoint search endpoint, but keep it readable",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:665:    "prompt_text": "add quick health thing for node npm git model endpoint search endpoint, but keep it readable",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:666:    "submitted_prompt": "add quick health thing for node npm git model endpoint search endpoint, but keep it readable",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:667:    "clean_control_submitted_prompt": "Reversible coder trial 15: add quick health thing for node npm git model endpoint search endpoint, but keep it readable",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:1686:    "messy_prompt": "show if search is healthy missing or broken",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:1687:    "prompt_text": "show if search is healthy missing or broken",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:1688:    "submitted_prompt": "show if search is healthy missing or broken",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:1689:    "clean_control_submitted_prompt": "Reversible coder trial 37: show if search is healthy missing or broken",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:2107:    "messy_prompt": "health card should show model search terminal browser git workspace all in one",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:2108:    "prompt_text": "health card should show model search terminal browser git workspace all in one",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:2109:    "submitted_prompt": "health card should show model search terminal browser git workspace all in one",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:2110:    "clean_control_submitted_prompt": "Reversible coder trial 46: health card should show model search terminal browser git workspace all in one",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:9873:    "messy_prompt": "backend health for model/search/terminal/browser/git and show as small caps row",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:9874:    "prompt_text": "backend health for model/search/terminal/browser/git and show as small caps row",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:9875:    "submitted_prompt": "backend health for model/search/terminal/browser/git and show as small caps row",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:9876:    "clean_control_submitted_prompt": "Reversible combined trial 12: backend health for model/search/terminal/browser/git and show as small caps row",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:10384:    "messy_prompt": "browser proof health in backend and UI",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:10385:    "prompt_text": "browser proof health in backend and UI",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:10386:    "submitted_prompt": "browser proof health in backend and UI",
./tests/ui-agent-trials/fixtures/actual-intelligence-prompts.json:10387:    "clean_control_submitted_prompt": "Reversible combined trial 23: browser proof health in backend and UI",
./services/jellyfin/docker-compose.yml:5:    restart: unless-stopped
./services/jellyfin/docker-compose.yml:30:    healthcheck:
./services/jellyfin/docker-compose.yml:31:      test: ["CMD-SHELL", "curl -fsS http://localhost:8096/health || exit 1"]
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221503Z.json:15:    "after": "M _blueprints/INDEX.md\n M _blueprints/_schema/blueprint-frontmatter.schema.md\n M _blueprints/components/cartographer_agent.md\n M _blueprints/current/dashboard_state.md\n M _blueprints/current/system_state.md\n M _blueprints/runbooks/cartographer_manual_checks.md\n M docs/continue-lite-console-plan.md\n M docs/proxy-test-runner-plan.md\n M requirements.txt\n M scout/src/scout/api/discovery_jobs.py\n M scout/src/scout/api/human.py\n M scout/src/scout/api/overview.py\n M scout/src/scout/api/packets.py\n M scout/src/scout/api/sources.py\n M scout/src/scout/sources/discovery_jobs.py\n M scout/src/scout/sources/scoring.py\n M scout/src/scout/sources/search_candidates.py\n M scout/src/scout/tests/test_discovery_jobs.py\n M scout/src/scout/tests/test_packets_api.py\n M scout/src/scout/tests/test_search_candidate_extraction.py\n M scout/src/scout/tests/test_sources_api.py\n M scripts/validate-blueprints.mjs\n M source_proxy/api/cartographer.py\n M source_proxy/api/coding_self_tests.py\n M source_proxy/api/sandbox_terminal.py\n M source_proxy/api/scout_intake.py\n M source_proxy/cartographer/apply.py\n M source_proxy/cartographer/audit_trail.py\n M source_proxy/cartographer/blueprint_registry.py\n M source_proxy/cartographer/branch_recommendations.py\n M source_proxy/cartographer/commit_proposals.py\n M source_proxy/cartographer/component_mapper.py\n M source_proxy/cartographer/drift.py\n M source_proxy/cartographer/git_status.py\n M source_proxy/cartographer/models.py\n M source_proxy/cartographer/project_discovery.py\n M source_proxy/cartographer/project_health.py\n M source_proxy/cartographer/proposal_previews.py\n M source_proxy/cartographer/proposals.py\n M source_proxy/cartographer/push_queue.py\n M source_proxy/cartographer/repo_map.py\n M source_proxy/cartographer/service.py\n M source_proxy/cartographer/starter_blueprints.py\n M source_proxy/decision/research.py\n M source_proxy/decision/router.py\n M source_proxy/decision/scout_research.py\n M source_proxy/proxy_memory/scout_intake.py\n M source_proxy/tasks/long_running.py\n M source_proxy/testing/runner.py\n M source_proxy/tests/test_cartographer_api.py\n M source_proxy/tests/test_cartographer_safety_audit.py\n M source_proxy/tests/test_coding_self_tests.py\n M source_proxy/tests/test_prompt_packet_context_metadata.py\n M source_proxy/tests/test_proxy_runner.py\n M source_proxy/tests/test_research_preview.py\n M source_proxy/tests/test_sandbox_terminal_api.py\n M source_proxy/tests/test_scout_intake.py\n M source_proxy/tests/test_scout_research_bridge.py\n M src/app/v1/cartographer/audit-trail/route.ts\n M src/app/v1/cartographer/branch-recommendations/route.ts\n M src/app/v1/cartographer/project-health/route.ts\n M src/app/v1/cartographer/proposals/[proposalId]/apply-approved/route.ts\n M src/app/v1/cartographer/proposals/route.ts\n M src/app/v1/cartographer/push-queue/route.ts\n M src/components/coding/CodingAgentInterface.tsx\n M src/components/coding/__tests__/coding-workflow-step.test.ts\n M src/components/dashboard/HomelabBlueprintReviewWidget.tsx\n M src/components/dashboard/HomelabCartographerWidget.tsx\n M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx\n M src/components/dashboard/HomelabTestRunnerWidget.tsx\n M src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabTestRunnerWidget.test.tsx\n M src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx\n M src/hooks/useScoutOverview.ts\n M src/lib/scout-overview.ts\n M src/styles/dashboard-demo-v4.css\n?? _blueprints/proposals/\n?? cartogrpaherPlanAuto.md\n?? docs/cartographer-trust-source-plan.md\n?? masterOverhual.md\n?? scouUi.md\n?? scout/=8,\n?? scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T160750Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T161258Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T194610Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T195549Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T210942Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T211119Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212209Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212434Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212527Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212803Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212901Z.json\n?? scoutRefinemint.md\n?? source_proxy/agents/\n?? source_proxy/cartographer/git_approvals.py\n?? source_proxy/cartographer/proposal_reviews.py\n?? source_proxy/cartographer/soak-logs/\n?? source_proxy/terminal_presets.py\n?? source_proxy/tests/test_agent_registry.py\n?? src/app/api/scout/source-candidates/batch-approve/\n?? src/app/api/scout/sources/\n?? src/app/intelligence/\n?? src/app/v1/cartographer/branch-recommendations/[recommendationId]/\n?? src/app/v1/cartographer/commit-proposals/[commitProposalId]/\n?? src/app/v1/cartographer/proposals/[proposalId]/review/\n?? src/app/v1/cartographer/push-queue/[pushId]/\n?? src/components/dashboard/ScoutIntelligenceCenter.tsx\n?? src/lib/scout-human-readable.ts",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221503Z.json:20:    "before": "M _blueprints/INDEX.md\n M _blueprints/_schema/blueprint-frontmatter.schema.md\n M _blueprints/components/cartographer_agent.md\n M _blueprints/current/dashboard_state.md\n M _blueprints/current/system_state.md\n M _blueprints/runbooks/cartographer_manual_checks.md\n M docs/continue-lite-console-plan.md\n M docs/proxy-test-runner-plan.md\n M requirements.txt\n M scout/src/scout/api/discovery_jobs.py\n M scout/src/scout/api/human.py\n M scout/src/scout/api/overview.py\n M scout/src/scout/api/packets.py\n M scout/src/scout/api/sources.py\n M scout/src/scout/sources/discovery_jobs.py\n M scout/src/scout/sources/scoring.py\n M scout/src/scout/sources/search_candidates.py\n M scout/src/scout/tests/test_discovery_jobs.py\n M scout/src/scout/tests/test_packets_api.py\n M scout/src/scout/tests/test_search_candidate_extraction.py\n M scout/src/scout/tests/test_sources_api.py\n M scripts/validate-blueprints.mjs\n M source_proxy/api/cartographer.py\n M source_proxy/api/coding_self_tests.py\n M source_proxy/api/sandbox_terminal.py\n M source_proxy/api/scout_intake.py\n M source_proxy/cartographer/apply.py\n M source_proxy/cartographer/audit_trail.py\n M source_proxy/cartographer/blueprint_registry.py\n M source_proxy/cartographer/branch_recommendations.py\n M source_proxy/cartographer/commit_proposals.py\n M source_proxy/cartographer/component_mapper.py\n M source_proxy/cartographer/drift.py\n M source_proxy/cartographer/git_status.py\n M source_proxy/cartographer/models.py\n M source_proxy/cartographer/project_discovery.py\n M source_proxy/cartographer/project_health.py\n M source_proxy/cartographer/proposal_previews.py\n M source_proxy/cartographer/proposals.py\n M source_proxy/cartographer/push_queue.py\n M source_proxy/cartographer/repo_map.py\n M source_proxy/cartographer/service.py\n M source_proxy/cartographer/starter_blueprints.py\n M source_proxy/decision/research.py\n M source_proxy/decision/router.py\n M source_proxy/decision/scout_research.py\n M source_proxy/proxy_memory/scout_intake.py\n M source_proxy/tasks/long_running.py\n M source_proxy/testing/runner.py\n M source_proxy/tests/test_cartographer_api.py\n M source_proxy/tests/test_cartographer_safety_audit.py\n M source_proxy/tests/test_coding_self_tests.py\n M source_proxy/tests/test_prompt_packet_context_metadata.py\n M source_proxy/tests/test_proxy_runner.py\n M source_proxy/tests/test_research_preview.py\n M source_proxy/tests/test_sandbox_terminal_api.py\n M source_proxy/tests/test_scout_intake.py\n M source_proxy/tests/test_scout_research_bridge.py\n M src/app/v1/cartographer/audit-trail/route.ts\n M src/app/v1/cartographer/branch-recommendations/route.ts\n M src/app/v1/cartographer/project-health/route.ts\n M src/app/v1/cartographer/proposals/[proposalId]/apply-approved/route.ts\n M src/app/v1/cartographer/proposals/route.ts\n M src/app/v1/cartographer/push-queue/route.ts\n M src/components/coding/CodingAgentInterface.tsx\n M src/components/coding/__tests__/coding-workflow-step.test.ts\n M src/components/dashboard/HomelabBlueprintReviewWidget.tsx\n M src/components/dashboard/HomelabCartographerWidget.tsx\n M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx\n M src/components/dashboard/HomelabTestRunnerWidget.tsx\n M src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabTestRunnerWidget.test.tsx\n M src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx\n M src/hooks/useScoutOverview.ts\n M src/lib/scout-overview.ts\n M src/styles/dashboard-demo-v4.css\n?? _blueprints/proposals/\n?? cartogrpaherPlanAuto.md\n?? docs/cartographer-trust-source-plan.md\n?? masterOverhual.md\n?? scouUi.md\n?? scout/=8,\n?? scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T160750Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T161258Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T194610Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T195549Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T210942Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T211119Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212209Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212434Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212527Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212803Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212901Z.json\n?? scoutRefinemint.md\n?? source_proxy/agents/\n?? source_proxy/cartographer/git_approvals.py\n?? source_proxy/cartographer/proposal_reviews.py\n?? source_proxy/cartographer/soak-logs/\n?? source_proxy/terminal_presets.py\n?? source_proxy/tests/test_agent_registry.py\n?? src/app/api/scout/source-candidates/batch-approve/\n?? src/app/api/scout/sources/\n?? src/app/intelligence/\n?? src/app/v1/cartographer/branch-recommendations/[recommendationId]/\n?? src/app/v1/cartographer/commit-proposals/[commitProposalId]/\n?? src/app/v1/cartographer/proposals/[proposalId]/review/\n?? src/app/v1/cartographer/push-queue/[pushId]/\n?? src/components/dashboard/ScoutIntelligenceCenter.tsx\n?? src/lib/scout-human-readable.ts",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221503Z.json:29:    "Review pending proposal bp-spiritos-project-readme-changed-9c7220f5 (project, None risk, 0 changed / 3 proposed); use the Blueprint Review dashboard or fetch details with curl -k -s https://10.0.0.186:3000/v1/cartographer/proposals | jq '.proposals[] | select(.proposal_id==\"bp-spiritos-project-readme-changed-9c7220f5\")'",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221503Z.json:30:    "Inspect drift 081f462c2fb501bf (project: readme_changed, 1 changed) with curl -k -s https://10.0.0.186:3000/v1/cartographer/drift | jq '.drift[] | select(.drift_id==\"081f462c2fb501bf\")'",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221503Z.json:31:    "Review commit proposal commit-prop-734a8eaf0d8f (blueprint-system, low risk, 1 files) with curl -k -s https://10.0.0.186:3000/v1/cartographer/commit-proposals | jq '.commit_proposals[] | select(.commit_proposal_id==\"commit-prop-734a8eaf0d8f\")'; do not approve until proposal/drift review is complete."
./backend/docker-compose.yml:24:    restart: unless-stopped
./backend/docker-compose.yml:35:    healthcheck:
./backend/docker-compose.yml:45:    restart: unless-stopped
./backend/docker-compose.yml:65:    healthcheck:
./backend/docker-compose.yml:84:    restart: unless-stopped
./backend/docker-compose.yml:98:    healthcheck:
./backend/docker-compose.yml:99:      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
./backend/docker-compose.yml:111:    restart: unless-stopped
./backend/docker-compose.yml:130:    healthcheck:
./backend/docker-compose.yml:131:      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
./backend/docker-compose.yml:142:    restart: unless-stopped
./backend/docker-compose.yml:154:    healthcheck:
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221209Z.json:15:    "after": "M _blueprints/INDEX.md\n M _blueprints/_schema/blueprint-frontmatter.schema.md\n M _blueprints/components/cartographer_agent.md\n M _blueprints/current/dashboard_state.md\n M _blueprints/current/system_state.md\n M _blueprints/runbooks/cartographer_manual_checks.md\n M docs/continue-lite-console-plan.md\n M docs/proxy-test-runner-plan.md\n M requirements.txt\n M scout/src/scout/api/discovery_jobs.py\n M scout/src/scout/api/human.py\n M scout/src/scout/api/overview.py\n M scout/src/scout/api/packets.py\n M scout/src/scout/api/sources.py\n M scout/src/scout/sources/discovery_jobs.py\n M scout/src/scout/sources/scoring.py\n M scout/src/scout/sources/search_candidates.py\n M scout/src/scout/tests/test_discovery_jobs.py\n M scout/src/scout/tests/test_packets_api.py\n M scout/src/scout/tests/test_search_candidate_extraction.py\n M scout/src/scout/tests/test_sources_api.py\n M scripts/validate-blueprints.mjs\n M source_proxy/api/cartographer.py\n M source_proxy/api/coding_self_tests.py\n M source_proxy/api/sandbox_terminal.py\n M source_proxy/api/scout_intake.py\n M source_proxy/cartographer/apply.py\n M source_proxy/cartographer/audit_trail.py\n M source_proxy/cartographer/blueprint_registry.py\n M source_proxy/cartographer/branch_recommendations.py\n M source_proxy/cartographer/commit_proposals.py\n M source_proxy/cartographer/component_mapper.py\n M source_proxy/cartographer/drift.py\n M source_proxy/cartographer/git_status.py\n M source_proxy/cartographer/models.py\n M source_proxy/cartographer/project_discovery.py\n M source_proxy/cartographer/project_health.py\n M source_proxy/cartographer/proposal_previews.py\n M source_proxy/cartographer/proposals.py\n M source_proxy/cartographer/push_queue.py\n M source_proxy/cartographer/repo_map.py\n M source_proxy/cartographer/service.py\n M source_proxy/cartographer/starter_blueprints.py\n M source_proxy/decision/research.py\n M source_proxy/decision/router.py\n M source_proxy/decision/scout_research.py\n M source_proxy/proxy_memory/scout_intake.py\n M source_proxy/tasks/long_running.py\n M source_proxy/testing/runner.py\n M source_proxy/tests/test_cartographer_api.py\n M source_proxy/tests/test_cartographer_safety_audit.py\n M source_proxy/tests/test_coding_self_tests.py\n M source_proxy/tests/test_prompt_packet_context_metadata.py\n M source_proxy/tests/test_proxy_runner.py\n M source_proxy/tests/test_research_preview.py\n M source_proxy/tests/test_sandbox_terminal_api.py\n M source_proxy/tests/test_scout_intake.py\n M source_proxy/tests/test_scout_research_bridge.py\n M src/app/v1/cartographer/audit-trail/route.ts\n M src/app/v1/cartographer/branch-recommendations/route.ts\n M src/app/v1/cartographer/project-health/route.ts\n M src/app/v1/cartographer/proposals/[proposalId]/apply-approved/route.ts\n M src/app/v1/cartographer/proposals/route.ts\n M src/app/v1/cartographer/push-queue/route.ts\n M src/components/coding/CodingAgentInterface.tsx\n M src/components/coding/__tests__/coding-workflow-step.test.ts\n M src/components/dashboard/HomelabBlueprintReviewWidget.tsx\n M src/components/dashboard/HomelabCartographerWidget.tsx\n M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx\n M src/components/dashboard/HomelabTestRunnerWidget.tsx\n M src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabTestRunnerWidget.test.tsx\n M src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx\n M src/hooks/useScoutOverview.ts\n M src/lib/scout-overview.ts\n M src/styles/dashboard-demo-v4.css\n?? _blueprints/proposals/\n?? cartogrpaherPlanAuto.md\n?? docs/cartographer-trust-source-plan.md\n?? masterOverhual.md\n?? scouUi.md\n?? scout/=8,\n?? scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T160750Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T161258Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T194610Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T195549Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T210942Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T211119Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212209Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212434Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212527Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212803Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212901Z.json\n?? scoutRefinemint.md\n?? source_proxy/agents/\n?? source_proxy/cartographer/git_approvals.py\n?? source_proxy/cartographer/proposal_reviews.py\n?? source_proxy/cartographer/soak-logs/\n?? source_proxy/terminal_presets.py\n?? source_proxy/tests/test_agent_registry.py\n?? src/app/api/scout/source-candidates/batch-approve/\n?? src/app/api/scout/sources/\n?? src/app/intelligence/\n?? src/app/v1/cartographer/branch-recommendations/[recommendationId]/\n?? src/app/v1/cartographer/commit-proposals/[commitProposalId]/\n?? src/app/v1/cartographer/proposals/[proposalId]/review/\n?? src/app/v1/cartographer/push-queue/[pushId]/\n?? src/components/dashboard/ScoutIntelligenceCenter.tsx\n?? src/lib/scout-human-readable.ts",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221209Z.json:20:    "before": "M _blueprints/INDEX.md\n M _blueprints/_schema/blueprint-frontmatter.schema.md\n M _blueprints/components/cartographer_agent.md\n M _blueprints/current/dashboard_state.md\n M _blueprints/current/system_state.md\n M _blueprints/runbooks/cartographer_manual_checks.md\n M docs/continue-lite-console-plan.md\n M docs/proxy-test-runner-plan.md\n M requirements.txt\n M scout/src/scout/api/discovery_jobs.py\n M scout/src/scout/api/human.py\n M scout/src/scout/api/overview.py\n M scout/src/scout/api/packets.py\n M scout/src/scout/api/sources.py\n M scout/src/scout/sources/discovery_jobs.py\n M scout/src/scout/sources/scoring.py\n M scout/src/scout/sources/search_candidates.py\n M scout/src/scout/tests/test_discovery_jobs.py\n M scout/src/scout/tests/test_packets_api.py\n M scout/src/scout/tests/test_search_candidate_extraction.py\n M scout/src/scout/tests/test_sources_api.py\n M scripts/validate-blueprints.mjs\n M source_proxy/api/cartographer.py\n M source_proxy/api/coding_self_tests.py\n M source_proxy/api/sandbox_terminal.py\n M source_proxy/api/scout_intake.py\n M source_proxy/cartographer/apply.py\n M source_proxy/cartographer/audit_trail.py\n M source_proxy/cartographer/blueprint_registry.py\n M source_proxy/cartographer/branch_recommendations.py\n M source_proxy/cartographer/commit_proposals.py\n M source_proxy/cartographer/component_mapper.py\n M source_proxy/cartographer/drift.py\n M source_proxy/cartographer/git_status.py\n M source_proxy/cartographer/models.py\n M source_proxy/cartographer/project_discovery.py\n M source_proxy/cartographer/project_health.py\n M source_proxy/cartographer/proposal_previews.py\n M source_proxy/cartographer/proposals.py\n M source_proxy/cartographer/push_queue.py\n M source_proxy/cartographer/repo_map.py\n M source_proxy/cartographer/service.py\n M source_proxy/cartographer/starter_blueprints.py\n M source_proxy/decision/research.py\n M source_proxy/decision/router.py\n M source_proxy/decision/scout_research.py\n M source_proxy/proxy_memory/scout_intake.py\n M source_proxy/tasks/long_running.py\n M source_proxy/testing/runner.py\n M source_proxy/tests/test_cartographer_api.py\n M source_proxy/tests/test_cartographer_safety_audit.py\n M source_proxy/tests/test_coding_self_tests.py\n M source_proxy/tests/test_prompt_packet_context_metadata.py\n M source_proxy/tests/test_proxy_runner.py\n M source_proxy/tests/test_research_preview.py\n M source_proxy/tests/test_sandbox_terminal_api.py\n M source_proxy/tests/test_scout_intake.py\n M source_proxy/tests/test_scout_research_bridge.py\n M src/app/v1/cartographer/audit-trail/route.ts\n M src/app/v1/cartographer/branch-recommendations/route.ts\n M src/app/v1/cartographer/project-health/route.ts\n M src/app/v1/cartographer/proposals/[proposalId]/apply-approved/route.ts\n M src/app/v1/cartographer/proposals/route.ts\n M src/app/v1/cartographer/push-queue/route.ts\n M src/components/coding/CodingAgentInterface.tsx\n M src/components/coding/__tests__/coding-workflow-step.test.ts\n M src/components/dashboard/HomelabBlueprintReviewWidget.tsx\n M src/components/dashboard/HomelabCartographerWidget.tsx\n M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx\n M src/components/dashboard/HomelabTestRunnerWidget.tsx\n M src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabTestRunnerWidget.test.tsx\n M src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx\n M src/hooks/useScoutOverview.ts\n M src/lib/scout-overview.ts\n M src/styles/dashboard-demo-v4.css\n?? _blueprints/proposals/\n?? cartogrpaherPlanAuto.md\n?? docs/cartographer-trust-source-plan.md\n?? masterOverhual.md\n?? scouUi.md\n?? scout/=8,\n?? scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T160750Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T161258Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T194610Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T195549Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T210942Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T211119Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212209Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212434Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212527Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212803Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212901Z.json\n?? scoutRefinemint.md\n?? source_proxy/agents/\n?? source_proxy/cartographer/git_approvals.py\n?? source_proxy/cartographer/proposal_reviews.py\n?? source_proxy/cartographer/soak-logs/\n?? source_proxy/terminal_presets.py\n?? source_proxy/tests/test_agent_registry.py\n?? src/app/api/scout/source-candidates/batch-approve/\n?? src/app/api/scout/sources/\n?? src/app/intelligence/\n?? src/app/v1/cartographer/branch-recommendations/[recommendationId]/\n?? src/app/v1/cartographer/commit-proposals/[commitProposalId]/\n?? src/app/v1/cartographer/proposals/[proposalId]/review/\n?? src/app/v1/cartographer/push-queue/[pushId]/\n?? src/components/dashboard/ScoutIntelligenceCenter.tsx\n?? src/lib/scout-human-readable.ts",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221209Z.json:29:    "Review pending proposal bp-spiritos-project-readme-changed-9c7220f5 (project, None risk, 0 changed / 3 proposed); use the Blueprint Review dashboard or fetch details with curl -k -s https://10.0.0.186:3000/v1/cartographer/proposals | jq '.proposals[] | select(.proposal_id==\"bp-spiritos-project-readme-changed-9c7220f5\")'",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221209Z.json:30:    "Inspect drift 081f462c2fb501bf (project: readme_changed, 1 changed) with curl -k -s https://10.0.0.186:3000/v1/cartographer/drift | jq '.drift[] | select(.drift_id==\"081f462c2fb501bf\")'",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T221209Z.json:31:    "Review commit proposal commit-prop-734a8eaf0d8f (blueprint-system, low risk, 1 files) with curl -k -s https://10.0.0.186:3000/v1/cartographer/commit-proposals | jq '.commit_proposals[] | select(.commit_proposal_id==\"commit-prop-734a8eaf0d8f\")'; do not approve until proposal/drift review is complete."
./source_proxy/cartographer/project_health.py:16:def build_project_health() -> list[ProjectHealth]:
./source_proxy/cartographer/project_health.py:47:    health: list[ProjectHealth] = []
./source_proxy/cartographer/project_health.py:51:        health.append(
./source_proxy/cartographer/project_health.py:57:                blueprint_health="missing_starter_blueprints",
./source_proxy/cartographer/project_health.py:88:        health.append(
./source_proxy/cartographer/project_health.py:98:                blueprint_health=_blueprint_health(
./source_proxy/cartographer/project_health.py:153:    return sorted(health, key=lambda item: (item.status != "active", item.name.lower()))
./source_proxy/cartographer/project_health.py:171:def _blueprint_health(*, blueprint_count: int, pending_drift: int) -> str:
./source_proxy/cartographer/project_health.py:176:    return "healthy"
./scripts/spiritdesktop-windows/agent.js:12:// (or whatever path you launch from) and **restart** the Node process (`node agent.js`).
./scripts/spiritdesktop-windows/agent.js:14://   http://<spiritdesktop-lan-ip>:3000/api/telemetry/self
./scripts/spiritdesktop-windows/agent.js:25:const PORT = Number.parseInt(process.env.PORT || "3000", 10);
./scripts/spiritdesktop-windows/agent.js:84:  if (s === "healthy" || s === "ok") return "Healthy";
./scripts/spiritdesktop-windows/agent.js:86:  if (s === "critical" || s === "unhealthy" || s === "failed" || s === "pred fail") return "Critical";
./scripts/spiritdesktop-windows/agent.js:148:  $health = $null
./scripts/spiritdesktop-windows/agent.js:158:            try { $health = $disk.HealthStatus.ToString() } catch {}
./scripts/spiritdesktop-windows/agent.js:172:              if ($vdHealth) { $health = $vdHealth }
./scripts/spiritdesktop-windows/agent.js:182:            if (-not $health) {
./scripts/spiritdesktop-windows/agent.js:187:                if ($poolHealth.Count -eq 1) { $health = $poolHealth[0] }
./scripts/spiritdesktop-windows/agent.js:193:        if (-not $media -or $media -eq 'Unspecified' -or -not $health) {
./scripts/spiritdesktop-windows/agent.js:199:              if (-not $health) { try { $health = $pd.HealthStatus.ToString() } catch {} }
./scripts/spiritdesktop-windows/agent.js:229:    PhysicalHealthStatus = $health
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T214242Z.json:15:    "after": "M _blueprints/INDEX.md\n M _blueprints/_schema/blueprint-frontmatter.schema.md\n M _blueprints/runbooks/cartographer_manual_checks.md\n M docs/continue-lite-console-plan.md\n M docs/proxy-test-runner-plan.md\n M requirements.txt\n M scout/src/scout/api/discovery_jobs.py\n M scout/src/scout/api/human.py\n M scout/src/scout/api/overview.py\n M scout/src/scout/api/packets.py\n M scout/src/scout/api/sources.py\n M scout/src/scout/sources/discovery_jobs.py\n M scout/src/scout/sources/scoring.py\n M scout/src/scout/sources/search_candidates.py\n M scout/src/scout/tests/test_discovery_jobs.py\n M scout/src/scout/tests/test_packets_api.py\n M scout/src/scout/tests/test_search_candidate_extraction.py\n M scout/src/scout/tests/test_sources_api.py\n M scripts/validate-blueprints.mjs\n M source_proxy/api/cartographer.py\n M source_proxy/api/coding_self_tests.py\n M source_proxy/api/sandbox_terminal.py\n M source_proxy/api/scout_intake.py\n M source_proxy/cartographer/apply.py\n M source_proxy/cartographer/audit_trail.py\n M source_proxy/cartographer/blueprint_registry.py\n M source_proxy/cartographer/branch_recommendations.py\n M source_proxy/cartographer/commit_proposals.py\n M source_proxy/cartographer/component_mapper.py\n M source_proxy/cartographer/drift.py\n M source_proxy/cartographer/git_status.py\n M source_proxy/cartographer/models.py\n M source_proxy/cartographer/project_discovery.py\n M source_proxy/cartographer/project_health.py\n M source_proxy/cartographer/proposal_previews.py\n M source_proxy/cartographer/proposals.py\n M source_proxy/cartographer/push_queue.py\n M source_proxy/cartographer/repo_map.py\n M source_proxy/cartographer/service.py\n M source_proxy/cartographer/starter_blueprints.py\n M source_proxy/decision/research.py\n M source_proxy/decision/router.py\n M source_proxy/decision/scout_research.py\n M source_proxy/proxy_memory/scout_intake.py\n M source_proxy/tasks/long_running.py\n M source_proxy/testing/runner.py\n M source_proxy/tests/test_cartographer_api.py\n M source_proxy/tests/test_cartographer_safety_audit.py\n M source_proxy/tests/test_coding_self_tests.py\n M source_proxy/tests/test_prompt_packet_context_metadata.py\n M source_proxy/tests/test_proxy_runner.py\n M source_proxy/tests/test_research_preview.py\n M source_proxy/tests/test_sandbox_terminal_api.py\n M source_proxy/tests/test_scout_intake.py\n M source_proxy/tests/test_scout_research_bridge.py\n M src/app/v1/cartographer/audit-trail/route.ts\n M src/app/v1/cartographer/branch-recommendations/route.ts\n M src/app/v1/cartographer/project-health/route.ts\n M src/app/v1/cartographer/proposals/[proposalId]/apply-approved/route.ts\n M src/app/v1/cartographer/proposals/route.ts\n M src/app/v1/cartographer/push-queue/route.ts\n M src/components/coding/CodingAgentInterface.tsx\n M src/components/coding/__tests__/coding-workflow-step.test.ts\n M src/components/dashboard/HomelabBlueprintReviewWidget.tsx\n M src/components/dashboard/HomelabCartographerWidget.tsx\n M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx\n M src/components/dashboard/HomelabTestRunnerWidget.tsx\n M src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabTestRunnerWidget.test.tsx\n M src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx\n M src/hooks/useScoutOverview.ts\n M src/lib/scout-overview.ts\n M src/styles/dashboard-demo-v4.css\n?? _blueprints/proposals/\n?? cartogrpaherPlanAuto.md\n?? docs/cartographer-trust-source-plan.md\n?? masterOverhual.md\n?? scouUi.md\n?? scout/=8,\n?? scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T160750Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T161258Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T194610Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T195549Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T210942Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T211119Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212209Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212434Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212527Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212803Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212901Z.json\n?? scoutRefinemint.md\n?? source_proxy/agents/\n?? source_proxy/cartographer/git_approvals.py\n?? source_proxy/cartographer/proposal_reviews.py\n?? source_proxy/cartographer/soak-logs/\n?? source_proxy/terminal_presets.py\n?? source_proxy/tests/test_agent_registry.py\n?? src/app/api/scout/source-candidates/batch-approve/\n?? src/app/intelligence/\n?? src/app/v1/cartographer/branch-recommendations/[recommendationId]/\n?? src/app/v1/cartographer/commit-proposals/[commitProposalId]/\n?? src/app/v1/cartographer/proposals/[proposalId]/review/\n?? src/app/v1/cartographer/push-queue/[pushId]/\n?? src/components/dashboard/ScoutIntelligenceCenter.tsx\n?? src/lib/scout-human-readable.ts",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-16T214242Z.json:20:    "before": "M _blueprints/INDEX.md\n M _blueprints/_schema/blueprint-frontmatter.schema.md\n M _blueprints/runbooks/cartographer_manual_checks.md\n M docs/continue-lite-console-plan.md\n M docs/proxy-test-runner-plan.md\n M requirements.txt\n M scout/src/scout/api/discovery_jobs.py\n M scout/src/scout/api/human.py\n M scout/src/scout/api/overview.py\n M scout/src/scout/api/packets.py\n M scout/src/scout/api/sources.py\n M scout/src/scout/sources/discovery_jobs.py\n M scout/src/scout/sources/scoring.py\n M scout/src/scout/sources/search_candidates.py\n M scout/src/scout/tests/test_discovery_jobs.py\n M scout/src/scout/tests/test_packets_api.py\n M scout/src/scout/tests/test_search_candidate_extraction.py\n M scout/src/scout/tests/test_sources_api.py\n M scripts/validate-blueprints.mjs\n M source_proxy/api/cartographer.py\n M source_proxy/api/coding_self_tests.py\n M source_proxy/api/sandbox_terminal.py\n M source_proxy/api/scout_intake.py\n M source_proxy/cartographer/apply.py\n M source_proxy/cartographer/audit_trail.py\n M source_proxy/cartographer/blueprint_registry.py\n M source_proxy/cartographer/branch_recommendations.py\n M source_proxy/cartographer/commit_proposals.py\n M source_proxy/cartographer/component_mapper.py\n M source_proxy/cartographer/drift.py\n M source_proxy/cartographer/git_status.py\n M source_proxy/cartographer/models.py\n M source_proxy/cartographer/project_discovery.py\n M source_proxy/cartographer/project_health.py\n M source_proxy/cartographer/proposal_previews.py\n M source_proxy/cartographer/proposals.py\n M source_proxy/cartographer/push_queue.py\n M source_proxy/cartographer/repo_map.py\n M source_proxy/cartographer/service.py\n M source_proxy/cartographer/starter_blueprints.py\n M source_proxy/decision/research.py\n M source_proxy/decision/router.py\n M source_proxy/decision/scout_research.py\n M source_proxy/proxy_memory/scout_intake.py\n M source_proxy/tasks/long_running.py\n M source_proxy/testing/runner.py\n M source_proxy/tests/test_cartographer_api.py\n M source_proxy/tests/test_cartographer_safety_audit.py\n M source_proxy/tests/test_coding_self_tests.py\n M source_proxy/tests/test_prompt_packet_context_metadata.py\n M source_proxy/tests/test_proxy_runner.py\n M source_proxy/tests/test_research_preview.py\n M source_proxy/tests/test_sandbox_terminal_api.py\n M source_proxy/tests/test_scout_intake.py\n M source_proxy/tests/test_scout_research_bridge.py\n M src/app/v1/cartographer/audit-trail/route.ts\n M src/app/v1/cartographer/branch-recommendations/route.ts\n M src/app/v1/cartographer/project-health/route.ts\n M src/app/v1/cartographer/proposals/[proposalId]/apply-approved/route.ts\n M src/app/v1/cartographer/proposals/route.ts\n M src/app/v1/cartographer/push-queue/route.ts\n M src/components/coding/CodingAgentInterface.tsx\n M src/components/coding/__tests__/coding-workflow-step.test.ts\n M src/components/dashboard/HomelabBlueprintReviewWidget.tsx\n M src/components/dashboard/HomelabCartographerWidget.tsx\n M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx\n M src/components/dashboard/HomelabTestRunnerWidget.tsx\n M src/components/dashboard/__tests__/HomelabBlueprintReviewWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx\n M src/components/dashboard/__tests__/HomelabTestRunnerWidget.test.tsx\n M src/components/dashboard/demo-v4/DashboardDemoV4FloatingNav.tsx\n M src/hooks/useScoutOverview.ts\n M src/lib/scout-overview.ts\n M src/styles/dashboard-demo-v4.css\n?? _blueprints/proposals/\n?? cartogrpaherPlanAuto.md\n?? docs/cartographer-trust-source-plan.md\n?? masterOverhual.md\n?? scouUi.md\n?? scout/=8,\n?? scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T160750Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T161258Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T194610Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T195549Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T210942Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T211119Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212209Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212434Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212527Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212803Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-16T212901Z.json\n?? scoutRefinemint.md\n?? source_proxy/agents/\n?? source_proxy/cartographer/git_approvals.py\n?? source_proxy/cartographer/proposal_reviews.py\n?? source_proxy/cartographer/soak-logs/\n?? source_proxy/terminal_presets.py\n?? source_proxy/tests/test_agent_registry.py\n?? src/app/api/scout/source-candidates/batch-approve/\n?? src/app/intelligence/\n?? src/app/v1/cartographer/branch-recommendations/[recommendationId]/\n?? src/app/v1/cartographer/commit-proposals/[commitProposalId]/\n?? src/app/v1/cartographer/proposals/[proposalId]/review/\n?? src/app/v1/cartographer/push-queue/[pushId]/\n?? src/components/dashboard/ScoutIntelligenceCenter.tsx\n?? src/lib/scout-human-readable.ts",
docs/plans/media/face-organizer-full-system-integration-20260613.md:10:This is a plan-only document. It does not authorize implementation, media movement, web evidence collection, face enrollment, organizer `--apply`, git mutation, or service restarts. Every phase and increment below has a manual pause gate. Britton must approve the next phase before work proceeds.
docs/plans/media/face-organizer-full-system-integration-20260613.md:389:- Do not start or restart services unless separately approved.
./src/styles/dashboard-demo-v4.css:3139:.dashboard-demo-v4-smart-healthy {
./src/styles/dashboard-demo-v4.css:3331:  .dashboard-demo-v4-smart-healthy,
./src/styles/dashboard-demo-v4.css:4179:  .dashboard-demo-v4-smart-healthy,
scripts/source-bwrap-network-probe.sh:5:PYTHON_BIN="${SOURCE_PROXY_PYTHON:-./.venv-source-proxy/bin/python}"
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-18T205758Z.json:28:    "after": "M README.md\n M chatDesign/components/chat/__tests__/ChatThreadSidebar.test.tsx\n M docs/cartographer-trust-source-plan.md\n M docs/codex-real-task-trial.md\n D proxyCLI.md\n M source_proxy/api/cartographer.py\n M source_proxy/api/codex_adapter.py\n M source_proxy/api/long_running_tasks.py\n M source_proxy/approval/gate.py\n M source_proxy/cartographer/apply.py\n M source_proxy/cartographer/audit_trail.py\n M source_proxy/cartographer/branch_recommendations.py\n M source_proxy/cartographer/change_scribe.py\n M source_proxy/cartographer/commit_proposals.py\n M source_proxy/cartographer/component_mapper.py\n M source_proxy/cartographer/drift.py\n M source_proxy/cartographer/git_approvals.py\n M source_proxy/cartographer/git_status.py\n M source_proxy/cartographer/models.py\n M source_proxy/cartographer/project_discovery.py\n M source_proxy/cartographer/project_health.py\n M source_proxy/cartographer/proposal_previews.py\n M source_proxy/cartographer/proposal_reviews.py\n M source_proxy/cartographer/proposals.py\n M source_proxy/cartographer/push_queue.py\n M source_proxy/cartographer/safety.py\n M source_proxy/cartographer/service.py\n M source_proxy/cartographer/starter_blueprints.py\n M source_proxy/cartographer/sub_cartographers.py\n M source_proxy/codex/__init__.py\n M source_proxy/codex/evidence.py\n M source_proxy/tasks/long_running.py\n M source_proxy/testing/runner.py\n M source_proxy/tests/test_cartographer_api.py\n M source_proxy/tests/test_codex_cli_adapter.py\n M source_proxy/tests/test_coding_regression_pack.py\n M source_proxy/tests/test_long_running_tasks.py\n M source_proxy/tests/test_proxy_runner.py\n M src/app/(dashboard)/page.tsx\n M src/app/api/scout/overview/route.ts\n M src/app/intelligence/page.tsx\n M src/app/v1/actions/execute-approved/__tests__/route.test.ts\n M src/app/v1/actions/execute-approved/route.ts\n M src/app/v1/cartographer/push-queue/route.ts\n M src/app/v1/coding/codex/route.ts\n M src/app/v1/tasks/long-running/route.ts\n M src/components/chat/__tests__/spirit-chat-oracle-contract.test.ts\n M src/components/coding/CodingAgentInterface.tsx\n M src/components/coding/__tests__/coding-workflow-step.test.ts\n M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx\n M src/components/dashboard/ScoutIntelligenceCenter.tsx\n M src/components/dashboard/SpiritDashboardHome.tsx\n M src/components/dashboard/__tests__/SpiritDashboardHome.test.tsx\n M src/components/dashboard/demo-v4/DashboardDemoV4.tsx\n M src/hooks/useClusterTelemetry.ts\n M src/hooks/useScoutOverview.ts\n M src/lib/server/capabilities/format-capability-answer.ts\n?? docs/agent-wrapper-reference-study.md\n?? docs/aionui-reference-study.md\n?? docs/plan-index.md\n?? docs/source-proxy-production-hardening-plan.md\n?? docs/source-proxy-remote-manual-checks.md\n?? docs/spirit-cowork-gap-report.md\n?? productionProxy.md\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T022851Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T041707Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T042305Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T042542Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T110315Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T110546Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T110712Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T185656Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T185757Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T190127Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T192908Z.json\n?? source_proxy/cartographer/autopilot_apply.py\n?? source_proxy/cartographer/autopilot_config.py\n?? source_proxy/cartographer/autopilot_dry_run.py\n?? source_proxy/cartographer/autopilot_soak.py\n?? source_proxy/cartographer/clutter_inventory.py\n?? source_proxy/cartographer/clutter_proposals.py\n?? source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-18T022743Z.json\n?? source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-18T205159Z.json\n?? source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-18T205758Z.json\n?? src/app/v1/cartographer/clutter-inventory/\n?? src/app/v1/cartographer/clutter-proposals/\n?? src/app/v1/cartographer/docs-autopilot/\n?? src/app/v1/cartographer/starter-blueprints/\n?? src/app/v1/coding/codex/__tests__/",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-18T205758Z.json:33:    "before": "M README.md\n M chatDesign/components/chat/__tests__/ChatThreadSidebar.test.tsx\n M docs/cartographer-trust-source-plan.md\n M docs/codex-real-task-trial.md\n D proxyCLI.md\n M source_proxy/api/cartographer.py\n M source_proxy/api/codex_adapter.py\n M source_proxy/api/long_running_tasks.py\n M source_proxy/approval/gate.py\n M source_proxy/cartographer/apply.py\n M source_proxy/cartographer/audit_trail.py\n M source_proxy/cartographer/branch_recommendations.py\n M source_proxy/cartographer/change_scribe.py\n M source_proxy/cartographer/commit_proposals.py\n M source_proxy/cartographer/component_mapper.py\n M source_proxy/cartographer/drift.py\n M source_proxy/cartographer/git_approvals.py\n M source_proxy/cartographer/git_status.py\n M source_proxy/cartographer/models.py\n M source_proxy/cartographer/project_discovery.py\n M source_proxy/cartographer/project_health.py\n M source_proxy/cartographer/proposal_previews.py\n M source_proxy/cartographer/proposal_reviews.py\n M source_proxy/cartographer/proposals.py\n M source_proxy/cartographer/push_queue.py\n M source_proxy/cartographer/safety.py\n M source_proxy/cartographer/service.py\n M source_proxy/cartographer/starter_blueprints.py\n M source_proxy/cartographer/sub_cartographers.py\n M source_proxy/codex/__init__.py\n M source_proxy/codex/evidence.py\n M source_proxy/tasks/long_running.py\n M source_proxy/testing/runner.py\n M source_proxy/tests/test_cartographer_api.py\n M source_proxy/tests/test_codex_cli_adapter.py\n M source_proxy/tests/test_coding_regression_pack.py\n M source_proxy/tests/test_long_running_tasks.py\n M source_proxy/tests/test_proxy_runner.py\n M src/app/(dashboard)/page.tsx\n M src/app/api/scout/overview/route.ts\n M src/app/intelligence/page.tsx\n M src/app/v1/actions/execute-approved/__tests__/route.test.ts\n M src/app/v1/actions/execute-approved/route.ts\n M src/app/v1/cartographer/push-queue/route.ts\n M src/app/v1/coding/codex/route.ts\n M src/app/v1/tasks/long-running/route.ts\n M src/components/chat/__tests__/spirit-chat-oracle-contract.test.ts\n M src/components/coding/CodingAgentInterface.tsx\n M src/components/coding/__tests__/coding-workflow-step.test.ts\n M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx\n M src/components/dashboard/ScoutIntelligenceCenter.tsx\n M src/components/dashboard/SpiritDashboardHome.tsx\n M src/components/dashboard/__tests__/SpiritDashboardHome.test.tsx\n M src/components/dashboard/demo-v4/DashboardDemoV4.tsx\n M src/hooks/useClusterTelemetry.ts\n M src/hooks/useScoutOverview.ts\n M src/lib/server/capabilities/format-capability-answer.ts\n?? docs/agent-wrapper-reference-study.md\n?? docs/aionui-reference-study.md\n?? docs/plan-index.md\n?? docs/source-proxy-production-hardening-plan.md\n?? docs/source-proxy-remote-manual-checks.md\n?? docs/spirit-cowork-gap-report.md\n?? productionProxy.md\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T022851Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T041707Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T042305Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T042542Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T110315Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T110546Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T110712Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T185656Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T185757Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T190127Z.json\n?? scout/soak-logs/scout-soak-snapshot-2026-05-18T192908Z.json\n?? source_proxy/cartographer/autopilot_apply.py\n?? source_proxy/cartographer/autopilot_config.py\n?? source_proxy/cartographer/autopilot_dry_run.py\n?? source_proxy/cartographer/autopilot_soak.py\n?? source_proxy/cartographer/clutter_inventory.py\n?? source_proxy/cartographer/clutter_proposals.py\n?? source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-18T022743Z.json\n?? source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-18T205159Z.json\n?? src/app/v1/cartographer/clutter-inventory/\n?? src/app/v1/cartographer/clutter-proposals/\n?? src/app/v1/cartographer/docs-autopilot/\n?? src/app/v1/cartographer/starter-blueprints/\n?? src/app/v1/coding/codex/__tests__/",
source_proxy/cartographer/soak-logs/cartographer-soak-snapshot-2026-05-18T205758Z.json:44:    "Review commit proposal commit-prop-62d33f2b07ae (cartographer, high risk, 6 files) with curl -k -s http://localhost:3000/v1/cartographer/commit-proposals | jq '.commit_proposals[] | select(.commit_proposal_id==\"commit-prop-62d33f2b07ae\")'; do not approve until proposal/drift review is complete."
./source_proxy/cartographer/level_14_autonomy_runtime.py:208:def build_level_14_recurring_health_check_dry_run(
./source_proxy/cartographer/level_14_autonomy_runtime.py:215:        reasons += ["unsupported_health_check_class"]
```

## Local Search: Failure Signals

```
./scoutRefinemint.md:22:- 1 blocked candidate.
./scoutRefinemint.md:78:- call a budget-blocked search smoke "normal pass"
./scoutRefinemint.md:103:- view poller support
./scoutRefinemint.md:123:What search jobs are queued, running, blocked, duplicate, stale, or over budget?
./scoutRefinemint.md:145:5. Search smoke reports BLOCKED_BY_BUDGET instead of generic FAIL when daily cap is reached.
./scoutRefinemint.md:146:6. Queued discovery jobs show stale, duplicate, blocked, running, failed, or completed status.
./scoutRefinemint.md:152:12. Approved unsupported source types show poller_supported false as an info state, not an error.
./scoutRefinemint.md:204:    "blocked_reason": "daily_limit_reached",
./scoutRefinemint.md:274:blocked_by_budget
./scoutRefinemint.md:460:blocked_reason: daily_limit_reached
./scoutRefinemint.md:484:Move to Phase 1 runner/report polish.
./scoutRefinemint.md:490:Phase 1: Runner and Diagnostic Report Polish
./scoutRefinemint.md:518:Every report should include:
./scoutRefinemint.md:535:All profiles use the same report structure.
./scoutRefinemint.md:540:Check profile-specific report builders.
./scoutRefinemint.md:544:Revert report formatting changes only.
./scoutRefinemint.md:810:May show poller_supported false.
./scoutRefinemint.md:870:poller support prediction
./scoutRefinemint.md:928:Show who approved, rejected, or blocked a candidate, when, and why.
./scoutRefinemint.md:997:"poller_supported": false,
./scoutRefinemint.md:1001:Unsupported source type should not look scary.
./scoutRefinemint.md:1029:Add source health and poller support labels.
./scoutRefinemint.md:1035:Increment 3.4: Source health and poller support labels
./scoutRefinemint.md:1044:poller_supported true/false
./scoutRefinemint.md:1056:Do not treat poller_supported false as failure.
./scoutRefinemint.md:1071:    poller:.poller_supported,
./scoutRefinemint.md:1083:Check poller support mapping.
./scoutRefinemint.md:1241:Keep blocked sources blocked.
./scoutRefinemint.md:1255:Check blocked source lookup.
./scoutRefinemint.md:1522:manual_import_only
./scoutRefinemint.md:1594:Check blocked/rejected override.
./scoutRefinemint.md:1675:UI must show poller support.
./scoutRefinemint.md:1677:No blocked/rejected candidates can be batch approved.
./scoutRefinemint.md:1702:Check partial failure reporting.
./scoutRefinemint.md:1728:Add a dry-run report:
./scoutRefinemint.md:1737:not blocked
./scoutRefinemint.md:1740:not unsupported unless explicitly allowed
./scoutRefinemint.md:1758:Check blocked/rejected filters.
./scoutRefinemint.md:1872:Rejected and blocked decisions stay durable.
./scoutRefinemint.md:1987:"Search smoke is blocked because the daily discovery job limit has been reached. Active sources were not changed. Candidates were not changed. Next safe step: inspect queued jobs, cancel stale duplicates, or wait for budget reset."
./scoutRefinemint.md:2019:Expose a clear discovery budget summary so Scout can explain when scout-search-smoke is blocked by the daily discovery job limit.
./scoutRefinemint.md:2048:blocked_reason
./scoutRefinemint.md:2101:budget.blocked_reason is daily_limit_reached when cap is exhausted.
./scoutRefinemint.md:2102:scout-search-smoke reports BLOCKED_BY_BUDGET or a clearer budget-blocked state instead of vague FAIL if you touch the runner.
./scoutRefinemint.md:2144:- `scout_v0_1` is up and Docker reports it as healthy.
./scoutRefinemint.md:2147:- Candidate counts are bounded: `needs_review: 2`, `approved: 2`, `recommended: 12`, `rejected: 1`, `blocked: 1`, `stored: 0`.
./scoutRefinemint.md:2174:- `blocked`: 1
./scoutRefinemint.md:2212:- `docker port spirit-ollama` reports no published port.
./scoutRefinemint.md:2251:- whether Ollama should be reached through a published host port or shared Docker network DNS
./scoutRefinemint.md:2272:docker port spirit-ollama 2>/dev/null || true
./vitest.config.mjs:1:import { defineConfig } from "vitest/config";
./vitest.config.mjs:2:import react from "@vitejs/plugin-react";
./vitest.config.mjs:3:import path from "path";
./vitest.config.mjs:4:import { fileURLToPath } from "url";
./vitest.config.mjs:6:const __dirname = path.dirname(fileURLToPath(import.meta.url));
./vitest.config.mjs:8:export default defineConfig({
./postcss.config.mjs:7:export default config;
./basic.js:1:export default class BasicReporter {
./basic.js:5:    console.log(`\nBasic reporter: ${passedFiles} passed files, ${failedFiles} failed files, ${errors.length} errors`);
./post-v1-diag.md:225:- dashboard reports ready with valid freeze marker
./services/jellyfin/docker-compose.yml:6:    ports:
./services/jellyfin/docker-compose.yml:33:      timeout: 10s
./services/jellyfin/sync_folder_playlists.py:9:from __future__ import annotations
./services/jellyfin/sync_folder_playlists.py:11:import json
./services/jellyfin/sync_folder_playlists.py:12:import sqlite3
./services/jellyfin/sync_folder_playlists.py:13:import sys
./services/jellyfin/sync_folder_playlists.py:14:import time
./services/jellyfin/sync_folder_playlists.py:15:import urllib.error
./services/jellyfin/sync_folder_playlists.py:16:import urllib.parse
./services/jellyfin/sync_folder_playlists.py:17:import urllib.request
./services/jellyfin/sync_folder_playlists.py:18:from dataclasses import dataclass
./services/jellyfin/sync_folder_playlists.py:79:            with urllib.request.urlopen(request, timeout=60) as response:
./productionProxy.md:17:- protected paths and traversal are blocked
./productionProxy.md:88:- live port 3000 route checks reliable
./productionProxy.md:91:- fresh closeout report is readable and honest
./productionProxy.md:98:- dangerous flags blocked
./productionProxy.md:99:- protected/secret paths blocked
./productionProxy.md:101:- live route is either safely enabled or cleanly config-blocked
./productionProxy.md:158:- report findings
./productionProxy.md:204:docs/spirit-cowork-gap-report.md
./productionProxy.md:345:If broad failures appear, stop and report.
./productionProxy.md:398:routes return JSON or a clear service-unavailable/config-blocked response
./productionProxy.md:408:If route crashes, isolate route handler.
./productionProxy.md:449:runner reports expected snapshot writes clearly
./productionProxy.md:478:Define exactly when /v1/coding/codex should return config-blocked versus run a safe readonly/proposal task.
./productionProxy.md:488:The route must support:
./productionProxy.md:490:config-blocked
./productionProxy.md:493:explicit blocked state for apply/commit/push
./productionProxy.md:511:route returns evidence or config-blocked
./productionProxy.md:512:no crash
./productionProxy.md:518:If env flag missing, return config-blocked with exact reason.
./productionProxy.md:573:unsafe route inputs blocked
./productionProxy.md:574:missing allowed_files blocked for proposal mode
./productionProxy.md:637:from source_proxy.codex.evidence import summarize_codex_evidence
./productionProxy.md:638:print("evidence summary import ok")
./productionProxy.md:800:blocked warning signs
./productionProxy.md:874:If runner mutates unexpectedly, classify output as blocked.
./productionProxy.md:982:If UI gets noisy, group by active, blocked, completed.
./productionProxy.md:1011:test report
./productionProxy.md:1052:Make blocked tasks explain what to do next.
./productionProxy.md:1063:config_blocked
./productionProxy.md:1087:blocked tasks say why
./productionProxy.md:1126:test reports
./productionProxy.md:1202:missing target is blocked
./productionProxy.md:1203:protected target is blocked
./productionProxy.md:1357:approval unavailable when blocked
./productionProxy.md:1650:If it says "blocked" for expected evidence only, refine reason code.
./productionProxy.md:1796:one readable PASS/WARN/BLOCKED report
./productionProxy.md:1803:If report too long, add summary plus detail sections.
./productionProxy.md:2003:missing provider is config-blocked
./productionProxy.md:2049:If model lacks tool support, classify as planning/review only.
./productionProxy.md:2272:"Do not patch. Confirm proxyCLI.md is retired, scan stale plan references, classify active vs historical docs, and report exactly what should become the new source-of-truth plan file."
./scout/scripts/import_promotion_dry_run.py:1:from __future__ import annotations
./scout/scripts/import_promotion_dry_run.py:3:import argparse
./scout/scripts/import_promotion_dry_run.py:4:import json
./scout/scripts/import_promotion_dry_run.py:5:import sys
./scout/scripts/import_promotion_dry_run.py:6:import urllib.error
./scout/scripts/import_promotion_dry_run.py:7:import urllib.request
./scout/scripts/import_promotion_dry_run.py:13:def _blocked_payload(detail: str, requested_by: str, status_code: int | None = None) -> dict:
./scout/scripts/import_promotion_dry_run.py:15:        "result": "blocked",
./scout/scripts/import_promotion_dry_run.py:40:        description="Dry-run one approved Scout promotion import without proxy writes.",
./scout/scripts/import_promotion_dry_run.py:47:        "--allow-blocked",
./scout/scripts/import_promotion_dry_run.py:60:        f"{args.base_url.rstrip('/')}/v1/scout/promotions/import-dry-run",
./scout/scripts/import_promotion_dry_run.py:66:        with urllib.request.urlopen(request, timeout=10) as response:
./scout/scripts/import_promotion_dry_run.py:75:            _blocked_payload(detail, args.requested_by, exc.code),
./scout/scripts/import_promotion_dry_run.py:78:        return 0 if args.allow_blocked else 2
./scout/scripts/import_promotion_dry_run.py:81:            _blocked_payload(str(exc), args.requested_by),
./scout/scripts/import_promotion_dry_run.py:84:        return 0 if args.allow_blocked else 2
./scout/scripts/review_promotions.py:1:from __future__ import annotations
./scout/scripts/review_promotions.py:3:import argparse
./scout/scripts/review_promotions.py:4:import os
./scout/scripts/review_promotions.py:5:import sys
./scout/scripts/review_promotions.py:6:from pathlib import Path
./scout/scripts/review_promotions.py:13:from scout.config import get_settings
./scout/scripts/review_promotions.py:14:from scout.packets.promotions import (
./scout/scripts/receipt_preview_harness.py:1:from __future__ import annotations
./scout/scripts/receipt_preview_harness.py:3:from datetime import datetime, timezone
./scout/scripts/receipt_preview_harness.py:4:import json
./scout/scripts/receipt_preview_harness.py:5:from pathlib import Path
./scout/scripts/receipt_preview_harness.py:6:import sys
./scout/scripts/receipt_preview_harness.py:7:from tempfile import TemporaryDirectory
./scout/scripts/receipt_preview_harness.py:14:from scout.config import ScoutSettings
./scout/scripts/receipt_preview_harness.py:15:from scout.debugger.verdict import DebuggerVerdict
./scout/scripts/receipt_preview_harness.py:16:from scout.packets.promotions import approve_promotion, dry_run_proxy_import, queue_promotion
./scout/scripts/receipt_preview_harness.py:17:from scout.packets.storage import insert_packet
./scout/scripts/receipt_preview_harness.py:18:from scout.storage.db import init_database, open_connection
./scout/scripts/receipt_preview_harness.py:19:from scout.storage.migrations import apply_migrations
./scout/scripts/receipt_preview_harness.py:20:from scout.tests.test_packet_schema import make_packet
./scout/scripts/receipt_preview_harness.py:87:        result = dry_run_proxy_import(settings, promotion_id)
./scout/scripts/receipt_preview_harness.py:91:            "import_ready": result["import_ready"] is True,
./scout/scripts/receipt_preview_harness.py:94:            == "scout_manual_import_receipt_preview",
./scout/scripts/receipt_preview_harness.py:95:            "receipt_not_imported": receipt.get("imported") is False,
./scout/scripts/receipt_preview_harness.py:104:            == "scout_manual_import_tombstone",
./scout/scripts/receipt_preview_harness.py:120:                "imported": receipt.get("imported"),
./scout/THREAT_MODEL.md:11:| Stale information presented as current | Old releases, old docs, or old reports may be surfaced as if they are fresh. | Phase 5.2 adds a staleness flag with per-source TTL rules. Packet timestamps are preserved for consumers. |
./scout/THREAT_MODEL.md:12:| LLM hallucination in packet summaries or impact analysis | Summaries may contain claims not supported by the source text. | Phase 5.4 Tier 3 hallucination check compares summary claims against wrapped raw extracted text. |
./scout/THREAT_MODEL.md:13:| Resource exhaustion from very large pages, very large repos, or deeply paginated feeds | Scout could consume excessive CPU, memory, disk, or network budget. | `SCOUT_FETCH_MAX_BYTES`, request timeouts, and per-source poll budgets bound external fetches. Phase 2 polling persists state and rate-limit metadata. |
./scout/THREAT_MODEL.md:30:Phase 5 keeps `sentence-transformers` optional for the CPU-only v0.1 image. The debugger imports it lazily only when a packet reaches Tier 3 embedding storage; if the package is unavailable, the embedding subcheck records a skipped finding and the verdict still completes. This avoids pulling CUDA Torch wheels into the default Scout container and preserves the Phase 1 CPU-only decision.
./scout/SCOPE.md:10:2. Structured extraction from fetched content under bounded timeout and size limits.
./scout/SCOPE.md:26:Scout v0.1 runs CPU-only. GPU scheduling is deferred so Scout does not contend with the proxy's local LLM for VRAM on the Dell workstation. GPU profiles belong to the portability phase once the basic local service is stable.
./chatDesign/styles/spirit-trinity-chat.css:2: * The imported zip is visual reference only; this layer keeps live SpiritChat runtime intact.
./chatDesign/styles/spirit-trinity-chat.css:95:    linear-gradient(135deg, #d9e3ea 0%, #aebcca 45%, #8495a5 100%) !important;
./chatDesign/styles/spirit-trinity-chat.css:265:  backdrop-filter: blur(var(--spirit-blur)) !important;
./chatDesign/styles/spirit-trinity-chat.css:266:  -webkit-backdrop-filter: blur(var(--spirit-blur)) !important;
./chatDesign/styles/spirit-trinity-chat.css:327:  max-width: 780px !important;
./chatDesign/styles/spirit-trinity-chat.css:332:  color: var(--trinity-text) !important;
./chatDesign/styles/spirit-trinity-chat.css:337:  color: rgba(15, 23, 42, 0.78) !important;
./chatDesign/styles/spirit-trinity-chat.css:354:  max-width: 690px !important;
./chatDesign/styles/spirit-trinity-chat.css:355:  border-radius: 18px !important;
./chatDesign/styles/spirit-trinity-chat.css:383:  border-color: rgba(255, 255, 255, 0.10) !important;
./chatDesign/styles/spirit-trinity-chat.css:384:  background: transparent !important;
./chatDesign/styles/spirit-trinity-chat.css:388:  max-width: none !important;
./chatDesign/styles/spirit-trinity-chat.css:389:  border-color: var(--trinity-line-strong) !important;
./chatDesign/styles/spirit-trinity-chat.css:390:  background: rgba(255, 255, 255, 0.24) !important;
./chatDesign/styles/spirit-trinity-chat.css:391:  color: rgba(15, 23, 42, 0.82) !important;
./chatDesign/styles/spirit-trinity-chat.css:405:  color: var(--trinity-text) !important;
./chatDesign/styles/spirit-trinity-chat.css:406:  font-size: 16px !important;
./chatDesign/styles/spirit-trinity-chat.css:407:  min-height: 44px !important;
./chatDesign/styles/spirit-trinity-chat.css:411:  color: rgba(51, 65, 85, 0.62) !important;
./chatDesign/styles/spirit-trinity-chat.css:417:  color: rgba(15, 23, 42, 0.76) !important;
./chatDesign/styles/spirit-trinity-chat.css:422:  border-color: rgba(255, 255, 255, 0.42) !important;
./chatDesign/styles/spirit-trinity-chat.css:423:  background: rgba(255, 255, 255, 0.16) !important;
./chatDesign/styles/spirit-trinity-chat.css:430:  border-color: rgba(30, 41, 59, 0.34) !important;
./chatDesign/styles/spirit-trinity-chat.css:431:  background: rgba(255, 255, 255, 0.34) !important;
./chatDesign/styles/spirit-trinity-chat.css:451:  background: rgba(52, 58, 68, 0.42) !important;
./chatDesign/styles/spirit-trinity-chat.css:452:  color: var(--trinity-text) !important;
./chatDesign/styles/spirit-trinity-chat.css:460:  color: rgba(30, 41, 59, 0.68) !important;
./chatDesign/styles/spirit-trinity-chat.css:464:  color: var(--trinity-text-soft) !important;
./chatDesign/styles/spirit-trinity-chat.css:470:  color: var(--trinity-text) !important;
./chatDesign/styles/spirit-trinity-chat.css:476:  color: var(--trinity-liquid-text-strong) !important;
./chatDesign/styles/spirit-trinity-chat.css:479:    0 0 14px rgba(186, 240, 255, 0.28) !important;
./chatDesign/styles/spirit-trinity-chat.css:483:  color: color-mix(in oklab, var(--trinity-liquid-muted) 92%, rgba(13, 24, 38, 0.85)) !important;
./chatDesign/styles/spirit-trinity-chat.css:484:  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.48) !important;
./chatDesign/styles/spirit-trinity-chat.css:489:  border-color: var(--trinity-line) !important;
./chatDesign/styles/spirit-trinity-chat.css:500:  background: rgba(255, 255, 255, 0.08) !important;
./chatDesign/styles/spirit-trinity-chat.css:504:  color: var(--trinity-text) !important;
./chatDesign/styles/spirit-trinity-chat.css:529:  position: relative !important;
./chatDesign/styles/spirit-trinity-chat.css:530:  isolation: isolate !important;
./chatDesign/styles/spirit-trinity-chat.css:531:  overflow: hidden !important;
./chatDesign/styles/spirit-trinity-chat.css:532:  border-radius: 999px !important;
./chatDesign/styles/spirit-trinity-chat.css:533:  border-width: 1px !important;
./chatDesign/styles/spirit-trinity-chat.css:534:  border-style: solid !important;
./chatDesign/styles/spirit-trinity-chat.css:535:  border-color: color-mix(in oklab, var(--trinity-liquid-cyan-edge) 68%, rgba(255, 255, 255, 0.72) 32%) !important;
./chatDesign/styles/spirit-trinity-chat.css:536:  background-color: var(--trinity-liquid-clear-center) !important;
./chatDesign/styles/spirit-trinity-chat.css:551:    radial-gradient(ellipse 80% 55% at 12% 100%, rgba(168, 228, 255, 0.32) 0%, transparent 60%) !important;
./chatDesign/styles/spirit-trinity-chat.css:552:  background-blend-mode: screen, screen, soft-light, normal !important;
./chatDesign/styles/spirit-trinity-chat.css:553:  color: var(--trinity-liquid-text-strong) !important;
./chatDesign/styles/spirit-trinity-chat.css:554:  font-weight: 650 !important;
./chatDesign/styles/spirit-trinity-chat.css:555:  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.45) !important;
./chatDesign/styles/spirit-trinity-chat.css:563:    0 2px 8px -4px rgba(15, 23, 42, 0.07) !important;
./chatDesign/styles/spirit-trinity-chat.css:566:  filter: none !important;
./chatDesign/styles/spirit-trinity-chat.css:567:  outline: none !important;
./chatDesign/styles/spirit-trinity-chat.css:613:  color: rgba(8, 18, 30, 0.92) !important;
./chatDesign/styles/spirit-trinity-chat.css:614:  stroke: currentColor !important;
./chatDesign/styles/spirit-trinity-chat.css:615:  fill: none !important;
./chatDesign/styles/spirit-trinity-chat.css:616:  opacity: 1 !important;
./chatDesign/styles/spirit-trinity-chat.css:617:  filter: none !important;
./chatDesign/styles/spirit-trinity-chat.css:621:  width: 0.875rem !important;
./chatDesign/styles/spirit-trinity-chat.css:622:  height: 0.875rem !important;
./chatDesign/styles/spirit-trinity-chat.css:623:  flex-shrink: 0 !important;
./chatDesign/styles/spirit-trinity-chat.css:642:  border-color: color-mix(in oklab, var(--trinity-liquid-cyan-edge) 78%, rgba(255, 255, 255, 0.88) 22%) !important;
./chatDesign/styles/spirit-trinity-chat.css:643:  background-color: var(--trinity-liquid-clear-fill) !important;
./chatDesign/styles/spirit-trinity-chat.css:658:    radial-gradient(ellipse 82% 52% at 14% 100%, rgba(158, 226, 255, 0.34) 0%, transparent 58%) !important;
./chatDesign/styles/spirit-trinity-chat.css:659:  background-blend-mode: screen, screen, soft-light, normal !important;
./chatDesign/styles/spirit-trinity-chat.css:666:    0 4px 14px -6px rgba(15, 23, 42, 0.08) !important;
./chatDesign/styles/spirit-trinity-chat.css:667:  filter: none !important;
./chatDesign/styles/spirit-trinity-chat.css:672:  border-color: rgba(186, 245, 255, 0.98) !important;
./chatDesign/styles/spirit-trinity-chat.css:678:    inset 0 -3px 14px -5px rgba(72, 198, 238, 0.34) !important;
./chatDesign/styles/spirit-trinity-chat.css:683:  opacity: 1 !important;
./chatDesign/styles/spirit-trinity-chat.css:684:  cursor: not-allowed !important;
./chatDesign/styles/spirit-trinity-chat.css:685:  border-color: color-mix(in oklab, var(--trinity-liquid-cyan-edge) 62%, rgba(255, 255, 255, 0.48) 38%) !important;
./chatDesign/styles/spirit-trinity-chat.css:686:  background-color: color-mix(in oklab, var(--trinity-liquid-clear-center) 85%, transparent) !important;
./chatDesign/styles/spirit-trinity-chat.css:701:    radial-gradient(ellipse 78% 50% at 12% 100%, rgba(158, 228, 255, 0.22) 0%, transparent 62%) !important;
./chatDesign/styles/spirit-trinity-chat.css:702:  background-blend-mode: screen, screen, soft-light, normal !important;
./chatDesign/styles/spirit-trinity-chat.css:703:  color: color-mix(in oklab, var(--trinity-liquid-text-strong) 72%, var(--trinity-liquid-muted)) !important;
./chatDesign/styles/spirit-trinity-chat.css:704:  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.35) !important;
./chatDesign/styles/spirit-trinity-chat.css:705:  filter: none !important;
./chatDesign/styles/spirit-trinity-chat.css:711:    0 4px 14px -10px var(--trinity-liquid-blue-shadow) !important;
./chatDesign/styles/spirit-trinity-chat.css:732:    display: flex !important;
./chatDesign/styles/spirit-trinity-chat.css:733:    flex-direction: column !important;
./chatDesign/styles/spirit-trinity-chat.css:734:    width: var(--chat-thread-rail-width) !important;
./chatDesign/styles/spirit-trinity-chat.css:738:    height: calc(100% - 2.25rem) !important;
./chatDesign/styles/spirit-trinity-chat.css:741:    border: 1px solid var(--trinity-sidebar-border) !important;
./chatDesign/styles/spirit-trinity-chat.css:742:    border-radius: 1rem !important;
./chatDesign/styles/spirit-trinity-chat.css:743:    background: var(--trinity-sidebar-glass) !important;
./chatDesign/styles/spirit-trinity-chat.css:748:      inset 0 -1px 0 rgba(255, 255, 255, 0.05) !important;
./chatDesign/styles/spirit-trinity-chat.css:754:    gap: 0.625rem !important;
./chatDesign/styles/spirit-trinity-chat.css:755:    border-bottom: 1px solid rgba(52, 62, 76, 0.18) !important;
./chatDesign/styles/spirit-trinity-chat.css:756:    padding: 0.7rem 0.7rem 0.75rem !important;
./chatDesign/styles/spirit-trinity-chat.css:760:    display: flex !important;
./chatDesign/styles/spirit-trinity-chat.css:761:    align-items: center !important;
./chatDesign/styles/spirit-trinity-chat.css:762:    gap: 0.5rem !important;
./chatDesign/styles/spirit-trinity-chat.css:766:    font-family: var(--font-sans), ui-sans-serif, system-ui, sans-serif !important;
./chatDesign/styles/spirit-trinity-chat.css:767:    font-size: 0.6875rem !important;
./chatDesign/styles/spirit-trinity-chat.css:768:    font-weight: 600 !important;
./chatDesign/styles/spirit-trinity-chat.css:769:    letter-spacing: 0.08em !important;
./chatDesign/styles/spirit-trinity-chat.css:770:    text-transform: uppercase !important;
./chatDesign/styles/spirit-trinity-chat.css:774:    font-family: var(--font-sans), ui-sans-serif, system-ui, sans-serif !important;
./chatDesign/styles/spirit-trinity-chat.css:775:    font-size: 0.625rem !important;
./chatDesign/styles/spirit-trinity-chat.css:776:    font-weight: 500 !important;
./chatDesign/styles/spirit-trinity-chat.css:777:    letter-spacing: 0.02em !important;
./chatDesign/styles/spirit-trinity-chat.css:781:    justify-content: stretch !important;
./chatDesign/styles/spirit-trinity-chat.css:782:    flex-wrap: nowrap !important;
./chatDesign/styles/spirit-trinity-chat.css:783:    gap: 0.5rem !important;
./chatDesign/styles/spirit-trinity-chat.css:788:    flex: 1 1 auto !important;
./chatDesign/styles/spirit-trinity-chat.css:789:    min-width: 0 !important;
./chatDesign/styles/spirit-trinity-chat.css:790:    min-height: 2.15rem !important;
./chatDesign/styles/spirit-trinity-chat.css:791:    font-family: var(--font-sans), ui-sans-serif, system-ui, sans-serif !important;
./chatDesign/styles/spirit-trinity-chat.css:792:    font-size: 0.75rem !important;
./chatDesign/styles/spirit-trinity-chat.css:793:    font-weight: 700 !important;
./chatDesign/styles/spirit-trinity-chat.css:794:    letter-spacing: 0.01em !important;
./chatDesign/styles/spirit-trinity-chat.css:795:    text-transform: none !important;
./chatDesign/styles/spirit-trinity-chat.css:799:    flex: 0 0 auto !important;
./chatDesign/styles/spirit-trinity-chat.css:800:    min-height: 2.15rem !important;
./chatDesign/styles/spirit-trinity-chat.css:801:    padding-inline: 0.7rem !important;
./chatDesign/styles/spirit-trinity-chat.css:802:    font-family: var(--font-sans), ui-sans-serif, system-ui, sans-serif !important;
./chatDesign/styles/spirit-trinity-chat.css:803:    font-size: 0.6875rem !important;
./chatDesign/styles/spirit-trinity-chat.css:804:    font-weight: 700 !important;
./chatDesign/styles/spirit-trinity-chat.css:805:    letter-spacing: 0.015em !important;
./chatDesign/styles/spirit-trinity-chat.css:806:    text-transform: none !important;
./chatDesign/styles/spirit-trinity-chat.css:810:    font-family: var(--font-sans), ui-sans-serif, system-ui, sans-serif !important;
./chatDesign/styles/spirit-trinity-chat.css:811:    font-size: 0.625rem !important;
./chatDesign/styles/spirit-trinity-chat.css:812:    font-weight: 600 !important;
./chatDesign/styles/spirit-trinity-chat.css:813:    letter-spacing: 0.08em !important;
./chatDesign/styles/spirit-trinity-chat.css:814:    text-transform: uppercase !important;
./chatDesign/styles/spirit-trinity-chat.css:815:    color: color-mix(in oklab, var(--trinity-liquid-text-strong) 90%, rgba(100, 200, 228, 0.18)) !important;
./chatDesign/styles/spirit-trinity-chat.css:819:    font-size: 0.875rem !important;
./chatDesign/styles/spirit-trinity-chat.css:820:    font-weight: 600 !important;
./chatDesign/styles/spirit-trinity-chat.css:821:    line-height: 1.32 !important;
./chatDesign/styles/spirit-trinity-chat.css:822:    color: rgba(22, 30, 42, 0.94) !important;
./chatDesign/styles/spirit-trinity-chat.css:826:    font-size: 0.6875rem !important;
./chatDesign/styles/spirit-trinity-chat.css:827:    font-weight: 500 !important;
./chatDesign/styles/spirit-trinity-chat.css:828:    color: rgba(52, 62, 74, 0.72) !important;
./chatDesign/styles/spirit-trinity-chat.css:834:    font-size: 0.875rem !important;
./chatDesign/styles/spirit-trinity-chat.css:835:    line-height: 1.32 !important;
./chatDesign/styles/spirit-trinity-chat.css:836:    color: rgba(22, 30, 42, 0.92) !important;
./chatDesign/styles/spirit-trinity-chat.css:840:    font-size: 0.6875rem !important;
./chatDesign/styles/spirit-trinity-chat.css:841:    color: rgba(52, 62, 74, 0.7) !important;
./chatDesign/styles/spirit-trinity-chat.css:846:  padding-inline: 1.25rem !important;
./chatDesign/styles/spirit-trinity-chat.css:850:  color: var(--trinity-text-muted) !important;
./chatDesign/styles/spirit-trinity-chat.css:854:  border-radius: 0.5rem !important;
./chatDesign/styles/spirit-trinity-chat.css:858:  color: inherit !important;
./chatDesign/styles/spirit-trinity-chat.css:863:  color: var(--trinity-text) !important;
./chatDesign/styles/spirit-trinity-chat.css:868:  color: var(--trinity-text) !important;
./chatDesign/styles/spirit-trinity-chat.css:944:  border: 1px solid rgba(42, 54, 68, 0.2) !important;
./chatDesign/styles/spirit-trinity-chat.css:947:    rgba(255, 255, 255, 0.05) !important;
./chatDesign/styles/spirit-trinity-chat.css:951:    0 26px 80px -56px rgba(15, 23, 42, 0.38) !important;
./chatDesign/styles/spirit-trinity-chat.css:960:    border-right: 1px solid var(--trinity-sidebar-border) !important;
./chatDesign/styles/spirit-trinity-chat.css:961:    background: var(--trinity-sidebar-glass) !important;
./chatDesign/styles/spirit-trinity-chat.css:966:      var(--trinity-sidebar-inner-shadow) !important;
./chatDesign/styles/spirit-trinity-chat.css:973:    min-height: 2.1rem !important;
./chatDesign/styles/spirit-trinity-chat.css:974:    font-size: 0.8125rem !important;
./chatDesign/styles/spirit-trinity-chat.css:975:    font-weight: 600 !important;
./chatDesign/styles/spirit-trinity-chat.css:979:    min-height: 2.1rem !important;
./chatDesign/styles/spirit-trinity-chat.css:980:    font-size: 0.75rem !important;
./chatDesign/styles/spirit-trinity-chat.css:981:    font-weight: 600 !important;
./chatDesign/styles/spirit-trinity-chat.css:986:  gap: 0.65rem !important;
./chatDesign/styles/spirit-trinity-chat.css:987:  padding: 0.85rem 0.75rem 0.7rem !important;
./chatDesign/styles/spirit-trinity-chat.css:991:  flex-direction: row !important;
./chatDesign/styles/spirit-trinity-chat.css:992:  align-items: stretch !important;
./chatDesign/styles/spirit-trinity-chat.css:993:  gap: 0.5rem !important;
./chatDesign/styles/spirit-trinity-chat.css:998:  border: 1px solid rgba(255, 255, 255, 0.38) !important;
./chatDesign/styles/spirit-trinity-chat.css:999:  border-radius: 999px !important;
./chatDesign/styles/spirit-trinity-chat.css:1002:    rgba(255, 255, 255, 0.12) !important;
./chatDesign/styles/spirit-trinity-chat.css:1003:  color: var(--trinity-text) !important;
./chatDesign/styles/spirit-trinity-chat.css:1010:  color: rgba(30, 41, 59, 0.66) !important;
./chatDesign/styles/spirit-trinity-chat.css:1016:    border: 1px solid color-mix(in oklab, var(--trinity-liquid-cyan-edge) 62%, rgba(255, 255, 255, 0.66) 38%) !important;
./chatDesign/styles/spirit-trinity-chat.css:1017:    background-color: var(--trinity-liquid-clear-center) !important;
./chatDesign/styles/spirit-trinity-chat.css:1032:      radial-gradient(ellipse 72% 48% at 8% 100%, rgba(158, 228, 255, 0.22) 0%, transparent 58%) !important;
./chatDesign/styles/spirit-trinity-chat.css:1033:    background-blend-mode: screen, screen, soft-light, normal !important;
./chatDesign/styles/spirit-trinity-chat.css:1034:    color: var(--trinity-liquid-text-strong) !important;
./chatDesign/styles/spirit-trinity-chat.css:1039:      0 8px 22px -14px var(--trinity-liquid-blue-shadow) !important;
./chatDesign/styles/spirit-trinity-chat.css:1045:    color: color-mix(in oklab, var(--trinity-liquid-muted) 88%, rgba(13, 24, 38, 0.5)) !important;
./chatDesign/styles/spirit-trinity-chat.css:1049:    border-color: rgba(255, 255, 255, 0.9) !important;
./chatDesign/styles/spirit-trinity-chat.css:1053:      inset 0 1px 0 rgba(255, 255, 255, 0.8) !important;
./chatDesign/styles/spirit-trinity-chat.css:1054:    outline: none !important;
./chatDesign/styles/spirit-trinity-chat.css:1058:    border-radius: 0.65rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1059:    border: 1px solid color-mix(in oklab, var(--trinity-liquid-cyan-edge) 64%, rgba(255, 255, 255, 0.62) 36%) !important;
./chatDesign/styles/spirit-trinity-chat.css:1060:    background-color: var(--trinity-liquid-clear-center) !important;
./chatDesign/styles/spirit-trinity-chat.css:1074:      radial-gradient(ellipse 74% 54% at 94% 90%, rgba(84, 206, 248, 0.38) 0%, transparent 54%) !important;
./chatDesign/styles/spirit-trinity-chat.css:1075:    background-blend-mode: screen, soft-light, normal !important;
./chatDesign/styles/spirit-trinity-chat.css:1080:      0 12px 30px -18px var(--trinity-liquid-blue-shadow) !important;
./chatDesign/styles/spirit-trinity-chat.css:1083:    color: var(--trinity-liquid-text-strong) !important;
./chatDesign/styles/spirit-trinity-chat.css:1087:    color: var(--trinity-liquid-text-strong) !important;
./chatDesign/styles/spirit-trinity-chat.css:1088:    font-weight: 650 !important;
./chatDesign/styles/spirit-trinity-chat.css:1092:    color: var(--trinity-liquid-muted) !important;
./chatDesign/styles/spirit-trinity-chat.css:1099:    border-radius: 999px !important;
./chatDesign/styles/spirit-trinity-chat.css:1100:    padding: 0.45rem 0.65rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1101:    border: 1px solid color-mix(in oklab, var(--trinity-liquid-cyan-edge) 64%, rgba(255, 255, 255, 0.72) 36%) !important;
./chatDesign/styles/spirit-trinity-chat.css:1102:    background-color: var(--trinity-liquid-clear-center) !important;
./chatDesign/styles/spirit-trinity-chat.css:1112:      radial-gradient(ellipse 68% 44% at 10% 100%, rgba(158, 228, 255, 0.22) 0%, transparent 56%) !important;
./chatDesign/styles/spirit-trinity-chat.css:1113:    background-blend-mode: screen, screen, soft-light, normal !important;
./chatDesign/styles/spirit-trinity-chat.css:1114:    color: var(--trinity-liquid-text-strong) !important;
./chatDesign/styles/spirit-trinity-chat.css:1121:      inset 0 9px 22px -16px rgba(255, 255, 255, 0.14) !important;
./chatDesign/styles/spirit-trinity-chat.css:1127:    color: color-mix(in oklab, var(--trinity-liquid-muted) 86%, rgba(13, 24, 38, 0.45)) !important;
./chatDesign/styles/spirit-trinity-chat.css:1131:    border-color: rgba(255, 255, 255, 0.9) !important;
./chatDesign/styles/spirit-trinity-chat.css:1136:      inset 0 0 0 1px rgba(255, 255, 255, 0.22) !important;
./chatDesign/styles/spirit-trinity-chat.css:1137:    outline: none !important;
./chatDesign/styles/spirit-trinity-chat.css:1141:    padding-top: 0 !important;
./chatDesign/styles/spirit-trinity-chat.css:1145:    border-radius: 0.65rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1146:    padding: 0.6rem 0.7rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1147:    border: 1px solid color-mix(in oklab, var(--trinity-liquid-cyan-edge) 62%, rgba(255, 255, 255, 0.66) 38%) !important;
./chatDesign/styles/spirit-trinity-chat.css:1148:    background-color: var(--trinity-liquid-clear-center) !important;
./chatDesign/styles/spirit-trinity-chat.css:1157:      radial-gradient(ellipse 62% 44% at 92% 94%, rgba(84, 206, 248, 0.4) 0%, transparent 54%) !important;
./chatDesign/styles/spirit-trinity-chat.css:1158:    background-blend-mode: screen, soft-light, normal !important;
./chatDesign/styles/spirit-trinity-chat.css:1163:      inset 0 0 0 1px rgba(255, 255, 255, 0.26) !important;
./chatDesign/styles/spirit-trinity-chat.css:1166:    color: var(--trinity-liquid-text-strong) !important;
./chatDesign/styles/spirit-trinity-chat.css:1170:    color: var(--trinity-liquid-text-strong) !important;
./chatDesign/styles/spirit-trinity-chat.css:1171:    font-weight: 650 !important;
./chatDesign/styles/spirit-trinity-chat.css:1175:    color: var(--trinity-liquid-muted) !important;
./chatDesign/styles/spirit-trinity-chat.css:1181:  padding: 0.42rem 0.5rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1182:  border-color: transparent !important;
./chatDesign/styles/spirit-trinity-chat.css:1183:  border-radius: 0.55rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1184:  background: transparent !important;
./chatDesign/styles/spirit-trinity-chat.css:1185:  box-shadow: none !important;
./chatDesign/styles/spirit-trinity-chat.css:1189:  border-color: transparent !important;
./chatDesign/styles/spirit-trinity-chat.css:1192:    color-mix(in oklab, var(--trinity-liquid-clear-center) 48%, rgba(13, 24, 38, 0.04)) !important;
./chatDesign/styles/spirit-trinity-chat.css:1193:  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.16) !important;
./chatDesign/styles/spirit-trinity-chat.css:1197:  border-color: transparent !important;
./chatDesign/styles/spirit-trinity-chat.css:1200:    color-mix(in oklab, var(--trinity-liquid-clear-fill) 56%, rgba(13, 24, 38, 0.06)) !important;
./chatDesign/styles/spirit-trinity-chat.css:1203:    inset 2px 0 0 color-mix(in oklab, var(--trinity-liquid-cyan-edge) 70%, transparent) !important;
./chatDesign/styles/spirit-trinity-chat.css:1207:  row-gap: 0 !important;
./chatDesign/styles/spirit-trinity-chat.css:1208:  column-gap: 0.35rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1212:  display: block !important;
./chatDesign/styles/spirit-trinity-chat.css:1213:  flex: 1 1 0% !important;
./chatDesign/styles/spirit-trinity-chat.css:1214:  min-width: 0 !important;
./chatDesign/styles/spirit-trinity-chat.css:1215:  overflow: hidden !important;
./chatDesign/styles/spirit-trinity-chat.css:1216:  text-overflow: ellipsis !important;
./chatDesign/styles/spirit-trinity-chat.css:1217:  white-space: nowrap !important;
./chatDesign/styles/spirit-trinity-chat.css:1218:  word-break: normal !important;
./chatDesign/styles/spirit-trinity-chat.css:1219:  -webkit-box-orient: unset !important;
./chatDesign/styles/spirit-trinity-chat.css:1220:  -webkit-line-clamp: unset !important;
./chatDesign/styles/spirit-trinity-chat.css:1221:  line-clamp: unset !important;
./chatDesign/styles/spirit-trinity-chat.css:1225:  margin: 0.14rem 0 0.06rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1226:  padding-inline: 0.48rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1227:  color: color-mix(in oklab, var(--trinity-liquid-muted) 68%, transparent) !important;
./chatDesign/styles/spirit-trinity-chat.css:1228:  font-size: 0.58rem !important;
./chatDesign/styles/spirit-trinity-chat.css:1229:  font-weight: 650 !important;
./chatDesign/styles/spirit-trinity-chat.css:1230:  letter-spacing: 0.18em !important;
./chatDesign/styles/spirit-trinity-chat.css:1234:  flex-wrap: nowrap !important;
```

## Latest Evidence Files

```
docs/evidence/source-proxy-orchestrator-correction/phase-2-scoring-generalization-closeout.md
docs/evidence/source-proxy-orchestrator-correction/phase-3-generic-artifact-intent-resolver-closeout.md
docs/evidence/source-proxy-orchestrator-correction/refined-plan.md
docs/evidence/source-proxy-post-run-300/plan-1-backend-bounded-diff-preview-route-cg001-cg005-implementation.md
docs/evidence/source-proxy-post-run-300/plan-1-backend-diff-generation-gap-micro-batch-cg001-cg005.md
docs/evidence/source-proxy-post-run-300/plan-1-implementation-gate-backend-bounded-diff-preview-route.md
docs/evidence/source-proxy-post-run-300/plan-1-phase-1-1-closeout.md
docs/evidence/source-proxy-post-run-300/plan-1-phase-1-2-closeout.md
docs/evidence/source-proxy-post-run-300/plan-1-phase-1-3-increment-1-classifier-receipt-implementation.md
docs/evidence/source-proxy-post-run-300/plan-1-phase-1-3-increment-1-implementation-gate.md
docs/evidence/source-proxy-post-run-300/plan-1-phase-1-3-increment-2-staged-run-300-rerun-evidence.md
docs/evidence/source-proxy-post-run-300/plan-1-phase-1-increment-1-baseline.md
docs/evidence/source-proxy-post-run-300/plan-1-receipt-classification-contract.md
docs/evidence/source-proxy-post-run-300/plan-1-run-300-category-map.md
docs/evidence/source-proxy-post-run-300/plan-1-safety-guardrail-test-matrix.md
docs/evidence/source-proxy-remaining-levels-daily-driver-readiness-20260612/baseline-check.md
docs/evidence/source-proxy-remaining-levels-daily-driver-readiness-20260612/index.md
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/advanced-diagnostics.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_post_behavior_repair.py
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10b-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10b.html
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10b.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10b-repair-rerun-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10b-repair-rerun-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10b-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10b-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10c-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10c.html
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10c.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10c-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10c-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10c-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-before-repair-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-browser-behavior-results-before-repair.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d.html
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-level3-stabilization-before-repair-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-level3-stabilization-browser-behavior-results-before-repair.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-level3-stabilization-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-level3-stabilization.html
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-level3-stabilization-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-level3-stabilization-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-level3-stabilization-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10d-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-before-repair-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-browser-behavior-results-before-repair.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e.html
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-level3-stabilization-before-repair-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-level3-stabilization-browser-behavior-results-before-repair.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-level3-stabilization-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-level3-stabilization.html
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-level3-stabilization-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-level3-stabilization-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-level3-stabilization-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10e-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10.html
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-post-repair-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-repair-rerun-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-repair-rerun-post-behavior-repair-summary.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-rerun-browser-behavior-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-rerun-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti-tailoring-random-10-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_run_batch.py
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/batch-run-receipt.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/browser-diagnostic-results.json
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/browser_open_console_probe.mjs
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/diagnostic-summary.md
docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/index.html
docs/evidence/source-proxy-v0.2-artifact-repair-plan/acceptance-criteria.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/diagnostic-lessons.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/evidence-inventory.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/implementation-increments.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/new-chat-handoff.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/next-step-packet.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-0-baseline.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-0-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-10-final-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-10-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-1-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-1-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-2-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-2-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-3-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-3-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-4-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-4-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-5-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-5-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-6-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-6-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-7-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-7-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-8-advisory-model-limitations.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-8-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-8-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-9-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-9-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-9-proof-rerun-plan.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-9-rerun-schema.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/phase-index.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/plan-closeout.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/plan-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/qwen-local-limitations.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/README.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/risk-and-permission-rules.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/v0.2-final-findings.json
docs/evidence/source-proxy-v0.2-artifact-repair-plan/v0.2-plan.md
docs/evidence/source-proxy-v0.2-artifact-repair-plan/verification-matrix.md
docs/evidence/source-proxy-v0.2-proof-diagnostic-rerun-20260612/artifact-behavior-report.html
docs/evidence/source-proxy-v0.2-proof-diagnostic-rerun-20260612/artifact-review-summary.json
docs/evidence/source-proxy-v0.2-proof-diagnostic-rerun-20260612/behavior-check-results.json
docs/evidence/source-proxy-v0.2-proof-diagnostic-rerun-20260612/diagnostic-summary.md
docs/evidence/source-proxy-v0.2-proof-diagnostic-rerun-20260612/manifest.json
docs/evidence/source-proxy-v0.2-proof-diagnostic-rerun-20260612/rerun-findings.json
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/anti-tailoring-audit.json
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/anti-tailoring-audit.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/autonomy-readiness-recommendation.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/final-step-1-3-closeout.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/final-step-1-3-findings.json
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/index.html
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/next-action-packet.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/operator-receipt.json
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/operator-receipt.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-1-closeout.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-1-proof-audit.json
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-1-proof-audit.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-2-closeout.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-2-failure-analysis.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-2-repair-changes.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-2-weather-habit-behavior-report.html
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-2-weather-habit-rerun-summary.json
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-3-anti-cheat-report.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-3-closeout.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-3-unseen-artifact-behavior-report.html
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-3-unseen-gauntlet-results.json
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-3-unseen-gauntlet-summary.md
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-3-unseen-prompt-bank.json
docs/evidence/source-proxy-v0.2-step-1-3-audit-repair-unseen-20260612/step-receipt-skeleton.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/baseline-capture.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/baseline-capture.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/final-stabilization-closeout.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/final-stabilization-findings.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/index.html
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/next-action-packet.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/operator-receipt.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/operator-receipt.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/README.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-1-closeout.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-1-root-cause-audit.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-1-root-cause-audit.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-2-closeout.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-2-target-preview-resolution.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-2-target-preview-resolution-tests.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-3-closeout.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-3-report-evidence-hardening.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-4-closeout.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-4-needs-fix-behavior-report.html
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-4-needs-fix-rerun-prompt-list.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-4-needs-fix-rerun-results.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-4-needs-fix-summary.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-5-behavior-fail-analysis.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-5-closeout.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-5-generic-repair-changes.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-5-targeted-fail-behavior-report.html
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-5-targeted-fail-rerun-results.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-6-anti-cheat-report.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-6-closeout.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-6-full-unseen-behavior-report.html
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-6-full-unseen-rerun-results.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-6-full-unseen-summary.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-7-autonomy-readiness.json
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-7-autonomy-readiness-recommendation.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-7-closeout.md
docs/evidence/source-proxy-v0.2-unseen-stabilization-20260612/step-index.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/audit-findings.json
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/audit-summary.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/brain-layer-map.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/coding-runner-status.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/memory-context-status.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/next-plan-input-packet.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/obsidian-readiness.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/risk-and-permission-status.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/source-proxy-status.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/tests-run.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/verification-status.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612/worker-route-status.md
docs/evidence/spiritos-brain-control-plane-preflight-audit-20260612.zip
docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/allowed-paths.json
docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/anti-scaffold-rules.md
docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/increment-ledger.json
docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/phase-index.md
docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/README.md
docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/revamp-v0.1-scope.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.1.1-lane-identity-and-evidence-root.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.1.2-main-repo-and-forbidden-shared-state-paths.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.2.1-read-only-git-status-snapshot.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.2.2-diff-summary.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.3.1-active-cartographer-soak-locations.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.3.2-cartographer-soak-forbidden-declaration.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.4.1-dirty-tree-classification.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.5.1-allowed-path-matrix.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.5.2-forbidden-path-matrix.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.6.1-isolated-test-output-directory.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.6.2-evidence-packet-naming-convention.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.7.1-rollback-without-git-mutation.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.8.1-plan-0-closeout-packet.md
docs/evidence/unified-proxy-coding-design-plan-10/plan-10-14-soak-result-gate-blocked-intake.md
docs/evidence/unified-proxy-coding-design-plan-12/plan-12-14-final-css-polish-readiness-closeout.md
docs/evidence/unified-proxy-coding-design-plan-13/plan-13-14-final-css-polish-execution-closeout.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.1.1-coding-current-first-viewport-ia.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.1.2-proxy-backend-diagnostics-boundary.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.1.3-coding-component-inventory.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.1.4-coding-lib-truth-surface-inventory.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.2.1-design-system-surface-inventory.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.2.2-design-token-component-vocabulary.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.3.1-source-proxy-loop-chip-state-contract.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.3.2-no-authority-backend-route-boundaries.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.4.1-design-packet-read-only-display-fields.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.4.2-no-apply-design-bridge-contract.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.5.1-settings-drawer-contract.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.5.2-diagnostics-drawer-contract.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.5.3-evidence-drawer-contract.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.5.4-design-intake-drawer-contract.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.6.1-active-task-transcript-data-model.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.6.2-bottom-composer-boundaries.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.6.3-project-workspace-context-object.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.6.4-provider-model-truth-object.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.6.5-dirty-tree-truth-object.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.7.1-drawer-keyboard-focus-contract.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.7.2-responsive-baseline-contract.md
docs/evidence/unified-proxy-coding-design-plan-1/increment-1.8.1-plan-1-architecture-closeout.md
docs/evidence/unified-proxy-coding-design-plan-2/plan-2-14-pivot-evidence-and-closeout.md
docs/evidence/unified-proxy-coding-design-plan-3/plan-3-14-validation-evidence-and-closeout.md
docs/evidence/unified-proxy-coding-design-plan-4/plan-4-14-active-task-feature-completion-closeout.md
docs/evidence/unified-proxy-coding-design-plan-5/plan-5-14-multimedia-work-chat-lanes-closeout.md
docs/evidence/unified-proxy-coding-design-plan-6/plan-6-14-projects-read-only-integration-closeout.md
docs/evidence/unified-proxy-coding-design-plan-7/plan-7-14-settings-window-integration-closeout.md
docs/evidence/unified-proxy-coding-design-plan-8/plan-8-14-pre-soak-stabilization-closeout.md
docs/evidence/unified-proxy-coding-design-plan-9/plan-9-14-cartographer-integration-preparation-closeout.md
```

## Current / Stale / Contradictory / Unknown

- Current: Any docs/evidence paths from the latest dated Source Proxy, backup-system, and runtime audit folders above should be treated as current candidates only after line-level review before proxy work resumes.
- Stale: older proof, trial, smoke, and debug evidence is historical unless referenced by current docs.
- Contradictory: local search should be used to resolve disagreements between accepted-state docs and live runtime health; raw search files are preserved under `raw/20_*.txt`.
- Unknown: exact accepted Source Proxy state still requires Britton-level selection if multiple dated evidence roots disagree. No proxy fixes or reruns were performed.
