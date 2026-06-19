# Process Cleanup

Britton approved narrow cleanup of only the runaway broad pytest processes started by this task.

## Verification before kill

Command:

```text
ps -fp 1121819 1121820 1236622 1236623 || true
```

Verified processes:

- `1121819`: wrapper shell for `.venv-source-proxy/bin/python -m pytest -q source_proxy/tests`
- `1121820`: `.venv-source-proxy/bin/python -m pytest -q source_proxy/tests`
- `1236622`: wrapper shell for `SOURCE_PROXY_GATE_INCREMENT=evaluation-round ... pytest -q source_proxy/tests`
- `1236623`: `.venv-source-proxy/bin/python -m pytest -q source_proxy/tests`

All four were runaway broad pytest processes started by this runtime health/status task.

## Cleanup action

Command:

```text
kill 1121820 1236623 1121819 1236622 2>/dev/null || true
sleep 3
ps -fp 1121819 1121820 1236622 1236623 || true
```

Result: graceful termination succeeded. No matching processes remained. `kill -9` was not used.

No Source Proxy, Next, Ollama, Docker, systemd, tmux, Jellyfin, SearXNG, CasaOS, spirit-whisper, or unrelated Python/node process was killed.
