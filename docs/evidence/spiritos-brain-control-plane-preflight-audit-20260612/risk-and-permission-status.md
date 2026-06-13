# Risk And Permission Status

## Where The System Asks Britton Before Action

Approval/gate surfaces:

- `/v1/chat/completions` requires `central_gate_check("model_call")`.
- Paid provider calls require spend-before-send approval.
- `/v1/tasks/long-running/{task_id}/execute-approved` requires `approved: true`, `approval_id`, `approved_by`, and approved diff.
- Diff preview says human review is required before apply.
- Codex route validates envelopes and returns `would_run_task: false`.
- Sandbox terminal reports `writes_allowed: false`.
- Cartographer has approval-token, approval-preview, safe-write, commit/push proposal, and apply-approved surfaces.

## Where It Acts Without Approval

Allowed without user approval in current code:

- read-only status manifests
- route/prompt-packet previews
- Obsidian read-only queries
- context inventory/index manifests
- deterministic bounded diff previews
- durable run store writes from `/coding`
- local preview-only route responses
- sandbox command execution in read-only bubblewrap if endpoint is called

This audit did not call mutating app routes other than creating audit docs.

## Inconsistent Approval Areas

- Cartographer has many authority-looking endpoints; some are dry-run/preview, others are apply/approve flows. They need a single current authority matrix before revamp.
- `/coding` has both UI-local preview state and durable server state; labels can blur preview vs apply vs behavior.
- Evidence docs sometimes use GO/PASS in ways that do not map to current product behavior proof.

## Fake-Green/Fake-Pass Risk

High-risk patterns:

- artifact exists but product behavior untested
- diff preview ready but no browser/product check
- class/theme toggle without visible change
- static component marked functional
- no-diff collapsed into generic pass
- configured model treated as successful model call
- docs/evidence intent treated as code wiring
- Obsidian note existence treated as memory readiness

## Protected File/Path Rules

`source_proxy/safety/paths.py` blocks:

- `.env`, `.pem`, `.key`, secret/token/credential names
- id_rsa/id_ed25519
- absolute paths
- UNC paths
- path escape with `..`
- percent-encoded path syntax

`source_proxy/verification/diff.py` treats package/config/runtime files as higher risk.

## Local Vs High-Usage Escalation

Current paid provider calls have spend-before-send approval and central model-call gate. A future basal ganglia layer should ask before high-usage API routes, live Codex tasks, local long-running jobs, or multi-worker lanes.

## Obsidian Boundaries

Current Obsidian reads:

- read-only
- include/exclude glob bounded
- safe excerpts
- secret-shaped redaction

Current Obsidian writes:

- not implemented
- no write audit or approval path

Future memory write-back must require Britton approval and preview note diffs.

## Memory Write-Back

Not ready for automatic memory write-back. Evidence docs and durable run store should remain proof-of-record. Obsidian can receive approved summaries only after a note schema, evidence links, and approval workflow exist.

## Grade

Risk/permission grade: PARTIAL

## Amygdala + Prefrontal v0.1 Requires

- Unified authority matrix for reads, context injection, model calls, workers, apply, git, memory writes, and evidence writes.
- Canonical result labels that cannot mark behavior PASS without behavior proof.
- Approval-gated Obsidian write-back.
- Risk scoring that accounts for user frustration, stale evidence, protected paths, high-cost routes, and workflow conflicts.
- Tests proving each forbidden action fails closed.
