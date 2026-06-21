# GLM Headroom Repair Log — 2026-06-21

## Initial Headroom status

- `curl http://127.0.0.1:8797/health` → **curl exit 52 "Empty reply from server"** (HTTP_CODE 000).
- `npm run context:headroom:check` (`scripts/context/headroom-check.sh`) → `headroom_present: true (venv/cli may exist)`, `headroom_proxy_reachable: false`, exit 1.
- A process WAS listening on 8797: `netstat` showed PID **10596** on `127.0.0.1:8797` and `[::1]:8797` (LISTENING) plus a TIME_WAIT socket.

## Root cause identified (read-only diagnosis)

- **PID 10596 is `Cursor.exe`** (the editor), path `C:\Users\smith\AppData\Local\Programs\cursor\Cursor.exe`, started 2026-06-18 19:14.
- **Cursor, not Headroom, owns port 8797.** That is why `/health` returns an empty reply: the port is held by a different service speaking a different protocol.
- Headroom CLI is installed in `/z/.venv-headroom/bin/headroom` but its shebang is `#!/home/source/SpiritOS/.venv-headroom/bin/python3` — a **Linux venv**. This shell session runs under **Windows git-bash**, so the binary cannot execute here.

## Commands tried (all bounded, all documented, no source/runtime mutation)

1. `curl -fsS --max-time 5 http://127.0.0.1:8797/health` → empty reply (Cursor, not Headroom).
2. `bash ./scripts/context/headroom-check.sh` → `headroom_proxy_reachable: false`.
3. Attempted bounded start on an **alternate port** to avoid touching Cursor, exactly as the task's allowed-repair block permits (the script honors `HEADROOM_PORT`):
   - `HEADROOM_PORT=8798 HEADROOM_HOST=127.0.0.1 timeout 12 bash scripts/headroom-proxy-dev.sh > /tmp/glm-headroom-proxy.log 2>&1 &`
   - Result: `scripts/headroom-proxy-dev.sh: line 34: /z/.venv-headroom/bin/headroom: cannot execute: required file not found`
   - Cause: Linux ELF/shebang binary cannot run under Windows git-bash; rebuilding the venv would require `pip install` which the task forbids.

## What I did NOT do (per task constraints)

- Did **not** kill PID 10596 (Cursor) — it is the editor, an unrelated service. Task forbids killing unrelated services, and killing the editor would disrupt Britton's session.
- Did **not** patch Headroom code.
- Did **not** install packages or rebuild the venv.
- Did **not** create service files or mutate systemd/launchd.
- Did **not** mutate runtime state beyond the bounded, self-terminating `timeout 12` start attempt above.

## Final Headroom status

- **`BLOCKED_ENV`** — Headroom cannot be started from this Windows git-bash session because (a) port 8797 is occupied by Cursor and (b) the only installed Headroom binary is a Linux venv that cannot execute on Windows.
- No source/runtime mutation occurred. Only a self-terminating 12-second start attempt that failed before binding any port.

## Whether fallback was needed

- **Yes — fallback required and used.** Per the documented design (`scripts/context/headroom-check.sh` and `docs/context-export/headroom-verification.md`), when the proxy is unreachable the tight tree-sitter Repomix profile is the supported fallback ("Headroom adds further token savings when `npm run headroom:proxy` is running").
- For the full-repo freeze (Stage 2), GLM authored an **audit-local repomix config** that includes all relevant code/docs across repo areas while excluding binary/media/build/runtime/secrets bloat. Headroom compression was **not** applied (proxy down); tree-sitter AST compression from repomix itself **was** applied.

## Exact blocker (for the Dell Linux side, not this audit)

- To run Headroom here in the future, either:
  1. start it from the Dell's native Linux environment where `/home/source/SpiritOS/.venv-headroom/bin/headroom` can execute, AND
  2. free port 8797 (move Cursor off 8797, or set `HEADROOM_PORT` to a free port consistently across `headroom-proxy-dev.sh`, `headroom-check.sh`, and `repomix-llm.mjs`).
- Neither is in scope for this read-only audit.

## Source/runtime mutation check

- `git diff --name-status` after the bounded attempt: unchanged from before (only the two pre-existing SpiritFlix/media dirty files and the new audit output dir).
- No source files modified. No services killed. No state mutated.
