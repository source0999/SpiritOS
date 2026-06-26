# Plan 5 Increment 5.2.1 - Scoped Apply Gate Approval Retry

Status: `RESOLVED_BY_SCOPED_RUNTIME_GATE_PROOF`.

## Human Decision Received

Britton explicitly approved a scoped Plan 5 apply gate decision for increment `5.2.1` only.

This approval is not broad apply authority, not Plan 6 approval, not package/env/secrets authority, and not permission to bypass Source Proxy central gate logic.

## Gate Mechanism Inspected

The official gate remains `source_proxy/approval/external_gate.py`.

`central_gate_check("apply")` requires:

- gate state status `APPROVED_INCREMENT` or `RUNNING_INCREMENT`
- `approved_increment` matching the requested/default increment
- non-empty `approval_token`
- `SOURCE_PROXY_GATE_ALLOWED_ACTIONS` containing `apply`

When the caller does not pass an increment id, the gate uses `SOURCE_PROXY_GATE_INCREMENT`, falling back to `1.3`.

## Live Runtime Finding

The running Source Proxy process is:

```text
/home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile /home/source/SpiritOS/certificates/spirit-dev.pem --ssl-keyfile /home/source/SpiritOS/certificates/spirit-dev-key.pem
```

The running process environment does not expose:

- `SOURCE_PROXY_GATE_ALLOWED_ACTIONS=apply`
- `SOURCE_PROXY_GATE_INCREMENT=5.2.1`

The live `.gate/state.json` remains:

```json
{
  "status": "RUNNING_INCREMENT",
  "approved_increment": "evaluation-round",
  "last_completed_increment": "2.4",
  "approval_token": "evaluation-round:temporary-model-call-eval",
  "updated_at": "2026-06-09T01:51:51.277Z",
  "notes": "Temporary model_call approval for messy prompt evaluation; no apply approval."
}
```

Updating only `.gate/state.json` would not satisfy the existing gate, because the allowed action list is read from the running process environment.

## Live Proof Retry

No live apply retry was performed in the original scoped approval retry turn.

Reason: satisfying the existing central gate requires changing the running Source Proxy process environment, which requires a runtime restart or equivalent process replacement. Britton approved the scoped 5.2.1 gate decision, but did not separately approve runtime interruption.

Britton subsequently approved that scoped Source Proxy runtime restart/replacement for increment `5.2.1` only. The productive live proof is recorded in:

`docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-05/increment-5-2-1-scoped-runtime-gate-live-proof-20260626.md`

## Required Operator Action

To retry 5.2.1 productively without bypassing the gate, Britton must separately approve a Source Proxy runtime restart or equivalent operator-managed process replacement with a scoped gate configuration:

```text
SOURCE_PROXY_GATE_INCREMENT=5.2.1
SOURCE_PROXY_GATE_ALLOWED_ACTIONS=apply
```

The gate state must also be updated to a matching scoped Plan 5 approval before the retry:

```json
{
  "status": "RUNNING_INCREMENT",
  "approved_increment": "5.2.1",
  "approval_token": "plan5-5.2.1-<fresh-token>",
  "notes": "Scoped Plan 5 5.2.1 apply proof only; proof target under plan-05 docs only."
}
```

That operator action must preserve the existing HTTPS Source Proxy route and must not grant package, env, secrets, generated XML, media, SpiritFlix, Obsidian, Plan 6, commit, or push authority.

## Current Verdict

Increment `5.2.1` is now GO by superseding scoped runtime proof.

Current status:

`PLAN5_INCREMENT_5_2_1_GO`
