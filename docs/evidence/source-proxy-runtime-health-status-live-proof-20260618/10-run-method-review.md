# Stage 1 Run Method Review

Raw review: `raw/10-run-method-review.txt`.

## Current Source Proxy Runtime

- Runtime owner: dedicated tmux session `source-proxy-lan`.
- Tmux pane command: `bash ./scripts/source-proxy-lan-watchdog.sh`.
- Watchdog starts: `npm run proxy:https:lan`.
- Node wrapper starts: `node ./scripts/source-proxy-dev.mjs --https --lan`.
- Uvicorn command on `:8787`: `.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile ... --ssl-keyfile ...`.
- Running Source Proxy uvicorn PID before reload: `1404461`.

## Selected Reload Method

Terminate only the exact uvicorn PID listening on `:8787`, after confirming its command contains `uvicorn source_proxy.main:app` and `--port 8787`. The existing `source-proxy-lan` watchdog then restarts only `npm run proxy:https:lan`.

## Why This Is Source Proxy Only

The selected PID is the listener for port `8787` and is a child of the dedicated `source-proxy-lan` watchdog tree. It is separate from Next on `:3000`, Ollama on `:11434`, Docker, Jellyfin, SearXNG, CasaOS, and spirit-whisper. No broad `pkill`/`killall` pattern was used by this task.
