# Integrated Level 6 Runtime Preflight

Date: 2026-06-15

Status: PLANNED_NOT_STARTED

No Level 6 implementation or matrix run was started.

## Purpose

These are the exact checks to run before any Britton-approved Level 6 implementation or matrix run. They are listed here for readiness only.

## Required Preflight Checks

Run from the repo root unless the command explicitly targets the Linux runtime checkout.

### 1. Confirm clean git tree

```text
git status --short
git status --branch --short
git log -1 --oneline --decorate
```

Expected:

- `git status --short` prints nothing.
- Branch is the expected branch.
- Latest commit hash is recorded in the Level 6 matrix JSON and closeout.

If dirty, stop with `NEEDS_REVIEW` and list exact dirty files. Do not write implementation files.

### 2. Confirm one Source Proxy uvicorn process on port 8787

```text
ssh source@10.0.0.186 "hostname; cd /home/source/SpiritOS && pgrep -af 'source_proxy.main:app|proxy:https:lan'; ss -ltnp '( sport = :8787 )'"
```

Expected:

- hostname is `source-server`;
- active checkout is `/home/source/SpiritOS`;
- exactly one `source_proxy.main:app` uvicorn process is listening on `:8787`;
- no duplicate Source Proxy runtime is competing for the port.

### 3. Confirm latest receipt endpoint

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python - <<'PY'
import httpx
r = httpx.get('https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest', verify=False, timeout=30)
print(r.status_code)
print(r.json().get('run_id'))
print(r.json().get('final_verdict'))
PY"
```

Expected:

- HTTP `200`;
- run ID and final verdict are recorded in preflight output.

### 4. Confirm latest trace endpoint

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python - <<'PY'
import httpx
r = httpx.get('https://127.0.0.1:8787/v1/decisions/fip0-receipts/latest/trace', verify=False, timeout=30)
data = r.json()
print(r.status_code)
print(data.get('run_id'))
print(data.get('final_verdict'))
print(data.get('trace_version'))
print(data.get('trace_authority'))
PY"
```

Expected:

- HTTP `200`;
- trace version is `fip6.operator_trace.v1`;
- trace authority is `operational_receipt_projection_no_private_reasoning`;
- latest trace run ID and verdict match latest receipt.

### 5. Confirm local model availability truth is recordable

```text
ssh source@10.0.0.186 "ollama list"
```

Expected:

- available local models are recorded before the run;
- absence, timeout, or model error is not treated as hidden fallback approval;
- expected models include the currently wired Qwen/Hermes/Gemma aliases where available.

### 6. Confirm Scout/SearXNG availability truth is recordable

Use existing runtime diagnostics or a read-only local endpoint check approved by the implementation prompt. The preflight result must record:

- Scout reachable/unreachable;
- Scout no-allowed-packets behavior if reachable;
- SearXNG reachable/unreachable;
- whether a local SearXNG provider query can return usable http/https results;
- any timeout/error classification.

Scout/SearXNG must not be marked `used` unless a real allowed Scout packet or live local SearXNG provider query is present in the row receipt.

### 7. Confirm npm typecheck command

```text
npm run typecheck -- --pretty false
```

Expected:

- passes before implementation or run;
- if it fails before implementation, classify as `config_blocked` for Level 6 readiness and stop.

### 8. Confirm focused pytest command

```text
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_scout_research_bridge.py -q"
```

Expected:

- passes before implementation or run.
- Last accepted baseline was `67 passed`.

### 9. Confirm diff hygiene

```text
git diff --check
```

Expected:

- exit `0`;
- CRLF warnings may be recorded if non-fatal and already known;
- no whitespace errors introduced by Level 6.

## Run-Time Evidence Checks

During the approved Level 6 matrix run, every row must perform:

- POST result capture;
- durable receipt retrieval by run ID;
- FIP-6 trace retrieval by run ID;
- latest receipt endpoint check after the row;
- latest trace endpoint check after the row;
- trace matches receipt check;
- trace private-reasoning leak scan;
- latest artifact freshness check;
- allowed mutation scope check.

## Post-Run Verification Checks

After the approved Level 6 run:

```text
npm run typecheck -- --pretty false
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py source_proxy/tests/test_scout_research_bridge.py -q"
git diff --check
git status --short
```

Expected:

- typecheck passes;
- focused pytest passes;
- diff check passes;
- git status shows only expected Level 6 evidence and approved implementation files, if implementation was approved.
