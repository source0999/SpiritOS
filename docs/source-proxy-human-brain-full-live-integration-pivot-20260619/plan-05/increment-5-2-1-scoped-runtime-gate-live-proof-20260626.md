# Plan 5 Increment 5.2.1 - Scoped Runtime Gate Live Proof

Status: `GO`.

## Scope

Britton approved a scoped Source Proxy runtime restart/replacement for Plan 5 increment `5.2.1` only, to install the already-approved apply gate into the running Source Proxy process environment.

This proof did not grant broad apply authority, commit authority, push authority, Plan 6 authority, package/env/secrets authority, or generated-pack authority.

## Runtime Before Scoped Replacement

Before replacement, Source Proxy was listening on `:8787` without scoped apply environment:

```text
PID: 3847245
Command: /home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile /home/source/SpiritOS/certificates/spirit-dev.pem --ssl-keyfile /home/source/SpiritOS/certificates/spirit-dev-key.pem
Environment summary: SPIRIT_PROJECT_PATH=<set>; no SOURCE_PROXY_GATE_INCREMENT; no SOURCE_PROXY_GATE_ALLOWED_ACTIONS
```

Pre-restart `.gate/state.json` was preserved at `/tmp/plan5-521-runtime/state.before.json` and contained the prior `evaluation-round` temporary model-call gate with no apply approval.

## Scoped Gate Installed

The scoped gate state was set to:

```json
{
  "status": "RUNNING_INCREMENT",
  "approved_increment": "5.2.1",
  "last_completed_increment": "5.1.2",
  "approval_token": "plan5-5.2.1-scoped-apply-proof-20260626",
  "notes": "Scoped Plan 5 5.2.1 apply proof only; proof target under plan-05 docs only. Restore immediately after proof."
}
```

The first direct scoped listener was healthy but was replaced by the existing Source Proxy LAN watchdog. The watchdog was then paused for this proof window only, and a detached scoped Source Proxy listener was started.

Exact scoped runtime command recorded at `/tmp/plan5-521-runtime/scoped.detached.command.txt`:

```text
cd /home/source/SpiritOS && setsid -f env SPIRIT_PROJECT_PATH=/home/source/SpiritOS SOURCE_PROXY_GATE_INCREMENT=5.2.1 SOURCE_PROXY_GATE_ALLOWED_ACTIONS=apply /home/source/SpiritOS/.venv-source-proxy/bin/python -m uvicorn source_proxy.main:app --host 0.0.0.0 --port 8787 --ssl-certfile /home/source/SpiritOS/certificates/spirit-dev.pem --ssl-keyfile /home/source/SpiritOS/certificates/spirit-dev-key.pem > /tmp/plan5-521-runtime/scoped.detached.log 2>&1 < /dev/null
```

Scoped listener proof:

```text
Source Proxy listener PID: 3389789
Health: https://127.0.0.1:8787/v1/self/status -> 200
Environment:
SPIRIT_PROJECT_PATH=<set>
SOURCE_PROXY_GATE_INCREMENT=5.2.1
SOURCE_PROXY_GATE_ALLOWED_ACTIONS=apply
```

The watchdog pause also stopped the existing Next `:3000` listener. Next was restored with the prior dev command and separately health-checked before the proof was counted:

```text
cd /home/source/SpiritOS && npm run dev:https:lan
https://127.0.0.1:3000/ -> 200
```

## Canonical Live Proof

Target route:

```text
https://127.0.0.1:3000/v1/actions/execute-approved
```

Source Proxy route reached by Next:

```text
https://127.0.0.1:8787/v1/tasks/long-running/{task_id}/execute-approved
```

Harmless proof target:

```text
docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-05/live-acceptance-target-20260625.txt
```

Approved diff changed only:

```text
PLAN5_5_2_1_LIVE_ACCEPTANCE_TARGET=before
```

to:

```text
PLAN5_5_2_1_LIVE_ACCEPTANCE_TARGET=after
```

Live result:

```text
HTTP status: 200
Task id: task_5a15fd142a97
Trace id: trace_86d67929bf7f4ddf
Execution invocation event id: invocation_c980bb063c974436
Execution consumer event id: consumer_8327bf46c5f246d4
Final task status: applied_needs_verification
Approved diff sha256: 4188e65b51d07e213917e4c788e27922ceefedf424bac503742e31e56734146e
Accepted output hash: ff31dc495813357b81cb517afc2656f6c1d527fd8217606f1899c754848a5641
```

The target file was read after the route returned and contained:

```text
PLAN5_5_2_1_LIVE_ACCEPTANCE_TARGET=after
```

No commit or push was performed by the live route.

## Downstream Consumption

The live execute-approved output was consumed by the operator surface record and then by the Plan 5 phase verifier on the same trace.

Operator consumption:

```text
Subsystem: source_proxy_execute_approved
Consumer subsystem: coding_operator_surface
Consumer event id: consumer_12402fbcc8e4411f
Changed state fields:
- ast_snapshot.plan_5_acceptance.source_proxy_execute_approved
- status
```

Phase verifier consumption:

```text
Subsystem: plan5_phase_verifier
Consumer subsystem: plan5_phase_acceptance_consumer
Phase verifier invocation event id: invocation_798ab5b1e19c49e2
Phase verifier consumer event id: consumer_fc85786f835d4e4e
Accepted output hash input: ff31dc495813357b81cb517afc2656f6c1d527fd8217606f1899c754848a5641
Changed state fields:
- ast_snapshot.plan_5_acceptance.phase_verifier
- status
```

Plan 5 phase gate:

```text
Status: GO
Failures: []
Output consumed by operator: true
Output consumed by phase verifier: true
Same trace: true
Forbidden states: []
```

Raw local runtime artifacts:

```text
/tmp/plan5-521-runtime/live-proof-success.json
/tmp/plan5-521-runtime/health.scoped.detached.json
/tmp/plan5-521-runtime/listeners.scoped.detached.txt
/tmp/plan5-521-runtime/env.scoped.detached.summary.txt
```

## Runtime Restore

After proof, the authority window was closed.

Restore command recorded at `/tmp/plan5-521-runtime/restore.command.txt`:

```text
cd /home/source/SpiritOS && nohup bash ./scripts/source-proxy-lan-watchdog.sh >> /home/source/source-proxy-https-lan.log 2>&1 < /dev/null &
```

Restored state:

```text
Source Proxy health: https://127.0.0.1:8787/v1/self/status -> 200
Restored listener PID: 3392272
Restored environment: SPIRIT_PROJECT_PATH=<set>; no SOURCE_PROXY_GATE_INCREMENT; no SOURCE_PROXY_GATE_ALLOWED_ACTIONS
Next listener present: true
```

Restored `.gate/state.json`:

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

## Post-Restore Blocked Apply Probe

After restore, a second apply attempt tried to change the same proof target from `after` to `blocked-probe`.

Result:

```text
Route: https://127.0.0.1:3000/v1/actions/execute-approved
HTTP status: 500
Task id: task_df08d44a0a39
No mutation: true
Target remained: PLAN5_5_2_1_LIVE_ACCEPTANCE_TARGET=after
```

Task readback showed a central-gate failure and readback consumer event:

```text
Trace id: trace_19dce15058134da2
Invocation event id: invocation_28e46b9af6b3443a
Failure event id: failure_cbc9d44be5e74965
Consumer event id: consumer_8e36d14a009e4e3f
Status after: failed_needs_human
Failure note: central gate blocked apply
```

Raw blocked-probe artifact:

```text
/tmp/plan5-521-runtime/post-restore-blocked-proof.json
```

## Self-Check Against Plan 5

- Live canonical route used: yes.
- Source Proxy canonical handler invoked: yes.
- Real output produced: yes, approved diff applied to the harmless Plan 5 proof target.
- Output consumed downstream: yes, by `coding_operator_surface` and `plan5_phase_acceptance_consumer`.
- Required causal fields present: task id, trace id, invocation event id, consumer event id, consumer subsystem, state fields changed, focused checks, git status, evidence budget status.
- Render-level/operator-surface caveat carried forward: existing focused `/coding` render assertion remains required in validation.
- Linux-path test refresh carried forward: focused tests must run from `/home/source/SpiritOS`.
- No preview-only, advisory-only, fixture-only, read-only, unconsumed, or fake productive GO.
- Scoped apply authority revoked after proof: yes.
- Non-approved apply blocked again after restore: yes.
- Plan 6 started: no.

## Verdict

Increment `5.2.1`: `GO`.
