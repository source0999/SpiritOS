# Increment 9.1 - Preflight and Proof Target Selection

## P - Preflight

Repo path:

- `Z:\`

Allowed files:

- `docs/evidence/spiritos-cognitive-control-plane-revamp-v0.1/**`

Forbidden files/actions:

- source code edits outside the evidence root
- production UI changes
- Source Proxy behavior changes
- worker execution
- provider/model calls
- Obsidian writes
- git mutation
- generated benchmark artifact mutation
- `execute-approved` route calls
- sandbox terminal command execution
- safe-write execution
- workflow runner execution
- artifact file mutation

Commands run:

- `git status --short`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-index.md -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-8\phase-8-closeout.md -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-8\integrated-dry-run-adapter-map.json -Raw`
- `rg -n "timer|00:02|00:00|start timer|Stop|pass-preservation|artifact|preview" docs\evidence -g "*.md" -g "*.json" -g "*.txt"`
- `rg --files | rg -i "timer|artifact|preview|diagnostic|benchmark|generated"`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-6\behavior-fixture-contract.json -Raw`
- `Get-Content docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1\phase-8\integrated-dry-run-examples.json -Raw`
- `rg -n "timer changed|00:00.*00:02|00:02.*Stop|start.*stop.*timer|timer.*PASS|timer.*FAIL|timer-false-negative" docs\evidence\source-proxy-tool-action-runtime-v1 docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1 docs\evidence\source-proxy-orchestrator-correction -g "*.json" -g "*.md" -g "*.txt"`
- `Get-ChildItem docs\evidence -Recurse -File -Filter *.html -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'timer|source-proxy-tool-action-runtime|artifact|preview' }`
- `Get-Content docs\evidence\source-proxy-general-intelligence-diagnostic-20260612\runs\01-make-a-timer-app\workspace\index.html -Raw`
- `Get-ChildItem docs\evidence\source-proxy-general-intelligence-diagnostic-20260612\runs\01-make-a-timer-app -Recurse -File`
- `rg -n "timer|00:00|Start|Stop|workspace/index.html|01-make-a-timer-app" docs\evidence\source-proxy-general-intelligence-diagnostic-20260612 docs\evidence\spiritos-cognitive-control-plane-revamp-v0.1 -g "*.md" -g "*.json" -g "*.txt" -g "*.html"`

## I - Implement

Selected the timer pass-preservation fixture and located its exact static artifact path.

Artifact selected:

- `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/runs/01-make-a-timer-app/workspace/index.html`

Related source files:

- `workspace/index.html`
- `workspace/script.js`
- `workspace/styles.css`

Historical note:

- `docs/evidence/source-proxy-general-intelligence-diagnostic-20260612/diagnostic-summary.md` marked `make a timer app` as `FAIL` with `timer_controls_or_ticking_logic_missing`.
- Read-only inspection found the artifact does include `#timer`, `#startBtn`, `#stopBtn`, and JavaScript tick/stop logic.

## V - Verify

Static/manual checks:

- Exact artifact path exists.
- Artifact includes timer display and Start/Stop controls.
- Artifact includes linked `script.js`.
- `script.js` includes interval-based timer increment and stop logic.

## O - Observe

Changed files:

- `phase-9/phase-9-plan.md`
- `phase-9/increment-9.1-preflight-and-proof-target-selection.md`
- `phase-9/controlled-live-proof-target.json`

## T - Triage

Verdict: GO

Reason:

- Exact target artifact was found and is eligible for a non-mutating controlled proof.

Next authorized increment:

- Increment 9.2 - Timer controlled live proof
