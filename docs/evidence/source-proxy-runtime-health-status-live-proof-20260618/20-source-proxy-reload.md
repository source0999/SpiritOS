# Stage 2 Source Proxy Reload

Raw files:

- `raw/20-before-source-proxy-reload.txt`
- `raw/20-reload-command.txt`
- `raw/20-after-source-proxy-reload.txt`

## Reload Method

`kill -TERM 1404461` was sent only after confirming PID `1404461` was the uvicorn process for `source_proxy.main:app` on port `8787`. The dedicated `source-proxy-lan` watchdog restarted `npm run proxy:https:lan`.

## PID Evidence

- Before reload uvicorn PID: `1404461`
- After reload uvicorn PID: `1440463`

## Result

Source Proxy reload: `GO`. The listener on `:8787` moved from PID `1404461` to PID `1440463` under the same `source-proxy-lan` watchdog tree.

No Next, Ollama, Docker, Jellyfin, SearXNG, CasaOS, or spirit-whisper restart was performed.
